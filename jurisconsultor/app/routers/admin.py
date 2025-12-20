import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pymongo.database import Database
from bson import ObjectId

from models import UserCreate, UserInDB, UserBase, UserUpdate, PyObjectId, UserResponse
from dependencies import get_db, get_admin_user, get_project_lead_user
from users import create_user, get_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)], # Protect all routes in this router
)

@router.get("/users", response_model=List[UserInDB])
def list_users_in_company(admin_user: UserInDB = Depends(get_admin_user), db: Database = Depends(get_db)):
    """Lists all users in the admin's company."""
    if not admin_user.company_id:
        raise HTTPException(status_code=400, detail="Admin user is not associated with a company.")
        
    # Query for users where company_id can be either a string or an ObjectId
    users_cursor = db.users.find({
        "company_id": {
            "$in": [str(admin_user.company_id), admin_user.company_id]
        }
    })
    users_list = [UserInDB(**user_data).model_dump(by_alias=False) for user_data in users_cursor]
    logger.info(f"Admin user company_id: {admin_user.company_id}")
    logger.info(f"MongoDB query for users: {{'company_id': '{admin_user.company_id}'}}")
    logger.info(f"Users returned from list_users_in_company: {users_list}")
    return users_list

# list_company_users moved to routers/users.py

@router.post("/users", response_model=UserBase, status_code=201)
def create_new_user(new_user: UserCreate, admin_user: UserInDB = Depends(get_admin_user), db: Database = Depends(get_db)):
    """Creates a new user within the admin's company."""
    if not admin_user.company_id:
        raise HTTPException(status_code=400, detail="Admin user is not associated with a company.")
    
    db_user = get_user(db, email=new_user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
        
    # Ensure the new user is created for the admin's company
    new_user.company_id = admin_user.company_id
    
    created_user = create_user(db, new_user)
    return created_user.model_dump(by_alias=True)

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: PyObjectId, admin_user: UserInDB = Depends(get_admin_user), db: Database = Depends(get_db)):
    """Deletes a user from the admin's company."""
    if not admin_user.company_id:
        raise HTTPException(status_code=400, detail="Admin user is not associated with a company.")
    
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself.")

    # Find the user to delete and ensure they belong to the admin's company
    user_to_delete = db.users.find_one({"_id": user_id, "company_id": {"$in": [str(admin_user.company_id), admin_user.company_id]}})
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found in this company.")
    
    db.users.delete_one({"_id": user_id})
    return {"message": "User deleted successfully."}

@router.put("/users/{user_id}", response_model=UserBase)
def update_user(user_id: PyObjectId, user_update: UserUpdate, admin_user: UserInDB = Depends(get_admin_user), db: Database = Depends(get_db)):
    """Updates a user's details within the admin's company."""
    logger.info(f"Attempting to update user with ID: {user_id} by admin: {admin_user.email}")
    
    if not admin_user.company_id:
        logger.warning(f"Admin user {admin_user.email} is not associated with a company.")
        raise HTTPException(status_code=400, detail="Admin user is not associated with a company.")
    
    # Find the user to update and ensure they belong to the admin's company
    user_to_update = db.users.find_one({"_id": user_id, "company_id": {"$in": [str(admin_user.company_id), admin_user.company_id]}})
    
    logger.info(f"Query for user_id {user_id} returned: {user_to_update}")

    if not user_to_update:
        logger.warning(f"User with ID {user_id} not found in company {admin_user.company_id}.")
        raise HTTPException(status_code=404, detail="User not found in this company.")
    
    update_data = user_update.dict(exclude_unset=True) # Only update provided fields
    logger.info(f"Update data: {update_data}") # New log
    
    # Prevent admin from changing their own role to non-admin
    if user_id == admin_user.id and "role" in update_data and update_data["role"] != "admin":
        logger.warning(f"Admin {admin_user.email} attempted to change their own role from admin.")
        raise HTTPException(status_code=400, detail="Cannot change your own role from admin.")

    result = db.users.update_one( # Store result
        {"_id": user_id},
        {"$set": update_data}
    )
    logger.info(f"Update result: {result.raw_result}") # New log
    
    updated_user = db.users.find_one({"_id": user_id})
    logger.info(f"User {user_id} updated successfully by admin {admin_user.email}.")
    return UserBase(**updated_user).model_dump(by_alias=True)

@router.get("/stats")
def get_admin_stats(admin_user: UserInDB = Depends(get_admin_user), db: Database = Depends(get_db)):
    """Returns statistics for the admin's company: user count, project count, task count."""
    if not admin_user.company_id:
        raise HTTPException(status_code=400, detail="Admin user is not associated with a company.")
    
    company_id_query = {"$in": [str(admin_user.company_id), admin_user.company_id]}
    
    # Count Users
    user_count = db.users.count_documents({"company_id": company_id_query})
    
    # Count Projects
    project_count = db.projects.count_documents({"company_id": company_id_query})
    
    # Count Tasks (need to filter by projects belonging to the company)
    # First get all project IDs for this company
    projects = db.projects.find({"company_id": company_id_query}, {"_id": 1})
    project_ids = [str(p["_id"]) for p in projects]
    # Also include ObjectIds if stored that way
    # Ideally standardized, but for safety:
    # We will just rely on the fact that task.project_id matches the project's _id format.
    # If project_ids are mixed strings/ObjectIds, we might need to be careful.
    # Assuming standard PyObjectId usage.
    
    # Actually, optimized way:
    # tasks collection has project_id. 
    # db.tasks.count_documents({"project_id": {"$in": project_ids}}) 
    # But project_ids need to match the type stored in tasks (ObjectId or str).
    # Let's get them as they are from the DB result.
    projects_cursor = db.projects.find({"company_id": company_id_query}, {"_id": 1})
    project_ids_raw = [p["_id"] for p in projects_cursor]
    
    task_count = 0
    if project_ids_raw:
        task_count = db.tasks.count_documents({"project_id": {"$in": project_ids_raw}})
        
    return {
        "user_count": user_count,
        "project_count": project_count,
        "task_count": task_count
    }