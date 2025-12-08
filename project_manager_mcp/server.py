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

import traceback

# --- Database Connection (MCP Server will connect to tenant DBs) ---
def get_tenant_db_connection(tenant_id: str):
    """
    Connects to the tenant's private database.
    First, connects to the Public DB to find the tenant's 'mongo_uri'.
    Then, connects to that URI.
    """
    try:
        # 1. Connect to Public DB
        public_mongo_uri = os.getenv("MONGO_URI") # Main/Public DB URI from env
        public_db_name = os.getenv("MONGO_DB_NAME", "jurisconsultor")
        
        if not public_mongo_uri:
             logger.error("Public MONGO_URI not found in env.")
             raise HTTPException(status_code=500, detail="Public MONGO_URI not found in env.")

        client_public = MongoClient(public_mongo_uri)
        db_public = client_public[public_db_name]
        
        # 2. Lookup Tenant
        company = None
        try:
            # Try finding by string ID first, then ObjectId
            logger.info(f"Looking for tenant {tenant_id}...")
            company = db_public.companies.find_one({"_id": ObjectId(tenant_id)})
        except:
            logger.warning(f"Could not convert {tenant_id} to ObjectId. Trying as string.")
            company = db_public.companies.find_one({"_id": tenant_id})
            
        if not company:
            client_public.close()
            logger.error(f"Tenant {tenant_id} not found in public directory.")
            raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found in public directory.")

        # 3. Get Private URI
        private_mongo_uri = company.get("mongo_uri")
        private_db_name = company.get("mongo_db_name")

        # Fallback for legacy static tenants (mi_primera_empresa) if migration script didn't run
        if not private_mongo_uri:
            # Check if it is the legacy hardcoded one
            if company.get("name") == "Mi Primera Empresa" or tenant_id == "69095aeed381a1dfeca80d50":
                 # Use the manual env var fallback
                 tenant_slug = "mi_primera_empresa"
                 tenant_id_upper = tenant_slug.upper()
                 mongo_user = os.getenv(f"TENANT_{tenant_id_upper}_MONGO_USER")
                 mongo_pass = os.getenv(f"TENANT_{tenant_id_upper}_MONGO_PASSWORD")
                 mongo_db = os.getenv(f"TENANT_{tenant_id_upper}_MONGO_DB")
                 if all([mongo_user, mongo_pass, mongo_db]):
                      private_mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@mongodb_{tenant_slug}:27017/{mongo_db}?authSource=admin"
                      private_db_name = mongo_db
        
        client_public.close()

        if not private_mongo_uri:
             logger.error(f"Tenant {tenant_id} validation failed: No 'mongo_uri' found.")
             raise HTTPException(status_code=500, detail=f"Tenant {tenant_id} validation failed: No 'mongo_uri' found and not a legacy tenant.")

        # 4. Connect to Private DB
        logger.info(f"Connecting to private DB: {private_db_name}")
        client_private = MongoClient(private_mongo_uri)
        db_private = client_private[private_db_name if private_db_name else "test"] # fallback name if missing

        return {"mongo": db_private, "postgres": None}
    except Exception as e:
        traceback.print_exc()
        raise e

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
        traceback.print_exc()
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
