import argparse
import os
import sys
from pymongo import MongoClient

# Add project root to path to allow imports from 'app'


from models import UserCreate
from users import create_user

def main():
    """
    Creates a new admin user in a specified MongoDB database.
    Connection details are passed via environment variables.
    """
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")

    if not all([mongo_uri, db_name]):
        print("Error: MONGO_URI and MONGO_DB_NAME environment variables must be set.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Create a new admin user for a tenant.")
    parser.add_argument("email", type=str, help="The email address of the admin user.")
    parser.add_argument("password", type=str, help="The password for the admin user.")
    parser.add_argument("--full_name", type=str, help="The full name of the admin user.", default="Admin User")
    parser.add_argument("--role", type=str, help="The role for the user (e.g., admin, member, project_lead).", default="member")
    
    args = parser.parse_args()

    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        db.command('ping')
        print("Database connection successful.")
    except Exception as e:
        print(f"Error: Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    user_data = UserCreate(
        email=args.email,
        password=args.password,
        full_name=args.full_name,
        role=args.role
    )

    print(f"Creating user for email: {args.email} in database '{db_name}'...")
    try:
        new_user = create_user(db, user_data)
        print("\nSuccessfully created user!")
        print(f"  Email: {new_user.email}")
        print(f"  Role: {new_user.role}")
        print(f"  Company ID: {new_user.company_id}")
    except Exception as e:
        print(f"Error: Failed to create user: {e}", file=sys.stderr)
    finally:
        client.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()