"""Admin management endpoints."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db
from app.models import User, AuditLog, SavedView, ApiKey
from app.schemas import UserResponse, AuditLogResponse, AdminUserCreate
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter()


async def log_audit(
    db: AsyncSession,
    user_id: UUID,
    username: str,
    action: str,
    resource_type: str,
    resource_id: str = None,
    details: dict = None,
    status: str = "success",
    ip_address: str = None,
):
    """Helper function to log audit events."""
    try:
        audit = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            status=status,
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log audit: {e}")


async def check_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to check if user is admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Get all users (admin only), in a stable creation-date order."""
    try:
        result = await db.execute(select(User).order_by(User.created_at))
        users = result.scalars().all()
        return users
    except Exception as exc:
        logger.error(f"Error listing users: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users",
        )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Create a new user account, optionally as admin (admin only)."""
    try:
        result = await db.execute(select(User).filter(User.username == user_in.username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        result = await db.execute(select(User).filter(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_admin=int(user_in.is_admin),
            is_active=1,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        await log_audit(
            db,
            UUID(admin_user["sub"]),
            admin_user["username"],
            "user_created_by_admin",
            "user",
            str(user.id),
            {"created_username": user.username, "is_admin": user_in.is_admin},
        )

        logger.info(f"User created by admin {admin_user['username']}: {user.username}")
        return user

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.error(f"Error creating user: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get audit logs (admin only)."""
    try:
        result = await db.execute(
            select(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        logs = result.scalars().all()
        return logs
    except Exception as exc:
        logger.error(f"Error getting audit logs: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs",
        )


@router.patch("/users/{user_id}/admin")
async def toggle_admin_status(
    user_id: UUID,
    is_admin: bool,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Toggle admin status for a user (admin only)."""
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        old_status = bool(user.is_admin)
        user.is_admin = int(is_admin)
        await db.commit()
        await db.refresh(user)

        # Log the audit
        await log_audit(
            db,
            UUID(admin_user["sub"]),
            admin_user["username"],
            "admin_status_changed",
            "user",
            str(user_id),
            {"old_admin": old_status, "new_admin": is_admin},
        )

        logger.info(f"Admin status updated for user {user.username}: {is_admin}")
        return {"message": "Admin status updated", "user": user}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error updating admin status: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin status",
        )


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Deactivate a user (admin only)."""
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if str(user_id) == admin_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself",
            )

        user.is_active = 0
        await db.commit()
        await db.refresh(user)

        # Log the audit
        await log_audit(
            db,
            UUID(admin_user["sub"]),
            admin_user["username"],
            "user_deactivated",
            "user",
            str(user_id),
        )

        logger.info(f"User deactivated: {user.username}")
        return {"message": "User deactivated", "user": user}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error deactivating user: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user",
        )


@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Activate a user (admin only)."""
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.is_active = 1
        await db.commit()
        await db.refresh(user)

        # Log the audit
        await log_audit(
            db,
            UUID(admin_user["sub"]),
            admin_user["username"],
            "user_activated",
            "user",
            str(user_id),
        )

        logger.info(f"User activated: {user.username}")
        return {"message": "User activated", "user": user}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error activating user: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user",
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Permanently delete a user account (admin only).

    Audit log entries referencing this user are kept but detached (user_id set
    to NULL) so the audit trail survives; saved views and API keys owned
    solely by this user are removed since they have no meaning without it.
    """
    try:
        if str(user_id) == admin_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself",
            )

        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.is_admin:
            admin_count = await db.execute(
                select(func.count(User.id)).filter(User.is_admin == 1)
            )
            if (admin_count.scalar() or 0) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last remaining admin",
                )

        deleted_username = user.username

        await db.execute(
            update(AuditLog).where(AuditLog.user_id == user_id).values(user_id=None)
        )
        await db.execute(delete(SavedView).where(SavedView.user_id == user_id))
        await db.execute(delete(ApiKey).where(ApiKey.user_id == user_id))
        await db.delete(user)
        await db.commit()

        await log_audit(
            db,
            UUID(admin_user["sub"]),
            admin_user["username"],
            "user_deleted",
            "user",
            str(user_id),
            {"deleted_username": deleted_username},
        )

        logger.info(f"User deleted: {deleted_username} by {admin_user['username']}")
        return {"message": "User deleted"}

    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.error(f"Error deleting user: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
