from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from pipelineforge import FileRunConfig, run_file_migration
from pipelineforge.file_pipeline import MigrationStats, reconcile

FIXTURES = Path("fixtures/catalog").resolve()


def _rows(pipeline: Any, table: str, columns: str) -> list[tuple[Any, ...]]:
    with (
        pipeline.sql_client() as client,
        client.execute_query(f"select {columns} from {table} order by 1") as cursor,
    ):
        return list(cursor.fetchall())


def test_csv_jsonl_parquet_migration_maps_quarantines_and_reconciles(tmp_path: Path) -> None:
    config = FileRunConfig(
        source_dir=FIXTURES,
        mapping_manifest=Path("contracts/catalog_orders.json").resolve(),
        duckdb_path=tmp_path / "migration.duckdb",
        pipelines_dir=tmp_path / "pipelines",
        evidence_dir=tmp_path / "evidence",
        pipeline_name="file_contract",
    )
    pipeline, load_infos, report = run_file_migration(config)

    assert len(load_infos) == 3
    assert all(not info.has_failed_jobs for info in load_infos)
    assert report.gate == "PASS"
    assert report.source_rows == 9
    assert report.valid_rows == 7
    assert report.quarantined_rows == 2
    assert report.expected_unique_rows == report.destination_rows == 5
    assert report.expected_amount == report.destination_amount == 1550
    assert _rows(pipeline, "catalog_orders", "id, amount") == [
        (10, 100),
        (11, 225),
        (12, 325),
        (13, 400),
        (14, 500),
    ]
    quarantine = _rows(pipeline, "quarantine", "row_digest, source_format")
    assert len(quarantine) == 2
    assert {row[1] for row in quarantine} == {"csv", "jsonl"}
    json_report = next((tmp_path / "evidence").glob("*.json"))
    html_report = next((tmp_path / "evidence").glob("*.html"))
    assert json.loads(json_report.read_text(encoding="utf-8"))["gate"] == "PASS"
    assert "Reconciliation dossier" in html_report.read_text(encoding="utf-8")

    repeated_pipeline, _, repeated_report = run_file_migration(config)
    assert repeated_report.gate == "PASS"
    assert _rows(repeated_pipeline, "catalog_orders", "id, amount") == _rows(
        pipeline, "catalog_orders", "id, amount"
    )

    expected = MigrationStats(
        source_rows=9,
        valid_rows=7,
        quarantined_rows=2,
        expected_by_id={
            row_id: {
                "id": row_id,
                "amount": amount,
                "updated_at": updated_at,
            }
            for row_id, amount, updated_at in [
                (10, 100, "2026-08-01T09:00:00Z"),
                (11, 225, "2026-08-02T10:00:00Z"),
                (12, 325, "2026-08-03T11:00:00Z"),
                (13, 400, "2026-08-03T12:00:00Z"),
                (14, 500, "2026-08-03T13:00:00Z"),
            ]
        },
    )
    with pipeline.sql_client() as client:
        client.execute_sql("update catalog_orders set amount = 999 where id = 14")
    mismatch = reconcile(pipeline, expected)
    assert mismatch.gate == "FAIL"
    assert next(check for check in mismatch.checks if check.name == "amount_total").passed is False


def test_postgres_requires_credentials(tmp_path: Path) -> None:
    config = FileRunConfig(
        source_dir=FIXTURES,
        mapping_manifest=Path("contracts/catalog_orders.json").resolve(),
        destination="postgres",
        postgres_url=None,
    )
    try:
        run_file_migration(config)
    except ValueError as exc:
        assert str(exc) == "postgres_url is required for the postgres destination"
    else:
        raise AssertionError("missing Postgres credentials were accepted")


def test_missing_source_directory_is_rejected(tmp_path: Path) -> None:
    config = FileRunConfig(
        source_dir=tmp_path / "missing",
        mapping_manifest=Path("contracts/catalog_orders.json").resolve(),
    )
    try:
        run_file_migration(config)
    except ValueError as exc:
        assert str(exc) == "source_dir must be an existing directory"
    else:
        raise AssertionError("missing source directory was accepted")


@pytest.mark.postgres
def test_file_migration_runs_against_postgres(tmp_path: Path) -> None:
    postgres_url = os.getenv("PIPELINEFORGE_TEST_POSTGRES_URL")
    if not postgres_url:
        pytest.skip("PIPELINEFORGE_TEST_POSTGRES_URL is not configured")
    _, load_infos, report = run_file_migration(
        FileRunConfig(
            source_dir=FIXTURES,
            mapping_manifest=Path("contracts/catalog_orders.json").resolve(),
            destination="postgres",
            postgres_url=postgres_url,
            pipelines_dir=tmp_path / "postgres-pipelines",
            evidence_dir=tmp_path / "postgres-evidence",
            pipeline_name="file_postgres_contract",
            dataset_name="pipelineforge_test",
        )
    )
    assert all(not info.has_failed_jobs for info in load_infos)
    assert report.gate == "PASS"
    assert report.destination_rows == 5
