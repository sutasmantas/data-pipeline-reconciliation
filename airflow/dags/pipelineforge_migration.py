"""Airflow 3 DAG entry point for the PipelineForge file migration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from airflow.sdk import dag, task

from pipelineforge.scheduler import run_scheduled_migration

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dag(
    dag_id="pipelineforge_file_migration",
    description="Load mapped catalog files and require a passing reconciliation gate",
    schedule="0 2 * * *",
    start_date=datetime(2026, 8, 1, tzinfo=UTC),
    catchup=False,
    tags=["pipelineforge", "migration", "reconciliation"],
)
def pipelineforge_file_migration() -> None:
    @task(retries=2, retry_delay=timedelta(minutes=2))
    def migrate_and_reconcile() -> dict[str, object]:
        return run_scheduled_migration(project_root=PROJECT_ROOT)

    migrate_and_reconcile()


pipelineforge_file_migration()
