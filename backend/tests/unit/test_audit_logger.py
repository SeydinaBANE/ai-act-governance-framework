from __future__ import annotations

import hashlib
import json

import pytest

from app.services.audit_logger import _compute_hash, verify_hash
from app.models.audit_log import AuditLog
from datetime import datetime, UTC
import uuid


def test_compute_hash_deterministic() -> None:
    h1 = _compute_hash("actor-1", "user.created", "res-1", "2026-01-01T00:00:00", {"key": "val"})
    h2 = _compute_hash("actor-1", "user.created", "res-1", "2026-01-01T00:00:00", {"key": "val"})
    assert h1 == h2


def test_compute_hash_changes_with_actor() -> None:
    h1 = _compute_hash("actor-1", "user.created", "res-1", "2026-01-01T00:00:00", None)
    h2 = _compute_hash("actor-2", "user.created", "res-1", "2026-01-01T00:00:00", None)
    assert h1 != h2


def test_compute_hash_changes_with_payload() -> None:
    h1 = _compute_hash("actor", "action", "res", "ts", {"key": "val1"})
    h2 = _compute_hash("actor", "action", "res", "ts", {"key": "val2"})
    assert h1 != h2


def test_compute_hash_is_sha256() -> None:
    h = _compute_hash("a", "b", "c", "d", None)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_verify_hash_valid() -> None:
    actor_id = uuid.uuid4()
    resource_id = uuid.uuid4()
    ts = datetime.now(UTC)
    payload = {"key": "value"}

    entry = AuditLog()
    entry.actor_id = actor_id
    entry.actor_email = "test@test.com"
    entry.action = "test.action"
    entry.resource_id = resource_id
    entry.resource_type = "test"
    entry.input_payload = payload
    entry.created_at = ts
    entry.payload_hash = _compute_hash(
        str(actor_id), "test.action", str(resource_id), ts.isoformat(), payload
    )

    assert verify_hash(entry) is True


def test_verify_hash_tampered() -> None:
    actor_id = uuid.uuid4()
    ts = datetime.now(UTC)

    entry = AuditLog()
    entry.actor_id = actor_id
    entry.actor_email = "test@test.com"
    entry.action = "test.action"
    entry.resource_id = None
    entry.resource_type = "test"
    entry.input_payload = {"key": "original"}
    entry.created_at = ts
    entry.payload_hash = "tampered_hash_that_is_64_chars_long_padding_padding_padding_pad"

    assert verify_hash(entry) is False
