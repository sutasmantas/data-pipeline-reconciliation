"""Scheduler-independent SQL extraction built from the inherited dlt demo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dlt
from dlt.common.pipeline import LoadInfo
from dlt.extract.incremental import Incremental
from sqlalchemy import create_engine

from sql_database import sql_database


@dataclass(frozen=True)
class SqlRunConfig:
    """Stable inputs for an incremental SQL-to-warehouse run."""

    source_url: str
    table: str
    cursor_column: str
    initial_value: str
    pipeline_name: str = "pipelineforge_sql"
    dataset_name: str = "client_data"
    destination: str = "duckdb"
    duckdb_path: Path = Path(".pipelineforge/warehouse.duckdb")
    pipelines_dir: Path = Path(".pipelineforge/pipelines")


def _destination(config: SqlRunConfig) -> Any:
    if config.destination == "duckdb":
        config.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        return dlt.destinations.duckdb(str(config.duckdb_path.resolve()))
    if config.destination == "postgres":
        return dlt.destinations.postgres()
    raise ValueError("destination must be 'duckdb' or 'postgres'")


def run_sql_incremental(config: SqlRunConfig) -> tuple[dlt.Pipeline, LoadInfo]:
    """Merge new and changed SQL rows using dlt's durable cursor state."""

    if not config.table.isidentifier() or not config.cursor_column.isidentifier():
        raise ValueError("table and cursor_column must be identifiers")

    engine = create_engine(config.source_url)
    source = sql_database(
        engine,
        table_names=[config.table],
        detect_precision_hints=None,
    )
    resource = source.resources[config.table]
    resource.apply_hints(
        incremental=Incremental(config.cursor_column, initial_value=config.initial_value, lag=60),
        write_disposition="merge",
    )

    pipeline = dlt.pipeline(
        pipeline_name=config.pipeline_name,
        destination=_destination(config),
        dataset_name=config.dataset_name,
        pipelines_dir=str(config.pipelines_dir.resolve()),
    )
    return pipeline, pipeline.run(source)
