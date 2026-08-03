from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, text

from pipelineforge import SqlRunConfig, run_sql_incremental


def _rows(pipeline: Any) -> list[tuple[int, int]]:
    with (
        pipeline.sql_client() as client,
        client.execute_query("select id, amount from orders order by id") as cursor,
    ):
        return list(cursor.fetchall())


def test_inherited_sql_pipeline_runs_incrementally_on_current_dlt(tmp_path: Path) -> None:
    source_path = tmp_path / "source.sqlite3"
    engine = create_engine(f"sqlite:///{source_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "create table orders ("
                "id integer primary key, updated_at text not null, amount integer not null)"
            )
        )
        connection.execute(
            text(
                "insert into orders values "
                "(1, '2026-08-01T00:00:00Z', 10), "
                "(2, '2026-08-02T00:00:00Z', 20)"
            )
        )

    config = SqlRunConfig(
        source_url=f"sqlite:///{source_path.as_posix()}",
        table="orders",
        cursor_column="updated_at",
        initial_value="2026-07-01T00:00:00Z",
        pipeline_name="foundation_test",
        duckdb_path=tmp_path / "warehouse.duckdb",
        pipelines_dir=tmp_path / "pipelines",
    )

    first_pipeline, first_info = run_sql_incremental(config)
    assert not first_info.has_failed_jobs
    assert _rows(first_pipeline) == [(1, 10), (2, 20)]

    with engine.begin() as connection:
        connection.execute(
            text("update orders set amount=25, updated_at='2026-08-03T00:00:00Z' where id=2")
        )
        connection.execute(text("insert into orders values (3, '2026-08-03T00:01:00Z', 30)"))

    second_pipeline, second_info = run_sql_incremental(config)
    assert not second_info.has_failed_jobs
    assert _rows(second_pipeline) == [(1, 10), (2, 25), (3, 30)]

    repeated_pipeline, repeated_info = run_sql_incremental(config)
    assert not repeated_info.has_failed_jobs
    assert _rows(repeated_pipeline) == [(1, 10), (2, 25), (3, 30)]


@pytest.mark.parametrize("field", ["bad-table", "bad cursor"])
def test_sql_identifiers_are_rejected(field: str, tmp_path: Path) -> None:
    config = SqlRunConfig(
        source_url="sqlite://",
        table=field,
        cursor_column=field,
        initial_value="1970-01-01T00:00:00Z",
        duckdb_path=tmp_path / "warehouse.duckdb",
        pipelines_dir=tmp_path / "pipelines",
    )
    with pytest.raises(ValueError, match="must be identifiers"):
        run_sql_incremental(config)
