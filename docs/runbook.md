# Phase 1 Runbook (NASA Only)

## Python version

- Python 3.10+ required (validated on Python 3.10.1).

## Selected dataset format

- Selected raw file: `data/nasa/nasa_samples.csv`
- Format: CSV
- Expected columns:
  - `run_id`
  - `time_s`
  - `voltage_v`
  - `current_a`
  - `temperature_c`
  - `cycle`
- Unit conversions to canonical:
  - `time_s` -> `timestamp` (seconds since run start, no conversion)
  - `voltage_v` -> `voltage` (volts, no conversion)
  - `current_a` -> `current` (amps, no conversion)
  - `temperature_c` -> `temperature` (celsius, no conversion)
  - `cycle` -> `cycle` (integer, no conversion)

## Commands

- Ingest NASA raw CSV:
  - `python -m src.ingest.nasa`
  - Expected console output pattern: `Ingested <N> NASA rows into canonical/nasa_ingested.csv`
- Normalize to canonical schema:
  - `python -m src.normalize.nasa_to_canonical`
  - Expected console output pattern: `Wrote <N> canonical rows to canonical/samples.csv`
- Derive fallback voltage sag metric:
  - `python -m src.derive.vbat_sag`
  - Expected console output pattern: `Wrote <N> rows with vbat_sag to canonical/samples_with_vbat_sag.csv`
- Plot voltage vs time:
  - `python -m src.visualize.voltage_time`
  - Expected console output pattern: `Wrote plot to outputs/voltage_vs_time.png`

## Expected output files

- `canonical/nasa_ingested.csv`
- `canonical/samples.csv`
- `canonical/samples_with_vbat_sag.csv`
- `outputs/voltage_vs_time.png`

## vbat_sag definition

- Load segments are not inferred for this minimal Phase 1 dataset.
- Deterministic fallback used:
  - For each `run_id`, `vbat_sag = first_voltage_in_run - min_voltage_in_run`.
  - The same per-run `vbat_sag` value is attached to each row in that run.

## Troubleshooting

- Missing columns:
  - Error: `missing required columns`
  - Fix: ensure raw CSV has exactly the required NASA column names listed above.
- Unit issues:
  - If `time_s` is not seconds, convert upstream before normalization.
  - If voltage/current are not in V/A, convert upstream before normalization.
- Schema failures:
  - Pydantic validation is strict and fails on invalid types or NaN values.
