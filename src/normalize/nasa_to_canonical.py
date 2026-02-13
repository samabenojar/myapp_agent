from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ValidationError

from src.ingest.nasa import RAW_NASA_FILE, REQUIRED_RAW_COLUMNS
from src.schema.canonical import CANONICAL_COLUMNS, CanonicalSample

CANONICAL_FILE = Path("canonical/samples.csv")


def _to_optional_float(value: str) -> float | None:
    stripped = value.strip()
    if stripped == "":
        return None
    return float(stripped)


def _to_optional_int(value: str) -> int | None:
    stripped = value.strip()
    if stripped == "":
        return None
    return int(stripped)


def normalize_nasa_to_canonical(
    raw_path: Path = RAW_NASA_FILE, output_path: Path = CANONICAL_FILE
) -> int:
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw NASA file not found: {raw_path}")

    with raw_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if reader.fieldnames is None:
            raise ValueError("Raw NASA file is missing a header row")
        missing = [name for name in REQUIRED_RAW_COLUMNS if name not in reader.fieldnames]
        if missing:
            raise ValueError(f"Raw NASA file missing required columns: {missing}")

        canonical_rows: list[CanonicalSample] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                sample = CanonicalSample(
                    run_id=str(row["run_id"]),
                    timestamp=float(row["time_s"]),
                    voltage=float(row["voltage_v"]),
                    current=float(row["current_a"]),
                    temperature=_to_optional_float(row["temperature_c"]),
                    cycle=_to_optional_int(row["cycle"]),
                )
            except (ValueError, ValidationError) as exc:
                raise ValueError(f"Failed to normalize row {row_number}: {exc}") from exc
            canonical_rows.append(sample)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        for sample in canonical_rows:
            writer.writerow(sample.model_dump())

    return len(canonical_rows)


def main() -> None:
    row_count = normalize_nasa_to_canonical()
    print(f"Wrote {row_count} canonical rows to {CANONICAL_FILE}")


if __name__ == "__main__":
    main()
