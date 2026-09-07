"""Pydantic v2 schemas for request/response validation."""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    """Schema for creating events."""

    source: str = Field(..., min_length=1, max_length=255, description="Event source identifier")
    event_type: str = Field(..., min_length=1, max_length=100, description="Classification of event")
    severity: str = Field(
        ...,
        pattern="^(INFO|WARNING|ERROR|CRITICAL)$",
        description="Event severity level",
    )
    message: str = Field(..., min_length=1, description="Event message")
    event_metadata: Optional[dict[str, Any]] = Field(None, description="Additional event metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "api-server-1",
                "event_type": "database_error",
                "severity": "ERROR",
                "message": "Connection timeout to primary database",
                "metadata": {
                    "endpoint": "/api/users",
                    "response_time_ms": 5000,
                    "retry_count": 3,
                },
            }
        }


class EventResponse(BaseModel):
    """Schema for event response."""

    id: UUID
    source: str
    event_type: str
    severity: str
    message: str
    event_metadata: Optional[dict[str, Any]] = None
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InsightCreate(BaseModel):
    """Schema for creating insights."""

    event_id: UUID = Field(..., description="UUID of related event")
    insight_type: str = Field(..., description="Type of insight (ANOMALY, RECOMMENDATION, ALERT)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    analysis: str = Field(..., min_length=1, description="Analysis text")
    recommendations: Optional[list[str]] = Field(None, description="List of recommendations")


class InsightResponse(BaseModel):
    """Schema for insight response."""

    id: UUID
    event_id: UUID
    insight_type: str
    confidence_score: float
    analysis: str
    recommendations: Optional[list[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    """Schema for analytics data response."""

    time_bucket: datetime
    source: str
    event_type: str
    count: int
    error_count: int
    avg_severity_score: Optional[float] = None
    aggregated_data: Optional[dict[str, Any]] = None


class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str = Field(..., min_length=3, max_length=255, description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")


class AdminUserCreate(UserCreate):
    """Schema for admin-initiated user creation."""

    is_admin: bool = Field(False, description="Grant admin privileges to the new user")


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    username: str
    email: str
    is_active: bool
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""

    id: UUID
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse = Field(..., description="Authenticated user profile")


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")


class SavedViewCreate(BaseModel):
    """Schema for creating saved filter views."""

    name: str = Field(..., min_length=1, max_length=255, description="View name")
    description: Optional[str] = Field(None, max_length=1000, description="View description")
    filters: dict[str, Any] = Field(..., description="Filter configuration")
    is_pinned: bool = Field(False, description="Pin view to sidebar")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production Errors",
                "description": "Critical errors in production",
                "filters": {
                    "severity": ["CRITICAL", "ERROR"],
                    "sourceFilter": "prod-*",
                    "timeRange": 24,
                },
                "is_pinned": True,
            }
        }


class SavedViewResponse(BaseModel):
    """Schema for saved view response."""

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    filters: dict[str, Any]
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnomalyAlertResponse(BaseModel):
    """Schema for anomaly alert response."""

    id: UUID
    source: str
    event_type: Optional[str] = None
    severity: Optional[str] = None
    anomaly_type: str  # 'spike', 'drop', 'trend_change'
    baseline_value: float
    observed_value: float
    deviation_percent: float
    z_score: float
    is_acknowledged: bool
    created_at: datetime
    detected_at: datetime

    class Config:
        from_attributes = True


__all__ = [
    "EventCreate",
    "EventResponse",
    "InsightCreate",
    "InsightResponse",
    "AnalyticsResponse",
    "UserCreate",
    "UserResponse",
    "AuditLogResponse",
    "SavedViewCreate",
    "SavedViewResponse",
    "AnomalyAlertResponse",
    "TokenResponse",
    "HealthCheckResponse",
]
