# Nexus Finance Engine

Nexus Finance Engine is a full-stack financial ledger and analytics application suitable for regulated-style workflows. The system pairs a FastAPI service with a React single-page client, PostgreSQL persistence, and Redis-backed response caching for aggregated reporting endpoints.

## Architecture

The solution follows a modular monolith pattern: a single versioned HTTP API (`/api/v1`) exposes authentication, accounts, transactions, and audit domains. The client consumes this API through a reverse proxy during development (Vite) or through an explicit origin allow list in production (CORS).

| Layer | Responsibility |
| --- | --- |
| API | Request validation, JWT authentication, department and role guards, transactional business logic |
| Data | PostgreSQL via SQLAlchemy/SQLModel; ACID semantics for multi-step operations |
| Cache | Redis (with in-memory fallback) for cached financial summary responses |
| Client | React 18, Vite, Tailwind CSS, Recharts; role-aware routing and navigation |

## ACID Compliance and Ledger Operations

Fund transfers persist as paired ledger entries (expense on the source account, income on the destination) within a single database transaction. Failure at any step triggers `session.rollback()`, preserving consistency across account balances and transaction rows.

Transaction removal is implemented as soft delete: `is_deleted` is set to `true` with audit logging. Where a transfer is identified, matching paired rows are soft-deleted in the same unit of work.

## Redis Caching

Financial summary aggregation endpoints may be cached with Redis to reduce database load. If Redis is unavailable at startup, the application falls back to an in-memory cache backend suitable for development only.

## Role-Based Access Control (RBAC)

Authorization is enforced at the API using department and role predicates. The client mirrors these rules:

| Role | Ledger read | Transfers | Deletes | Audit logs |
| --- | --- | --- | --- | --- |
| Admin | Yes | Yes | Yes | Yes |
| Dev_Admin | Yes | No | No | Yes |
| Analyst | Yes | No | No | No |
| Viewer | Yes | No | No | No |

Audit log access is restricted to `Admin` and `Dev_Admin` on the API and in the navigation shell.

## Security Configuration

- JWT signing keys and database credentials are supplied through environment variables (Pydantic `BaseSettings`).
- Production deployments must set `SECRET_KEY` and `DATABASE_URL`; do not commit credentials.
- CORS is restricted to explicit origins via `CORS_ORIGINS` (comma-separated). Wildcard origins are not used with credential-bearing requests.

## Prerequisites

- Docker Engine and Docker Compose (for containerized PostgreSQL and Redis)
- Node.js 18 or newer (for the web client)
- Python 3.11+ (for local backend execution outside the API container)

## Local Development

### Backend (Docker Compose)

From the repository root:

```bash
docker compose up -d
```

Set `SECRET_KEY` to a long random value in `.env` before issuing tokens; an empty `SECRET_KEY` rejects login. The API service reads `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, and `CORS_ORIGINS` from the environment.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The development server proxies `/api` to `http://127.0.0.1:8000`. Ensure the API listens on `8000` or adjust the proxy target.

### Database Migrations

Alembic reads `sqlalchemy.url` from `app.core.config.settings.database_url` (see `alembic/env.py`). Run migrations from the `backend` directory with `DATABASE_URL` set appropriately.

## Testing

```bash
cd backend
pytest
```

## License

See repository for license terms applicable to the open-source distribution.
