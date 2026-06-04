import sentry_sdk
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from src.core.authenticator import verify_access_token  # ideally raises specific errors
from src.core.logger import get_logger

logger = get_logger("auth-middleware")

EXCLUDED_PREFIXES = (
    "/public",
    "/healthcheck",
    "/user/auth/login",
    "/user/auth/refresh",
    "/auth/google",
    "/user/auth/lookup",
    "/user/auth/register",
    "/user/auth/send-verification",
    "/user/auth/confirm-email",
    "/user/auth/magic-link",
    "/user/auth/reset-password",
    "/contact",
    "/contact/enterprise",
    "/support/contact",
    "/newsletter/subscribe",
    "/newsletter/unsubscribe",
    "/docs",
    "/openapi.json",
    "/redoc",
)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        try:
            # Bypass preflight and open routes
            if request.method == "OPTIONS":
                return await call_next(request)
            if path in EXCLUDED_PREFIXES or any(path.startswith(p) for p in EXCLUDED_PREFIXES):
                logger.info("Skipping authentication for %s", path)
                return await call_next(request)

            # Auth header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return self._unauthorized_response(path, "No token provided.")

            token = auth_header[7:]  # strip "Bearer "

            # Verify
            try:
                verify_access_token(token)
            except HTTPException:
                # If verify_token itself raises HTTPException, handle uniformly
                return self._unauthorized_response(path, "Invalid token.")
            except Exception as err:
                return self._unauthorized_response(path, f"Token verification failed: {err}")

            # Continue
            return await call_next(request)

        except HTTPException as e:
            return self._handle_http_exception(request, e)

        except Exception as e:
            # Unexpected server error: log + Sentry + 500 without bubbling
            logger.exception("Unhandled error in auth middleware")
            sentry_sdk.capture_exception(e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error."},
            )

    @staticmethod
    def _unauthorized_response(path: str, reason: str) -> JSONResponse:
        # RFC 6750 recommends this header on 401
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Unauthorized"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        # Explicitly handle 401s quietly
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return AuthMiddleware._unauthorized_response(request.url.path, str(exc.detail))

        if 500 <= exc.status_code < 600:
            logger.error("HTTPException %s in auth middleware for %s: %s", exc.status_code, request.url.path, exc.detail)
            sentry_sdk.capture_exception(exc)
        else:
            logger.info("HTTPException %s in auth middleware for %s: %s", exc.status_code, request.url.path, exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
