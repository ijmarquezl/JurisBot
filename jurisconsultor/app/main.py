import logging
from logging.config import dictConfig
from logging_config import LOGGING_CONFIG

# Apply logging configuration as early as possible
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Depends, HTTPException, status, Body, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pymongo.database import Database
from jose import JWTError
from pydantic import BaseModel
from typing import Optional, List

from graph_agent import graph # New LangGraph agent
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.errors import GraphRecursionError

from models import UserCreate, UserInDB, Token, TokenData, UserBase, UserResponse
from security import create_access_token, create_refresh_token, verify_password, verify_token
from users import create_user, get_user
from utils import get_mongo_client
from routers import projects, tasks, admin, documents, sources, superadmin
from dependencies import get_db, get_current_user, oauth2_scheme

from db_manager import close_db_connection

app = FastAPI(
    title="Jurisconsultor API",
    description="API for the Jurisconsultor AI agent.",
    version="0.6.0", # Version bump for new DB architecture
)

# --- CORS Middleware ---
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup. MongoDB client initialized.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing MongoDB connection.")
    close_db_connection()

# --- API Routers ---
auth_router = APIRouter()

@auth_router.post("/users/register", response_model=UserBase, tags=["Auth"])
def register(user: UserCreate, db: Database = Depends(get_db)):
    """Register a new user."""
    logger.info(f"Registering new user: {user.email}")
    db_user = get_user(db, email=user.email)
    if db_user:
        logger.warning(f"Registration failed for email {user.email}: Email already registered.")
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    logger.info(f"User {user.email} registered successfully.")
    return new_user

@auth_router.post("/token", response_model=Token, tags=["Auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Database = Depends(get_db)):
    """Login user and return access and refresh tokens."""
    logger.info(f"Login attempt for user: {form_data.username}")
    user = get_user(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    logger.info(f"User {form_data.username} logged in successfully.")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@auth_router.post("/refresh", response_model=Token, tags=["Auth"])
def refresh_access_token(refresh_token: str = Body(..., embed=True), db: Database = Depends(get_db)):
    """Refresh an access token."""
    logger.info("Attempting to refresh access token.")
    try:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type for refresh.")
            raise HTTPException(status_code=401, detail="Invalid token type")
        email = payload.get("sub")
        if email is None:
            logger.warning("Invalid token: no email subject.")
            raise HTTPException(status_code=401, detail="Invalid token")
        user = get_user(db, email=email)
        if user is None:
            logger.warning(f"User not found for token refresh: {email}")
            raise HTTPException(status_code=401, detail="User not found")
        
        new_access_token = create_access_token(data={"sub": user.email})
        logger.info(f"Token refreshed successfully for user: {email}")
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except JWTError:
        logger.error("Invalid refresh token.", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@auth_router.get("/users/me", response_model=UserResponse, tags=["Auth"])
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Get the current logged-in user."""
    return current_user

app.include_router(auth_router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(superadmin.router, prefix="/api")

class AskRequest(BaseModel):
    question: str

@app.get("/")
def read_root():
    """Root endpoint for health checks."""
    return {"status": "ok"}

@app.post("/ask")
async def ask(
    request: AskRequest,
    current_user: UserInDB = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    """Endpoint to interact with the new LangGraph conversational agent."""
    logger.info(f"User {current_user.email} is asking: '{request.question}'")
    logger.info(f"[BEFORE TRY] About to invoke graph")
    
    config = {"configurable": {"thread_id": current_user.email}, "recursion_limit": 50}
    # Pass the access token into the graph's state
    inputs = {"messages": [HumanMessage(content=request.question)], "access_token": token, "company_id": str(current_user.company_id)}
    final_answer = "Lo siento, no pude procesar tu solicitud."
    
    try:
        logger.info(f"[IN TRY] Invoking graph with inputs: messages={len(inputs['messages'])}, company_id={inputs['company_id']}")
        final_state = graph.invoke(inputs, config=config)
        logger.info(f"[AFTER INVOKE] Graph returned. Type: {type(final_state)}")
        if final_state and final_state.get("messages"):
            logger.info(f"[MESSAGES] Number of messages in final_state: {len(final_state['messages'])}")
            last_message = final_state["messages"][-1]
            logger.info(f"[LAST MSG] Last message type: {type(last_message).__name__}")
            if hasattr(last_message, 'content'):
                content_preview = str(last_message.content)[:200]
                logger.info(f"[CONTENT] Last message content preview: {content_preview}")
            if isinstance(last_message, AIMessage):
                final_answer = last_message.content
            else:
                final_answer = str(last_message)

        logger.info(f"Agent provided answer to {current_user.email}.")
        return {"answer": final_answer}
    except GraphRecursionError as e:
        logger.error(f"[EXCEPTION] Agent recursion limit reached: {e}", exc_info=True)
        return {"answer": "Lo siento, el agente entró en un bucle y no pudo completar tu solicitud. Por favor, intenta reformular tu pregunta."}
    except Exception as e:
        logger.error(f"[EXCEPTION] An unexpected error occurred in the agent: {e}", exc_info=True)
        return {"answer": "Lo siento, ocurrió un error inesperado al procesar tu solicitud."}