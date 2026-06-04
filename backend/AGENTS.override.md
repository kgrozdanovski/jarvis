# Backend agent instructions (override)

Scope: `backend/**`

## Do not run commands

This agent environment is sandboxed; do **not** run backend commands to “check” work:
`uv …`, `python …`, `uvicorn …`, `pytest …`, `docker …`, `psql …`, etc. The user must run these locally.

## Code organization (follow existing boundaries)

- API entrypoint: `backend/main.py` (FastAPI app + middleware + router registration).
- Routers: `backend/src/routers/` (HTTP endpoints only; keep thin).
- Request/response models: `backend/src/model/` (Pydantic models; reuse before adding new ones).
- Business logic: `backend/src/service/` (pure logic and orchestration).
- Persistence: `backend/src/repository/` (SQL/DBAL access; no HTTP concerns).
- Core utilities: `backend/src/core/` (logging, security, storage primitives, DBAL).
- External systems: `backend/src/integration/` (third-party wrappers when this project adds them).

## Style and conventions

- Follow PEP 8 and the existing typing style (annotate public functions; keep types readable).
- Prefer explicit names over cleverness; keep functions small and side-effects obvious.
- Use the existing logger (`from src.core.logger import get_logger`) rather than `print`.
- Keep error handling consistent with FastAPI patterns (`HTTPException`, clear status codes/messages).
- Don’t introduce new dependencies unless explicitly requested (this repo uses `pyproject.toml` + `uv.lock`).

## Database + migrations

- DB access uses the in-repo DBAL (`backend/src/core/dbal.py`); don’t introduce ORM layers.
- Migrations are timestamp-ordered files under `backend/migrations/`.
  - Generation scripts live in `backend/scripts/` (see `backend/scripts/generate_migration.py`).
  - To generate a new migration, the user should run `uv run backend/scripts/script.py --name generate_migration` from the `backend/` directory.
- When changing schema, cross-check relevant docs:
  - `docs/backend/migration.md`, `docs/backend/dbal.md`.
- `database.sql` at repo root is a reference DDL dump; use it to orient yourself, and if you add migrations that change schema, also update `database.sql` to match (edit `CREATE TABLE` statements, add new tables, etc.).

## Avoid touching

- `backend/.venv/`, `backend/__pycache__/`, `backend/log/`, any `*~` files.
