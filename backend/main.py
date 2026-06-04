import os
import uvicorn
import src.environment

import logging
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.routers import default, users, google_auth, admin
from src.core.logger import get_logger
from src.core.storage import validate_storage_on_startup
from src.middleware.authentication import AuthMiddleware
from src.service.announcement import initialize_announcement_alert
from src.service.traffic_log_ingestion import start_traffic_log_ingestion
from socketio_server import integrate_with_fastapi

# Initialize the logger
logger = get_logger("main")

# Configure Sentry
sentry_dsn = os.getenv("BACKEND_SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.getenv("APP_ENV", "dev"),
        integrations=[
            FastApiIntegration(),
            # Capture DEBUG+ as breadcrumbs; only ERROR+ creates Sentry events.
            # This gives us the full DEBUG trail leading up to any error
            # without flooding Sentry with routine debug noise.
            LoggingIntegration(
                level=logging.DEBUG,        # breadcrumb capture threshold
                event_level=logging.ERROR,  # event creation threshold
            ),
        ],
        traces_sample_rate=0.0,
        profiles_sample_rate=0.0,
    )

app = FastAPI()

logger.debug("Registering middlewares...")
origins = [
    "https://jarvis.local",
    "http://localhost",
    "https://localhost",
    "http://localhost:3000",
    "https://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

logger.debug("Registering routers...")
app.include_router(default.router)
app.include_router(users.router)
app.include_router(google_auth.router)
app.include_router(admin.router)

# Integrate Socket.IO with FastAPI
app = integrate_with_fastapi(app)

# Validate storage config early so we fail fast (and loudly) on bad endpoints.
try:
    validate_storage_on_startup()
except Exception as exc:  # noqa: BLE001
    logger.critical("Storage startup validation failed: %s", exc)
    raise

initialize_announcement_alert()


@app.on_event("startup")
async def _startup_tasks():
    await start_traffic_log_ingestion()


def _serialize_validation_body(value: Any) -> Any:
    if isinstance(value, UploadFile):
        return {
            "filename": value.filename,
            "content_type": value.content_type,
        }
    if isinstance(value, dict):
        return {str(k): _serialize_validation_body(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_validation_body(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_validation_body(item) for item in value]
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>"
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


# Create custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    safe_body = _serialize_validation_body(exc.body)
    safe_errors = _serialize_validation_body(exc.errors())

    # Log detailed information about the validation error
    logger.error("Validation error in path %s: %s | Body: %s", request.url.path, safe_errors, safe_body)
    # Return the default 422 JSON response or customize as needed.
    return JSONResponse(
        status_code=422,
        content={"detail": safe_errors, "body": safe_body}
    )


if __name__ == "__main__":
    try:
        logger.debug("Starting the FastAPI server on port 8080...")
        config = uvicorn.Config(app, host='0.0.0.0', port=8080, log_level="info")

        server = uvicorn.Server(config)
        server.run()

    except Exception as e:
        logger.error(f"An unhandled error occurred: {e}")
