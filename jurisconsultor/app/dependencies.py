from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.database import Database
from jose import JWTError

from app.models import TokenData, UserInDB
from app.security import verify_token
from app.users import get_user
from app.utils import get_mongo_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get the database connection
def get_db() -> Database:
    client = get_mongo_client()
    try:
        yield client.jurisconsultor
    finally:
        client.close()

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
    """
    Dependency to get the current user and check if they are an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="The user does not have admin privileges.")
    return current_user

def get_project_lead_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """
    Dependency to get the current user and check if they are a project lead or admin.
    """
    if current_user.role not in ["admin", "lead"]:
        raise HTTPException(status_code=403, detail="The user does not have project lead privileges.")
    return current_user
