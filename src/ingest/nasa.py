from __future__ import annotations

import csv
from pathlib import Path

from src.events.consumer import RawIngestedToValidatedConsumer
from src.events.envelope import EventEnvelope
from src.events.store import EventStore, get_default_event_store

RAW_NASA_FILE = Path("data/nasa/nasa_samples.csv")
INGESTED_FILE = Path("canonical/nasa_ingested.csv")
REQUIRED_RAW_COLUMNS = ["run_id", "time_s", "voltage_v", "current_a", "temperature_c", "cycle"]


def _validate_columns(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("Raw NASA file is missing a header row")
    missing = [name for name in REQUIRED_RAW_COLUMNS if name not in fieldnames]
    if missing:
        raise ValueError(f"Raw NASA file missing required columns: {missing}")


def ingest_nasa(
    raw_path: Path = RAW_NASA_FILE,
    output_path: Path = INGESTED_FILE,
    event_store: EventStore | None = None,
    projection_consumer: RawIngestedToValidatedConsumer | None = None,
) -> int:
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw NASA file not found: {raw_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        _validate_columns(reader.fieldnames)
        rows = list(reader)
        for row_number, row in enumerate(rows, start=2):
            missing_values = [
                column for column in REQUIRED_RAW_COLUMNS if column not in row or row[column] is None
            ]
            if missing_values:
                raise ValueError(
                    f"Raw NASA row {row_number} is malformed and missing values for: {missing_values}"
                )

    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=REQUIRED_RAW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in REQUIRED_RAW_COLUMNS})

    active_store = event_store or get_default_event_store()
    raw_ingested = EventEnvelope.create(
        event_type="RawIngested",
        event_version="1",
        producer="src.ingest.nasa.ingest_nasa",
        idempotency_key=f"{raw_path}:{output_path}:{len(rows)}",
        payload={
            "raw_path": str(raw_path),
            "output_path": str(output_path),
            "required_columns": list(REQUIRED_RAW_COLUMNS),
            "row_count": len(rows),
        },
        metadata={"pipeline_step": "ingest"},
    )
    active_store.append(raw_ingested)

    active_consumer = projection_consumer or RawIngestedToValidatedConsumer(active_store)
    active_consumer.consume()

    return len(rows)


def main() -> None:
    row_count = ingest_nasa()
    print(f"Ingested {row_count} NASA rows into {INGESTED_FILE}")


if __name__ == "__main__":
    main()
