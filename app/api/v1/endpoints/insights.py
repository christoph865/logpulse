"""Insight query and creation endpoints."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db
from app.schemas import InsightCreate, InsightResponse
from app.services import InsightService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=InsightResponse, status_code=status.HTTP_201_CREATED)
async def create_insight(
    insight_in: InsightCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> InsightResponse:
    """Create a new insight for an event.
    
    Args:
        insight_in: Insight creation schema
        db: Database session
        
    Returns:
        Created InsightResponse
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        insight = await InsightService.create_insight(db, insight_in)
        logger.info(f"Insight created for event {insight_in.event_id}")
        return insight
    except Exception as exc:
        logger.error(f"Error creating insight: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create insight",
        )


@router.get("", response_model=list[InsightResponse])
async def list_insights(
    event_id: Optional[UUID] = Query(None, description="Filter by event ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[InsightResponse]:
    """List insights with optional filtering.
    
    Args:
        event_id: Optional filter by event ID
        limit: Maximum number of results (default 100, max 1000)
        db: Database session
        
    Returns:
        List of InsightResponse objects
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        insights = await InsightService.get_insights(db, event_id=event_id, limit=limit)
        return insights
    except Exception as exc:
        logger.error(f"Error listing insights: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve insights",
        )


@router.get("/high-confidence", response_model=list[InsightResponse])
async def get_high_confidence_insights(
    min_confidence: float = Query(0.8, ge=0.0, le=1.0, description="Minimum confidence score"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[InsightResponse]:
    """Get high-confidence insights (default min 0.8).
    
    Args:
        min_confidence: Minimum confidence score threshold (default 0.8)
        limit: Maximum number of results (default 50, max 500)
        db: Database session
        
    Returns:
        List of high-confidence InsightResponse objects
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        insights = await InsightService.get_high_confidence_insights(
            db, min_confidence=min_confidence, limit=limit
        )
        return insights
    except Exception as exc:
        logger.error(f"Error retrieving high-confidence insights: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve high-confidence insights",
        )


__all__ = ["router"]
