import csv
import math
from pathlib import Path

import pytest

from src.ingest.nasa import ingest_nasa
from src.derive.vbat_sag import derive_vbat_sag
from src.normalize.nasa_to_canonical import normalize_nasa_to_canonical
from src.schema.canonical import CANONICAL_COLUMNS


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        return list(reader)


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
