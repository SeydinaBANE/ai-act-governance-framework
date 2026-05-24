# AI Act Governance Framework

## Aperçu
Framework de gouvernance IA conforme à l'AI Act européen. Permet aux DSI de classifier leurs systèmes IA par niveau de risque, générer des model cards EU, tracer les décisions, scanner les PII et piloter la conformité.

## Stack
- **Backend** : Python 3.12 + FastAPI 0.115 + SQLAlchemy 2.0 async + asyncpg + Alembic
- **Frontend** : Next.js 15 + TypeScript + Tailwind CSS + React Query + Recharts
- **Base de données** : PostgreSQL 16
- **PII** : Microsoft Presidio (containers Docker)
- **LLM** : OpenRouter (`anthropic/claude-haiku-4.5`) via httpx async
- **Infra** : Docker Compose

## Commandes essentielles

```bash
make up         # Démarrer tous les services
make down       # Arrêter
make logs       # Logs du backend
make migrate    # Appliquer les migrations Alembic
make seed       # Peupler la DB avec des données de démo
make test       # Lancer les tests pytest
make lint       # ruff + mypy + eslint
make format     # ruff format + prettier
make shell      # Bash dans le container backend
```

## Variables d'environnement requises
Copier `.env.example` → `.env` et remplir :
- `SECRET_KEY` : clé JWT (32+ chars)
- `OPENROUTER_API_KEY` : clé OpenRouter
- `POSTGRES_PASSWORD` : mot de passe PostgreSQL

## Structure des modules backend

```
app/
  main.py           # Application FastAPI, lifespan, middlewares
  config.py         # Settings pydantic-settings (lecture .env)
  database.py       # AsyncEngine, AsyncSession, get_db dependency
  core/
    security.py     # JWT encode/decode, password hash/verify
    dependencies.py # Depends: get_current_user, require_role
    exceptions.py   # Handlers HTTP globaux
  models/           # SQLAlchemy ORM (Base, tous les modèles)
  schemas/          # Pydantic v2 (request/response par domaine)
  routers/          # FastAPI APIRouter (HTTP layer uniquement)
  services/         # Logique métier (appelé par les routers)
  data/             # questionnaire.json (règles AI Act externalisées)
```

## Conventions de code

### Python
- `from __future__ import annotations` en haut de chaque fichier
- Type hints complets sur toutes les fonctions
- `async def` partout (pas de fonctions sync bloquantes)
- Pydantic v2 : `model_config = ConfigDict(from_attributes=True)`
- Logging via structlog : `log = structlog.get_logger(__name__)`
- Jamais de SQL dans les routers — uniquement dans les services

### TypeScript / Next.js 15
- Server Components par défaut
- `"use client"` uniquement si state/effects/handlers nécessaires
- `tsconfig.json` : `"strict": true` — pas de `any`
- Zod pour valider toutes les réponses API

## Ports
| Service | Port local |
|---------|-----------|
| Backend API | 8000 |
| Frontend | 3000 |
| PostgreSQL | 5432 |
| Presidio Analyzer | 5001 |
| Presidio Anonymizer | 5002 |

## Règles AI Act codifiées
Le fichier `backend/app/data/questionnaire.json` contient les questions. Le service `backend/app/services/risk_scorer.py` contient le moteur de règles (3 niveaux : Art.5 interdit → Annexe III haut risque → score pondéré).

**Ne jamais modifier les règles directement dans le code** — éditer `questionnaire.json` et les poids dans `risk_scorer.py::RULE_WEIGHTS`.

## Tests
```bash
# Tous les tests
make test

# Un fichier spécifique
docker compose exec backend pytest tests/unit/test_risk_scorer.py -v

# Avec coverage HTML
docker compose exec backend pytest --cov=app --cov-report=html
```

La DB de test est une vraie instance PostgreSQL (Testcontainers). Pas de mocks SQLAlchemy.
