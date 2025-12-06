from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pymongo.database import Database
from jose import JWTError

from models import TokenData, UserInDB
from security import verify_token
from users import get_user
from db_manager import get_db as get_db_from_manager # Import the new DB getter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get the database connection
def get_db() -> Database:
    """Dependency to get the database connection from the central DB manager."""
    return get_db_from_manager()

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Database = Depends(get_db)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# --- Role-based Dependencies ---

def get_admin_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="The user does not have admin privileges.")
    return current_user

def get_project_lead_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role not in ["admin", "lead", "superadmin"]:
        raise HTTPException(status_code=403, detail="The user does not have project lead privileges.")
    return current_user

def get_super_admin_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="The user does not have super admin privileges.")
    return current_user
