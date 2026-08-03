# Cover-letter claim ledger

## Supported

- Built on an inherited dlt PostgreSQL pipeline and upgraded it to current dlt
  with tested incremental merge behavior.
- Implemented authenticated, cursor-paginated REST ingestion with bounded page
  size, checkpointed increments, rolling late-data restatement, additive schema
  evolution, and DuckDB merge loading.
- Migrated CSV, JSONL, and Parquet records through a mapping contract into
  DuckDB or PostgreSQL, with invalid records quarantined and repeat runs
  idempotent for the fixed cases.
- Added exact row-count, amount, completeness, uniqueness, freshness, and
  quarantine reconciliation with machine-readable JSON and client-readable
  HTML/inspector evidence.
- Added bounded retry, durable dead-letter, replay, duplicate suppression,
  payload-conflict refusal, redacted alert events, and an Airflow 3 DAG entry
  point.
- Packaged the application with a digest-pinned Python image, a digest-pinned
  PostgreSQL integration service, checksum-verified component wheels/fixtures,
  and CI definitions for tests, packaging, Docker, Postgres, and Airflow parse.

## Evidence anchors

- SQL increment/repeat: `tests/test_foundation_sql.py`
- REST initial/incremental/late/schema/rate-limit: `tests/test_rest_pipeline.py`
- migration/quarantine/reconciliation/Postgres: `tests/test_file_pipeline.py`
- dead-letter/replay/refusal: `tests/test_operations.py`
- CLI/inspector and scheduler adapter: `tests/test_inspector_cli.py`,
  `tests/test_scheduler.py`
- committed artifact integrity: `tests/test_supply_chain.py`

## Not supported

Do not claim production scale, benchmarked throughput, change-data capture,
distributed exactly-once delivery, a hosted Airflow deployment, a managed cloud
warehouse, named SaaS connectors, or operation on client data. The committed
fixtures are deterministic synthetic evidence.
