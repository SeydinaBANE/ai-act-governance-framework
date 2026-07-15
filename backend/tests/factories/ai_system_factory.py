from __future__ import annotations

import uuid
from datetime import UTC, datetime

import factory
from app.models.ai_system import AISystem, SystemStatus


class AISystemFactory(factory.Factory):
    class Meta:
        model = AISystem

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Système {n}")
    description = "Système de test"
    status = SystemStatus.DRAFT
    current_risk_category = None
    is_autonomous = False
    affects_persons = False
    created_by = factory.LazyFunction(uuid.uuid4)
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
