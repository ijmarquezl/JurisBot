import os
import argparse
import psycopg2
from dotenv import load_dotenv

def main(db_type: str, vector_size: int):
    """
    Main function to run the database migration on the specified database.
    
    Args:
        db_type (str): The type of database to migrate ('public' or 'private').
        vector_size (int): The dimension of the embedding vectors.
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

        # Drop existing tables for a clean slate
        cur.execute("DROP TABLE IF EXISTS documents CASCADE;")
        cur.execute("DROP TABLE IF EXISTS document_ownership CASCADE;")
        print("Dropped existing tables (documents, document_ownership).")

        # Create the documents table with the specified vector size
        cur.execute(f"""
            CREATE TABLE documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding VECTOR({vector_size}),
                source VARCHAR(255)
            );
        """)
        print(f"Documents table created successfully with vector size {vector_size} for {db_type} database.")

        # Create the document_ownership table
        cur.execute("""
            CREATE TABLE document_ownership (
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
    parser.add_argument("--vector-size", type=int, default=384, help="The dimension of the embedding vectors.")
    
    args = parser.parse_args()
    
    main(args.db_type, args.vector_size)