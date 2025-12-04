import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pymongo.database import Database
from bson import ObjectId

from models import UserCreate, UserInDB, UserUpdate, PyObjectId, CompanyCreate, CompanyInDB, UserResponse
from dependencies import get_db, get_super_admin_user
from users import create_user, get_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/superadmin",
    tags=["superadmin"],
    dependencies=[Depends(get_super_admin_user)],
)

# --- User Management ---

@router.get("/users", response_model=List[UserInDB])
def list_all_users(db: Database = Depends(get_db)):
    """Lists all users across all companies."""
    users_cursor = db.users.find({})
    return [UserInDB(**user_data) for user_data in users_cursor]

@router.post("/users", response_model=UserInDB, status_code=201)
def create_any_user(new_user: UserCreate, db: Database = Depends(get_db)):
    """Creates a new user, optionally assigning them to a company."""
    if get_user(db, email=new_user.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    # If company_id is provided, ensure it exists
    if new_user.company_id:
        company = db.companies.find_one({"_id": new_user.company_id})
        if not company:
            raise HTTPException(status_code=404, detail=f"Company with id {new_user.company_id} not found.")

    created_user = create_user(db, new_user)
    return created_user

@router.put("/users/{user_id}", response_model=UserInDB)
def update_any_user(user_id: PyObjectId, user_update: UserUpdate, db: Database = Depends(get_db)):
    """Updates any user's details."""
    user_to_update = db.users.find_one({"_id": user_id})
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found.")

    update_data = user_update.dict(exclude_unset=True)
    
    # If password is being updated, it needs to be hashed.
    # The `create_user` function handles hashing, but here we need to do it manually
    # or refactor user creation/update logic. For now, let's assume a direct update,
    # but this is a security concern to be addressed.
    # A better approach would be to have a dedicated password update endpoint.
    if "password" in update_data:
        # This is NOT ideal. Refactor to use a password hashing function.
        # For now, demonstrating the flow.
        from security import get_password_hash
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))


    db.users.update_one({"_id": user_id}, {"$set": update_data})
    
    updated_user = db.users.find_one({"_id": user_id})
    return UserInDB(**updated_user)

@router.delete("/users/{user_id}", status_code=204)
def delete_any_user(user_id: PyObjectId, db: Database = Depends(get_db)):
    """Deletes any user."""
    result = db.users.delete_one({"_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")
    return 

# --- Company (Tenant) Management ---

@router.get("/companies", response_model=List[CompanyInDB])
def list_all_companies(db: Database = Depends(get_db)):
    """Lists all companies (tenants)."""
    companies_cursor = db.companies.find({})
    return [CompanyInDB(**company_data) for company_data in companies_cursor]

@router.post("/companies", response_model=CompanyInDB, status_code=201)
def create_company(company: CompanyCreate, db: Database = Depends(get_db)):
    """Creates a new company (tenant)."""
    company_dict = company.dict()
    result = db.companies.insert_one(company_dict)
    created_company = db.companies.find_one({"_id": result.inserted_id})
    return CompanyInDB(**created_company)

@router.delete("/companies/{company_id}", status_code=204)
def delete_company(company_id: PyObjectId, db: Database = Depends(get_db)):
    """
    Deletes a company and all associated users and projects.
    This is a destructive operation.
    """
    company = db.companies.find_one({"_id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    # Delete associated users
    db.users.delete_many({"company_id": company_id})
    
    # Delete associated projects
    db.projects.delete_many({"company_id": company_id})

    # Delete the company itself
    db.companies.delete_one({"_id": company_id})
    
    return

# --- Log Management ---

LOG_FILE_PATH = "jurisconsultor.log"

@router.get("/logs", response_model=List[str])
def get_system_logs(lines: int = 200):
    """
    Retrieves the last N lines from the system log file.
    """
    try:
        with open(LOG_FILE_PATH, 'r') as f:
            # Read all lines and return the last N
            lines_from_file = f.readlines()
            return lines_from_file[-lines:]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Log file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {e}")
