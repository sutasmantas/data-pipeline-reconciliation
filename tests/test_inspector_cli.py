from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from pipelineforge.cli import main
from pipelineforge.inspector import create_inspector


def test_cli_migration_and_read_only_inspector(tmp_path: Path, capsys: object) -> None:
    work_dir = tmp_path / "work"
    assert (
        main(
            [
                "migrate-files",
                "--source-dir",
                "fixtures/catalog",
                "--manifest",
                "contracts/catalog_orders.json",
                "--work-dir",
                str(work_dir),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    run_id = json.loads(output)["run_id"]
    client = TestClient(create_inspector(work_dir / "evidence"))

    assert client.get("/health").json() == {"status": "ok"}
    runs = client.get("/api/runs")
    assert runs.status_code == 200
    assert runs.json()[0]["run_id"] == run_id
    selected = client.get(f"/api/runs/{run_id}")
    assert selected.json()["gate"] == "PASS"
    page = client.get(f"/?run={run_id}")
    assert page.status_code == 200
    assert "Source register" in page.text
    assert "Destination register" in page.text
    assert 'data-label="Status"' in page.text
    assert "dark sidebar" not in page.text
    assert client.get("/api/runs/not-safe").status_code == 404
    assert client.get("/?run=../../secrets").status_code == 404


def test_inspector_empty_state(tmp_path: Path) -> None:
    client = TestClient(create_inspector(tmp_path))
    assert client.get("/api/runs").json() == []
    assert "No reconciliation evidence yet" in client.get("/").text
