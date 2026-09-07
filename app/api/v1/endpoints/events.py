"""Event management endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db
from app.schemas import EventCreate, EventResponse
from app.services import EventService
from app.tasks import process_event_insight

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_in: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> EventResponse:
    """Create a new event and trigger insight generation.
    
    Args:
        event_in: Event creation schema
        db: Database session
        
    Returns:
        Created EventResponse
        
    Raises:
        HTTPException: If event creation fails
    """
    try:
        event = await EventService.create_event(db, event_in)

        # Trigger async insight generation task
        process_event_insight.delay(
            str(event.id),
            {
                "message": event.message,
                "event_metadata": event.event_metadata,
                "severity": event.severity,
                "event_type": event.event_type,
                "source": event.source,
            },
        )

        logger.info(f"Event created: {event.id}")
        return event
        
    except Exception as exc:
        logger.error(f"Error creating event: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event",
        )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> EventResponse:
    """Retrieve event by ID.
    
    Args:
        event_id: Event UUID
        db: Database session
        
    Returns:
        EventResponse
        
    Raises:
        HTTPException: If event not found or retrieval fails
    """
    try:
        event = await EventService.get_event(db, event_id)
        if not event:
            logger.warning(f"Event not found: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found",
            )
        return event
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving event {event_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event",
        )


@router.get("", response_model=list[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    source: Optional[str] = Query(None, description="Filter by event source"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[EventResponse]:
    """List events with optional filtering and pagination.
    
    Args:
        skip: Pagination offset
        limit: Pagination limit (max 1000)
        source: Optional source filter
        severity: Optional severity filter
        db: Database session
        
    Returns:
        List of EventResponse objects
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        events = await EventService.get_events(
            db, skip=skip, limit=limit, source=source, severity=severity
        )
        return events
    except Exception as exc:
        logger.error(f"Error listing events: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list events",
        )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete an event by ID.
    
    Args:
        event_id: Event UUID to delete
        db: Database session
        
    Raises:
        HTTPException: If event not found or deletion fails
    """
    try:
        event = await EventService.get_event(db, event_id)
        if not event:
            logger.warning(f"Event not found for deletion: {event_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found",
            )
        await db.delete(event)
        await db.commit()
        logger.info(f"Event deleted: {event_id}")
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error deleting event {event_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event",
        )


__all__ = ["router"]
