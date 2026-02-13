from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ValidationError

from src.normalize.nasa_to_canonical import CANONICAL_FILE
from src.schema.canonical import CANONICAL_COLUMNS, CanonicalSample

DERIVED_FILE = Path("canonical/samples_with_vbat_sag.csv")


def derive_vbat_sag(
    canonical_path: Path = CANONICAL_FILE, output_path: Path = DERIVED_FILE
) -> int:
    if not canonical_path.exists():
        raise FileNotFoundError(f"Canonical file not found: {canonical_path}")

    with canonical_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if reader.fieldnames is None:
            raise ValueError("Canonical file is missing a header row")
        if reader.fieldnames != CANONICAL_COLUMNS:
            raise ValueError(
                f"Canonical file columns must exactly match {CANONICAL_COLUMNS}, "
                f"got {reader.fieldnames}"
            )

        rows: list[CanonicalSample] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                sample = CanonicalSample(
                    run_id=str(row["run_id"]),
                    timestamp=float(row["timestamp"]),
                    voltage=float(row["voltage"]),
                    current=float(row["current"]),
                    temperature=(
                        None if row["temperature"].strip() == "" else float(row["temperature"])
                    ),
                    cycle=None if row["cycle"].strip() == "" else int(row["cycle"]),
                )
            except (ValueError, ValidationError) as exc:
                raise ValueError(f"Invalid canonical row {row_number}: {exc}") from exc
            rows.append(sample)

    by_run: dict[str, list[CanonicalSample]] = {}
    for sample in rows:
        by_run.setdefault(sample.run_id, []).append(sample)

    run_sag: dict[str, float] = {}
    for run_id, run_samples in by_run.items():
        if not run_samples:
            raise ValueError(f"Run {run_id} has no samples")

        # Fallback deterministic sag definition for datasets where load segments
        # are not reliably inferable: first voltage in run minus minimum run voltage.
        reference_voltage = run_samples[0].voltage
        minimum_voltage = min(sample.voltage for sample in run_samples)
        sag = reference_voltage - minimum_voltage
        run_sag[run_id] = sag

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_columns = [*CANONICAL_COLUMNS, "vbat_sag"]
    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_columns)
        writer.writeheader()
        for sample in rows:
            row = sample.model_dump()
            row["vbat_sag"] = run_sag[sample.run_id]
            writer.writerow(row)

    return len(rows)


def main() -> None:
    row_count = derive_vbat_sag()
    print(f"Wrote {row_count} rows with vbat_sag to {DERIVED_FILE}")


if __name__ == "__main__":
    main()
