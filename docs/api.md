# Référence API

Base URL : `http://localhost:8000/api/v1`
Documentation interactive : http://localhost:8000/docs

Tous les endpoints (sauf `/auth/login` et `/health`) requièrent un header :
```
Authorization: Bearer <access_token>
```

---

## Authentification

### `POST /auth/login`
```json
// Request
{ "email": "admin@aiact-governance.fr", "password": "admin1234" } // pragma: allowlist secret

// Response 200
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 28800 }
```

### `GET /auth/me`
Retourne l'utilisateur courant.

### `POST /auth/users` *(admin)*
Créer un utilisateur.
```json
{ "email": "user@example.com", "full_name": "Prénom Nom", "password": "Secure123!", "role": "reviewer" } // pragma: allowlist secret
```

---

## Systèmes IA

### `GET /systems`
Liste paginée avec filtres.

| Paramètre | Type | Description |
|-----------|------|-------------|
| `page` | int | Page (défaut: 1) |
| `per_page` | int | Par page (max: 100) |
| `status` | string | Filtre statut |
| `risk_category` | string | Filtre risque |
| `search` | string | Recherche par nom |

### `POST /systems` *(reviewer+)*
```json
{
  "name": "Scoring CV RH",
  "description": "...",
  "version": "1.0.0",
  "owner_team": "RH",
  "tech_stack": ["Python", "scikit-learn"],
  "deployment_env": "production",
  "use_case": "...",
  "data_types": ["CV", "emails"],
  "is_autonomous": true,
  "affects_persons": true
}
```

### `GET /systems/{id}`
Détail d'un système.

### `PATCH /systems/{id}` *(reviewer+)*
Mise à jour partielle. Tous les champs sont optionnels.

### `DELETE /systems/{id}` *(admin)*
Suppression définitive.

---

## Risk Scorer

### `GET /risk/questionnaire`
Retourne le questionnaire AI Act complet (5 sections, 20 questions).

```json
{
  "version": "1.0",
  "sections": [
    {
      "id": "s1",
      "title": "Usage et domaine d'application",
      "questions": [
        {
          "id": "q1_biometric_realtime",
          "text": "Le système effectue-t-il une identification biométrique...",
          "type": "boolean",
          "ai_act_ref": "Art. 5(1)(b)",
          "triggers_prohibited": true
        }
      ]
    }
  ]
}
```

### `POST /risk/assess/{system_id}` *(reviewer+)*
Lance une évaluation AI Act.

```json
// Request
{
  "answers": {
    "q1_biometric_realtime": false,
    "q7_employment": true,
    "q12_autonomous_decision": true
  }
}

// Response 201
{
  "id": "uuid",
  "risk_category": "high_risk",
  "total_score": 65,
  "justification": "Le système opère dans le domaine de l'emploi...",
  "ai_act_articles": ["Annexe III §4", "Art. 9", "Art. 10"],
  "required_actions": [
    {
      "article": "Art. 9",
      "obligation": "Système de gestion des risques",
      "deadline": "Immédiatement"
    }
  ],
  "valid_until": "2027-05-24"
}
```

**Catégories possibles** : `prohibited` · `high_risk` · `limited_risk` · `minimal_risk`

### `GET /risk/assessments/{system_id}`
Historique des évaluations d'un système.

---

## Model Cards

### `GET /model-cards/{system_id}`
Liste des model cards d'un système.

### `POST /model-cards/{system_id}` *(reviewer+)*
Créer une model card. Tous les champs texte sont optionnels.

```json
{
  "model_name": "Scoring CV RH v2",
  "model_type": "Classification binaire",
  "architecture": "Random Forest + BERT embeddings",
  "framework": "scikit-learn 1.3",
  "license": "Propriétaire",
  "limitations": "Performances dégradées sur CV non francophones...",
  "out_of_scope_uses": "Ne pas utiliser pour des décisions finales...",
  "ethical_considerations": "...",
  "conformity_measures": "...",
  "human_oversight": "...",
  "known_biases": "...",
  "developer_contact": "ia-team@company.fr",
  "dpo_contact": "dpo@company.fr"
}
```

### `PATCH /model-cards/{card_id}` *(reviewer+)*
Mise à jour partielle.

### `POST /model-cards/{card_id}/publish` *(reviewer+)*
Passe le statut de `draft` à `published`.

### `POST /model-cards/{system_id}/generate` *(reviewer+)*
**Auto-génération LLM** : génère les 6 sections textuelles via OpenRouter/Claude Haiku.

```json
// Response 200
{
  "limitations": "...",
  "out_of_scope_uses": "...",
  "ethical_considerations": "...",
  "conformity_measures": "...",
  "human_oversight": "...",
  "known_biases": "..."
}
```

---

## Audit Logs

### `GET /audit` *(admin)*
Journal global avec filtres.

| Paramètre | Description |
|-----------|-------------|
| `action` | Filtrer par action (ex: `ai_system.created`) |
| `resource_type` | Type de ressource |
| `actor_id` | UUID de l'acteur |
| `from_date` / `to_date` | Plage de dates ISO 8601 |

### `GET /audit/{resource_type}/{resource_id}` *(reviewer+)*
Audit trail d'une ressource spécifique.

```bash
GET /audit/ai_system/cf77e278-...
GET /audit/risk_assessment/abc123-...
```

### `GET /audit/entry/{log_id}/verify` *(admin)*
Vérifie l'intégrité SHA-256 d'une entrée.

```json
{
  "log_id": "uuid",
  "valid": true,
  "hash_match": true,
  "stored_hash": "a1b2c3...",
  "computed_hash": "a1b2c3..."
}
```

---

## PII Scanner

### `POST /pii/scan/text` *(reviewer+)*
Scanner un texte libre.

```json
// Request
{
  "text": "Jean Dupont, 06 12 34 56 78, jean@example.com...",
  "confidence_threshold": 0.85,
  "ai_system_id": "uuid (optionnel)"
}

// Response 201
{
  "pii_found": true,
  "findings": [
    { "entity_type": "PERSON", "score": 0.95, "start": 0, "end": 11, "context": "Jean Dupont" },
    { "entity_type": "PHONE_NUMBER", "score": 0.90, "start": 13, "end": 25 }
  ],
  "entity_summary": { "PERSON": 1, "PHONE_NUMBER": 1, "EMAIL_ADDRESS": 1 },
  "risk_level": "high",
  "recommendations": ["Anonymiser les noms avant traitement", "..."]
}
```

### `POST /pii/scan/file` *(reviewer+)*
Scanner un fichier (TXT, CSV, JSON — max 10 MB).

```bash
curl -X POST http://localhost:8000/api/v1/pii/scan/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@dataset.csv"
```

### `GET /pii/scans`
Historique des scans de l'utilisateur courant.

---

## Dashboard

### `GET /dashboard/summary`
```json
{
  "total_systems": 12,
  "compliant": 4,
  "under_review": 5,
  "non_compliant": 2,
  "not_assessed": 1,
  "risk_distribution": {
    "prohibited": 0,
    "high_risk": 3,
    "limited_risk": 6,
    "minimal_risk": 3
  },
  "compliance_rate": 33
}
```

### `GET /dashboard/actions-required`
Actions réglementaires en attente sur tous les systèmes évalués.

### `GET /dashboard/timeline`
Dates limites réglementaires AI Act (2024-2027).

---

## Exports

### `GET /exports/compliance-report/{system_id}`
Télécharge un rapport de conformité PDF.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/exports/compliance-report/{system_id} \
  -o rapport_conformite.pdf
```

Le PDF inclut : informations système · évaluation risque · obligations réglementaires · model card · dernières entrées d'audit.

---

## Codes d'erreur

| Code | Signification |
|------|--------------|
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Non autorisé (rôle insuffisant) |
| 404 | Ressource introuvable |
| 409 | Conflit (email déjà utilisé) |
| 413 | Fichier trop volumineux |
| 415 | Format de fichier non supporté |
| 422 | Validation Pydantic échouée |
| 503 | Service externe indisponible (Presidio, OpenRouter) |

Format des erreurs :
```json
{ "error": "Description du problème", "status_code": 403 }
```
