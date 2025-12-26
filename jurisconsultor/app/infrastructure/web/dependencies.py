from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pymongo.database import Database
from jose import JWTError

from domain.models.models import TokenData, UserInDB
from infrastructure.web.security import verify_token
from infrastructure.db.users import get_user
from infrastructure.db.db_manager import get_db as get_db_from_manager # Import the new DB getter

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

from infrastructure.db.db_manager import get_tenant_db

def get_current_tenant_db(
    current_user: UserInDB = Depends(get_current_user),
    db: Database = Depends(get_db)
) -> Database:
    """
    Dependency to get the database specific to the current user's company (tenant).
    If user has no company or company is not provisioned, falls back to main DB or raises error.
    """
    if not current_user.company_id:
        # Fallback for users without company (e.g. initial superadmin) - or raise error?
        # For now, let's return the main DB or raise, depending on strictness.
        # Strict isolation: raise.
        raise HTTPException(status_code=400, detail="User does not belong to any company/tenant.")

    company = db.companies.find_one({"_id": current_user.company_id})
    if not company:
        raise HTTPException(status_code=404, detail="User's company not found.")
    
    if not company.get("mongo_uri"):
        # Not provisioned yet? use main DB? 
        # For legacy "static" tenants, we might not have updated mongo_uri in DB yet.
        # But for new dynamic ones we do.
        # Let's assume strict dynamic:
        raise HTTPException(status_code=400, detail="Tenant database not provisioned.")

    return get_tenant_db(company["mongo_uri"], company["mongo_db_name"])
