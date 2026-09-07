"""Service layer for business logic."""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, Insight, AnalyticsAggregation
from app.schemas import EventCreate, InsightCreate


class EventService:
    """Service for event operations."""

    @staticmethod
    async def create_event(db: AsyncSession, event_in: EventCreate) -> Event:
        """Create a new event in the database.
        
        Args:
            db: Database session
            event_in: Event creation schema
            
        Returns:
            Created Event model instance
        """
        event = Event(
            source=event_in.source,
            event_type=event_in.event_type,
            severity=event_in.severity,
            message=event_in.message,
            event_metadata=event_in.event_metadata,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_event(db: AsyncSession, event_id: UUID) -> Optional[Event]:
        """Retrieve event by ID.
        
        Args:
            db: Database session
            event_id: Event UUID
            
        Returns:
            Event if found, None otherwise
        """
        result = await db.execute(select(Event).filter(Event.id == event_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_events(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        source: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> list[Event]:
        """Retrieve events with optional filtering.
        
        Args:
            db: Database session
            skip: Pagination offset
            limit: Pagination limit
            source: Optional source filter
            severity: Optional severity filter
            
        Returns:
            List of Event instances
        """
        query = select(Event)

        if source:
            query = query.filter(Event.source == source)
        if severity:
            query = query.filter(Event.severity == severity)

        query = query.order_by(Event.timestamp.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def delete_old_events(db: AsyncSession, days: int = 30) -> int:
        """Delete events older than specified days.
        
        Args:
            db: Database session
            days: Number of days to retain
            
        Returns:
            Number of deleted events
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(Event).filter(Event.created_at < cutoff_date)
        )
        events = result.scalars().all()
        for event in events:
            await db.delete(event)
        await db.commit()
        return len(events)


class InsightService:
    """Service for insight operations."""

    @staticmethod
    async def create_insight(db: AsyncSession, insight_in: InsightCreate) -> Insight:
        """Create a new insight.
        
        Args:
            db: Database session
            insight_in: Insight creation schema
            
        Returns:
            Created Insight model instance
        """
        insight = Insight(
            event_id=insight_in.event_id,
            insight_type=insight_in.insight_type,
            confidence_score=insight_in.confidence_score,
            analysis=insight_in.analysis,
            recommendations=insight_in.recommendations,
        )
        db.add(insight)
        await db.commit()
        await db.refresh(insight)
        return insight

    @staticmethod
    async def get_insights(
        db: AsyncSession,
        event_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> list[Insight]:
        """Retrieve insights with optional filtering.
        
        Args:
            db: Database session
            event_id: Optional event ID filter
            limit: Maximum number to return
            
        Returns:
            List of Insight instances
        """
        query = select(Insight)

        if event_id:
            query = query.filter(Insight.event_id == event_id)

        query = query.order_by(Insight.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_high_confidence_insights(
        db: AsyncSession,
        min_confidence: float = 0.8,
        limit: int = 50,
    ) -> list[Insight]:
        """Retrieve high confidence insights.
        
        Args:
            db: Database session
            min_confidence: Minimum confidence score threshold
            limit: Maximum number to return
            
        Returns:
            List of high-confidence Insight instances
        """
        query = (
            select(Insight)
            .filter(Insight.confidence_score >= min_confidence)
            .order_by(Insight.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()


class AnalyticsService:
    """Service for analytics and reporting."""

    @staticmethod
    async def get_event_statistics(
        db: AsyncSession,
        source: Optional[str] = None,
        hours: int = 24,
    ) -> dict[str, Any]:
        """Calculate event statistics for a time period.
        
        Args:
            db: Database session
            source: Optional source filter
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with statistics including:
            - total_events: Total event count
            - by_severity: Count by severity level
            - by_type: Count by event type
            - time_range_hours: Hours analyzed
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = select(Event).filter(Event.created_at >= cutoff_time)

        if source:
            query = query.filter(Event.source == source)

        result = await db.execute(query)
        events = result.scalars().all()

        # Aggregate statistics
        severity_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        
        for event in events:
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
            type_counts[event.event_type] = type_counts.get(event.event_type, 0) + 1

        return {
            "total_events": len(events),
            "by_severity": severity_counts,
            "by_type": type_counts,
            "time_range_hours": hours,
        }

    @staticmethod
    async def create_aggregation(
        db: AsyncSession,
        time_bucket: datetime,
        source: str,
        event_type: str,
        count: int,
        error_count: int,
        avg_score: Optional[float] = None,
    ) -> AnalyticsAggregation:
        """Create time-series aggregation record.
        
        Args:
            db: Database session
            time_bucket: Time bucket for aggregation
            source: Event source
            event_type: Event type
            count: Total event count
            error_count: Error event count
            avg_score: Optional average severity score
            
        Returns:
            Created AnalyticsAggregation instance
        """
        agg = AnalyticsAggregation(
            time_bucket=time_bucket,
            source=source,
            event_type=event_type,
            count=count,
            error_count=error_count,
            avg_severity_score=avg_score,
        )
        db.add(agg)
        await db.commit()
        await db.refresh(agg)
        return agg


__all__ = ["EventService", "InsightService", "AnalyticsService"]
