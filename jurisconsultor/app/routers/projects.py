
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from typing import List

from app.models import ProjectCreate, ProjectInDB, UserInDB
from app.dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.post("/", response_model=ProjectInDB, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """Create a new project. The owner is the currently logged-in user."""
    project_dict = project.dict()
    project_dict["owner_email"] = current_user.email
    project_dict["members"] = [current_user.email] # Owner is a member by default
    
    result = db.projects.insert_one(project_dict)
    created_project = db.projects.find_one({"_id": result.inserted_id})
    
    return ProjectInDB.parse_obj(created_project)

@router.get("/", response_model=List[ProjectInDB])
def list_projects(db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """List all projects where the current user is a member or the owner."""
    projects = db.projects.find({"members": current_user.email})
    return [ProjectInDB.parse_obj(p) for p in projects]
