from __future__ import annotations

import uuid
from typing import Protocol

from app.models.user import User


class UserRepository(Protocol):
    async def get(self, user_id: uuid.UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None: ...
