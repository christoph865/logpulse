"""Celery configuration and background task definitions."""
import logging
from typing import Any

from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "logpulse",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_event_insight(self, event_id: str, event_data: dict[str, Any]) -> dict[str, Any]:
    """Process event and generate AI-powered insight.
    
    Args:
        event_id: UUID of the event
        event_data: Dictionary containing event details
        
    Returns:
        Dictionary with analysis results
        
    Raises:
        Retries on exception with exponential backoff
    """
    try:
        from app.services.ai_service import ai_service
        
        # Call AI service synchronously (no async needed)
        result = ai_service.analyze_event(
            event_data.get("message", ""),
            event_data.get("event_metadata"),
        )
        logger.info(f"Generated insight for event {event_id}")
        return {
            "event_id": event_id,
            "analysis": result["analysis"],
            "confidence": result["confidence_score"],
            "recommendations": result["recommendations"],
        }
            
    except Exception as exc:
        logger.error(f"Error processing event {event_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task
def cleanup_old_events(days: int = 30) -> dict[str, Any]:
    """Clean up events older than specified days.
    
    Args:
        days: Number of days to retain (default: 30)
        
    Returns:
        Dictionary with deletion stats
    """
    try:
        import asyncio
        from app.db import async_session_maker
        from app.services import EventService
        
        async def cleanup() -> int:
            async with async_session_maker() as db:
                return await EventService.delete_old_events(db, days)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            deleted_count = loop.run_until_complete(cleanup())
            logger.info(f"Deleted {deleted_count} events older than {days} days")
            return {"deleted_events": deleted_count, "days_retained": days}
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Error during cleanup: {exc}", exc_info=True)
        raise


@celery_app.task
def generate_daily_report() -> dict[str, Any]:
    """Generate daily analytics report.
    
    Returns:
        Dictionary with report summary
    """
    try:
        import asyncio
        from app.db import async_session_maker
        from app.services import AnalyticsService
        from app.services.ai_service import ai_service
        
        async def report() -> str:
            async with async_session_maker() as db:
                stats = await AnalyticsService.get_event_statistics(db, hours=24)
                summary = await ai_service.generate_performance_report(stats)
                return summary
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(report())
            logger.info("Daily report generated successfully")
            return {"report": result, "period": "daily"}
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Error generating report: {exc}", exc_info=True)
        raise


__all__ = ["celery_app", "process_event_insight", "cleanup_old_events", "generate_daily_report"]
