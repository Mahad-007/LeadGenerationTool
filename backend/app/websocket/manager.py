"""WebSocket connection manager for real-time pipeline updates."""

import asyncio
import logging
import uuid
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

MAX_CONNECTIONS = 100


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> str:
        """Accept a new WebSocket connection and return client ID."""
        async with self._lock:
            # Check connection limit
            if len(self.active_connections) >= MAX_CONNECTIONS:
                await websocket.close(code=1013, reason="Max connections reached")
                raise ConnectionError("Max connections reached")

            await websocket.accept()
            client_id = str(uuid.uuid4())
            self.active_connections[client_id] = websocket

        # Send connected event (outside lock to avoid holding lock during I/O)
        await self.send_personal_message(
            {"type": "connected", "client_id": client_id},
            websocket
        )

        logger.info(f"WebSocket client connected: {client_id}")
        return client_id

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Send a message to a specific client."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        # Get snapshot of connections to avoid iteration issues
        async with self._lock:
            connections = list(self.active_connections.items())

        disconnected = []
        for client_id, connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for client_id in disconnected:
                    self.active_connections.pop(client_id, None)

    async def handle_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Handle incoming WebSocket message."""
        msg_type = message.get("type")

        if msg_type == "ping":
            await self.send_personal_message({"type": "pong"}, websocket)


# Global connection manager instance
manager = ConnectionManager()
