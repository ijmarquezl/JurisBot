from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from typing import List

from app.models import ProjectCreate, ProjectInDB, UserInDB, PyObjectId
from app.dependencies import get_db, get_current_user, get_project_lead_user

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
    
    return ProjectInDB(**created_project)

@router.get("/", response_model=List[ProjectInDB])
def list_projects(db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """List all projects for the user's company where the user is a member."""
    if not current_user.company_id:
        return [] # Or raise an error, returning empty list is safer
        
    projects_cursor = db.projects.find({
        "company_id": {"$in": [str(current_user.company_id), current_user.company_id]},
        "members": current_user.email
    })
    return [ProjectInDB(**p) for p in projects_cursor]

@router.post("/{project_id}/members", response_model=ProjectInDB)
def add_project_member(
    project_id: PyObjectId,
    member_email: str,
    db: Database = Depends(get_db),
    lead_user: UserInDB = Depends(get_project_lead_user),
):
    """Adds a user to a project. Only admins or project leads can add members."""
    project = db.projects.find_one({"_id": project_id, "company_id": {"$in": [str(lead_user.company_id), lead_user.company_id]}})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this company.")

    user_to_add = db.users.find_one({"email": member_email, "company_id": {"$in": [str(lead_user.company_id), lead_user.company_id]}})
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User to add not found in this company.")

    db.projects.update_one(
        {"_id": project_id},
        {"$addToSet": {"members": member_email}}
    )
    
    updated_project = db.projects.find_one({"_id": project_id})
    return ProjectInDB(**updated_project)

@router.delete("/{project_id}/members", response_model=ProjectInDB)
def remove_project_member(
    project_id: PyObjectId,
    member_email: str,
    db: Database = Depends(get_db),
    lead_user: UserInDB = Depends(get_project_lead_user),
):
    """Removes a user from a project. Only admins or project leads can remove members."""
    project = db.projects.find_one({"_id": project_id, "company_id": {"$in": [str(lead_user.company_id), lead_user.company_id]}})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this company.")

    if project["owner_email"] == member_email:
        raise HTTPException(status_code=400, detail="Cannot remove the project owner.")

    db.projects.update_one(
        {"_id": project_id},
        {"$pull": {"members": member_email}}
    )
    
    updated_project = db.projects.find_one({"_id": project_id})
    return ProjectInDB(**updated_project)