from pydantic import BaseModel, Field, ConfigDict, GetJsonSchemaHandler
from pydantic_core import core_schema
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# Helper for MongoDB ObjectId, compatible with Pydantic v2
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> "core_schema.JsonSchemaValue": # Changed to string literal
        # Represent ObjectId as a string in JSON Schema
        return handler(core_schema.string_schema())

# Common Pydantic model configuration for DB models
model_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    json_encoders={ObjectId: str},
)

# --- Company Models ---
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyInDB(CompanyBase):
    model_config = model_config
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

# --- User Models ---
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    company_id: Optional[PyObjectId] = None # Optional for now, can be made mandatory

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    company_id: Optional[PyObjectId] = None
    role: Optional[str] = None

class UserInDB(UserBase):
    model_config = model_config
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str
    company_id: Optional[PyObjectId] = None
    role: str = "member" # e.g., admin, lead, member

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

class ProjectCreate(ProjectBase):
    pass

class ProjectInDB(ProjectBase):
    model_config = model_config
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    company_id: PyObjectId
    owner_email: str
    members: List[str] = [] # List of member emails
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- Task Models ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"

class TaskCreate(TaskBase):
    pass

class TaskInDB(TaskBase):
    model_config = model_config
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    project_id: PyObjectId
    creator_email: str
    assignee_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)