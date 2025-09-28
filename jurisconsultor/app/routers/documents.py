from fastapi import APIRouter, Depends
from pymongo.database import Database
from typing import List

from app.models import DocumentInDB, UserInDB
from app.dependencies import get_db, get_current_user
from app.utils import get_public_db_conn # Use the postgres connection

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.get("/", response_model=List[DocumentInDB])
def list_documents(db: Database = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """List all documents available to the user's company."""
    # Note: Current implementation returns all documents as there is no company_id in the documents table yet.
    # This should be refined when multi-tenancy for documents is implemented.
    conn = get_public_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, source, content FROM documents ORDER BY id DESC;")
    documents = cur.fetchall()
    cur.close()
    conn.close()
    return [DocumentInDB(id=doc[0], source=doc[1], content=doc[2]) for doc in documents]
