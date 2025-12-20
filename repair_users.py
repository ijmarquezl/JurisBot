from pymongo import MongoClient
import os
from passlib.context import CryptContext
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# Setup hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Connect to DB
mongo_uri = os.getenv("MONGO_URI", "mongodb://jurisbot-db:27017")
client = MongoClient(mongo_uri)
db = client[os.getenv("MONGO_DB_NAME", "jurisconsultor_db")]

def repair_users():
    print("Starting user repair...")
    users = db.users.find({})
    
    count = 0
    for user in users:
        updated = False
        update_data = {}
        unset_data = {}

        # 1. Check for plain text password
        if "password" in user:
            print(f"User {user['email']} has plain text password.")
            plain_pass = user["password"]
            
            # Re-hash it to be sure
            new_hash = get_password_hash(plain_pass)
            update_data["hashed_password"] = new_hash
            unset_data["password"] = "" # Remove plain text
            updated = True
            print(f" -> Re-hashed password for {user['email']}")

        # 2. Convert company_id string to ObjectId if needed
        if "company_id" in user and isinstance(user["company_id"], str):
             try:
                 obj_id = ObjectId(user["company_id"])
                 update_data["company_id"] = obj_id
                 updated = True
                 print(f" -> Converted company_id to ObjectId for {user['email']}")
             except Exception as e:
                 print(f" -> Failed to convert company_id: {e}")

        # Perform update
        if updated:
            ops = {}
            if update_data:
                ops["$set"] = update_data
            if unset_data:
                ops["$unset"] = unset_data
            
            db.users.update_one({"_id": user["_id"]}, ops)
            count += 1

    print(f"Repair complete. Updated {count} users.")

if __name__ == "__main__":
    repair_users()
