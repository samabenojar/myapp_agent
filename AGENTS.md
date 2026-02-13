# AGENTS.md — Battery Telemetry Platform

## 🎯 Mission

Build a reproducible, scientifically grounded battery telemetry pipeline that:

- Ingests open battery datasets (NASA, CALCE, Kaggle)
- Normalizes to a canonical schema
- Computes sag & recovery metrics
- Enables SoH modeling
- Supports reproducible analytics & visualization

The system must prioritize correctness, clarity, and scientific validity over clever abstractions.

---

# 🧠 Global Engineering Principles

1. Reproducibility > speed
2. Explicit schema > implicit inference
3. Deterministic transformations
4. No silent data mutation
5. No magic constants without explanation
6. Code must be readable by another engineer

---

# 📦 Canonical Schema Rules

All datasets must normalize into:

run_id: str  
timestamp: float  
voltage: float  
current: float  
temperature: float | None  
cycle: int | None  

No dataset-specific columns should leak into canonical tables.

Derived metrics must be added as new columns, not overwrite raw values.

---

# 📥 Ingestion Rules

- Raw data must remain untouched in /data
- Normalized data goes to /canonical
- Validate records using Pydantic
- Fail loudly if schema mismatches occur
- No auto-fixing silently

---

# 🔄 Transformation Rules

- All normalization logic must be deterministic
- Units must be documented (seconds, volts, amps, °C)
- Timestamp must represent seconds since run start
- No time zone ambiguity

---

# 🧮 Derived Metrics Rules

All derived metrics must:

- Be implemented in /src/derive
- Be mathematically explained in comments
- Not depend on dataset-specific quirks

Initial derived metrics allowed:

- vbat_sag
- t50_recovery
- t90_recovery
- internal resistance proxy
- soh_est (clearly marked experimental)

---

# 🧪 Testing Requirements

Every ingestion script must:

- Include a small validation test
- Assert required columns exist
- Validate no NaN in voltage/current unless documented

---

# 🧑‍💼 Role Definitions

## PM Agent

Responsibilities:
- Define acceptance criteria
- Define metric definitions
- Prevent scope creep
- Keep focus on minimal viable scientific pipeline

PM does NOT:
- Write implementation code
- Refactor Dev code

---

## Dev Agent

Responsibilities:
- Implement ingestion
- Implement normalization
- Implement derived metrics
- Keep code minimal and explicit
- Add docstrings

Dev must:
- Follow canonical schema strictly
- Avoid premature abstraction
- Avoid adding dependencies unless justified

---

## Reviewer Agent

Responsibilities:
- Validate scientific correctness
- Validate schema consistency
- Check numerical stability
- Ensure no silent data mutation
- Ensure tests exist

Reviewer must:
- Be conservative
- Suggest improvements with reasoning
- Not rewrite entire modules unnecessarily

---

# 📊 Visualization Rules

- Plots must clearly label units
- Voltage vs time must be primary diagnostic plot
- Sag overlays must highlight load segments
- No misleading axis scaling

---

# 🚫 Disallowed Patterns

- Hardcoding dataset-specific hacks
- Silent try/except pass
- Implicit type coercion
- Global mutable state
- Mixing ingestion and derived logic

---

# 📈 Definition of Done (Phase 1)

The project is considered functional when:

1. NASA dataset can be ingested
2. Data is normalized to canonical schema
3. Sag metric is computed
4. A voltage vs time plot renders correctly
5. Reviewer signs off on scientific validity

---

# 📌 Future Expansion (Do Not Implement Yet)

- Snowflake integration
- API endpoints
- Health scoring models
- ML prediction pipelines
- Real-time streaming

Stay focused on dataset normalization first.
