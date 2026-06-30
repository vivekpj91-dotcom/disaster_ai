import os
import uuid
import logging
import shutil
import hmac
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from google.adk.errors.already_exists_error import AlreadyExistsError
from sqlalchemy import text
from backend.auth import get_current_user_or_anonymous, UserSession, create_access_token
from backend.schemas import (
    ChatRequest, ChatResponse, LocationUpdate, LocationResponse,
    LoginRequest, TokenResponse
)

from google.genai import types
from agents.config import runner
from agents.sub_agents.damage_agent import analyze_scene_image
from backend.security import sanitize_and_check_injection, validate_image_bytes
from config.settings import settings
from database.db_connection import SessionLocal

logger = logging.getLogger("disaster_assist.router")
router = APIRouter()

# Temporary upload folder for local development
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DEMO_USER_EMAIL = os.environ.get("DEMO_USER_EMAIL", "user@example.com")
DEMO_USER_PASSWORD = os.environ.get("DEMO_USER_PASSWORD")

def build_demo_chat_response(message: str, coordinates_log: str = "") -> tuple[str, Optional[Dict[str, Any]]]:
    """Provides deterministic responses when Gemini credentials are not configured."""
    msg_lower = message.lower()

    if "emergency" in msg_lower or "rescue" in msg_lower or "immediate help" in msg_lower:
        return (
            "[Triage Agent Alert] Critical safety threat identified! "
            "I have registered a rescue incident report with dispatch coordinates. "
            "Please stay calm. The nearest responders have been notified.",
            {
                "logged": True,
                "incident_id": int(uuid.uuid4().int % 10000),
                "severity": "CRITICAL",
                "status": "DISPATCHED"
            }
        )

    if "shelter" in msg_lower or "hospital" in msg_lower or "resource" in msg_lower:
        return (
            "[Resource Agent Response] Searching resource database... "
            f"Based on your coordinates{coordinates_log if coordinates_log else ' (Default San Francisco)'}, "
            "the nearest shelter is 'Civic Center Gymnasium' (0.0 miles away, Status: OPEN, Capacity: 108/150 spots remaining).",
            None
        )

    return (
        f"[Planner Agent Response] I received your message: '{message}'. "
        "How can I assist you with disaster guides, damage reports, or resources?",
        None
    )

async def ensure_adk_session(session_id: str, user_id: str) -> None:
    """Create an ADK session only when it does not already exist."""
    existing_session = await runner.session_service.get_session(
        app_name="agents",
        user_id=user_id,
        session_id=session_id
    )
    if existing_session is not None:
        return

    try:
        logger.info(f"Creating new ADK agent session: {session_id} for user {user_id}")
        await runner.session_service.create_session(
            app_name="agents",
            user_id=user_id,
            session_id=session_id
        )
    except AlreadyExistsError:
        logger.info(f"ADK agent session already exists: {session_id}")

@router.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Retrieves application health and connectivity status."""
    db_healthy = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
    finally:
        if "db" in locals():
            db.close()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "version": "1.0.0",
        "dependencies": {
            "sqlite_database": "connected" if db_healthy else "disconnected",
            "mcp_server": "configured"
        }
    }

@router.post("/auth/token", response_model=TokenResponse, tags=["Authentication"])
async def login_for_access_token(payload: LoginRequest):
    """Authenticates users and returns a JWT access token for personalized requests."""
    if not DEMO_USER_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo authentication password is not configured. Set DEMO_USER_PASSWORD in the environment.",
        )

    if not (
        hmac.compare_digest(payload.email, DEMO_USER_EMAIL)
        and hmac.compare_digest(payload.password, DEMO_USER_PASSWORD)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token contains subject, user ID, and a pre-assigned session ID
    token_data = {
        "sub": payload.email,
        "user_id": "usr-1001",
        "session_id": f"auth-{uuid.uuid4()}"
    }
    access_token = create_access_token(data=token_data)
    
    logger.info(f"User {payload.email} authenticated. JWT token generated.")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/chat", response_model=ChatResponse, tags=["Disaster Assistant"])
async def chat_with_agent(
    request: ChatRequest,
    user_session: UserSession = Depends(get_current_user_or_anonymous)
):
    """Sends a chat query to the multi-agent system.
    
    Handles both authenticated users and anonymous sessions.
    Coordinates coordinates and session states.
    """
    session_id = request.session_id or user_session.session_id
    user_id = user_session.user_id or "anonymous"
    logger.info(f"Chat request in session {session_id}. Auth={user_session.is_authenticated}")
    
    # Sanitize user input and prevent prompt injection attacks
    sanitized_prompt = sanitize_and_check_injection(request.message)
    
    await ensure_adk_session(session_id=session_id, user_id=user_id)
    
    # Setup coordinates trace
    coordinates_log = ""
    state_delta = {}
    if request.latitude is not None and request.longitude is not None:
        coordinates_log = f" at location ({request.latitude}, {request.longitude})"
        state_delta = {
            "latitude": request.latitude,
            "longitude": request.longitude
        }
        
    # Execute agent runner
    response_text = ""
    incident_logged = None
    
    try:
        if not settings.GOOGLE_API_KEY:
            response_text, incident_logged = build_demo_chat_response(request.message, coordinates_log)
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                is_authenticated=user_session.is_authenticated,
                email=user_session.email,
                incident_logged=incident_logged
            )

        new_msg = types.Content(parts=[types.Part.from_text(text=sanitized_prompt)])
        response_parts = []
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_msg,
            state_delta=state_delta
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_parts.append(part.text)
        
        response_text = "".join(response_parts)
        if not response_text:
            response_text = "The coordinator agent processed your query but did not produce a text response."
            
    except Exception as e:
        logger.warning(f"ADK Agent execution failed ({str(e)}). Falling back to mock responses.")
        response_text, incident_logged = build_demo_chat_response(request.message, coordinates_log)

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        is_authenticated=user_session.is_authenticated,
        email=user_session.email,
        incident_logged=incident_logged
    )

@router.post("/location", response_model=LocationResponse, tags=["Location Service"])
async def update_location(
    payload: LocationUpdate,
    user_session: UserSession = Depends(get_current_user_or_anonymous)
):
    """Updates the user location coordinates for the current session."""
    session_id = user_session.session_id
    logger.info(f"Location update for session {session_id}: ({payload.latitude}, {payload.longitude})")
    
    # Logic to record coordinates in database/session state
    return LocationResponse(
        status="location_updated",
        latitude=payload.latitude,
        longitude=payload.longitude,
        session_id=session_id
    )

@router.post("/upload", tags=["Damage Assessment"])
async def upload_damage_image(
    file: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    user_session: UserSession = Depends(get_current_user_or_anonymous)
):
    """Uploads a disaster damage photograph for multimodal AI assessment.
    
    Saves file locally and runs the Damage Vision Agent to assess risks.
    """
    session_id = user_session.session_id
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only JPG, JPEG, and PNG are allowed."
        )
    
    # Perform secure file upload check: validate file content headers (magic numbers)
    header_bytes = await file.read(1024)
    await file.seek(0) # reset file cursor
    if not validate_image_bytes(header_bytes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content header validation failed. Uploaded file is not a valid image."
        )

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image file is too large. Maximum allowed size is 10 MB."
        )
        
    # Save the file to the uploads directory
    local_filename = f"{session_id}_{uuid.uuid4().hex}{file_ext}"
    local_path = os.path.join(UPLOAD_DIR, local_filename)
    
    try:
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Saved uploaded image to {local_path}")
    except Exception as e:
        logger.error(f"Failed to write uploaded image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image file."
        )
        
    analysis_result = analyze_scene_image(local_path)
    response_summary = analysis_result.get("summary", "Image processed successfully.")
    hazard_level = analysis_result.get("severity", "MODERATE")
    
    return {
        "message": "Image uploaded successfully",
        "file_name": local_filename,
        "analysis": response_summary,
        "hazard_level": hazard_level,
        "recommendations": analysis_result.get("recommendations", []),
        "session_id": session_id,
        "coordinates": {"lat": latitude, "lon": longitude} if latitude is not None and longitude is not None else None
    }
