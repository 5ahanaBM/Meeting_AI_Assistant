"""
WebSocket placeholder for audio ingestion.

This module defines a WebSocket endpoint that will accept audio frames
from the browser extension in Phase 1. For Phase 0, it echoes metadata only.
"""

from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/ws/ingest")
async def ws_ingest(websocket: WebSocket) -> None:
    """
    Accept a WebSocket connection for future audio ingestion.

    Args:
        websocket (WebSocket): Client WebSocket connection.

    Returns:
        None: This function runs until the client disconnects.
    """
    await websocket.accept()
    await websocket.send_text("Ingest socket connected. Phase 1 will stream audio frames here.")
    # Keep alive until disconnect (no frame handling in Phase 0)
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_text("Echo: placeholder in Phase 0.")
    except Exception:
        await websocket.close()
