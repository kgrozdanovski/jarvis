# ========== Base builder stage ==========
FROM python:3.12-bullseye AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV PYTHONUNBUFFERED=1

RUN apt update && apt install -qy libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY ./backend/pyproject.toml ./backend/uv.lock /backend/
WORKDIR /backend

RUN uv sync --frozen

# ========== Final runtime stage ==========
FROM python:3.12-slim

RUN apt update && apt install -qy libpq-dev libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=build /bin/uv /bin/uv

COPY --from=build . /code
ENV PATH=".venv/bin:$PATH"

COPY ./backend /code

WORKDIR /code
ENTRYPOINT ["uv", "run", "main.py"]
