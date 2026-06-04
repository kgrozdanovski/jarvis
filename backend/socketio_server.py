import os
import socketio
from fastapi import FastAPI
from src.core.logger import get_logger

# Initialize the logger
logger = get_logger("socketio_server")


# Default origins cover local dev + deployed hosts; override via env if needed
_DEFAULT_SOCKET_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://jarvis.local"
]


def _load_allowed_origins() -> list[str]:
    raw = os.getenv("SOCKET_ALLOWED_ORIGINS")
    if not raw:
        return _DEFAULT_SOCKET_ORIGINS
    parsed = [origin.strip() for origin in raw.split(",")]
    return [origin for origin in parsed if origin]


# Create a Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=_load_allowed_origins()
)

# Create an ASGI application
socket_app = socketio.ASGIApp(sio)

# Dictionary to store active research sessions
active_sessions = {}


def get_socket_app():
    """Return the Socket.IO ASGI application"""
    return socket_app


def integrate_with_fastapi(app: FastAPI):
    """Integrate Socket.IO with a FastAPI application"""
    app.mount("/socket.io", socket_app)
    return app


@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"Client connected: {sid}")
    # Initialize session data
    active_sessions[sid] = {
        "digest_id": None,
        "progress": 0,
        "last_update": 0
    }


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client disconnected: {sid}")
    # Clean up session data
    if sid in active_sessions:
        del active_sessions[sid]


@sio.event
async def join_job(sid, data):
    """Allow clients to join a room tied to a specific processing job."""
    job_id = (data or {}).get("jobId")
    if not job_id:
        logger.warning("Client %s attempted to join a job without providing a jobId.", sid)
        return

    await sio.enter_room(sid, job_id)
    logger.debug("Client %s joined job room %s", sid, job_id)


@sio.event
async def leave_job(sid, data):
    """Allow clients to leave a previously joined processing job room."""
    job_id = (data or {}).get("jobId")
    if not job_id:
        return

    await sio.leave_room(sid, job_id)
    logger.debug("Client %s left job room %s", sid, job_id)
