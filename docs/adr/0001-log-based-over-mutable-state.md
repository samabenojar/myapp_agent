# ADR 0001: Choose Log-Based Event Architecture Over Mutable Pipeline State

- Status: Accepted
- Date: 2026-02-17
- Deciders: PM branch architecture track

## Context
The pipeline currently targets deterministic ingestion, canonicalization, derived metrics, and visualization. We need to evolve toward event-driven processing while preserving current outputs and avoiding broad rewrites.

The main choice is:
1. Keep mutable stage-state tables/files as the primary source of truth.
2. Adopt an immutable event log where state is derived from ordered events.

## Decision
We choose **immutable, log-based architecture** with a versioned event envelope and explicit state transition events:

`RawIngested -> RawValidated -> Canonicalized -> DerivedComputed -> Visualized`

Postgres is used as the event store with append-only semantics.

## Why This Decision
1. **Auditability and scientific traceability**
   Every stage output is preserved as an immutable fact; no hidden overwrites.

2. **Deterministic replay**
   Recompute canonical/derived/visual outputs by replaying events.

3. **Idempotency and recovery**
   Event IDs and idempotency keys provide safe retries and crash recovery.

4. **Minimal-change migration**
   Existing modules can be wrapped as producers/consumers instead of rewritten.

5. **CDC readiness**
   Append-only Postgres event log aligns naturally with logical replication and downstream consumers.

## Consequences

### Positive
- Strong lineage from raw ingestion to plot artifacts.
- Better debugging via correlation/causation metadata.
- Easier future integrations (warehouse, service consumers, streaming bridges).

### Negative
- Additional metadata/schema management.
- Need discipline around event versioning and contract evolution.
- Read models/projections add operational components.

## Alternatives Considered

### Mutable stage tables only
- Pros: simpler initial implementation.
- Cons: weaker traceability, harder replay, harder dedup semantics, less CDC-friendly.

### Full streaming platform now (Kafka-first)
- Pros: native streaming ecosystem.
- Cons: premature infrastructure complexity for current scope; conflicts with minimal-change requirement.

## Implementation Notes (Scope Boundary)
- This ADR defines architecture and contracts only.
- No production logic rewrite is included in this branch.
- Existing outputs remain as required.

