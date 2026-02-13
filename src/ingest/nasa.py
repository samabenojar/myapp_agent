from __future__ import annotations

import csv
from pathlib import Path

RAW_NASA_FILE = Path("data/nasa/nasa_samples.csv")
INGESTED_FILE = Path("canonical/nasa_ingested.csv")
REQUIRED_RAW_COLUMNS = ["run_id", "time_s", "voltage_v", "current_a", "temperature_c", "cycle"]


def _validate_columns(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("Raw NASA file is missing a header row")
    missing = [name for name in REQUIRED_RAW_COLUMNS if name not in fieldnames]
    if missing:
        raise ValueError(f"Raw NASA file missing required columns: {missing}")


def ingest_nasa(raw_path: Path = RAW_NASA_FILE, output_path: Path = INGESTED_FILE) -> int:
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw NASA file not found: {raw_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with raw_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        _validate_columns(reader.fieldnames)
        rows = list(reader)

    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=REQUIRED_RAW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in REQUIRED_RAW_COLUMNS})

    return len(rows)


def main() -> None:
    row_count = ingest_nasa()
    print(f"Ingested {row_count} NASA rows into {INGESTED_FILE}")


if __name__ == "__main__":
    main()
