import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from models import UserInDB, UserResponse
from dependencies import get_db, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.get("/", response_model=List[UserResponse])
def list_company_users(current_user: UserInDB = Depends(get_current_user), db: Database = Depends(get_db)):
    """Lists all users in the current user's company."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User is not associated with a company.")
    
    users_cursor = db.users.find({
        "company_id": {
            "$in": [str(current_user.company_id), current_user.company_id]
        }
    })
    
    # Return UserResponse (safe, no passwords)
    return [UserResponse(email=u.email, full_name=u.full_name, role=u.role) for u in [UserInDB(**user_data) for user_data in users_cursor]]
