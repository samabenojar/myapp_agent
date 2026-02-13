# Phase 1 Plan (NASA Minimal Pipeline)

## Required assertions

1. Canonical schema is exactly:
   - `run_id,timestamp,voltage,current,temperature,cycle`
2. Units are preserved and documented:
   - `timestamp` in seconds since run start
   - `voltage` in volts
   - `current` in amps
   - `temperature` in celsius
3. Normalization and derived metric steps are deterministic for identical input.
4. Pipeline fails loudly on schema mismatch or invalid values.
5. Raw data under `data/` is never modified by ingestion/normalization/derivation.
6. `vbat_sag` is documented and non-negative for physically sensible traces.
7. Runbook contains executable commands, expected outputs, and troubleshooting.
