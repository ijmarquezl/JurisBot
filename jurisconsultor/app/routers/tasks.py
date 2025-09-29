from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
from typing import List

from app.models import TaskCreate, TaskInDB, UserInDB, ProjectInDB, PyObjectId, TaskUpdate
from app.dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

# Helper function to verify project membership and company access
def verify_project_membership(project_id: PyObjectId, current_user: UserInDB, db: Database) -> ProjectInDB:
    project_data = db.projects.find_one({
        "_id": project_id, 
        "company_id": {"$in": [str(current_user.company_id), current_user.company_id]}
    })
    if not project_data:
        raise HTTPException(status_code=404, detail="Project not found or user does not have access")
        
    project = ProjectInDB(**project_data)

    if current_user.email not in project.members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this project",
        )
    return project

@router.post("/", response_model=TaskInDB, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """Create a new task within a specific project. User must be a member of the project."""
    verify_project_membership(task.project_id, current_user, db)
    
    task_dict = task.dict()
    task_dict["creator_email"] = current_user.email
    # Ensure project_id is an ObjectId, not a string from .dict()
    task_dict["project_id"] = task.project_id
    
    result = db.tasks.insert_one(task_dict)
    created_task = db.tasks.find_one({"_id": result.inserted_id})
    
    return TaskInDB(**created_task)

@router.get("/project/{project_id}", response_model=List[TaskInDB])
def list_tasks_for_project(project_id: PyObjectId, db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """List all tasks for a specific project. User must be a member of the project."""
    verify_project_membership(project_id, current_user, db)
    
    tasks_cursor = db.tasks.find({"project_id": project_id})
    return [TaskInDB(**t) for t in tasks_cursor]

@router.put("/{task_id}", response_model=TaskInDB)
def update_task(task_id: PyObjectId, task_update: TaskUpdate, db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """Updates a task. User must be a member of the task's project."""
    task_to_update = db.tasks.find_one({"_id": task_id})
    if not task_to_update:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify user has access to the project this task belongs to
    verify_project_membership(task_to_update['project_id'], current_user, db)

    update_data = task_update.dict(exclude_unset=True)
    
    db.tasks.update_one(
        {"_id": task_id},
        {"$set": update_data}
    )
    
    updated_task = db.tasks.find_one({"_id": task_id})
    return TaskInDB(**updated_task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: PyObjectId, db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """Deletes a task. User must be a member of the task's project."""
    task_to_delete = db.tasks.find_one({"_id": task_id})
    if not task_to_delete:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify user has access to the project this task belongs to
    verify_project_membership(task_to_delete['project_id'], current_user, db)

    db.tasks.delete_one({"_id": task_id})
    return
