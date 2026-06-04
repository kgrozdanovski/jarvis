# JARVIS agent guide

Jarvis is a monorepo for a comprehensive, multi-platform AI-assistant:
- `backend/`: Python 3.12 + FastAPI API.
- `frontend/`: Nuxt 3 (Vue 3 + TypeScript) web app.
- `docs/`: operational + user documentation.
- `infrastructure/` + `docker-compose*.yml`: container build/run configuration.

## Non-negotiables for this repo (sandboxed agent)

- Do **not** try to validate changes by running commands (they won’t work reliably in this agent sandbox).
  - Examples (non-exhaustive): `npm run …`, `pnpm …`, `yarn …`, `nuxt …`, `uv …`, `python …`, `pytest …`,
    `docker …`, `docker compose …`, `make …`.
  - Instead: review your own diffs carefully, reason about correctness, and ask the **user** to run any commands
    locally and paste results if needed.
- Never ask for approval/escalation. Avoid operations that would require network access or elevated permissions.
- Never read the .env file in the root dir, refer to the .env.template instead.
- Never edit existing migrations when making database changes - create a new migration file instead.

## Where to look first

Extensive documentation for the system, policies, research and third-party integrations is available in the `/docs` directory.

- Setup / deployment: `docs/setup.md`
- Backend metering + billing data model: `docs/usage.md`, `docs/pricing.md`
- Backend internals: `docs/backend/`
- Frontend configuration and runtime env: `frontend/nuxt.config.ts`, `frontend/README.md`
- Contribution conventions: `CONTRIBUTING.md` (PEP 8, Conventional Commits)
- Database schema reference: `database.sql` (DDL dump used as a navigational reference; keep it updated when schema changes land).
- Architectural Decision Records: `docs/decisions`

Additionally, a long-term project plan is available under `docs/plan.md`, and it is subject to change. Refer to this
file when you need broader context on the project, goals and parts as well as when reviewing your final code to ensure
it is aligned with the project's and user request's goals.

## General change guidelines

- Prefer the smallest correct change; keep edits localized and consistent with surrounding patterns.
- Always try to make use of existing code and styling patterns where possible - e.g. if user asks for a modal dialog, try to find and reuse or modify existing dialogs.
- Don’t edit generated/vendor artifacts:
  - `**/node_modules/`, `frontend/.nuxt/`, `frontend/.data/`, `backend/.venv/`, `**/__pycache__/`, `backend/log/`.
- Don’t add editor/backup files (`*~`) and don’t “clean up” existing ones unless explicitly asked.
- Ensure the code you create is easily human-readable and visually organized rather than cluttered or condensed.
- Treat secrets as secrets:
  - Don’t hardcode API keys/tokens.
  - Don’t paste `.env` contents into chat output.
  - Use `.env.template` as the reference for required variables.
- If documentation is impacted, update the relevant `docs/*.md` or module README.
- If making or instructed for a major architectural decision as per `docs/decisions/guide.md`, be sure to create a new
ADR file under `/docs/decisions/<subdirs...>/<decision>.md` (e.g. /docs/decisions/backend/agents/0003-use-ollama.md).
Don't read into the ADR guidance unless you are certain you are making significant architectural changes.

## Architecture expectations

- **Backend**: routing → service/business logic → repository/DB access, with shared primitives in `src/core/` and
  third-party wrappers in `src/integration/`. Prefer the existing `DBAL` and migration system.
- **Frontend**: Nuxt pages/layouts/components, with environment values routed through Nuxt runtime config.

## Overrides

More specific instructions live in:
- `backend/AGENTS.override.md`
- `frontend/AGENTS.override.md`
