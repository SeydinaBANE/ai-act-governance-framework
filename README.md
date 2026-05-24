# AI Act Governance Framework

Framework de gouvernance IA conforme à l'AI Act européen. Permet aux équipes DSI/DPO de classifier leurs systèmes IA par niveau de risque, générer des model cards EU, tracer les décisions et scanner les données personnelles.

## Fonctionnalités

| Module | Description |
|--------|-------------|
| **Risk Scorer** | Moteur de règles AI Act (Art. 5 + Annexe III + score pondéré) |
| **Model Card Generator** | Formulaire 6 sections + auto-génération LLM (OpenRouter) |
| **Audit Log** | Traçabilité immuable SHA-256, vérification d'intégrité |
| **PII Scanner** | Détection données personnelles via Microsoft Presidio |
| **Dashboard DSI** | KPIs, distribution risques, obligations réglementaires |
| **Export PDF** | Rapport de conformité téléchargeable (reportlab) |

## Stack technique

- **Backend** : Python 3.12 · FastAPI 0.115 · SQLAlchemy 2.0 async · PostgreSQL 16 · Alembic
- **Frontend** : Next.js 15 · TypeScript · Tailwind CSS · React Query · Recharts
- **IA** : Microsoft Presidio (PII) · OpenRouter / Claude Haiku 4.5 (LLM)
- **Infra** : Docker Compose · multi-stage Dockerfiles

## Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Une clé [OpenRouter](https://openrouter.ai) (pour la génération de model cards)

### Installation

```bash
# 1. Cloner et configurer les variables d'environnement
cp .env.example .env
# Éditer .env : SECRET_KEY, OPENROUTER_API_KEY, POSTGRES_PASSWORD

# 2. Démarrer tous les services
make up

# 3. Appliquer les migrations
make migrate

# 4. Peupler la base avec des données de démo
make seed
```

### Accès

| Service | URL |
|---------|-----|
| Interface web | http://localhost:3000 |
| API (Swagger) | http://localhost:8000/docs |
| API (ReDoc) | http://localhost:8000/redoc |

### Comptes de démonstration

| Email | Mot de passe | Rôle |
|-------|-------------|------|
| admin@aiact-governance.fr | admin1234 | Admin |
| reviewer@aiact-governance.fr | Review@123456 | Reviewer |
| viewer@aiact-governance.fr | View@123456 | Lecteur |

## Commandes

```bash
make up          # Démarrer tous les services
make down        # Arrêter
make logs        # Logs du backend en temps réel
make migrate     # Appliquer les migrations Alembic
make seed        # Données de démonstration
make test        # Tests pytest avec coverage
make lint        # ruff + mypy + eslint
make format      # ruff format + prettier
make shell       # Bash dans le container backend
```

## Structure du projet

```
projet-3/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── routers/            # Endpoints HTTP
│   │   ├── services/           # Logique métier
│   │   │   ├── risk_scorer.py      # Moteur règles AI Act ⭐
│   │   │   ├── audit_logger.py     # Hash SHA-256
│   │   │   ├── pii_scanner.py      # Wrapper Presidio
│   │   │   ├── model_card_generator.py  # LLM OpenRouter
│   │   │   └── pdf_exporter.py     # Rapport PDF
│   │   ├── models/             # ORM SQLAlchemy
│   │   ├── schemas/            # Pydantic v2
│   │   └── data/
│   │       └── questionnaire.json  # Questions AI Act externalisées
│   └── tests/
│       ├── unit/               # 19 tests (risk scorer, audit)
│       └── integration/        # 24 tests (API complète)
├── frontend/                   # Next.js 15
│   └── src/app/
│       ├── dashboard/          # KPIs et graphiques
│       ├── systems/            # Registre systèmes IA
│       │   └── [id]/
│       │       ├── risk/       # Wizard évaluation AI Act
│       │       ├── model-card/ # Model card 6 sections
│       │       └── audit/      # Journal d'audit
│       ├── pii-scanner/        # Scanner PII
│       └── audit/              # Journal global
├── docs/                       # Documentation
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Niveaux de risque AI Act

| Catégorie | Critères | Obligations |
|-----------|---------|-------------|
| 🔴 **Interdit** | Art. 5 : biométrie temps réel, scoring social, manipulation subliminale | Interdiction totale |
| 🟠 **Haut risque** | Annexe III : infrastructure critique, emploi, justice, migration... | Conformité obligatoire avant mise sur marché |
| 🟡 **Risque limité** | Systèmes autonomes affectant des personnes, données sensibles | Obligations de transparence |
| 🟢 **Risque minimal** | Chatbots simples, filtres spam, jeux | Bonnes pratiques recommandées |

## Rôles utilisateurs

| Rôle | Permissions |
|------|-------------|
| `admin` | Tout (y compris suppression, journal d'audit global) |
| `reviewer` | Création/modification systèmes, évaluations, model cards, scans PII |
| `readonly` | Lecture seule |

## Tests

```bash
# Tous les tests (43 total)
make test

# Tests unitaires uniquement
docker compose exec backend pytest tests/unit/ -v

# Tests d'intégration
docker compose exec backend pytest tests/integration/ -v

# Coverage HTML
docker compose exec backend pytest --cov=app --cov-report=html
```

Coverage actuelle : **72%** (seuil minimum : 70%)

## Documentation complémentaire

- [Architecture technique](docs/architecture.md)
- [Référence API](docs/api.md)
- [Guide de déploiement production](docs/deployment.md)
