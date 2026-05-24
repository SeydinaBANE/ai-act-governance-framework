#!/bin/bash
set -e

echo "Attente que PostgreSQL soit prêt..."
until docker compose exec -T postgres pg_isready -U aiact; do
  sleep 1
done

echo "Lancement des migrations Alembic..."
docker compose exec backend alembic upgrade head

echo "Migrations terminées."
