from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from typing import List
from bson import ObjectId # Keep ObjectId for queries

from app.models import TaskCreate, TaskInDB, UserInDB, ProjectInDB
from app.dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

# Helper function to verify project membership and company access
def verify_project_membership(project_id: str, current_user: UserInDB, db: Database) -> ProjectInDB:
    project_data = db.projects.find_one({"_id": ObjectId(project_id)})
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project = ProjectInDB(**project_data)

    if project.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="User does not have access to this project's company.")

    if current_user.email not in project.members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this project",
        )
    return project

@router.post("/projects/{project_id}", response_model=TaskInDB, status_code=status.HTTP_201_CREATED)
def create_task_for_project(project_id: str, task: TaskCreate, db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """Create a new task within a specific project. User must be a member of the project."""
    verify_project_membership(project_id, current_user, db)
    
    task_dict = task.dict()
    task_dict["project_id"] = ObjectId(project_id)
    task_dict["creator_email"] = current_user.email
    
    result = db.tasks.insert_one(task_dict)
    created_task = db.tasks.find_one({"_id": result.inserted_id})
    
    return TaskInDB.parse_obj(created_task).model_dump(by_alias=True)

@router.get("/projects/{project_id}", response_model=List[TaskInDB])
def list_tasks_for_project(project_id: str, db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """List all tasks for a specific project. User must be a member of the project."""
    verify_project_membership(project_id, current_user, db)
    
    tasks = db.tasks.find({"project_id": ObjectId(project_id)})
    return [TaskInDB.parse_obj(t).model_dump(by_alias=True) for t in tasks]