import os
import argparse
import psycopg2
from dotenv import load_dotenv

def main(db_type: str):
    """
    Main function to run the database migration on the specified database.
    
    Args:
        db_type (str): The type of database to migrate ('public' or 'private').
    """
    load_dotenv()

    if db_type == 'public':
        postgres_uri = os.getenv("PUBLIC_POSTGRES_URI")
    elif db_type == 'private':
        postgres_uri = os.getenv("PRIVATE_POSTGRES_URI")
    else:
        raise ValueError("Invalid db_type specified. Must be 'public' or 'private'.")

    if not postgres_uri:
        print(f"{db_type.upper()}_POSTGRES_URI environment variable not set.")
        return

    try:
        conn = psycopg2.connect(postgres_uri)
        cur = conn.cursor()

        # Enable the vector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print(f"Vector extension enabled for {db_type} database.")

        # Create the documents table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding VECTOR(1024),
                source VARCHAR(255)
            );
        """)
        print(f"Documents table created successfully for {db_type} database.")

        # Create the document_ownership table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_ownership (
                id SERIAL PRIMARY KEY,
                source VARCHAR(255) NOT NULL,
                company_id VARCHAR(255) NOT NULL,
                UNIQUE (source, company_id)
            );
        """)
        print(f"Document ownership table created successfully for {db_type} database.")

        conn.commit()
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run database migrations.")
    parser.add_argument("db_type", type=str, choices=['public', 'private'], help="The type of database to migrate ('public' or 'private').")
    
    args = parser.parse_args()
    
    main(args.db_type)