# Architecture technique

## Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────┐
│                        Docker Compose                            │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐ │
│  │  Next.js 15 │───▶│  FastAPI    │───▶│   PostgreSQL 16      │ │
│  │  :3000      │    │  :8000      │    │   :5432              │ │
│  └─────────────┘    └──────┬──────┘    └──────────────────────┘ │
│                            │                                     │
│                    ┌───────┴────────┐                           │
│                    │                │                           │
│             ┌──────▼──────┐  ┌──────▼──────┐                  │
│             │  Presidio   │  │  OpenRouter  │                  │
│             │  Analyzer   │  │  (externe)   │                  │
│             │  :5001      │  └─────────────┘                   │
│             │  Anonymizer │                                     │
│             │  :5002      │                                     │
│             └─────────────┘                                     │
└──────────────────────────────────────────────────────────────────┘
```

## Backend — FastAPI

### Couches

```
HTTP Request
    │
    ▼
Router (app/routers/)          ← Validation HTTP, auth, codes de statut
    │
    ▼
Service (app/services/)        ← Logique métier, règles AI Act
    │
    ▼
Model (app/models/)            ← SQLAlchemy ORM, mapping DB
    │
    ▼
PostgreSQL
```

**Règle stricte** : pas de SQL dans les routers, pas de logique métier dans les models.

### Modules principaux

#### `risk_scorer.py` — Moteur de règles AI Act

Le fichier le plus critique du projet. Implémente 3 niveaux de classification :

```
1. Interdictions absolues (Art. 5)
   → q1_biometric_realtime, q2_social_scoring, q3_subliminal, q4_emotion_workplace
   → Score = 100, catégorie = prohibited

2. Domaines haut risque (Annexe III)
   → q5 à q11 : infrastructure, éducation, emploi, services essentiels,
                 forces de l'ordre, migration, justice, biométrie
   → Catégorie = high_risk

3. Score pondéré (30-69 = limited_risk, <30 = minimal_risk)
   → Questions autonomie, données sensibles, irréversibilité
   → Questions mitigantes (inverted=true) : explicabilité, oversight
```

**Ne jamais modifier les règles dans le code** — éditer `data/questionnaire.json`.

#### `audit_logger.py` — Intégrité SHA-256

Chaque action est tracée avec un hash :
```python
payload_hash = SHA-256(actor_id || action || resource_id || timestamp || input_payload)
```

Endpoint de vérification : `GET /audit/entry/{id}/verify` recompute et compare.

#### `pii_scanner.py` — Wrapper Presidio

Appels HTTP asynchrones vers les containers Presidio :
- `POST http://presidio-analyzer:3000/analyze` → détection entités
- Recognizers custom FR : SIRET (`\b\d{14}\b`), NIR INSEE, IBAN FR

#### `model_card_generator.py` — LLM OpenRouter

Génération automatique des sections textuelles via Claude Haiku 4.5 :
- Prompt structuré avec contexte du système + assessment
- Extraction JSON robuste (gère markdown code blocks)
- Fallback gracieux si clé absente ou API down

### Authentification

JWT Bearer Token :
- Expiration : 480 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Payload : `{sub: user_id, email, role, exp, iat}`
- Rôles : `admin > reviewer > readonly`

```python
# Dépendances FastAPI
CurrentUser          # Tout utilisateur authentifié
ReviewerOrAbove      # reviewer ou admin
AdminUser            # admin uniquement
```

### Modèles de données

```sql
users
  id UUID PK | email UNIQUE | hashed_password | role | is_active

ai_systems
  id UUID PK | name | status | current_risk_category | created_by FK
  tech_stack JSONB | data_types JSONB | is_autonomous | affects_persons

risk_assessments
  id UUID PK | ai_system_id FK | questionnaire JSONB | score_details JSONB
  total_score | risk_category | ai_act_articles JSONB | required_actions JSONB
  valid_until | assessed_by FK

model_cards
  id UUID PK | ai_system_id FK | [6 sections de texte] | status | created_by FK

audit_logs  ← append-only
  id UUID PK | actor_id FK | actor_email | action | resource_type | resource_id
  input_payload JSONB | output_summary JSONB | payload_hash VARCHAR(64)

pii_scans
  id UUID PK | source_type | source_hash | pii_found | findings JSONB
  entity_summary JSONB | risk_level | recommendations JSONB
```

## Frontend — Next.js 15

### Conventions

- **Server Components par défaut** — `"use client"` uniquement si state/effects nécessaires
- **React Query** pour toutes les mutations et invalidations de cache
- **Zod** pour valider les formulaires côté client
- **`strict: true`** en TypeScript — pas de `any`

### Gestion de l'authentification

```typescript
// JWT stocké en localStorage (access_token)
// AuthGuard vérifie la validité après hydratation côté client
// Pattern : ready=false → useEffect → setReady(true) ou redirect
```

### Pages

```
/dashboard              → KPIs, donut risques, actions requises
/systems                → Liste avec recherche/filtres/pagination
/systems/new            → Formulaire création
/systems/[id]           → Détail + bannière risque + actions
/systems/[id]/risk      → Wizard questionnaire (5 sections)
/systems/[id]/model-card → Formulaire 6 sections accordéon + LLM
/systems/[id]/audit     → Audit trail du système
/audit                  → Journal global + vérification SHA-256
/pii-scanner            → Scanner texte/fichier + historique
```

## Sécurité

| Mesure | Implémentation |
|--------|---------------|
| Authentification | JWT HS256, expiration 8h |
| Autorisation | RBAC (admin/reviewer/readonly) |
| Mots de passe | bcrypt (12 rounds) |
| CORS | Liste blanche (`ALLOWED_ORIGINS`) |
| Headers HTTP | X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| Upload | Validation type MIME + taille max (10 MB) |
| Audit | SHA-256 payload hash pour chaque action |
| Secrets | pydantic-settings + .env (jamais en dur) |

## Décisions d'architecture

### Pourquoi SQLAlchemy async + asyncpg ?

Les scans PII et appels LLM peuvent prendre 5-30 secondes. L'async permet de gérer plusieurs requêtes concurrentes sans bloquer le serveur.

### Pourquoi les règles AI Act externalisées dans questionnaire.json ?

Le règlement AI Act évolue (amendements jusqu'en 2027). Modifier les règles sans toucher au code Python permet de déployer des mises à jour sans redéployement complet ni risque de régression.

### Pourquoi NullPool pour les tests ?

asyncpg maintient un pool de connexions. Plusieurs fixtures async partageant la même connexion provoquent `"another operation is in progress"`. NullPool garantit une connexion fraîche par test.
