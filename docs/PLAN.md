# Phase 1 Plan - Battery Telemetry (NASA Only)

## 1. Objective
Deliver a minimal, scientifically correct Phase 1 pipeline that ingests one NASA battery dataset, normalizes it to the canonical schema, computes `vbat_sag`, and produces one voltage-vs-time diagnostic plot with basic validation.

## 2. Definition of Done
- [ ] Exactly one NASA dataset is selected, documented, and ingested from raw source files in `/data` (raw untouched).
- [ ] Normalized output is written to `/canonical` with canonical fields only.
- [ ] Canonical schema validation is enforced (Pydantic) and fails loudly on mismatch.
- [ ] `vbat_sag` is computed as a derived column without overwriting raw canonical values.
- [ ] One voltage vs time plot is generated with clearly labeled units.
- [ ] Basic validation checks pass (required columns, no undocumented NaN in voltage/current).
- [ ] Reviewer confirms schema consistency and scientific validity.

## 3. Canonical Schema Definition (Fields + Units)
Canonical table fields (no dataset-specific leakage):
- `run_id` (str): unique run/test identifier.
- `timestamp` (float, seconds): elapsed seconds since run start.
- `voltage` (float, volts, V): measured battery voltage.
- `current` (float, amps, A): measured battery current.
- `temperature` (float | None, degrees C, C): measured temperature if available.
- `cycle` (int | None, unitless): cycle index if available.

Derived metric for Phase 1:
- `vbat_sag` (float, volts, V): voltage drop from pre-load reference to minimum voltage during load segment; definition must be documented in code comments and applied deterministically.

## 4. Step-by-Step Dev Tasks
1. Select and document one NASA dataset for Phase 1 (file names, expected columns, run granularity).
2. Place raw files under `/data` and keep them immutable.
3. Implement ingestion script that reads raw NASA files and emits records without silent coercion.
4. Implement normalization mapping from NASA source columns to canonical schema fields.
5. Ensure `timestamp` is converted to elapsed seconds from run start (deterministic, no timezone ambiguity).
6. Add Pydantic validation for canonical records and fail on schema/type violations.
7. Write canonical output to `/canonical` with only canonical fields.
8. Implement `vbat_sag` in `/src/derive` as an additional derived column.
9. Generate one voltage-vs-time plot as primary diagnostic, with axes labeled in seconds and volts.
10. Add concise documentation of assumptions (missing `temperature`/`cycle`, run boundary logic, sag definition).

## 5. Testing Plan (Commands to Run)
Use project-specific entrypoints as implemented by Dev; minimum command set:
```powershell
# 1) Run ingestion for the selected NASA dataset
python -m src.ingest.nasa

# 2) Run normalization to canonical schema
python -m src.normalize.nasa_to_canonical

# 3) Run derived metric computation (vbat_sag only for Phase 1)
python -m src.derive.vbat_sag

# 4) Run validation tests
pytest -q

# 5) Generate diagnostic voltage-vs-time plot
python -m src.visualize.voltage_time
```
Required test assertions:
- Canonical output contains exactly: `run_id,timestamp,voltage,current,temperature,cycle` (+ `vbat_sag` only in derived output).
- `timestamp` is numeric and non-decreasing within each `run_id`.
- No NaN in `voltage` or `current` unless explicitly documented and approved.
- Raw `/data` files are unchanged after pipeline runs.

## 6. Risks and Edge Cases
- Missing required source columns (cannot map to canonical fields).
- Units mismatch (e.g., milliseconds vs seconds, mV vs V, mA vs A).
- Multiple runs in one file with ambiguous run boundaries.
- Non-monotonic or reset timestamps within a run.
- NaN/invalid numeric values in voltage/current.
- Missing temperature or cycle fields (must map to `None`, not fabricated).
- Sign convention ambiguity for current (charge/discharge) affecting sag segment selection.

## 7. Explicit Out of Scope (Phase 1)
- Any non-NASA datasets (CALCE, Kaggle, etc.).
- Derived metrics other than `vbat_sag` (`t50_recovery`, `t90_recovery`, IR proxy, `soh_est`).
- SoH modeling or any ML prediction workflow.
- Snowflake/database integration.
- API endpoints or services.
- Real-time/streaming ingestion.
- Broad refactors or abstraction frameworks beyond minimal pipeline needs.
