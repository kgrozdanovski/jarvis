FROM python:3.12-bullseye AS deps

# 1. Copy uv binary so we can lock+sync very quickly
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 2. Install build dependencies (needed to compile wheels like psycopg2)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         libpq-dev \
         gcc \
    && rm -rf /var/lib/apt/lists/*

# 3. Create working directory & copy lock files
WORKDIR /build

# 4. Copy only the lockfiles so that rebuilding happens only when deps change
COPY backend/pyproject.toml backend/uv.lock ./

# 5. Create a virtualenv named .venv and install all pinned wheels into it
RUN uv venv .venv --python 3.12 \
    && . .venv/bin/activate \
    && uv sync --frozen

# 6. Make the venv’s bin/ appear on PATH for all subsequent steps
ENV PATH="/build/.venv/bin:$PATH"


FROM python:3.12-slim AS prod

# 1. Install runtime libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         libpq5 \
         libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy over the fully populated virtualenv from `deps`
COPY --from=deps /build/.venv /opt/venv

# 3. (Optional) If you ever need the `uv` binary at runtime:
COPY --from=deps /bin/uv /bin/uv

# 4. Ensure PATH is set
ENV PATH="/opt/venv/bin:$PATH"

# 5. Create the application directory & copy your backend code
WORKDIR /code
COPY backend/ .

# 6. Create any extra directories your app needs
RUN mkdir -p /attachments \
    && chmod 777 /attachments

# 7. Production entrypoint: use the venv’s python to run main.py
ENTRYPOINT ["python", "main.py"]
