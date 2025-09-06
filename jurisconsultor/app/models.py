from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId # Keep ObjectId for manual conversion

# Common Pydantic model configuration for DB models
model_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    json_encoders={ObjectId: str}, # This will convert ObjectId to str during serialization
    # Removed: arbitrary_types_allowed=True,
)

# --- Company Models ---
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyInDB(CompanyBase):
    model_config = model_config
    id: str = Field(alias="_id") # Changed to str

# --- User Models ---
class UserBase(BaseModel):

    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    company_id: Optional[str] = None # Changed to str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    company_id: Optional[str] = None # Changed to str
    role: Optional[str] = None

class UserInDB(UserBase):
    model_config = model_config
    id: str = Field(alias="_id") # Changed to str
    hashed_password: str
    company_id: Optional[str] = None # Changed to str
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
    id: str = Field(alias="_id") # Changed to str
    company_id: str # Changed to str
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
    id: str = Field(alias="_id") # Changed to str
    project_id: str # Changed to str
    creator_email: str
    assignee_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)