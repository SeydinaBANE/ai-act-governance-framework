# Guide de déploiement

## Environnement de développement

```bash
# Démarrage complet
make up

# Vérifier que tout est healthy
docker compose ps

# Appliquer les migrations
make migrate

# Données de démo
make seed

# Suivre les logs
make logs
```

## Variables d'environnement

Copier `.env.example` → `.env` et configurer :

### Obligatoires

| Variable | Description | Exemple |
|----------|-------------|---------|
| `SECRET_KEY` | Clé JWT (32+ chars hex) | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | `changeme_prod_2026` |
| `OPENROUTER_API_KEY` | Clé API OpenRouter | `sk-or-v1-...` |

### Optionnelles

| Variable | Défaut | Description |
|----------|--------|-------------|
| `OPENROUTER_MODEL` | `anthropic/claude-haiku-4.5` | Modèle LLM |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Expiration JWT (8h) |
| `PRESIDIO_CONFIDENCE_THRESHOLD` | `0.85` | Seuil détection PII |
| `MAX_UPLOAD_SIZE_MB` | `10` | Taille max upload |
| `LOG_LEVEL` | `INFO` | Niveau de log |
| `ENVIRONMENT` | `development` | `development` ou `production` |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS (format JSON) |

## Migrations Alembic

```bash
# Appliquer toutes les migrations
make migrate

# Générer une nouvelle migration après modification d'un modèle
make migrate-generate

# Voir l'historique
docker compose exec backend alembic history

# Revenir en arrière d'une version
docker compose exec backend alembic downgrade -1
```

## Tests

```bash
# Suite complète (43 tests, ~10 secondes)
make test

# Avec rapport HTML de coverage
docker compose exec backend pytest --cov=app --cov-report=html
# Ouvrir backend/htmlcov/index.html

# Tests unitaires uniquement (rapides, sans DB)
docker compose exec backend pytest tests/unit/ -v

# Un test spécifique
docker compose exec backend pytest tests/unit/test_risk_scorer.py::test_prohibited_biometric_realtime -v
```

La DB de test (`aiact_governance_test`) doit exister :
```bash
docker compose exec postgres psql -U aiact -d aiact_governance -c "CREATE DATABASE aiact_governance_test;"
```

## Déploiement production

### Checklist sécurité

- [ ] `SECRET_KEY` générée avec `secrets.token_hex(32)` (jamais la valeur exemple)
- [ ] `POSTGRES_PASSWORD` fort et unique
- [ ] `ENVIRONMENT=production` (logs JSON, pas de mode debug)
- [ ] `ALLOWED_ORIGINS` restreint aux domaines de production
- [ ] `.env` hors du dépôt git (vérifier `.gitignore`)
- [ ] HTTPS activé (reverse proxy nginx/traefik)

### Build production

Les Dockerfiles sont multi-stage. Le target `production` crée des images minimales :

```bash
# Build images production
docker compose -f docker-compose.yml build --target production

# Ou avec un fichier compose dédié prod
docker compose -f docker-compose.prod.yml up -d
```

### Variables spécifiques production

```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=["https://aiact.votre-domaine.fr"]
ACCESS_TOKEN_EXPIRE_MINUTES=60  # Réduire en prod
```

### Base de données

En production, ne jamais utiliser `Base.metadata.create_all()`. Toujours passer par Alembic :

```bash
docker compose exec backend alembic upgrade head
```

### Healthchecks

Tous les services exposent des healthchecks Docker Compose :
- PostgreSQL : `pg_isready`
- Backend : `GET /health` → `{"status": "ok"}`
- Frontend : port 3000 accessible

```bash
# Vérifier l'état
docker compose ps
curl http://localhost:8000/health
```

## Sauvegarde des données

```bash
# Dump PostgreSQL
docker compose exec postgres pg_dump \
  -U aiact aiact_governance \
  > backup_$(date +%Y%m%d).sql

# Restauration
docker compose exec -T postgres psql \
  -U aiact aiact_governance \
  < backup_20260524.sql
```

## Mise à jour

```bash
# Arrêter les services
make down

# Récupérer les nouvelles images/sources
git pull

# Reconstruire si nécessaire
docker compose build backend frontend

# Redémarrer
make up

# Appliquer les nouvelles migrations
make migrate
```

## Dépannage

### Le backend ne démarre pas

```bash
make logs
# Vérifier ALLOWED_ORIGINS format JSON dans .env
# Vérifier DATABASE_URL accessible
```

### Erreur de connexion PostgreSQL

```bash
docker compose exec postgres pg_isready -U aiact -d aiact_governance
# Si KO : vérifier POSTGRES_PASSWORD dans .env
```

### Presidio indisponible

Le scanner PII retourne 503 si Presidio est down. Pour tester sans Presidio :
```bash
docker compose logs presidio-analyzer
# Images volumineuses (~2 GB), prévoir le temps de pull au premier démarrage
```

### Token JWT expiré

Le frontend redirige automatiquement vers `/login`. Durée configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`.
