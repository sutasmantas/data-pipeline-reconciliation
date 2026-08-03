# Architecture

PipelineForge keeps data movement, delivery governance, orchestration, and
inspection as separate boundaries.

```text
PostgreSQL / REST / CSV+JSONL+Parquet
                 |
       dlt source + incremental state
                 |
    AdapterProof mapping + dlt contracts
           |                 |
      quarantine       DuckDB/PostgreSQL
                             |
                 SQL reconciliation gate
                             |
                JSON + HTML run evidence
                             |
             read-only FastAPI inspector

Airflow DAG --------> scheduler-neutral migration function
DeliveryGuard ------> retry / dead letter / replay around REST runs
```

The adopted GitHub foundation supplies the SQL extraction shape and retained
history. dlt owns extraction state, normalization, schema evolution, and load
semantics. AdapterProof and DeliveryGuard are consumed as checksummed wheels;
their state machines are not copied. PipelineForge owns only its source
configuration, typed quarantine envelope, fixed cross-destination SQL checks,
report adapter, and read-only inspector.

Airflow is optional and imports the scheduler-neutral function through the
public `airflow.sdk` API. The core does not depend on an Airflow database or
scheduler, which keeps CLI and test execution deterministic.
