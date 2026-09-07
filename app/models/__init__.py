"""Database models."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Integer,
    Boolean,
    JSON,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Event(Base):
    """Event model for storing log events."""

    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    event_metadata = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationship to insights
    insights = relationship("Insight", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_event_timestamp_source", "timestamp", "source"),
        Index("idx_event_severity_type", "severity", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type={self.event_type}, severity={self.severity})>"


class Insight(Base):
    """Insight model for AI-generated analysis."""

    __tablename__ = "insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    insight_type = Column(String(100), nullable=False)  # ANOMALY, RECOMMENDATION, ALERT
    confidence_score = Column(Float, nullable=False)
    analysis = Column(Text, nullable=False)
    recommendations = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationship to event
    event = relationship("Event", back_populates="insights")

    __table_args__ = (Index("idx_insight_timestamp_type", "created_at", "insight_type"),)

    def __repr__(self) -> str:
        return f"<Insight(id={self.id}, type={self.insight_type}, confidence={self.confidence_score})>"


class AnalyticsAggregation(Base):
    """Time-series aggregation of events for analytics."""

    __tablename__ = "analytics_aggregations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_bucket = Column(DateTime(timezone=True), nullable=False, index=True)  # 5-minute, 1-hour buckets
    source = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    avg_severity_score = Column(Float, nullable=True)
    aggregated_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_aggregation_time_source", "time_bucket", "source"),
        Index("idx_aggregation_time_type", "time_bucket", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsAggregation(time_bucket={self.time_bucket}, source={self.source})>"


class User(Base):
    """User model for API authentication."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    is_admin = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class ApiKey(Base):
    """API key model for external integrations."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    is_active = Column(Integer, nullable=False, default=1)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name})>"


class AuditLog(Base):
    """Audit log model for tracking all system actions."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # user_created, user_deleted, user_updated, user_login, event_created, etc.
    resource_type = Column(String(100), nullable=False, index=True)  # user, event, admin_panel, etc.
    resource_id = Column(String(255), nullable=True, index=True)
    details = Column(JSONB, nullable=True)  # Stores what was changed
    ip_address = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="success")  # success, failed
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_audit_user_timestamp", "user_id", "created_at"),
        Index("idx_audit_action_resource", "action", "resource_type"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.username})>"


class SavedView(Base):
    """Saved filter views for user workflows."""

    __tablename__ = "saved_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filters = Column(JSONB, nullable=False)  # {severity: ['CRITICAL'], sourceFilter: 'api', timeRange: 24, etc}
    is_pinned = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_saved_view_user", "user_id"),
        Index("idx_saved_view_pinned", "user_id", "is_pinned"),
    )

    def __repr__(self) -> str:
        return f"<SavedView(id={self.id}, user_id={self.user_id}, name={self.name})>"


class AnomalyAlert(Base):
    """Detected anomalies in event patterns."""

    __tablename__ = "anomaly_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=True, index=True)
    severity = Column(String(50), nullable=True)  # The severity being checked
    anomaly_type = Column(String(50), nullable=False)  # 'spike', 'drop', 'trend_change'
    baseline_value = Column(Float, nullable=False)
    observed_value = Column(Float, nullable=False)
    deviation_percent = Column(Float, nullable=False)  # How much % above/below baseline
    z_score = Column(Float, nullable=False)  # Statistical z-score
    is_acknowledged = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    detected_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_anomaly_source_time", "source", "created_at"),
        Index("idx_anomaly_unacknowledged", "is_acknowledged", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AnomalyAlert(id={self.id}, type={self.anomaly_type}, deviation={self.deviation_percent}%)>"
