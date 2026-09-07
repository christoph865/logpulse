"""API v1 routes and routing."""
from fastapi import APIRouter

from app.api.v1.endpoints import events, insights, analytics, auth, admin, saved_views, anomalies, websocket

# Create API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(saved_views.router)
api_router.include_router(anomalies.router)
api_router.include_router(websocket.router)

__all__ = ["api_router"]
