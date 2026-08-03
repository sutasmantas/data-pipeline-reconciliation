from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
import requests
import uvicorn

from pipelineforge import RestRunConfig, run_rest_incremental
from pipelineforge.fake_api import DEMO_TOKEN, create_app


@pytest.fixture
def fixture_api() -> Iterator[str]:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
    server = uvicorn.Server(
        uvicorn.Config(create_app(), host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            if requests.get(f"{base_url}/health", timeout=0.2).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.02)
    else:
        server.should_exit = True
        thread.join(timeout=2)
        pytest.fail("fixture API did not become ready")
    yield base_url
    server.should_exit = True
    thread.join(timeout=5)


def _rows(pipeline: Any, columns: str = "id, amount") -> list[tuple[Any, ...]]:
    with (
        pipeline.sql_client() as client,
        client.execute_query(f"select {columns} from orders order by id") as cursor,
    ):
        return list(cursor.fetchall())


def _config(tmp_path: Path, fixture_api: str, scenario: str) -> RestRunConfig:
    return RestRunConfig(
        base_url=fixture_api,
        token=DEMO_TOKEN,
        scenario=scenario,  # type: ignore[arg-type]
        pipeline_name="rest_contract",
        duckdb_path=tmp_path / "warehouse.duckdb",
        pipelines_dir=tmp_path / "pipelines",
        initial_value="2026-07-01T00:00:00Z",
    )


def test_fixture_api_requires_auth_and_bounds_pagination(fixture_api: str) -> None:
    unauthorized = requests.get(f"{fixture_api}/v1/orders", timeout=2)
    assert unauthorized.status_code == 401
    invalid = requests.get(
        f"{fixture_api}/v1/orders",
        params={"limit": 101},
        headers={"Authorization": f"Bearer {DEMO_TOKEN}"},
        timeout=2,
    )
    assert invalid.status_code == 422


def test_rest_initial_incremental_late_schema_and_repeat(
    tmp_path: Path, fixture_api: str
) -> None:
    initial_pipeline, initial_info = run_rest_incremental(
        _config(tmp_path, fixture_api, "initial")
    )
    assert not initial_info.has_failed_jobs
    assert _rows(initial_pipeline) == [(1, 100), (2, 200), (3, 300)]

    repeat_pipeline, repeat_info = run_rest_incremental(_config(tmp_path, fixture_api, "initial"))
    assert not repeat_info.has_failed_jobs
    assert _rows(repeat_pipeline) == [(1, 100), (2, 200), (3, 300)]

    incremental_pipeline, incremental_info = run_rest_incremental(
        _config(tmp_path, fixture_api, "incremental")
    )
    assert not incremental_info.has_failed_jobs
    assert _rows(incremental_pipeline) == [(1, 100), (2, 200), (3, 300), (4, 400)]

    late_pipeline, late_info = run_rest_incremental(_config(tmp_path, fixture_api, "late"))
    assert not late_info.has_failed_jobs
    assert _rows(late_pipeline) == [(1, 100), (2, 250), (3, 300), (4, 400)]

    schema_pipeline, schema_info = run_rest_incremental(_config(tmp_path, fixture_api, "schema"))
    assert not schema_info.has_failed_jobs
    assert _rows(schema_pipeline, "id, amount, sales_region") == [
        (1, 100, None),
        (2, 250, None),
        (3, 300, None),
        (4, 400, None),
        (5, 500, "EU"),
    ]


def test_rest_transient_rate_limit_is_retried(tmp_path: Path, fixture_api: str) -> None:
    pipeline, info = run_rest_incremental(_config(tmp_path, fixture_api, "failure_once"))
    assert not info.has_failed_jobs
    assert len(_rows(pipeline)) == 5


@pytest.mark.parametrize(
    ("base_url", "token", "message"),
    [
        ("https://example.com", DEMO_TOKEN, "loopback"),
        ("http://127.0.0.1:1", "", "token"),
    ],
)
def test_rest_config_fails_closed(
    tmp_path: Path, base_url: str, token: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        run_rest_incremental(
            RestRunConfig(
                base_url=base_url,
                token=token,
                duckdb_path=tmp_path / "warehouse.duckdb",
                pipelines_dir=tmp_path / "pipelines",
            )
        )
