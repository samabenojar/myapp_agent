# Event Envelope Contract

## Objective
Define a versioned event contract used by every producer/consumer stage.

## Envelope (v1)
```json
{
  "envelope_version": 1,
  "event_id": "uuid",
  "event_type": "RawIngested",
  "event_version": 1,
  "stream_id": "run_id-or-dataset-scope",
  "correlation_id": "uuid",
  "causation_id": "uuid-or-null",
  "producer": "src.ingest.nasa",
  "idempotency_key": "deterministic-string",
  "occurred_at": "2026-02-17T00:00:00Z",
  "payload_schema_ref": "schema://raw_ingested/v1",
  "payload_hash": "sha256-hex",
  "payload": {}
}
```

## Field Semantics
- `envelope_version`: version of envelope structure itself.
- `event_id`: unique immutable event identifier (UUID).
- `event_type`: domain state transition event name.
- `event_version`: payload contract version for this event type.
- `stream_id`: aggregation key, usually `run_id`.
- `correlation_id`: ties all events of one pipeline run/request.
- `causation_id`: parent event that caused this event.
- `producer`: fully qualified module or service name.
- `idempotency_key`: deterministic key used for deduplication.
- `occurred_at`: UTC timestamp when event was created.
- `payload_schema_ref`: canonical schema reference URI/string.
- `payload_hash`: content hash for tamper detection.
- `payload`: event body.

## Event Types (Initial)
1. `RawIngested`
2. `RawValidated`
3. `Canonicalized`
4. `DerivedComputed`
5. `Visualized`

## Payload Contracts (v1)

### `RawIngested`
```json
{
  "dataset": "NASA",
  "source_uri": "data/raw/path-or-uri",
  "run_id": "string",
  "raw_record_count": 0,
  "units": {
    "time": "seconds|milliseconds|unknown",
    "voltage": "V|mV|unknown",
    "current": "A|mA|unknown",
    "temperature": "C|unknown"
  }
}
```

### `RawValidated`
```json
{
  "run_id": "string",
  "is_valid": true,
  "checks": [
    {
      "name": "required_columns_present",
      "passed": true,
      "detail": "all required columns present"
    }
  ],
  "validated_record_count": 0
}
```

### `Canonicalized`
```json
{
  "run_id": "string",
  "canonical_schema_version": 1,
  "record_count": 0,
  "columns": [
    "run_id",
    "timestamp",
    "voltage",
    "current",
    "temperature",
    "cycle"
  ]
}
```

### `DerivedComputed`
```json
{
  "run_id": "string",
  "metric_set_version": 1,
  "metrics": [
    "vbat_sag"
  ],
  "record_count": 0
}
```

### `Visualized`
```json
{
  "run_id": "string",
  "plot_type": "voltage_vs_time",
  "artifact_uri": "path-or-uri",
  "units": {
    "x": "seconds",
    "y": "volts"
  }
}
```

## Versioning Rules
- `envelope_version` changes only when envelope shape/semantics change.
- `event_version` changes when payload schema for a specific `event_type` changes.
- Backward compatibility policy:
  - Additive fields: minor upgrade, old consumers ignore unknown fields.
  - Breaking changes: increment `event_version` and run parallel consumers or translators.

## Idempotency Rules
- `idempotency_key` must be deterministic from source input + event type + version.
- Recommended key material:
  - `event_type`
  - `stream_id`
  - source checksum or upstream `event_id`
  - `event_version`

## Validation Rules
- Reject events missing required envelope fields.
- Reject invalid UUID/timestamp formats.
- Reject events where `payload_hash` does not match `payload`.
- Reject unknown `event_type` unless feature-flagged.

