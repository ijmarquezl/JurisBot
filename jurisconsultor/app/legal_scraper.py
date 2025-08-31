import os
import glob
from pypdf import PdfReader
from app.utils import get_mongo_client, get_postgres_conn, generate_embedding

PDF_DIRECTORY = "documentos_legales"

def process_and_store_documents():
    """
    Processes and stores legal documents from PDF files.
    """
    try:
        # Get database connections
        mongo_client = get_mongo_client()
        db = mongo_client.jurisconsultor
        documents_collection = db.documents

        conn = get_postgres_conn()
        cur = conn.cursor()

        pdf_files = glob.glob(os.path.join(PDF_DIRECTORY, "*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in the '{PDF_DIRECTORY}' directory.")
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
                    "postgres_id": document_id
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
    process_and_store_documents()