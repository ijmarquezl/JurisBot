
import os
import psycopg2
from dotenv import load_dotenv

def main():
    """
    Main function to run the database migration.
    """
    load_dotenv()

    postgres_uri = os.getenv("POSTGRES_URI")

    if not postgres_uri:
        print("POSTGRES_URI environment variable not set.")
        return

    try:
        conn = psycopg2.connect(postgres_uri)
        cur = conn.cursor()

        # Enable the vector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("Vector extension enabled.")

        # Create the documents table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding VECTOR(1024),
                source VARCHAR(255)
            );
        """)
        print("Documents table created successfully.")

        conn.commit()
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    main()
