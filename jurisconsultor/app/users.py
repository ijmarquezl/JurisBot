
from pymongo.database import Database
from app.models import UserCreate, UserInDB
from app.security import get_password_hash

def get_user(db: Database, email: str):
    """Retrieves a user from the database by email."""
    user = db.users.find_one({"email": email})
    if user:
        return UserInDB(**user)
    return None

def create_user(db: Database, user: UserCreate):
    """Creates a new user in the database."""
    hashed_password = get_password_hash(user.password)
    user_in_db = UserInDB(email=user.email, full_name=user.full_name, hashed_password=hashed_password)
    db.users.insert_one(user_in_db.dict())
    return user_in_db
