from __future__ import annotations

import json
from pathlib import Path

from src.events.envelope import EventEnvelope
from src.events.store import EventStore


class RawIngestedToValidatedConsumer:
    """Projection that converts RawIngested events into RawValidated events once."""

    def __init__(
        self,
        event_store: EventStore,
        state_path: Path = Path("canonical/projections/raw_validated_state.json"),
    ) -> None:
        self.event_store = event_store
        self.state_path = state_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def consume(self) -> int:
        state = self._load_state()
        processed_ids: set[str] = set(state.get("processed_event_ids", []))
        produced_count = 0

        for stored_event in self.event_store.read_all(event_type="RawIngested"):
            envelope = stored_event.envelope
            state["last_sequence"] = stored_event.sequence

            if envelope.event_id in processed_ids:
                continue

            payload = dict(envelope.payload)
            row_count = int(payload.get("row_count", 0))
            if row_count < 0:
                raise ValueError(f"RawIngested event {envelope.event_id} has negative row_count")

            validated = EventEnvelope.create(
                event_type="RawValidated",
                event_version="1",
                producer="src.events.consumer.RawIngestedToValidatedConsumer",
                idempotency_key=f"raw-validated:{envelope.event_id}",
                payload={
                    "source_event_id": envelope.event_id,
                    "raw_path": payload.get("raw_path"),
                    "output_path": payload.get("output_path"),
                    "row_count": row_count,
                    "is_valid": True,
                },
                metadata={"projection": "RawIngestedToValidated"},
            )
            self.event_store.append(validated)

            processed_ids.add(envelope.event_id)
            state["processed_event_ids"] = sorted(processed_ids)
            produced_count += 1

        self._save_state(state)
        return produced_count

    def _load_state(self) -> dict[str, object]:
        if not self.state_path.exists():
            return {
                "projection": "RawIngestedToValidated",
                "last_sequence": 0,
                "processed_event_ids": [],
            }
        with self.state_path.open("r", encoding="utf-8") as infile:
            return json.load(infile)

    def _save_state(self, state: dict[str, object]) -> None:
        with self.state_path.open("w", encoding="utf-8") as outfile:
            json.dump(state, outfile, indent=2, sort_keys=True)
            outfile.write("\n")
