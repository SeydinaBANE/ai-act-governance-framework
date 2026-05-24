#!/usr/bin/env python3
"""Seed script — données de démonstration pour l'environnement de dev."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire backend au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.core.security import hash_password
from app.database import Base
from app.models.ai_system import AISystem, RiskCategory, SystemStatus
from app.models.user import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as db:
        # Utilisateurs
        admin = User(
            email="admin@aiact-governance.fr",
            full_name="Administrateur",
            hashed_password=hash_password("Admin@123456"),
            role=UserRole.ADMIN,
        )
        reviewer = User(
            email="reviewer@aiact-governance.fr",
            full_name="Analyste Conformité",
            hashed_password=hash_password("Review@123456"),
            role=UserRole.REVIEWER,
        )
        readonly = User(
            email="viewer@aiact-governance.fr",
            full_name="Lecteur DSI",
            hashed_password=hash_password("View@123456"),
            role=UserRole.READONLY,
        )
        db.add_all([admin, reviewer, readonly])
        await db.flush()

        # Systèmes IA de démonstration
        system_rag = AISystem(
            name="Plateforme RAG Entreprise",
            description="Système de question-réponse sur documents internes via RAG (Retrieval-Augmented Generation).",
            version="1.0.0",
            owner_team="DSI — IA & Data",
            tech_stack=["Python", "FastAPI", "pgvector", "LangChain", "Claude Haiku"],
            deployment_env="production",
            use_case="Permettre aux collaborateurs d'interroger la base documentaire (PDF, Confluence, Slack) via un chat IA.",
            data_types=["documents internes", "emails Slack", "pages Confluence"],
            is_autonomous=False,
            affects_persons=True,
            status=SystemStatus.UNDER_REVIEW,
            current_risk_category=RiskCategory.LIMITED_RISK,
            created_by=admin.id,
        )
        system_hr = AISystem(
            name="Scoring CV RH",
            description="Système d'aide à la présélection de candidatures par analyse automatique des CV.",
            version="2.1.0",
            owner_team="RH — Recrutement",
            tech_stack=["Python", "scikit-learn", "BERT"],
            deployment_env="production",
            use_case="Classer automatiquement les candidatures reçues selon leur adéquation au poste.",
            data_types=["CV", "lettres de motivation", "profils LinkedIn"],
            is_autonomous=True,
            affects_persons=True,
            status=SystemStatus.NON_COMPLIANT,
            current_risk_category=RiskCategory.HIGH_RISK,
            created_by=reviewer.id,
        )
        system_chatbot = AISystem(
            name="Chatbot Support Client",
            description="Assistant virtuel pour le support de niveau 1.",
            version="3.0.0",
            owner_team="Support Client",
            tech_stack=["Python", "Rasa", "OpenAI GPT-4o-mini"],
            deployment_env="production",
            use_case="Répondre aux questions fréquentes des clients et router vers un agent humain si nécessaire.",
            data_types=["conversations client", "tickets support"],
            is_autonomous=False,
            affects_persons=True,
            status=SystemStatus.COMPLIANT,
            current_risk_category=RiskCategory.LIMITED_RISK,
            created_by=admin.id,
        )
        db.add_all([system_rag, system_hr, system_chatbot])
        await db.commit()

    await engine.dispose()

    print("✓ Seed terminé.")
    print("\nComptes créés :")
    print("  admin@aiact-governance.fr / Admin@123456 [admin]")
    print("  reviewer@aiact-governance.fr / Review@123456 [reviewer]")
    print("  viewer@aiact-governance.fr / View@123456 [readonly]")
    print("\nSystèmes créés : 3 (RAG, Scoring CV, Chatbot)")
    print("\nAccès : http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
