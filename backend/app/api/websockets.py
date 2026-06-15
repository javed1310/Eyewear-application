"""
OptiFlow — WebSocket Router
Handles real-time connections from clients and broadcasts updates via Redis Pub/Sub.
"""

import asyncio
import json
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.core.database import redis_client

router = APIRouter(prefix="/ws", tags=["Realtime"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.redis_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Start listening to Redis if this is the first connection
        if not self.redis_task or self.redis_task.done():
            self.redis_task = asyncio.create_task(self.listen_to_redis())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def listen_to_redis(self):
        """Listens to the Redis Pub/Sub channel for order updates and broadcasts to clients."""
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("order_updates")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    # Broadcast to all connected clients
                    disconnected = set()
                    for connection in self.active_connections:
                        try:
                            await connection.send_text(data)
                        except Exception:
                            disconnected.add(connection)
                            
                    for conn in disconnected:
                        self.disconnect(conn)
        except Exception as e:
            print(f"Redis listen error: {e}")

manager = ConnectionManager()

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """Client connects here for real-time order updates."""
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect client to send much, mostly they just listen.
            # But we must await receive() to keep connection alive and detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_order_update(order_id: int, action: str, data: dict):
    """
    Called from API routes/services to publish an update to Redis.
    action can be 'created', 'updated', 'status_changed'.
    """
    message = json.dumps({
        "order_id": order_id,
        "action": action,
        "data": data
    })
    if redis_client:
        await redis_client.publish("order_updates", message)
