"""WebSocket endpoint for real-time event streaming."""
import logging
import json
from typing import Dict, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.core.security import decode_token
from app.models import Event

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

# Connection manager to track active WebSocket connections
class ConnectionManager:
    """Manage WebSocket connections for broadcasting."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            await self.disconnect(conn)
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
connection_manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_events_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time event streaming.
    
    Query params:
        token: JWT authentication token
        source: (optional) Filter by source
        severity: (optional) Filter by severity
    """
    # Authenticate user
    decoded = decode_token(token)
    if not decoded:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    user_id = decoded.get("sub")
    logger.info(f"WebSocket connection attempt from user {user_id}")
    
    await connection_manager.connect(websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to real-time event stream",
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle ping/pong for keep-alive
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                
                # Handle filter updates
                elif message.get("type") == "filter":
                    logger.debug(f"Received filter update: {message}")
                    
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
                continue
    
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await connection_manager.disconnect(websocket)


@router.websocket("/ws/events/{source}")
async def websocket_source_events(
    websocket: WebSocket,
    source: str,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time events from specific source.
    
    Path params:
        source: Event source to filter
    """
    # Authenticate user
    decoded = decode_token(token)
    if not decoded:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    await connection_manager.connect(websocket)
    
    try:
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                continue
    
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for source {source}: {e}")
        await connection_manager.disconnect(websocket)


async def broadcast_event(event: Event):
    """
    Broadcast new event to all connected WebSocket clients.
    This function should be called when a new event is created.
    """
    try:
        message = {
            "type": "event",
            "data": {
                "id": str(event.id),
                "source": event.source,
                "event_type": event.event_type,
                "severity": event.severity,
                "message": event.message,
                "timestamp": event.timestamp.isoformat(),
                "created_at": event.created_at.isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        await connection_manager.broadcast(message)
        logger.debug(f"Broadcasted event {event.id} to {connection_manager.get_connection_count()} clients")
    except Exception as e:
        logger.error(f"Error broadcasting event: {e}")


async def broadcast_anomaly(anomaly_type: str, details: dict):
    """Broadcast anomaly alert to connected clients."""
    try:
        message = {
            "type": "anomaly",
            "anomaly_type": anomaly_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        await connection_manager.broadcast(message)
        logger.debug(f"Broadcasted anomaly to {connection_manager.get_connection_count()} clients")
    except Exception as e:
        logger.error(f"Error broadcasting anomaly: {e}")
