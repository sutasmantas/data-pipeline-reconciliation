from __future__ import annotations

from pathlib import Path

import pytest

from pipelineforge.scheduler import config_from_environment, run_scheduled_migration


def test_scheduler_adapter_uses_environment_and_returns_pass(tmp_path: Path) -> None:
    environment = {
        "PIPELINEFORGE_SOURCE_DIR": str(Path("fixtures/catalog").resolve()),
        "PIPELINEFORGE_MANIFEST": str(Path("contracts/catalog_orders.json").resolve()),
        "PIPELINEFORGE_WORK_DIR": str(tmp_path / "work"),
    }

    config = config_from_environment(environment)
    result = run_scheduled_migration(environment)

    assert config.duckdb_path == tmp_path / "work" / "migration.duckdb"
    assert result["gate"] == "PASS"
    assert result["destination_rows"] == 5


def test_scheduler_adapter_rejects_unknown_destination() -> None:
    with pytest.raises(
        ValueError,
        match="PIPELINEFORGE_DESTINATION must be 'duckdb' or 'postgres'",
    ):
        config_from_environment({"PIPELINEFORGE_DESTINATION": "bigquery"})
