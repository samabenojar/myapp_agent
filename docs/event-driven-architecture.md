# Event-Driven, Log-Based Architecture (Phase 1 Extension)

## Purpose
This document defines an additive architecture extension that keeps current pipeline outputs working while introducing an event-driven, immutable-log model.

The current pipeline stages remain conceptually the same, but each stage becomes an event producer:

1. Raw ingest
2. Raw validation
3. Canonicalization
4. Derived metrics
5. Visualization

## Design Goals
- Keep existing outputs (`/canonical`, plots, derived artifacts) unchanged.
- Avoid full rewrite; use additive adapters and contracts.
- Make all stage transitions explicit and traceable.
- Support idempotent reprocessing and recovery.
- Enable future CDC replication from Postgres with minimal redesign.

## Core Components
1. **Event Envelope (versioned contract)**
   All stage outputs are wrapped in a stable event envelope (`envelope_version` + `event_type` + metadata + payload).

2. **Immutable Event Log (Postgres)**
   Events are append-only in `event_log`. No in-place updates or deletes to prior events.

3. **Stage Consumers/Producers**
   Each stage consumes one event type and emits the next event type:
   - `RawIngested` -> `RawValidated` -> `Canonicalized` -> `DerivedComputed` -> `Visualized`

4. **Materialized Views / Read Models**
   Existing outputs remain as read-model artifacts built from events (files and/or SQL views/tables).

## Postgres Event Store (Proposed)
Recommended minimal tables:

- `event_log`
  - `event_id UUID PRIMARY KEY`
  - `stream_id TEXT NOT NULL` (usually `run_id`)
  - `event_type TEXT NOT NULL`
  - `event_version INT NOT NULL`
  - `envelope_version INT NOT NULL`
  - `producer TEXT NOT NULL`
  - `idempotency_key TEXT NOT NULL`
  - `causation_id UUID NULL`
  - `correlation_id UUID NOT NULL`
  - `occurred_at TIMESTAMPTZ NOT NULL`
  - `payload JSONB NOT NULL`
  - `payload_schema_ref TEXT NOT NULL`
  - `payload_hash TEXT NOT NULL`
  - Unique: (`producer`, `idempotency_key`)
  - Index: (`stream_id`, `occurred_at`)
  - Index: (`event_type`, `occurred_at`)

- `consumer_offsets`
  - `consumer_name TEXT NOT NULL`
  - `partition_key TEXT NOT NULL` (e.g., stream shard or `stream_id`)
  - `last_event_id UUID NOT NULL`
  - `updated_at TIMESTAMPTZ NOT NULL`
  - Primary key: (`consumer_name`, `partition_key`)

- `processed_events`
  - `consumer_name TEXT NOT NULL`
  - `event_id UUID NOT NULL`
  - `processed_at TIMESTAMPTZ NOT NULL`
  - Primary key: (`consumer_name`, `event_id`)

## Application Exactly-Once Semantics
Exactly-once is achieved at the application layer using transactional writes:

1. Read next event from `event_log`.
2. In one DB transaction:
   - Check `processed_events` for (`consumer_name`, `event_id`).
   - If present: no-op and commit.
   - If absent: execute stage logic, append next event(s), insert `processed_events`, update `consumer_offsets`.
3. Commit once.

This prevents duplicate side effects under retries/crashes while preserving immutable history.

## Idempotent Consumer Rules
- Consumer logic must be deterministic for same input event.
- Side effects must be guarded by idempotency records.
- New event emission must include deterministic `idempotency_key`.
- Consumers must tolerate redelivery and out-of-order events across streams.

## CDC-Ready Design (Future Postgres Logical Replication)
Design choices for compatibility:
- Append-only `event_log` table with stable primary key.
- JSONB payload with explicit schema reference and version.
- Metadata columns suitable for downstream routing/filtering.
- No hard dependency on internal file paths in payload contract.

CDC consumers can subscribe to inserts from `event_log` and build downstream projections/services without changing upstream producers.

## Proposed Folder Structure (Additive)
```text
docs/
  event-driven-architecture.md
  event-envelope.md
  state-machine.md
  adr/
    0001-log-based-over-mutable-state.md

src/
  events/
    envelope.py            # Envelope models + validators
    types.py               # Event type constants/enums
    store.py               # Event append/read API (Postgres)
    idempotency.py         # Idempotency key helpers
  consumers/
    raw_validate_consumer.py
    canonicalize_consumer.py
    derive_consumer.py
    visualize_consumer.py
  producers/
    raw_ingest_producer.py
    raw_validate_producer.py
    canonicalize_producer.py
    derive_producer.py
    visualize_producer.py
  projections/
    canonical_projection.py
    derived_projection.py
    visualization_projection.py
```

Note: existing modules under `src/ingest`, `src/schema`, `src/normalize`, and `src/visualize` remain and are adapted incrementally to produce/consume events.

## Incremental Adoption Plan (No Rewrite)
1. Introduce envelope and event store contracts.
2. Wrap existing raw ingest output into `RawIngested` events.
3. Add validation consumer to emit `RawValidated`.
4. Add canonicalization consumer to emit `Canonicalized` and continue writing current canonical outputs.
5. Add derived and visualization consumers to emit terminal events while preserving existing artifacts.

