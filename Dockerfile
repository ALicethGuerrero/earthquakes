FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project

COPY src ./src
COPY ingestion.py .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
