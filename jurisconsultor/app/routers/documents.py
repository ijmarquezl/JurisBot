from fastapi import APIRouter, Depends
from typing import List

from app.models import DocumentInDB, UserInDB
from app.dependencies import get_current_user
# Import both connection utilities
from app.utils import get_public_db_conn, get_private_db_conn

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.get("/", response_model=List[DocumentInDB])
def list_documents(current_user: UserInDB = Depends(get_current_user)):
    """
    List all public documents and all documents private to the user's company.
    """
    all_documents = []
    
    # 1. Fetch public documents
    try:
        public_conn = get_public_db_conn()
        public_cur = public_conn.cursor()
        public_cur.execute("SELECT id, source, content FROM documents ORDER BY id DESC;")
        public_docs = public_cur.fetchall()
        public_cur.close()
        public_conn.close()
        all_documents.extend([DocumentInDB(id=doc[0], source=f"[Público] {doc[1]}", content=doc[2]) for doc in public_docs])
    except Exception as e:
        print(f"Could not connect to or query public documents DB: {e}")

    # 2. Fetch private documents
    try:
        private_conn = get_private_db_conn()
        private_cur = private_conn.cursor()
        # In this siloed model, we don't need to filter by company_id, as the entire DB is private.
        private_cur.execute("SELECT id, source, content FROM documents ORDER BY id DESC;")
        private_docs = private_cur.fetchall()
        private_cur.close()
        private_conn.close()
        all_documents.extend([DocumentInDB(id=doc[0], source=f"[Privado] {doc[1]}", content=doc[2]) for doc in private_docs])
    except Exception as e:
        print(f"Could not connect to or query private documents DB: {e}")

    return all_documents