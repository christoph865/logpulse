"""Saved views endpoints for user filter workflows."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.api.dependencies import get_current_user
from app.models import SavedView
from app.schemas import SavedViewCreate, SavedViewResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/saved-views", tags=["saved-views"])


@router.post("", response_model=SavedViewResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_view(
    view_data: SavedViewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new saved filter view."""
    try:
        user_id = UUID(current_user["sub"])
        
        new_view = SavedView(
            user_id=user_id,
            name=view_data.name,
            description=view_data.description,
            filters=view_data.filters,
            is_pinned=int(view_data.is_pinned),
        )
        
        db.add(new_view)
        await db.commit()
        await db.refresh(new_view)
        
        logger.info(f"Saved view created: {new_view.id} by user {user_id}")
        return new_view
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating saved view: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create saved view",
        )


@router.get("", response_model=List[SavedViewResponse])
async def list_saved_views(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all saved views for the current user."""
    try:
        user_id = UUID(current_user["sub"])
        
        result = await db.execute(
            select(SavedView)
            .filter(SavedView.user_id == user_id)
            .order_by(desc(SavedView.is_pinned), desc(SavedView.created_at))
        )
        
        views = result.scalars().all()
        return views
    except Exception as e:
        logger.error(f"Error fetching saved views: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch saved views",
        )


@router.get("/{view_id}", response_model=SavedViewResponse)
async def get_saved_view(
    view_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific saved view."""
    try:
        user_id = UUID(current_user["sub"])
        
        result = await db.execute(
            select(SavedView)
            .filter(SavedView.id == view_id)
            .filter(SavedView.user_id == user_id)
        )
        
        view = result.scalar_one_or_none()
        if not view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved view not found",
            )
        
        return view
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching saved view {view_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch saved view",
        )


@router.patch("/{view_id}", response_model=SavedViewResponse)
async def update_saved_view(
    view_id: UUID,
    view_data: SavedViewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a saved view."""
    try:
        user_id = UUID(current_user["sub"])
        
        result = await db.execute(
            select(SavedView)
            .filter(SavedView.id == view_id)
            .filter(SavedView.user_id == user_id)
        )
        
        view = result.scalar_one_or_none()
        if not view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved view not found",
            )
        
        view.name = view_data.name
        view.description = view_data.description
        view.filters = view_data.filters
        view.is_pinned = int(view_data.is_pinned)
        
        await db.commit()
        await db.refresh(view)
        
        logger.info(f"Saved view updated: {view_id}")
        return view
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating saved view {view_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update saved view",
        )


@router.delete("/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_view(
    view_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a saved view."""
    try:
        user_id = UUID(current_user["sub"])
        
        result = await db.execute(
            select(SavedView)
            .filter(SavedView.id == view_id)
            .filter(SavedView.user_id == user_id)
        )
        
        view = result.scalar_one_or_none()
        if not view:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved view not found",
            )
        
        await db.delete(view)
        await db.commit()
        
        logger.info(f"Saved view deleted: {view_id}")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting saved view {view_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete saved view",
        )
