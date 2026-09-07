"""Authentication and user registration endpoints."""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password, create_access_token
from app.db import get_db
from app.models import User, Event, AuditLog
from app.schemas import UserCreate, TokenResponse, UserResponse, EventCreate
from app.services import EventService

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., min_length=3, description="Username")
    password: str = Field(..., min_length=8, description="Password")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account.
    
    Args:
        user_in: User creation schema with username, email, and password
        db: Database session
        
    Returns:
        UserResponse with created user details
        
    Raises:
        HTTPException: If username/email exists or creation fails
    """
    try:
        # Check username uniqueness
        result = await db.execute(select(User).filter(User.username == user_in.username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Registration failed: username already exists: {user_in.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Check email uniqueness
        result = await db.execute(select(User).filter(User.email == user_in.email))
        existing_email = result.scalar_one_or_none()

        if existing_email:
            logger.warning(f"Registration failed: email already exists: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user with hashed password
        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Log user registration as an event
        try:
            event_data = EventCreate(
                source="system",
                event_type="user_registration",
                severity="INFO",
                message=f"New user registered: {user.username}",
                event_metadata={
                    "username": user.username,
                    "email": user.email,
                    "user_id": str(user.id)
                }
            )
            await EventService.create_event(db, event_data)
        except Exception as event_exc:
            logger.warning(f"Failed to log registration event: {event_exc}")
            # Don't fail registration if event logging fails

        # Log audit event for user registration
        try:
            audit = AuditLog(
                username=user.username,
                action="user_created",
                resource_type="user",
                resource_id=str(user.id),
                details={
                    "username": user.username,
                    "email": user.email,
                },
                status="success",
            )
            db.add(audit)
            await db.commit()
        except Exception as audit_exc:
            logger.warning(f"Failed to log audit event: {audit_exc}")

        logger.info(f"User registered successfully: {user.username}")
        return user
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error during registration: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_req: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return JWT access token.
    
    Args:
        login_req: Login request with username and password
        db: Database session
        
    Returns:
        TokenResponse with access token and expiration
        
    Raises:
        HTTPException: If credentials invalid or user inactive
    """
    try:
        # Find user by username
        result = await db.execute(select(User).filter(User.username == login_req.username))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Login failed: user not found: {login_req.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Verify password
        if not verify_password(login_req.password, user.hashed_password):
            logger.warning(f"Login failed: invalid password for user: {login_req.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Check account active
        if not user.is_active:
            logger.warning(f"Login failed: user account inactive: {login_req.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Create JWT access token
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username, "is_admin": bool(user.is_admin)}
        )

        # Log audit event for login
        try:
            audit = AuditLog(
                user_id=user.id,
                username=user.username,
                action="user_login",
                resource_type="user",
                resource_id=str(user.id),
                status="success",
            )
            db.add(audit)
            await db.commit()
        except Exception as audit_exc:
            logger.warning(f"Failed to log login audit event: {audit_exc}")

        logger.info(f"User logged in successfully: {user.username}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            user=user,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error during login: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


__all__ = ["router"]
