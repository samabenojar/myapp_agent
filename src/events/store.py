from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.events.envelope import EventEnvelope

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency
    psycopg = None


@dataclass(frozen=True)
class StoredEvent:
    sequence: int
    envelope: EventEnvelope


class EventStore(Protocol):
    def append(self, envelope: EventEnvelope) -> int:
        ...

    def read_all(self, event_type: str | None = None) -> list[StoredEvent]:
        ...


class JsonlEventStore:
    """Append-only JSONL event store for local replayable execution."""

    def __init__(self, path: Path = Path("canonical/event_log.jsonl")) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, envelope: EventEnvelope) -> int:
        sequence = sum(1 for _ in self.path.open("r", encoding="utf-8")) + 1 if self.path.exists() else 1
        with self.path.open("a", encoding="utf-8") as outfile:
            outfile.write(json.dumps(envelope.to_dict(), separators=(",", ":"), sort_keys=True))
            outfile.write("\n")
        return sequence

    def read_all(self, event_type: str | None = None) -> list[StoredEvent]:
        if not self.path.exists():
            return []

        events: list[StoredEvent] = []
        with self.path.open("r", encoding="utf-8") as infile:
            for index, line in enumerate(infile, start=1):
                if line.strip() == "":
                    continue
                envelope = EventEnvelope.from_dict(json.loads(line))
                if event_type is None or envelope.event_type == event_type:
                    events.append(StoredEvent(sequence=index, envelope=envelope))
        return events


class PostgresEventStore:
    """Append-only Postgres-backed event log when DATABASE_URL and psycopg are available."""

    def __init__(self, dsn: str) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg is not installed")

        self.dsn = dsn
        self._ensure_table()

    def _connect(self):
        return psycopg.connect(self.dsn)

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS event_log (
                        sequence BIGSERIAL PRIMARY KEY,
                        envelope JSONB NOT NULL
                    )
                    """
                )
            conn.commit()

    def append(self, envelope: EventEnvelope) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO event_log (envelope) VALUES (%s::jsonb) RETURNING sequence",
                    [json.dumps(envelope.to_dict())],
                )
                sequence = int(cur.fetchone()[0])
            conn.commit()
        return sequence

    def read_all(self, event_type: str | None = None) -> list[StoredEvent]:
        clause = ""
        params: list[str] = []
        if event_type is not None:
            clause = " WHERE envelope->>'event_type' = %s"
            params.append(event_type)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT sequence, envelope FROM event_log{clause} ORDER BY sequence", params)
                rows = cur.fetchall()

        events: list[StoredEvent] = []
        for sequence, envelope in rows:
            data = json.loads(envelope) if isinstance(envelope, str) else dict(envelope)
            events.append(StoredEvent(sequence=int(sequence), envelope=EventEnvelope.from_dict(data)))
        return events


def get_default_event_store(
    *,
    jsonl_path: Path = Path("canonical/event_log.jsonl"),
    database_url: str | None = None,
) -> EventStore:
    dsn = database_url or os.getenv("DATABASE_URL")
    if dsn:
        try:
            return PostgresEventStore(dsn)
        except Exception:
            # Fall back to JSONL when Postgres is unavailable in local runs.
            pass
    return JsonlEventStore(jsonl_path)

