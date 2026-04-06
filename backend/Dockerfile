# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

WORKDIR /opt/venv

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv .

COPY requirements.txt .
RUN . bin/activate \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/usr/local/bin:/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Application source, including alembic.ini and alembic/ (required for upgrade at runtime).
COPY . .

# Alembic CLI must always load /app/alembic.ini (script_location); wrap the venv entrypoint.
RUN mv /opt/venv/bin/alembic /opt/venv/bin/_alembic \
    && install -m 0755 docker/alembic.sh /usr/local/bin/alembic \
    && sed -i 's/\r$//' /usr/local/bin/alembic

# Fail the image build if Alembic config is missing from the build context
RUN test -f /app/alembic.ini && test -d /app/alembic

EXPOSE 8000

# Run migrations before the ASGI server (e.g. Render). PORT is honored when set by the platform.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
