"""Anomaly detection service using statistical analysis."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from statistics import mean, stdev

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, AnomalyAlert

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Service for detecting anomalies in event patterns."""

    # Configurable thresholds
    Z_SCORE_THRESHOLD = 2.0  # Standard deviations from mean
    MIN_SAMPLES = 5  # Minimum data points to detect anomaly
    TIME_WINDOW_HOURS = 24  # Look back period

    @staticmethod
    async def detect_anomalies(
        db: AsyncSession,
        lookback_hours: int = 24,
    ) -> List[AnomalyAlert]:
        """
        Detect anomalies in event patterns.
        
        Args:
            db: Database session
            lookback_hours: Hours to look back for analysis
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        try:
            # Get unique sources
            result = await db.execute(select(Event.source).distinct())
            sources = result.scalars().all()
            
            for source in sources:
                # Check for spike/drop anomalies
                source_anomalies = await AnomalyDetectionService._check_source_anomalies(
                    db, source, lookback_hours
                )
                anomalies.extend(source_anomalies)
            
            logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    @staticmethod
    async def _check_source_anomalies(
        db: AsyncSession,
        source: str,
        lookback_hours: int,
    ) -> List[AnomalyAlert]:
        """Check a specific source for anomalies."""
        anomalies = []
        
        try:
            # Get hourly event counts for the source
            now = datetime.utcnow()
            start_time = now - timedelta(hours=lookback_hours)
            
            # Get events by severity
            for severity in ["CRITICAL", "ERROR", "WARNING", "INFO"]:
                hourly_counts = await AnomalyDetectionService._get_hourly_counts(
                    db, source, severity, start_time, now
                )
                
                if len(hourly_counts) >= AnomalyDetectionService.MIN_SAMPLES:
                    # Check for anomalies
                    detected = AnomalyDetectionService._detect_statistical_anomalies(
                        hourly_counts, source, severity
                    )
                    anomalies.extend(detected)
        
        except Exception as e:
            logger.error(f"Error checking source {source} for anomalies: {e}")
        
        return anomalies

    @staticmethod
    async def _get_hourly_counts(
        db: AsyncSession,
        source: str,
        severity: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[int, int]:
        """Get hourly event counts for a source and severity."""
        try:
            result = await db.execute(
                select(
                    func.date_trunc("hour", Event.timestamp).label("hour"),
                    func.count(Event.id).label("count"),
                )
                .filter(Event.source == source)
                .filter(Event.severity == severity)
                .filter(Event.timestamp >= start_time)
                .filter(Event.timestamp <= end_time)
                .group_by("hour")
                .order_by("hour")
            )
            
            rows = result.all()
            return {int(row[0].timestamp()): row[1] for row in rows} if rows else {}
            
        except Exception as e:
            logger.error(f"Error getting hourly counts: {e}")
            return {}

    @staticmethod
    def _detect_statistical_anomalies(
        hourly_counts: Dict[int, int],
        source: str,
        severity: str,
    ) -> List[AnomalyAlert]:
        """Detect anomalies using statistical analysis (z-score)."""
        anomalies = []
        
        try:
            if not hourly_counts:
                return anomalies
            
            values = list(hourly_counts.values())
            
            # Calculate statistics
            avg = mean(values)
            std_dev = stdev(values) if len(values) > 1 else 0
            
            # Check each hour
            for timestamp, count in hourly_counts.items():
                if std_dev == 0:
                    continue
                
                z_score = abs((count - avg) / std_dev)
                
                if z_score > AnomalyDetectionService.Z_SCORE_THRESHOLD:
                    deviation_percent = ((count - avg) / (avg + 1)) * 100
                    anomaly_type = "spike" if count > avg else "drop"
                    
                    anomaly = AnomalyAlert(
                        source=source,
                        severity=severity,
                        anomaly_type=anomaly_type,
                        baseline_value=avg,
                        observed_value=count,
                        deviation_percent=deviation_percent,
                        z_score=z_score,
                        detected_at=datetime.fromtimestamp(timestamp),
                        is_acknowledged=0,
                    )
                    anomalies.append(anomaly)
        
        except Exception as e:
            logger.error(f"Error detecting statistical anomalies: {e}")
        
        return anomalies

    @staticmethod
    async def acknowledge_anomaly(
        db: AsyncSession,
        anomaly_id: str,
    ) -> bool:
        """Mark an anomaly as acknowledged."""
        try:
            result = await db.execute(
                select(AnomalyAlert).filter(AnomalyAlert.id == anomaly_id)
            )
            anomaly = result.scalar_one_or_none()
            
            if anomaly:
                anomaly.is_acknowledged = 1
                await db.commit()
                logger.info(f"Anomaly {anomaly_id} acknowledged")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error acknowledging anomaly: {e}")
            await db.rollback()
            return False
