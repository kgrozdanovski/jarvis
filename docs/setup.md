# Jarvis Setup

Jarvis is a FastAPI + Nuxt monorepo for a local-network home AI assistant.

## Components

- `backend/`: FastAPI API, authentication, admin user management, email, and persistence.
- `frontend/`: Nuxt 3 web app.
- `database.sql`: Reference PostgreSQL schema baseline.
- `backend/migrations/`: Timestamped migrations applied by the backend migration script.
- `infrastructure/` and `docker-compose*.yml`: Container build/run configuration.

## Environment

Create a root `.env` from `.env.template` and fill local values for database, mail, auth, Google OAuth, and optional analytics. Do not commit secrets.

## Running Locally

This repository's agent instructions intentionally avoid running local validation commands from the sandbox. Run setup, migrations, backend, frontend, and Docker commands on your machine and paste errors back when needed.

## Removed From The Copied Baseline

Jarvis does not include the copied commerce, usage-metering, or image-workflow surfaces.
