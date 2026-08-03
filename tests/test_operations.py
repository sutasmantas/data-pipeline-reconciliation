from __future__ import annotations

import json
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
from deliveryguard import ActionState, Classification, RetryPolicy

from pipelineforge import GovernedRestRunner, RestRunConfig
from pipelineforge.fake_api import DEMO_TOKEN, create_app


@pytest.fixture
def controlled_api() -> Iterator[tuple[str, Any]]:
    app = create_app()
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
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
        pytest.fail("controlled API did not become ready")
    yield base_url, app
    server.should_exit = True
    thread.join(timeout=5)


def _runner(tmp_path: Path, base_url: str) -> GovernedRestRunner:
    return GovernedRestRunner(
        RestRunConfig(
            base_url=base_url,
            token=DEMO_TOKEN,
            scenario="schema",
            pipeline_name="governed_rest",
            duckdb_path=tmp_path / "warehouse.duckdb",
            pipelines_dir=tmp_path / "pipelines",
            request_retries=False,
        ),
        database_path=tmp_path / "delivery.sqlite3",
        event_log_path=tmp_path / "events.jsonl",
        policy=RetryPolicy(max_attempts=2),
    )


def test_provider_outage_dead_letters_then_replays_once(
    tmp_path: Path, controlled_api: tuple[str, Any]
) -> None:
    base_url, app = controlled_api
    runner = _runner(tmp_path, base_url)
    app.state.forced_outage = True

    failed = runner.deliver("schema", correlation_id="run-outage")
    assert failed.state is ActionState.DEAD_LETTER
    assert failed.attempt_count == 2
    assert failed.last_classification is Classification.SERVER_ERROR
    failed_evidence = runner.evidence(failed.id)
    assert len(failed_evidence["attempts"]) == 2
    assert {attempt["cycle"] for attempt in failed_evidence["attempts"]} == {1}

    app.state.forced_outage = False
    replayed = runner.replay(failed.id, "schema", correlation_id="run-replay")
    assert replayed.state is ActionState.DELIVERED
    assert replayed.cycle == 2
    replay_evidence = runner.evidence(replayed.id)
    assert len(replay_evidence["attempts"]) == 3
    assert [attempt["cycle"] for attempt in replay_evidence["attempts"]] == [1, 1, 2]

    app.state.forced_outage = True
    duplicate = runner.deliver("schema")
    assert duplicate.id == replayed.id
    assert len(runner.evidence(replayed.id)["attempts"]) == 3

    events = [
        json.loads(line)
        for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["event"] for event in events] == [
        "pipeline.dead_letter",
        "pipeline.run",
        "pipeline.run",
    ]
    assert DEMO_TOKEN not in (tmp_path / "events.jsonl").read_text(encoding="utf-8")


def test_idempotency_key_refuses_changed_pipeline_payload(
    tmp_path: Path, controlled_api: tuple[str, Any]
) -> None:
    base_url, _ = controlled_api
    runner = _runner(tmp_path, base_url)
    first = runner.deliver("initial", idempotency_key="fixed-pipeline-key")
    assert first.state is ActionState.DELIVERED
    with pytest.raises(ValueError, match="different destination or payload"):
        runner.deliver("incremental", idempotency_key="fixed-pipeline-key")
