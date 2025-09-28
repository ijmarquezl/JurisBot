
# --- Document Models ---
class DocumentBase(BaseModel):
    source: str
    content: str

class DocumentInDB(DocumentBase):
    model_config = model_config
    id: int # Postgres uses integer IDs
