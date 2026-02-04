import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import (
    pipeline_router,
    discovery_router,
    verification_router,
    audit_router,
    outreach_router,
)
from app.websocket import manager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Shopify UI Audit API",
    description="Backend API for Shopify UI Audit MVP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include API routers
app.include_router(pipeline_router)
app.include_router(discovery_router)
app.include_router(verification_router)
app.include_router(audit_router)
app.include_router(outreach_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    """WebSocket endpoint for real-time pipeline updates."""
    try:
        client_id = await manager.connect(websocket)
    except ConnectionError:
        return

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await manager.handle_message(message, websocket)
            except json.JSONDecodeError:
                logger.warning(f"Malformed WebSocket message from {client_id}: {data[:100]}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
