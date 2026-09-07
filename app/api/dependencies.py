"""API dependencies for authentication and database access."""
from typing import Any
import logging

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db import get_db

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> dict[str, Any]:
    """Extract and validate current user from JWT token in Authorization header.
    
    Args:
        request: HTTP request object
        
    Returns:
        Dictionary containing decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"Invalid Authorization header format: {auth_header[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    payload = decode_token(token)
    
    if payload is None:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_db_session() -> AsyncSession:
    """Get database session as dependency.
    
    Yields:
        AsyncSession: Database session
    """
    async with get_db() as db:
        yield db


__all__ = ["get_current_user", "get_db_session"]
