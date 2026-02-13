# Phase 1 Review (Reviewer)

## Findings (ordered by severity)

1. Medium: malformed CSV rows were previously ingested with silent empty-fill behavior, which could mask broken raw rows.
   - Evidence: prior implementation used `row.get(column, "")` in `src/ingest/nasa.py`.
   - Fix applied: ingest now raises on row-level missing values and writes direct indexed fields only (`src/ingest/nasa.py:30`, `src/ingest/nasa.py:35`, `src/ingest/nasa.py:43`).

2. Medium: normalization previously coerced `run_id` with `str(...)`, allowing accidental `"None"`/blank identifiers.
   - Evidence: `run_id=str(row["run_id"])` could silently convert invalid values.
   - Fix applied: explicit required/non-empty `run_id` validation (`src/normalize/nasa_to_canonical.py:24`, `src/normalize/nasa_to_canonical.py:55`).

3. Low: test coverage did not directly assert malformed-row loud failure, deterministic derivation equality, or raw file immutability.
   - Fix applied: added tests for all three (`tests/test_phase1_nasa_pipeline.py:66`, `tests/test_phase1_nasa_pipeline.py:101`, `tests/test_phase1_nasa_pipeline.py:115`).

4. Low: plan and runbook were underspecified for review traceability.
   - Fix applied: documented explicit Phase 1 required assertions (`docs/PLAN.md:1`) and expected command output patterns (`docs/runbook.md:28`).

## Checklist Verdict

1. Schema-only canonical columns: PASS  
   - Canonical columns are explicitly fixed to `run_id,timestamp,voltage,current,temperature,cycle` (`src/schema/canonical.py:8`, `src/normalize/nasa_to_canonical.py:68`).

2. Units: PASS  
   - Mapping is explicit and unit-preserving in runbook (`docs/runbook.md:15`) and labels in plotting (`src/visualize/voltage_time.py:47`).

3. Determinism: PASS  
   - No randomness/stateful behavior in normalization/derivation; deterministic test added (`tests/test_phase1_nasa_pipeline.py:101`).

4. No silent failures/coercion: PASS (after fixes)  
   - No bare `except`/`pass`; malformed rows and empty `run_id` now fail loudly (`src/ingest/nasa.py:35`, `src/normalize/nasa_to_canonical.py:24`).

5. Raw data immutability: PASS  
   - Pipeline reads from `data/` and writes to `canonical/`/`outputs`; immutability test added (`tests/test_phase1_nasa_pipeline.py:115`).

6. `vbat_sag` definition/documentation/sensible values: PASS  
   - Definition is documented in code comment and runbook; by construction uses `first - min` and remains non-negative (`src/derive/vbat_sag.py:54`, `docs/runbook.md:48`).

7. Tests and PLAN alignment: PASS (after fixes)  
   - `docs/PLAN.md` now defines required assertions and tests cover key schema/quality/determinism/error behaviors (`docs/PLAN.md:1`, `tests/test_phase1_nasa_pipeline.py:13`).

8. Runbook completeness: PASS (after fixes)  
   - Includes exact commands, expected output patterns, output files, and troubleshooting (`docs/runbook.md:24`, `docs/runbook.md:37`, `docs/runbook.md:54`).

## Verification notes

- `python -m compileall src tests` passes (syntax-level validation).
- `python -m pytest -q` could not be executed in this environment because `pytest` is not installed.
