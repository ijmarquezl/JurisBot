from fastapi import APIRouter, Depends, HTTPException, status, Body
from pymongo.database import Database
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

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

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: PyObjectId, db: Database = Depends(get_db), lead_user: UserInDB = Depends(get_project_lead_user)):
    """Deletes a project and all its associated tasks. Only project leads or admins can delete projects."""
    # Verify project exists and belongs to the user's company
    project_to_delete = db.projects.find_one({
        "_id": project_id,
        "company_id": {"$in": [str(lead_user.company_id), lead_user.company_id]}
    })
    if not project_to_delete:
        raise HTTPException(status_code=404, detail="Project not found or user does not have access.")

    # Delete all tasks associated with this project
    db.tasks.delete_many({"project_id": project_id})
    logger.info(f"Deleted tasks for project {project_id}")

    # Delete the project itself
    db.projects.delete_one({"_id": project_id})
    logger.info(f"Deleted project {project_id}")

    return # 204 No Content

@router.put("/{project_id}/archive", response_model=ProjectInDB)
def archive_project(
    project_id: PyObjectId,
    archive_status: bool = Body(..., embed=True), # True to archive, False to unarchive
    db: Database = Depends(get_db),
    lead_user: UserInDB = Depends(get_project_lead_user)
):
    """Archives or unarchives a project. Only project leads or admins can change archive status."""
    project_to_update = db.projects.find_one({
        "_id": project_id,
        "company_id": {"$in": [str(lead_user.company_id), lead_user.company_id]}
    })
    if not project_to_update:
        raise HTTPException(status_code=404, detail="Project not found or user does not have access.")
    
    db.projects.update_one(
        {"_id": project_id},
        {"$set": {"is_archived": archive_status}}
    )
    
    updated_project = db.projects.find_one({"_id": project_id})
    return ProjectInDB(**updated_project)

@router.get("/", response_model=List[ProjectInDB])
def list_projects(
    db: Database = Depends(get_db), 
    current_user: UserInDB = Depends(get_current_user),
    include_archived: Optional[bool] = False # New query parameter
):
    """List all projects for the user's company where the user is a member."""
    if not current_user.company_id:
        return [] # Or raise an error, returning empty list is safer
        
    query_filter = {
        "company_id": {"$in": [str(current_user.company_id), current_user.company_id]},
        "members": current_user.email
    }
    if not include_archived:
        query_filter["is_archived"] = False # Filter out archived by default

    logger.info(f"Querying projects with filter: {query_filter}") # ADDED LOG

    projects_cursor = db.projects.find(query_filter)
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