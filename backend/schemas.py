from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """Payload to send a chat message to the agent."""
    message: str = Field(..., description="User prompt text")
    session_id: Optional[str] = Field(None, description="Active session ID, if continuing a thread")
    latitude: Optional[float] = Field(None, description="User current latitude")
    longitude: Optional[float] = Field(None, description="User current longitude")

class ChatResponse(BaseModel):
    """Payload returned by the chat interface."""
    response: str = Field(..., description="Agent synthesized text response")
    session_id: str = Field(..., description="Session ID associated with the interaction")
    is_authenticated: bool = Field(..., description="Whether the session is authenticated")
    email: Optional[str] = Field(None, description="User email if authenticated")
    incident_logged: Optional[Dict[str, Any]] = Field(None, description="Details of any registered incident reports")

class LocationUpdate(BaseModel):
    """Payload to update coordinates for a session."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

class LocationResponse(BaseModel):
    """Response returned after updating user coordinates."""
    status: str
    latitude: float
    longitude: float
    session_id: str

class LoginRequest(BaseModel):
    """Payload to request an access token."""
    email: str = Field(..., example="user@example.com")
    password: str = Field(..., example="demo-password")

class TokenResponse(BaseModel):
    """JWT response structure."""
    access_token: str
    token_type: str = "bearer"
