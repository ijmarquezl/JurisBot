import os
import glob
import argparse
from pypdf import PdfReader
from app.utils import get_mongo_client, get_public_db_conn, get_private_db_conn, generate_embedding

def process_and_store_documents(pdf_directory: str, db_type: str):
    """
    Processes and stores legal documents from PDF files into the specified database.
    
    Args:
        pdf_directory (str): The path to the directory containing the PDF files.
        db_type (str): The type of database to use ('public' or 'private').
    """
    try:
        # Get database connections
        mongo_client = get_mongo_client()
        db = mongo_client.jurisconsultor
        documents_collection = db.documents # Consider separating this by company in the future

        if db_type == 'public':
            conn = get_public_db_conn()
        elif db_type == 'private':
            conn = get_private_db_conn()
        else:
            raise ValueError("Invalid db_type specified. Must be 'public' or 'private'.")
            
        cur = conn.cursor()

        pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in the '{pdf_directory}' directory.")
            return

        for pdf_path in pdf_files:
            print(f"Processing document: {pdf_path}")
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"

            # Simple chunking by paragraphs
            chunks = [p.strip() for p in text.split("\n\n") if p.strip()]

            for i, chunk in enumerate(chunks):
                # Skip very small chunks
                if len(chunk) < 100:
                    continue

                # Generate embedding
                embedding = generate_embedding(chunk)
                source_name = os.path.basename(pdf_path)

                # Store in PostgreSQL
                cur.execute(
                    "INSERT INTO documents (content, embedding, source) VALUES (%s, %s, %s) RETURNING id;",
                    (chunk, embedding.tolist(), source_name)
                )
                document_id = cur.fetchone()[0]
                print(f"  - Stored chunk {i+1}/{len(chunks)} in PostgreSQL with id: {document_id}")

                # Store metadata in MongoDB
                mongo_doc = {
                    "source": source_name,
                    "chunk_index": i,
                    "postgres_id": document_id,
                    "db_type": db_type # Add db_type to metadata
                }
                documents_collection.insert_one(mongo_doc)

        conn.commit()
        cur.close()
        conn.close()
        mongo_client.close()
        print("\nProcessing complete.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process PDF documents and store them in a database.")
    parser.add_argument("directory", type=str, help="The path to the directory containing the PDF files.")
    parser.add_argument("db_type", type=str, choices=['public', 'private'], help="The type of database to use ('public' or 'private').")
    
    args = parser.parse_args()
    
    process_and_store_documents(args.directory, args.db_type)
