# CI/CD Notes

Jarvis keeps deployment documentation intentionally lightweight in this cleaned baseline.

## Expected Pipeline Shape

1. Build the frontend static output.
2. Build backend and nginx/container images if using Docker.
3. Apply backend migrations.
4. Deploy the frontend and backend to the local-network host.

## Environment

Relevant values are database, mail, auth/session, Google OAuth, optional analytics, and optional Sentry settings.

The cleaned Jarvis baseline only requires environment values for the active local assistant app.
