import os
import json
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from pymongo import MongoClient
from psycopg2 import connect
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
from datetime import datetime # Import datetime
from bson import ObjectId # Import ObjectId for MongoDB ObjectIds

# Setup logger for this module
logger = logging.getLogger(__name__)

# Load environment variables from the project root .env file
load_dotenv()

app = FastAPI(
    title="Project Manager MCP Server",
    description="MCP Server for Project and Task Management Tools.",
    version="0.1.0",
)

# --- Database Connection (MCP Server will connect to tenant DBs) ---
def get_tenant_db_connection(tenant_id: str):
    # HOTFIX: Map specific ObjectId to tenant slug for the demo environment
    if tenant_id == "69095aeed381a1dfeca80d50":
        tenant_id = "mi_primera_empresa"

    tenant_id_upper = tenant_id.upper().replace('-', '_') # Ensure valid env var name

    # MongoDB connection
    mongo_user = os.getenv(f"TENANT_{tenant_id_upper}_MONGO_USER")
    mongo_pass = os.getenv(f"TENANT_{tenant_id_upper}_MONGO_PASSWORD")
    mongo_db = os.getenv(f"TENANT_{tenant_id_upper}_MONGO_DB")
    
    if not all([mongo_user, mongo_pass, mongo_db]):
        raise HTTPException(status_code=500, detail=f"MongoDB credentials for tenant {tenant_id} not found.")
    
    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@mongodb_{tenant_id}:27017/{mongo_db}?authSource=admin"
    mongo_client = MongoClient(mongo_uri)
    mongo_db_conn = mongo_client[mongo_db]

    # PostgreSQL connection (not used by these tools, but kept for completeness)
    pg_user = os.getenv(f"TENANT_{tenant_id_upper}_POSTGRES_USER")
    pg_pass = os.getenv(f"TENANT_{tenant_id_upper}_POSTGRES_PASSWORD")
    pg_db = os.getenv(f"TENANT_{tenant_id_upper}_POSTGRES_DB")

    # We don't raise an error if PG credentials are not found, as these tools only use Mongo
    pg_conn = None
    if all([pg_user, pg_pass, pg_db]):
        pg_uri = f"postgresql://{pg_user}:{pg_pass}@postgres_{tenant_id}:5432/{pg_db}"
        pg_conn = connect(pg_uri)

    return {"mongo": mongo_db_conn, "postgres": pg_conn}


# --- MCP Tools (exposed as API endpoints) ---

from pydantic import BaseModel

class CreateProjectRequest(BaseModel):
    project_name: str
    tenant_id: str
    user_email: str # Added user_email to associate the project with a user
    project_description: Optional[str] = None

class CreateTaskRequest(BaseModel):
    project_id: str
    title: str
    tenant_id: str
    description: Optional[str] = None

@app.post("/tools/create_project")
async def create_project_tool(request: CreateProjectRequest):
    """Crea un nuevo proyecto en el sistema de gestión legal para un tenant específico."""
    try:
        tenant_id = request.tenant_id
        db_conns = get_tenant_db_connection(tenant_id)
        mongo_db = db_conns["mongo"]
        
        project_doc = {
            "name": request.project_name,
            "description": request.project_description,
            "company_id": tenant_id,
            "owner_email": request.user_email, # Use the user's email from the request
            "members": [request.user_email], # Add the user as the first member
            "created_at": datetime.utcnow(),
            "is_archived": False # Explicitly set is_archived to False on creation
        }
        
        result = mongo_db.projects.insert_one(project_doc)
        project_id = str(result.inserted_id)
        
        return {"success": True, "project_id": project_id, "project_name": request.project_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {e}")

@app.get("/tools/list_projects")
async def list_projects_tool(tenant_id: str):
    """Lista todos los proyectos disponibles para un tenant específico."""
    try:
        db_conns = get_tenant_db_connection(tenant_id)
        mongo_db = db_conns["mongo"]
        
        projects_cursor = mongo_db.projects.find({
            "$or": [
                {"company_id": tenant_id},
                {"company_id": ObjectId(tenant_id)}
            ]
        })
        projects_list = []
        for project in projects_cursor:
            project["_id"] = str(project["_id"]) # Convert ObjectId to string
            if isinstance(project.get("company_id"), ObjectId):
                project["company_id"] = str(project["company_id"])
            projects_list.append(project)
            
        return {"success": True, "projects": projects_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {e}")

@app.post("/tools/create_task")
async def create_task_tool(request: CreateTaskRequest):
    """Crea una nueva tarea para un proyecto dado en el sistema de gestión legal para un tenant específico."""
    try:
        tenant_id = request.tenant_id
        project_id = request.project_id
        
        db_conns = get_tenant_db_connection(tenant_id)
        mongo_db = db_conns["mongo"]
        
        # Verify project exists and belongs to tenant
        project = mongo_db.projects.find_one({
            "_id": ObjectId(project_id),
            "$or": [{"company_id": tenant_id}, {"company_id": ObjectId(tenant_id)}]
        })
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found for tenant {tenant_id}.")

        task_doc = {
            "project_id": ObjectId(project_id),
            "title": request.title,
            "description": request.description,
            "creator_email": "system@mcp.com", # Placeholder
            "assignee_email": None,
            "status": "todo",
            "created_at": datetime.utcnow()
        }
        
        result = mongo_db.tasks.insert_one(task_doc)
        task_id = str(result.inserted_id)
        
        return {"success": True, "task_id": task_id, "task_title": request.title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {e}")

@app.get("/tools/list_tasks_for_project")
async def list_tasks_for_project_tool(project_id: str, tenant_id: str):
    """Lista todas las tareas para un proyecto dado en el sistema de gestión legal para un tenant específico."""
    try:
        db_conns = get_tenant_db_connection(tenant_id)
        mongo_db = db_conns["mongo"]
        
        # Verify project exists and belongs to tenant
        project = mongo_db.projects.find_one({
            "_id": ObjectId(project_id),
            "$or": [{"company_id": tenant_id}, {"company_id": ObjectId(tenant_id)}]
        })
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found for tenant {tenant_id}.")
        
        # Find all tasks for this project
        tasks_cursor = mongo_db.tasks.find({"project_id": ObjectId(project_id)})
        tasks_list = []
        for task in tasks_cursor:
            task["_id"] = str(task["_id"])  # Convert ObjectId to string
            task["project_id"] = str(task["project_id"])  # Convert ObjectId to string
            tasks_list.append(task)
        
        return {"success": True, "tasks": tasks_list, "project_id": project_id}
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks for project {project_id}: {e}")
