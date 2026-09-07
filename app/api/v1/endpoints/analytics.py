"""Analytics endpoints."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db
from app.services import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/statistics", response_model=dict)
async def get_statistics(
    source: Optional[str] = Query(None, description="Filter by event source"),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get event statistics for the specified time period.
    
    Args:
        source: Optional event source filter
        hours: Time window in hours (default 24, max 720)
        db: Database session
        
    Returns:
        Dictionary with event statistics and timestamp
    """
    try:
        stats = await AnalyticsService.get_event_statistics(db, source=source, hours=hours)
        return {
            "data": stats,
            "timestamp": datetime.utcnow().isoformat(),
            "time_window_hours": hours,
        }
    except Exception as exc:
        logger.error(f"Error retrieving statistics: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )


@router.get("/summary", response_model=dict)
async def get_summary(
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get analytics summary with aggregated statistics.
    
    Args:
        hours: Time window in hours
        db: Database session
        
    Returns:
        Dictionary with summary data and current timestamp
    """
    try:
        stats = await AnalyticsService.get_event_statistics(db, hours=hours)
        return {
            "summary": stats,
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
        }
    except Exception as exc:
        logger.error(f"Error generating summary: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary",
        )


__all__ = ["router"]
