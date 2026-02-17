# Pipeline State Machine

## Objective
Define explicit, auditable stage transitions for telemetry processing.

## States
1. `RawIngested`
2. `RawValidated`
3. `Canonicalized`
4. `DerivedComputed`
5. `Visualized`

## Transition Graph
```text
RawIngested
  -> RawValidated
    -> Canonicalized
      -> DerivedComputed
        -> Visualized
```

## Transition Contracts

### 1. `RawIngested -> RawValidated`
- Input event: `RawIngested`
- Guard conditions:
  - source metadata present
  - required raw columns discoverable
- Output event: `RawValidated`
- Failure handling:
  - emit validation failure details in payload (`is_valid=false`)
  - do not progress downstream for invalid runs

### 2. `RawValidated -> Canonicalized`
- Input event: `RawValidated` with `is_valid=true`
- Guard conditions:
  - mapping to canonical fields is fully defined
  - units are known or explicitly normalized deterministically
- Output event: `Canonicalized`
- Invariants:
  - canonical columns are exactly:
    - `run_id,timestamp,voltage,current,temperature,cycle`
  - timestamp is elapsed seconds since run start

### 3. `Canonicalized -> DerivedComputed`
- Input event: `Canonicalized`
- Guard conditions:
  - canonical validation passes
  - required columns for metric computation exist
- Output event: `DerivedComputed`
- Invariants:
  - derived metrics are additive columns only
  - raw canonical fields are never overwritten

### 4. `DerivedComputed -> Visualized`
- Input event: `DerivedComputed`
- Guard conditions:
  - metric output present
  - plotting inputs are finite/valid
- Output event: `Visualized`
- Invariants:
  - voltage-time plot labels include units
  - visualization does not mutate canonical/derived data

## Failure and Retry Model
- Consumers are at-least-once invoked.
- Each consumer enforces idempotency (`processed_events` + deterministic `idempotency_key`).
- Retries on transient failure are safe because output emission is deduplicated.

## Ordering Model
- Ordered processing is required per `stream_id` (`run_id`).
- Cross-stream concurrency is allowed.
- Out-of-order cross-stream events must not violate per-stream invariants.

## Exactly-Once Semantics (Application Layer)
Exactly-once behavior is enforced by transactionally combining:
1. Read input event.
2. Check/insert processed marker.
3. Append output event(s).
4. Commit offset.

If a retry happens after partial work, dedup checks prevent duplicate transitions.

## Observability Requirements
- Every transition records:
  - `event_id`
  - `correlation_id`
  - `causation_id`
  - producer/consumer name
  - processing timestamp
- Enables end-to-end lineage from raw input to final visualization.

