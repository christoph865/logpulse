"""Anomaly detection endpoints."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.api.dependencies import get_current_user
from app.models import AnomalyAlert
from app.schemas import AnomalyAlertResponse
from app.services.anomaly_detection import AnomalyDetectionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("/alerts", response_model=List[AnomalyAlertResponse])
async def get_anomalies(
    limit: int = 50,
    offset: int = 0,
    acknowledged: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get detected anomalies."""
    try:
        query = select(AnomalyAlert)
        
        if not acknowledged:
            query = query.filter(AnomalyAlert.is_acknowledged == False)
        
        query = query.order_by(desc(AnomalyAlert.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        anomalies = result.scalars().all()
        
        return anomalies
    except Exception as e:
        logger.error(f"Error fetching anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch anomalies",
        )


@router.post("/detect", response_model=List[AnomalyAlertResponse])
async def run_anomaly_detection(
    lookback_hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Run anomaly detection and return detected anomalies."""
    try:
        # Detect anomalies
        anomalies = await AnomalyDetectionService.detect_anomalies(db, lookback_hours)
        
        # Store in database
        for anomaly in anomalies:
            db.add(anomaly)
        
        await db.commit()
        
        logger.info(f"Anomaly detection complete: {len(anomalies)} anomalies detected")
        return anomalies
    except Exception as e:
        await db.rollback()
        logger.error(f"Error running anomaly detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run anomaly detection",
        )


@router.patch("/acknowledge/{anomaly_id}", response_model=AnomalyAlertResponse)
async def acknowledge_anomaly(
    anomaly_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Acknowledge an anomaly alert."""
    try:
        result = await db.execute(
            select(AnomalyAlert).filter(AnomalyAlert.id == anomaly_id)
        )
        anomaly = result.scalar_one_or_none()
        
        if not anomaly:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Anomaly not found",
            )
        
        anomaly.is_acknowledged = True
        await db.commit()
        await db.refresh(anomaly)
        
        logger.info(f"Anomaly {anomaly_id} acknowledged by {current_user['username']}")
        return anomaly
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error acknowledging anomaly: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge anomaly",
        )


@router.get("/summary", response_model=dict)
async def get_anomaly_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get summary of recent anomalies."""
    try:
        from sqlalchemy import func
        
        result = await db.execute(
            select(
                func.count(AnomalyAlert.id).label("total"),
                func.count(
                    AnomalyAlert.id
                ).filter(AnomalyAlert.is_acknowledged == False).label("unacknowledged"),
            )
        )
        
        row = result.first()
        
        return {
            "total_anomalies": row[0] or 0,
            "unacknowledged": row[1] or 0,
        }
    except Exception as e:
        logger.error(f"Error getting anomaly summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get anomaly summary",
        )
