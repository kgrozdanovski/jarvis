# Security Architecture

Jarvis uses stateless API workers backed by persistent token records in PostgreSQL.

## Session Model

- Access tokens are returned to the frontend and sent as `Authorization: Bearer ...`.
- Refresh tokens are stored as `HttpOnly` cookies on `/user/auth`.
- Refresh rotates the refresh token and issues a new access token.
- The default refresh cookie name is `jarvis_refresh`.

## Passwords

Password-based auth sends password fields to the backend over HTTPS and stores bcrypt hashes in the database. Do not expose `USER_SIGNATURE_PRIVATE_KEY` to the browser; it is used for backend token encryption.

## Google Sign-In

Google Identity Services provides an ID token to the browser. The backend verifies that token, creates or links a Jarvis user, then issues the same Jarvis access/refresh session pair.

## CSP And Origins

Frontend CSP is configured in `frontend/nuxt.config.ts`. Keep allowed script/connect/frame origins limited to the local backend, Google sign-in, optional analytics, and Sentry if enabled.

## Removed Risk Areas

The Jarvis baseline no longer includes the removed commerce or image-workflow risk areas from the source project.
