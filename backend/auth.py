import jwt
import datetime
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from config.settings import settings

logger = logging.getLogger("disaster_assist.auth")

# FastAPI security scheme for parsing Bearer tokens
security_scheme = HTTPBearer(auto_error=False)

class UserSession(BaseModel):
    """Represents a session, which can be authenticated or anonymous."""
    session_id: str
    is_authenticated: bool
    email: Optional[str] = None
    user_id: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generates a JWT access token for authentication."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user_or_anonymous(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> UserSession:
    """Dependency that extracts user session. 
    
    If valid Bearer token is provided, returns an Authenticated UserSession.
    If no token is provided, returns an Anonymous UserSession with a new UUID.
    """
    if credentials is None:
        # Generate anonymous session
        anon_id = f"anon-{uuid.uuid4()}"
        logger.debug(f"Allocating new anonymous session: {anon_id}")
        return UserSession(
            session_id=anon_id,
            is_authenticated=False
        )
        
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        session_id: str = payload.get("session_id") or f"auth-{uuid.uuid4()}"
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload invalid, subject missing"
            )
            
        return UserSession(
            session_id=session_id,
            is_authenticated=True,
            email=email,
            user_id=user_id
        )
    except jwt.PyJWTError as e:
        logger.warning(f"Failed to decode token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
