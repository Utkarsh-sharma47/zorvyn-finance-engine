.PHONY: up down build logs alembic-revision alembic-upgrade

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

# api image wraps `alembic` to always use /app/alembic.ini
alembic-revision:
	docker compose exec -w /app api alembic revision --autogenerate -m "init models"

alembic-upgrade:
	docker compose exec -w /app api alembic upgrade head
