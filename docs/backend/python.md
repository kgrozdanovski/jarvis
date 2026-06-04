# Backend Python Notes

The backend targets Python 3.12 and FastAPI.

## Structure

- `main.py`: FastAPI app, middleware, startup hooks, and router registration.
- `src/routers/`: HTTP endpoints.
- `src/service/`: business logic.
- `src/repository/`: DBAL-backed persistence.
- `src/core/`: shared auth, security, logging, storage, and database primitives.
- `migrations/`: timestamped migration files.

## Local Validation

Run install, migration, and server commands locally. The agent sandbox for this repo is instructed not to run backend commands.
