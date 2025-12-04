import argparse
import os
import sys
from pymongo import MongoClient
from getpass import getpass

# This is a bit of a hack to allow importing from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import UserCreate
from app.users import create_user, get_user

def main():
    """
    Creates a new superadmin user in the main MongoDB database.
    Connection details are passed via environment variables.
    """
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")

    if not all([mongo_uri, db_name]):
        print("Error: MONGO_URI and MONGO_DB_NAME environment variables must be set.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Create a new superadmin user.")
    parser.add_argument("email", type=str, help="The email address of the superadmin user.")
    parser.add_argument("--password", type=str, help="The password for the superadmin user. If not provided, it will be prompted for securely.")
    parser.add_argument("--full_name", type=str, help="The full name of the superadmin user.", default="Super Admin")
    
    args = parser.parse_args()

    password = args.password if args.password else getpass("Enter password for superadmin: ")

    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        db.command('ping')
        print("Database connection successful.")
    except Exception as e:
        print(f"Error: Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    if get_user(db, args.email):
        print(f"Error: User with email '{args.email}' already exists.", file=sys.stderr)
        client.close()
        sys.exit(1)

    user_data = UserCreate(
        email=args.email,
        password=password,
        full_name=args.full_name,
        role="superadmin",
        company_id=None # Superadmin is not tied to a company
    )

    print(f"Creating superadmin user for email: {args.email} in database '{db_name}'...")
    try:
        new_user = create_user(db, user_data)
        print("\nSuccessfully created superadmin user!")
        print(f"  Email: {new_user.email}")
        print(f"  Role: {new_user.role}")
    except Exception as e:
        print(f"Error: Failed to create user: {e}", file=sys.stderr)
    finally:
        client.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()
