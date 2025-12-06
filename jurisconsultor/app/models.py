from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema

# Custom Pydantic type for ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any,
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ]),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

# Common Pydantic model configuration for DB models
model_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    json_encoders={ObjectId: str},
    arbitrary_types_allowed=True,
)

# --- Company Models ---
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyInDB(CompanyBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')

# --- User Models ---
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    model_config = model_config
    password: str
    company_id: Optional[PyObjectId] = None
    role: Optional[str] = None

class UserUpdate(BaseModel):
    model_config = model_config
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    company_id: Optional[PyObjectId] = None
    role: Optional[str] = None

class UserInDB(UserBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')
    hashed_password: str
    company_id: Optional[PyObjectId] = None
    role: str = "member"

class UserResponse(UserBase):
    role: str

# --- Token Models ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Project Models ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_archived: bool = False

class ProjectCreate(ProjectBase):
    pass

class ProjectInDB(ProjectBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')
    company_id: PyObjectId
    owner_email: str
    members: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- Task Models ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"

class TaskCreate(TaskBase):
    project_id: PyObjectId

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assignee_email: Optional[str] = None

class TaskInDB(TaskBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')
    project_id: PyObjectId
    creator_email: str
    assignee_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- Document Models ---
class DocumentBase(BaseModel):
    source: str
    content: str

class DocumentInDB(DocumentBase):
    model_config = model_config
    id: int # Postgres uses integer IDs

# --- Generated Document Models ---
class GeneratedDocumentBase(BaseModel):
    file_name: str
    project_id: PyObjectId
    owner_email: str

class GeneratedDocumentCreate(GeneratedDocumentBase):
    pass

class GeneratedDocumentInDB(GeneratedDocumentBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')
    file_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_archived: bool = False

# --- Agent Conversation State Models ---
class ConversationState(BaseModel):
    model_config = model_config
    id: PyObjectId = Field(alias='_id', default_factory=PyObjectId)
    user_email: str
    workflow: Optional[str] = None
    workflow_data: dict = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# --- Scraping Source Models ---
class ScrapingSourceBase(BaseModel):
    name: str
    url: Optional[str] = None # This is now optional
    local_filename: Optional[str] = None
    scraper_type: str = "generic_html" # New field: e.g., "generic_html", "ordenjuridico_special"
    
    # New fields for flexible PDF link finding
    pdf_direct_url: Optional[str] = None # If provided, scraper downloads directly from here
    pdf_link_contains: Optional[str] = None # If not direct, look for links on 'url' containing this string
    pdf_link_ends_with: Optional[str] = None # If not direct, look for links on 'url' ending with this string

class ScrapingSourceCreate(ScrapingSourceBase):
    pass

class ScrapingSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    local_filename: Optional[str] = None
    scraper_type: Optional[str] = None
    pdf_direct_url: Optional[str] = None
    pdf_link_contains: Optional[str] = None
    pdf_link_ends_with: Optional[str] = None

class ScrapingSourceInDB(ScrapingSourceBase):
    model_config = model_config
    id: PyObjectId = Field(alias='_id')
    last_downloaded_at: Optional[datetime] = None
    last_known_hash: Optional[str] = None
    status: str = "pending" # e.g., pending, success, failed
    error_message: Optional[str] = None
