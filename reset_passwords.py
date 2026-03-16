import os
from pymongo import MongoClient
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://jurisbot-db:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "jurisconsultor_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

new_password = "admin"
hashed_pw = get_password_hash(new_password)

result = db.users.update_many(
    {}, 
    {"$set": {"hashed_password": hashed_pw}}
)

print(f"Updated {result.modified_count} users to have password '{new_password}'")
