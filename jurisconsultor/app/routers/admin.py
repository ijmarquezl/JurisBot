import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pymongo.database import Database
from bson import ObjectId

from app.models import UserCreate, UserInDB, UserBase, UserUpdate
from app.dependencies import get_db, get_admin_user
from app.users import create_user, get_user

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
        
    users_cursor = db.users.find({"company_id": ObjectId(admin_user.company_id)})
    users_list = []
    for user_data in users_cursor:
        user_data["_id"] = str(user_data["_id"])
        if "company_id" in user_data and user_data["company_id"] is not None:
            user_data["company_id"] = str(user_data["company_id"])
        users_list.append(UserInDB(**user_data).model_dump(by_alias=True))
    logger.info(f"Admin user company_id: {admin_user.company_id}")
    logger.info(f"MongoDB query for users: {{'company_id': '{admin_user.company_id}'}}")
    logger.info(f"Users returned from list_users_in_company: {users_list}")
    return users_list

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
def delete_user(user_id: str, admin_user: UserInDB = Depends(get_admin_user), db: Database = Depends(get_db)):
    """Deletes a user from the admin's company."""
    if not admin_user.company_id:
        raise HTTPException(status_code=400, detail="Admin user is not associated with a company.")
    
    if user_id == str(admin_user.id): # Convert ObjectId to string for comparison
        raise HTTPException(status_code=400, detail="Cannot delete yourself.")

    # Find the user to delete and ensure they belong to the admin's company
    user_to_delete = db.users.find_one({"_id": ObjectId(user_id), "company_id": ObjectId(admin_user.company_id)})
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found in this company.")
    
    db.users.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully."}

@router.put("/users/{user_id}", response_model=UserBase)
def update_user(user_id: str, user_update: UserUpdate, admin_user: UserInDB = Depends(get_admin_user), db: Database = Depends(get_db)):
    """Updates a user's details within the admin's company."""
    logger.info(f"Attempting to update user with ID: {user_id} by admin: {admin_user.email}")
    
    if not admin_user.company_id:
        logger.warning(f"Admin user {admin_user.email} is not associated with a company.")
        raise HTTPException(status_code=400, detail="Admin user is not associated with a company.")
    
    # Find the user to update and ensure they belong to the admin's company
    user_to_update = db.users.find_one({"_id": ObjectId(user_id), "company_id": ObjectId(admin_user.company_id)})
    
    logger.info(f"Query for user_id {user_id} returned: {user_to_update}")

    if not user_to_update:
        logger.warning(f"User with ID {user_id} not found in company {admin_user.company_id}.")
        raise HTTPException(status_code=404, detail="User not found in this company.")
    
    update_data = user_update.dict(exclude_unset=True) # Only update provided fields

    # Prevent admin from changing their own role to non-admin
    if user_id == str(admin_user.id) and "role" in update_data and update_data["role"] != "admin":
        logger.warning(f"Admin {admin_user.email} attempted to change their own role from admin.")
        raise HTTPException(status_code=400, detail="Cannot change your own role from admin.")

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    updated_user = db.users.find_one({"_id": ObjectId(user_id)})
    logger.info(f"User {user_id} updated successfully by admin {admin_user.email}.")
    return UserBase(**updated_user).model_dump(by_alias=True)