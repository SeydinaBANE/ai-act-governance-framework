.PHONY: up down logs shell migrate seed test lint format build clean help

# ---- Infrastructure ----

up:
	docker compose up -d
	@echo "Services démarrés. Backend: http://localhost:8000/docs | Frontend: http://localhost:3000"

down:
	docker compose down

restart:
	docker compose restart backend

logs:
	docker compose logs -f backend

logs-all:
	docker compose logs -f

ps:
	docker compose ps

build:
	docker compose build --no-cache

clean:
	docker compose down -v --remove-orphans
	@echo "Volumes supprimés."

# ---- Base de données ----

migrate:
	docker compose exec backend alembic upgrade head

migrate-down:
	docker compose exec backend alembic downgrade -1

migrate-generate:
	@read -p "Nom de la migration: " name; \
	docker compose exec backend alembic revision --autogenerate -m "$$name"

migrate-history:
	docker compose exec backend alembic history

seed:
	docker compose exec backend python scripts/seed_db.py

# ---- Tests ----

test:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

test-unit:
	docker compose exec backend pytest tests/unit/ -v

test-integration:
	docker compose exec backend pytest tests/integration/ -v

test-html:
	docker compose exec backend pytest --cov=app --cov-report=html
	@echo "Rapport HTML: backend/htmlcov/index.html"

# ---- Qualité ----

lint:
	docker compose exec backend ruff check app/ tests/
	docker compose exec backend mypy app/
	docker compose exec frontend npx eslint src/

format:
	docker compose exec backend ruff format app/ tests/
	docker compose exec frontend npx prettier --write src/

type-check:
	docker compose exec backend mypy app/ --strict
	docker compose exec frontend npx tsc --noEmit

# ---- Dev ----

shell:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U aiact -d aiact_governance

shell-frontend:
	docker compose exec frontend sh

install:
	docker compose exec backend pip install -r requirements.txt
	docker compose exec frontend npm install

# ---- Pre-commit ----

pre-commit-install:
	pre-commit install
	pre-commit install --hook-type commit-msg

pre-commit-run:
	pre-commit run --all-files

# ---- Help ----

help:
	@echo ""
	@echo "AI Act Governance Framework — Commandes disponibles"
	@echo "===================================================="
	@echo ""
	@echo "Infrastructure:"
	@echo "  make up              Démarrer tous les services"
	@echo "  make down            Arrêter tous les services"
	@echo "  make restart         Redémarrer le backend"
	@echo "  make logs            Logs du backend (live)"
	@echo "  make logs-all        Logs de tous les services"
	@echo "  make build           Rebuild les images Docker"
	@echo "  make clean           Supprimer containers + volumes"
	@echo ""
	@echo "Base de données:"
	@echo "  make migrate         Appliquer les migrations"
	@echo "  make migrate-down    Annuler la dernière migration"
	@echo "  make migrate-generate Créer une nouvelle migration"
	@echo "  make seed            Peupler la DB (données démo)"
	@echo ""
	@echo "Tests:"
	@echo "  make test            Tous les tests + coverage"
	@echo "  make test-unit       Tests unitaires uniquement"
	@echo "  make test-integration Tests d'intégration uniquement"
	@echo ""
	@echo "Qualité:"
	@echo "  make lint            ruff + mypy + eslint"
	@echo "  make format          ruff format + prettier"
	@echo "  make type-check      mypy strict + tsc"
	@echo ""
	@echo "Dev:"
	@echo "  make shell           Bash dans le container backend"
	@echo "  make shell-db        psql dans PostgreSQL"
	@echo ""
