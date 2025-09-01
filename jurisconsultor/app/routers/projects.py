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
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User is not associated with a company.")
        
    project_dict = project.dict()
    project_dict["company_id"] = current_user.company_id
    project_dict["owner_email"] = current_user.email
    project_dict["members"] = [current_user.email] # Owner is a member by default
    
    result = db.projects.insert_one(project_dict)
    created_project = db.projects.find_one({"_id": result.inserted_id})
    
    return ProjectInDB.parse_obj(created_project)

@router.get("/", response_model=List[ProjectInDB])
def list_projects(db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """List all projects for the user's company where the user is a member."""
    if not current_user.company_id:
        return [] # Or raise an error, returning empty list is safer
        
    projects = db.projects.find({
        "company_id": current_user.company_id,
        "members": current_user.email
    })
    return [ProjectInDB.parse_obj(p) for p in projects]