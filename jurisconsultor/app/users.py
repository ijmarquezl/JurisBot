import logging
from pymongo.database import Database
from app.models import UserCreate, UserInDB, CompanyInDB
from app.security import get_password_hash
from bson import ObjectId # Import ObjectId

logger = logging.getLogger(__name__)

def get_user(db: Database, email: str) -> UserInDB:
    logger.info(f"Attempting to get user: {email}")
    user_data = db.users.find_one({"email": email})
    logger.info(f"User data from DB: {user_data}")
    if user_data:
        return UserInDB(**user_data) # Removed explicit conversion
    return None

def get_or_create_company(db: Database, company_name: str) -> CompanyInDB:
    """Gets a company by name, creating it if it doesn't exist."""
    logger.info(f"Attempting to get or create company: {company_name}")
    company_data = db.companies.find_one({"name": company_name})
    logger.info(f"Company data from DB: {company_data}")
    if company_data:
        company_data["_id"] = str(company_data["_id"])
        return CompanyInDB(**company_data)
    else:
        company_doc = {"name": company_name}
        logger.info(f"Creating new company: {company_name}")
        result = db.companies.insert_one(company_doc)
        new_company_data = db.companies.find_one({"_id": result.inserted_id})
        new_company_data["_id"] = str(new_company_data["_id"])
        logger.info(f"New company created: {new_company_data}")
        return CompanyInDB(**new_company_data)

def create_user(db: Database, user: UserCreate) -> UserInDB:
    """Creates a new user in the database."""
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict(exclude={"password"})
    user_dict["hashed_password"] = hashed_password
    
    # Handle company assignment
    if not user.company_id:
        # If no company_id is provided, derive from email and get or create company
        email_domain = user.email.split('@')[1]
        company = get_or_create_company(db, company_name=email_domain)
        user_dict["company_id"] = company.id
    
    # For now, the first user of a company becomes an admin
    existing_users_in_company = db.users.count_documents({"company_id": user_dict["company_id"]})
    if existing_users_in_company == 0:
        user_dict["role"] = "admin"
    else:
        user_dict["role"] = "member"

    result = db.users.insert_one(user_dict)
    created_user = db.users.find_one({"_id": result.inserted_id})
    
    return UserInDB(**created_user)