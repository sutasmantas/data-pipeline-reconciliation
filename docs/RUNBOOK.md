# Functional runbook

## Local fixed migration

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install vendor\adapterproof-0.1.0-py3-none-any.whl vendor\deliveryguard-0.1.0-py3-none-any.whl
.\.venv\Scripts\python -m pip install -e ".[test]"
.\.venv\Scripts\pipelineforge migrate-files --work-dir .pipelineforge
.\.venv\Scripts\pipelineforge serve --evidence-dir .pipelineforge\evidence
```

Open `http://127.0.0.1:8080`. A successful fixed run reports 9 observed rows,
7 valid rows, 2 quarantined rows, 5 unique destination rows, and amount 1550.

## PostgreSQL destination

```powershell
docker compose up -d --wait postgres
$env:PIPELINEFORGE_TEST_POSTGRES_URL = "postgresql://pipelineforge:pipelineforge@127.0.0.1:35432/pipelineforge"
.\.venv\Scripts\python -m pytest tests\test_file_pipeline.py -m postgres -q
docker compose down
```

For the CLI, add `--destination postgres --postgres-url $env:PIPELINEFORGE_TEST_POSTGRES_URL`.

## Application image

```powershell
docker build -t pipelineforge:local .
docker volume create pipelineforge-data
docker run --rm -v pipelineforge-data:/data pipelineforge:local migrate-files --work-dir /data
docker run --rm -p 127.0.0.1:8080:8080 -v pipelineforge-data:/data pipelineforge:local
```

## Airflow

Set `AIRFLOW__CORE__DAGS_FOLDER` to `airflow/dags`. Runtime configuration uses
`PIPELINEFORGE_SOURCE_DIR`, `PIPELINEFORGE_MANIFEST`,
`PIPELINEFORGE_DESTINATION`, `PIPELINEFORGE_POSTGRES_URL`, and
`PIPELINEFORGE_WORK_DIR`. The task raises on a failed reconciliation gate.

## Failure handling

- contract-invalid rows go to the `quarantine` table with a digest and reason;
- a reconciliation mismatch sets the report gate to `FAIL`;
- exhausted governed REST runs become DeliveryGuard dead letters;
- replay starts a new delivery cycle after the provider recovers;
- reusing an idempotency key with changed payload is refused.
