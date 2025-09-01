from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pymongo.database import Database
from jose import JWTError
from pydantic import BaseModel
from typing import Optional, List

from app.rag_agent import run_agent # Changed import
from app.models import UserCreate, UserInDB, Token, TokenData, UserBase
from app.security import create_access_token, create_refresh_token, verify_password, verify_token
from app.users import create_user, get_user
from app.utils import get_mongo_client
from app.routers import projects, tasks
from app.dependencies import get_db, get_current_user, oauth2_scheme

app = FastAPI(
    title="Jurisconsultor API",
    description="API for the Jurisconsultor AI agent.",
    version="0.4.0", # Version bump for agent upgrade
)

# --- CORS Middleware ---
origins = [
    "http://localhost:5173", # Default Vite dev server
    "http://localhost:3000", # Default Create React App dev server
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
app.include_router(projects.router)
app.include_router(tasks.router)

@app.post("/users/register", response_model=UserBase)
def register(user: UserCreate, db: Database = Depends(get_db)):
    """Register a new user."""
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    return new_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db)):
    """Login user and return access and refresh tokens."""
    user = get_user(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@app.post("/refresh", response_model=Token)
def refresh_access_token(refresh_token: str = Body(..., embed=True), db: Database = Depends(get_db)):
    """Refresh an access token."""
    try:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = get_user(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        new_access_token = create_access_token(data={"sub": user.email})
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.get("/users/me", response_model=UserBase)
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Get the current logged-in user."""
    return current_user

class AskRequest(BaseModel):
    question: str
    history: Optional[List[str]] = None

@app.get("/")
def read_root():
    """
    Root endpoint for health checks.
    """
    return {"status": "ok"}

@app.post("/ask")
def ask(request: AskRequest, token: str = Depends(oauth2_scheme)):
    """
    Endpoint to interact with the conversational agent.
    The agent can answer questions or perform actions like creating projects.
    Requires authentication.
    """
    # We pass the raw token to the agent so it can use it for subsequent API calls (tools).
    answer = run_agent(user_query=request.question, history=request.history, auth_token=token)
    return {"answer": answer}