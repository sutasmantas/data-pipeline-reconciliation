"""Scheduler adapter kept independent from any orchestration runtime."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from pipelineforge.file_pipeline import FileRunConfig, run_file_migration


def config_from_environment(
    environment: Mapping[str, str] | None = None,
    *,
    project_root: Path | None = None,
) -> FileRunConfig:
    """Build one migration run from explicit environment configuration."""
    values = os.environ if environment is None else environment
    root = (project_root or Path.cwd()).resolve()
    work_dir = Path(values.get("PIPELINEFORGE_WORK_DIR", root / ".pipelineforge"))
    destination = values.get("PIPELINEFORGE_DESTINATION", "duckdb")
    if destination not in {"duckdb", "postgres"}:
        raise ValueError("PIPELINEFORGE_DESTINATION must be 'duckdb' or 'postgres'")
    return FileRunConfig(
        source_dir=Path(values.get("PIPELINEFORGE_SOURCE_DIR", root / "fixtures/catalog")),
        mapping_manifest=Path(
            values.get(
                "PIPELINEFORGE_MANIFEST",
                root / "contracts/catalog_orders.json",
            )
        ),
        destination=destination,  # type: ignore[arg-type]
        postgres_url=values.get("PIPELINEFORGE_POSTGRES_URL"),
        duckdb_path=work_dir / "migration.duckdb",
        pipelines_dir=work_dir / "pipelines",
        evidence_dir=work_dir / "evidence",
    )


def run_scheduled_migration(
    environment: Mapping[str, str] | None = None,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Run the core migration and fail the scheduler task on a bad gate."""
    _, _, report = run_file_migration(
        config_from_environment(environment, project_root=project_root)
    )
    if report.gate != "PASS":
        raise RuntimeError(f"reconciliation gate failed for run {report.run_id}")
    return asdict(report)
