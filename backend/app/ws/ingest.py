"""
WebSocket audio ingestion (Phase 1, robust).

This module accepts WebSocket connections from the browser extension and
handles two kinds of messages:
1) Text JSON "init" metadata from the sender describing the audio container/codec.
2) Binary frames (e.g., audio/webm;codecs=opus) produced by MediaRecorder.

It maintains in-memory counters per connection and handles disconnects
without raising RuntimeError after a client closes.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import time
import uuid
import logging
import os

router = APIRouter(prefix="/ws", tags=["ws"])

# Simple in-memory stats by connection id
_INGEST_STATS: Dict[str, Dict[str, Any]] = {}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Optional debug dump to file. Set to a path to write the raw webm chunks.
_DEBUG_DUMP_PATH = r"F:\\projects\\meeting_assistant\\backend\\debug_audio.webm"


@router.get("/ingest/stats")
def ingest_stats() -> Dict[str, Dict[str, Any]]:
    """
    Return ingestion statistics for all active and recent connections.

    Returns:
        dict: Mapping of connection_id to counters and metadata such as
              total_bytes, frames_received, started_at, last_message_at,
              and the last 'init' payload received from the client.
    """
    return _INGEST_STATS


@router.websocket("/ingest")
async def ws_ingest(websocket: WebSocket) -> None:
    """
    Accept a WebSocket connection and receive audio frames until the client disconnects.

    The client should first send a small JSON 'init' message:
        {"type":"init","format":"audio/webm;codecs=opus","timeslice_ms":500}

    Subsequent messages are expected to be binary audio chunks.

    Args:
        websocket (WebSocket): The client connection.

    Returns:
        None
    """
    await websocket.accept()
    conn_id = str(uuid.uuid4())
    _INGEST_STATS[conn_id] = {
        "total_bytes": 0,
        "frames_received": 0,
        "init": None,
        "started_at": time.time(),
        "last_message_at": None,
        "closed": False,
        "close_reason": None,
        "remote": f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown",
    }

    logger.info("connection open: %s", conn_id)
    await websocket.send_text("ingest:connected")

    # Initialize debug dump if enabled
    if _DEBUG_DUMP_PATH:
        try:
            # Remove existing file so each connection starts fresh
            if os.path.exists(_DEBUG_DUMP_PATH):
                os.remove(_DEBUG_DUMP_PATH)
        except Exception as e:
            logger.warning("could not reset debug dump file: %r", e)

    try:
        while True:
            try:
                # Receive the next ASGI event from the client
                message = await websocket.receive()
            except WebSocketDisconnect:
                # Normal client disconnect
                _INGEST_STATS[conn_id]["closed"] = True
                _INGEST_STATS[conn_id]["close_reason"] = "disconnect"
                logger.info("connection closed (WebSocketDisconnect): %s", conn_id)
                break
            except RuntimeError as exc:
                # Starlette raises this if receive() is called after disconnect
                _INGEST_STATS[conn_id]["closed"] = True
                _INGEST_STATS[conn_id]["close_reason"] = f"runtime:{exc}"
                logger.info("connection closed (RuntimeError after disconnect): %s", conn_id)
                break

            _INGEST_STATS[conn_id]["last_message_at"] = time.time()

            # ASGI message type can help us identify disconnects explicitly
            msg_type = message.get("type")
            if msg_type == "websocket.disconnect":
                _INGEST_STATS[conn_id]["closed"] = True
                _INGEST_STATS[conn_id]["close_reason"] = "event:disconnect"
                logger.info("connection closed (event disconnect): %s", conn_id)
                break

            # Text messages carry control/metadata
            if "text" in message and message["text"] is not None:
                try:
                    payload = json.loads(message["text"])
                    if payload.get("type") == "init":
                        _INGEST_STATS[conn_id]["init"] = payload
                        await websocket.send_text("ingest:init:ok")
                    else:
                        await websocket.send_text("ingest:unknown_text")
                except json.JSONDecodeError:
                    await websocket.send_text("ingest:text_non_json")
                continue

            # Binary messages carry audio data
            if "bytes" in message and message["bytes"] is not None:
                chunk: bytes = message["bytes"]
                _INGEST_STATS[conn_id]["total_bytes"] += len(chunk)
                _INGEST_STATS[conn_id]["frames_received"] += 1

                # Optional debug: append to a .webm file for manual inspection
                if _DEBUG_DUMP_PATH:
                    try:
                        with open(_DEBUG_DUMP_PATH, "ab") as f:
                            f.write(chunk)
                    except Exception as e:
                        logger.warning("debug dump write failed: %r", e)

                # Occasional ack to client
                if _INGEST_STATS[conn_id]["frames_received"] % 20 == 0:
                    await websocket.send_text(
                        f"ingest:frames={_INGEST_STATS[conn_id]['frames_received']}"
                    )

    except Exception as exc:
        # Unexpected error path
        _INGEST_STATS[conn_id]["closed"] = True
        _INGEST_STATS[conn_id]["close_reason"] = f"error:{exc!r}"
        logger.exception("WebSocket error for %s: %r", conn_id, exc)
        try:
            await websocket.close()
        except Exception:
            pass
