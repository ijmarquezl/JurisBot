from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pymongo.database import Database

from app.models import UserCreate, UserInDB, UserBase
from app.dependencies import get_db, get_admin_user
from app.users import create_user, get_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)], # Protect all routes in this router
)

@router.get("/users", response_model=List[UserBase])
def list_users_in_company(admin_user: UserInDB = Depends(get_admin_user), db: Database = Depends(get_db)):
    """Lists all users in the admin's company."""
    if not admin_user.company_id:
        raise HTTPException(status_code=400, detail="Admin user is not associated with a company.")
        
    users_cursor = db.users.find({"company_id": admin_user.company_id})
    return [UserBase(**user) for user in users_cursor]

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
    return created_user