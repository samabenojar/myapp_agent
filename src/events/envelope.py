from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class EventEnvelope:
    """Versioned event contract shared by producers, log, and consumers."""

    event_id: str
    event_type: str
    event_version: str
    occurred_at: str
    producer: str
    idempotency_key: str
    payload: dict[str, Any]
    metadata: dict[str, Any]

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        event_version: str,
        producer: str,
        idempotency_key: str,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> "EventEnvelope":
        occurred_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            event_version=event_version,
            occurred_at=occurred_at,
            producer=producer,
            idempotency_key=idempotency_key,
            payload=dict(payload),
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at,
            "producer": self.producer,
            "idempotency_key": self.idempotency_key,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventEnvelope":
        return cls(
            event_id=str(data["event_id"]),
            event_type=str(data["event_type"]),
            event_version=str(data["event_version"]),
            occurred_at=str(data["occurred_at"]),
            producer=str(data["producer"]),
            idempotency_key=str(data["idempotency_key"]),
            payload=dict(data.get("payload", {})),
            metadata=dict(data.get("metadata", {})),
        )
