# TODO — AI Act Governance Framework

## Phase 1 — Fondations (infrastructure & auth)

### Fichiers de configuration
- [x] `CLAUDE.md`
- [x] `docker-compose.yml`
- [x] `.env.example`
- [x] `.env`
- [x] `.gitignore`
- [x] `Makefile`
- [x] `.pre-commit-config.yaml`

### Backend — setup
- [x] `backend/Dockerfile` (multi-stage: development + production)
- [x] `backend/requirements.txt`
- [x] `backend/pyproject.toml` (ruff, mypy, pytest config)
- [x] `backend/alembic.ini`
- [x] `backend/alembic/env.py`
- [x] `backend/app/__init__.py`
- [x] `backend/app/main.py` (FastAPI app, lifespan, middlewares)
- [x] `backend/app/config.py` (pydantic-settings)
- [x] `backend/app/database.py` (AsyncEngine, AsyncSession, get_db)
- [x] `backend/app/core/security.py` (JWT + bcrypt)
- [x] `backend/app/core/dependencies.py` (get_current_user, require_role)
- [x] `backend/app/core/exceptions.py`

### Modèles & migrations
- [x] `backend/app/models/user.py`
- [ ] `backend/alembic/versions/001_create_users.py` (à générer avec `make migrate-generate`)
- [x] `backend/app/schemas/auth.py`
- [x] `backend/app/routers/auth.py`
- [x] `backend/app/services/audit_logger.py` (SHA-256 — TESTÉ ✓)

### Tests fondations
- [x] `backend/tests/conftest.py`
- [ ] `backend/tests/factories/user_factory.py`
- [x] `backend/tests/unit/test_audit_logger.py`
- [x] `backend/tests/integration/test_auth_api.py`

### Frontend — setup
- [x] `frontend/` (structure Next.js 15)
- [x] `frontend/src/app/layout.tsx`
- [x] `frontend/src/app/(auth)/login/page.tsx`
- [x] `frontend/src/components/layout/Sidebar.tsx`
- [x] `frontend/src/components/layout/AuthGuard.tsx`
- [x] `frontend/src/lib/api.ts` (fetch wrapper)
- [x] `frontend/src/lib/auth.ts` (JWT store)
- [ ] `frontend/src/hooks/useAuth.ts`

### Scripts
- [x] `backend/scripts/seed_db.py`
- [x] `scripts/run_migrations.sh`

---

## Phase 2 — Registre des systèmes IA

- [x] `backend/app/models/ai_system.py`
- [ ] `backend/alembic/versions/002_create_ai_systems.py`
- [ ] `backend/app/schemas/ai_system.py`
- [ ] `backend/app/routers/ai_systems.py`
- [ ] `backend/tests/factories/system_factory.py`
- [ ] `backend/tests/integration/test_systems_api.py`
- [ ] `frontend/src/app/systems/page.tsx`
- [ ] `frontend/src/app/systems/new/page.tsx`
- [ ] `frontend/src/app/systems/[id]/page.tsx`
- [ ] `frontend/src/components/ui/DataTable.tsx`
- [ ] `frontend/src/components/ui/Badge.tsx`

---

## Phase 3 — Risk Scorer

- [ ] `backend/app/models/risk_assessment.py`
- [ ] `backend/alembic/versions/003_create_risk_assessments.py`
- [ ] `backend/app/data/questionnaire.json` (25 questions AI Act)
- [ ] `backend/app/services/risk_scorer.py` (moteur de règles)
- [ ] `backend/app/schemas/risk_assessment.py`
- [ ] `backend/app/routers/risk_scorer.py`
- [ ] `backend/tests/unit/test_risk_scorer.py`
- [ ] `backend/tests/integration/test_risk_api.py`
- [ ] `frontend/src/app/systems/[id]/risk/page.tsx`
- [ ] `frontend/src/components/risk-scorer/QuestionnaireWizard.tsx`
- [ ] `frontend/src/components/risk-scorer/RiskResultCard.tsx`
- [ ] `frontend/src/components/risk-scorer/CategoryExplainer.tsx`
- [ ] Export PDF risk assessment (reportlab)

---

## Phase 4 — Model Card Generator

- [ ] `backend/app/models/model_card.py`
- [ ] `backend/alembic/versions/004_create_model_cards.py`
- [ ] `backend/app/schemas/model_card.py`
- [ ] `backend/app/services/model_card_generator.py` (OpenRouter)
- [ ] `backend/app/routers/model_cards.py`
- [ ] `frontend/src/app/systems/[id]/model-card/page.tsx`
- [ ] `frontend/src/components/model-card/ModelCardForm.tsx`
- [ ] `frontend/src/components/model-card/ModelCardPreview.tsx`
- [ ] Export PDF model card

---

## Phase 5 — PII Scanner

- [ ] `backend/app/models/pii_scan.py`
- [ ] `backend/alembic/versions/006_create_pii_scans.py`
- [ ] `presidio/presidio-config.yaml` (recognizers FR custom)
- [ ] `backend/app/services/pii_scanner.py` (wrapper async Presidio)
- [ ] `backend/app/schemas/pii_scan.py`
- [ ] `backend/app/routers/pii_scanner.py`
- [ ] `backend/tests/unit/test_pii_scanner.py`
- [ ] `backend/tests/integration/test_pii_api.py`
- [ ] `frontend/src/app/pii-scanner/page.tsx`
- [ ] `frontend/src/components/pii-scanner/FileUploadZone.tsx`
- [ ] `frontend/src/components/pii-scanner/ScanResultsTable.tsx`
- [ ] `frontend/src/components/pii-scanner/PIIHighlighter.tsx`

---

## Phase 6 — Dashboard DSI/DPO

- [ ] `backend/app/models/audit_log.py` (trigger append-only)
- [ ] `backend/alembic/versions/005_create_audit_logs.py`
- [ ] `backend/app/routers/audit_logs.py`
- [ ] `backend/app/routers/dashboard.py`
- [ ] `frontend/src/app/dashboard/page.tsx`
- [ ] `frontend/src/app/audit/page.tsx`
- [ ] `frontend/src/app/systems/[id]/audit/page.tsx`
- [ ] `frontend/src/components/dashboard/RiskDistributionChart.tsx`
- [ ] `frontend/src/components/dashboard/ComplianceStatusWidget.tsx`
- [ ] `frontend/src/components/dashboard/ActionRequiredPanel.tsx`
- [ ] `frontend/src/components/dashboard/SystemsAtRiskTable.tsx`
- [ ] `frontend/src/components/audit/AuditLogTable.tsx`
- [ ] `frontend/src/components/audit/AuditLogFilter.tsx`

---

## Phase 7 — Polish & Production

- [ ] `backend/app/routers/exports.py` (PDF complet + portfolio)
- [ ] `backend/app/services/pdf_exporter.py` (reportlab templates)
- [ ] Rate limiting (slowapi)
- [ ] CORS strict + security headers
- [ ] Dockerfile multi-stage backend + frontend
- [ ] Tests Playwright E2E (login → risk assessment flow)
- [ ] `README.md` complet
- [ ] `docs/api-spec.yaml` (OpenAPI export)
- [ ] `docs/risk-scoring-rules.md`
- [ ] CI/CD GitHub Actions (lint + test + build)
