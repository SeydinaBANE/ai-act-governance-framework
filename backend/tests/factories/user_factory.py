from __future__ import annotations

import uuid

import factory
from app.models.user import User, UserRole


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    full_name = factory.Faker("name")
    hashed_password = "hashed"
    role = UserRole.REVIEWER
    is_active = True
