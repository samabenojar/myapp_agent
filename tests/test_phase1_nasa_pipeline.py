import csv
import math
from pathlib import Path

import pytest

from src.derive.vbat_sag import derive_vbat_sag
from src.events.consumer import RawIngestedToValidatedConsumer
from src.events.envelope import EventEnvelope
from src.events.store import JsonlEventStore
from src.ingest.nasa import ingest_nasa
from src.normalize.nasa_to_canonical import normalize_nasa_to_canonical
from src.schema.canonical import CANONICAL_COLUMNS


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        return list(reader)


def _raw_ingested_event(event_id: str, row_count: int = 2) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id,
        event_type="RawIngested",
        event_version="1",
        occurred_at="2026-02-17T00:00:00Z",
        producer="tests",
        idempotency_key=f"raw:{event_id}",
        payload={
            "raw_path": "data/nasa/nasa_samples.csv",
            "output_path": "canonical/nasa_ingested.csv",
            "required_columns": [
                "run_id",
                "time_s",
                "voltage_v",
                "current_a",
                "temperature_c",
                "cycle",
            ],
            "row_count": row_count,
        },
        metadata={"pipeline_step": "ingest"},
    )


def test_canonical_output_columns_and_quality(tmp_path: Path) -> None:
    raw_path = Path("data/nasa/nasa_samples.csv")
    canonical_path = tmp_path / "samples.csv"

    normalize_nasa_to_canonical(raw_path=raw_path, output_path=canonical_path)

    with canonical_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        assert reader.fieldnames == CANONICAL_COLUMNS
        rows = list(reader)

    by_run_timestamps: dict[str, list[float]] = {}
    for row in rows:
        timestamp = float(row["timestamp"])
        voltage = float(row["voltage"])
        current = float(row["current"])

        assert not math.isnan(voltage)
        assert not math.isnan(current)

        by_run_timestamps.setdefault(row["run_id"], []).append(timestamp)

    for timestamps in by_run_timestamps.values():
        assert timestamps == sorted(timestamps)


def test_derived_output_adds_vbat_sag_and_keeps_canonical_columns(tmp_path: Path) -> None:
    raw_path = Path("data/nasa/nasa_samples.csv")
    canonical_path = tmp_path / "samples.csv"
    derived_path = tmp_path / "samples_with_vbat_sag.csv"

    normalize_nasa_to_canonical(raw_path=raw_path, output_path=canonical_path)
    derive_vbat_sag(canonical_path=canonical_path, output_path=derived_path)

    rows = _read_csv(derived_path)
    assert rows

    with derived_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        assert reader.fieldnames == [*CANONICAL_COLUMNS, "vbat_sag"]

    for row in rows:
        for column in CANONICAL_COLUMNS:
            assert column in row
        assert "vbat_sag" in row
        assert float(row["vbat_sag"]) >= 0.0


def test_ingest_fails_on_malformed_row_with_missing_columns(tmp_path: Path) -> None:
    raw_path = tmp_path / "malformed.csv"
    raw_path.write_text(
        "\n".join(
            [
                "run_id,time_s,voltage_v,current_a,temperature_c,cycle",
                "run_1,0.0,4.1,0.0,25.0,1",
                "run_1,1.0,4.0,1.2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="malformed and missing values"):
        ingest_nasa(raw_path=raw_path, output_path=tmp_path / "ingested.csv")


def test_normalize_fails_on_empty_run_id(tmp_path: Path) -> None:
    raw_path = tmp_path / "empty_run_id.csv"
    raw_path.write_text(
        "\n".join(
            [
                "run_id,time_s,voltage_v,current_a,temperature_c,cycle",
                ",0.0,4.1,0.0,25.0,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="run_id must not be empty"):
        normalize_nasa_to_canonical(raw_path=raw_path, output_path=tmp_path / "samples.csv")


def test_vbat_sag_is_deterministic_for_same_input(tmp_path: Path) -> None:
    raw_path = Path("data/nasa/nasa_samples.csv")
    canonical_path = tmp_path / "samples.csv"
    derived_path_1 = tmp_path / "samples_with_vbat_sag_1.csv"
    derived_path_2 = tmp_path / "samples_with_vbat_sag_2.csv"

    normalize_nasa_to_canonical(raw_path=raw_path, output_path=canonical_path)
    derive_vbat_sag(canonical_path=canonical_path, output_path=derived_path_1)
    derive_vbat_sag(canonical_path=canonical_path, output_path=derived_path_2)

    assert derived_path_1.read_text(encoding="utf-8") == derived_path_2.read_text(encoding="utf-8")


def test_pipeline_does_not_modify_raw_data_file(tmp_path: Path) -> None:
    raw_path = Path("data/nasa/nasa_samples.csv")
    before = raw_path.read_text(encoding="utf-8")

    canonical_path = tmp_path / "samples.csv"
    derived_path = tmp_path / "samples_with_vbat_sag.csv"
    normalize_nasa_to_canonical(raw_path=raw_path, output_path=canonical_path)
    derive_vbat_sag(canonical_path=canonical_path, output_path=derived_path)

    after = raw_path.read_text(encoding="utf-8")
    assert before == after


def test_consumer_ignores_duplicate_event_id(tmp_path: Path) -> None:
    store = JsonlEventStore(tmp_path / "event_log.jsonl")
    state_path = tmp_path / "projection_state.json"

    duplicate_id = "event-duplicate-1"
    store.append(_raw_ingested_event(duplicate_id, row_count=3))
    store.append(_raw_ingested_event(duplicate_id, row_count=3))

    consumer = RawIngestedToValidatedConsumer(store, state_path=state_path)
    produced = consumer.consume()

    raw_validated = [
        stored.envelope for stored in store.read_all() if stored.envelope.event_type == "RawValidated"
    ]
    assert produced == 1
    assert len(raw_validated) == 1


def test_consumer_is_replay_safe_across_reruns(tmp_path: Path) -> None:
    store = JsonlEventStore(tmp_path / "event_log.jsonl")
    state_path = tmp_path / "projection_state.json"

    consumer = RawIngestedToValidatedConsumer(store, state_path=state_path)

    output_path = tmp_path / "nasa_ingested.csv"
    ingest_nasa(
        raw_path=Path("data/nasa/nasa_samples.csv"),
        output_path=output_path,
        event_store=store,
        projection_consumer=consumer,
    )

    produced_on_rerun = consumer.consume()

    raw_ingested = [
        stored.envelope for stored in store.read_all() if stored.envelope.event_type == "RawIngested"
    ]
    raw_validated = [
        stored.envelope for stored in store.read_all() if stored.envelope.event_type == "RawValidated"
    ]

    assert output_path.exists()
    assert len(raw_ingested) == 1
    assert len(raw_validated) == 1
    assert produced_on_rerun == 0
