"""Incremental REST-to-warehouse flow using dlt's maintained REST source."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dlt
import requests
from dlt.common.pipeline import LoadInfo
from dlt.sources.rest_api import rest_api_source
from dlt.sources.rest_api.typing import ClientConfig, RESTAPIConfig

from pipelineforge.fake_api import Scenario


@dataclass(frozen=True)
class RestRunConfig:
    """Stable inputs for the reusable REST adaptation."""

    base_url: str
    token: str
    scenario: Scenario = "initial"
    initial_value: str = "1970-01-01T00:00:00Z"
    pipeline_name: str = "pipelineforge_rest"
    dataset_name: str = "client_data"
    duckdb_path: Path = Path(".pipelineforge/warehouse.duckdb")
    pipelines_dir: Path = Path(".pipelineforge/pipelines")
    request_retries: bool = True


def _source(config: RestRunConfig) -> Any:
    if not config.base_url.startswith(("http://127.0.0.1:", "http://localhost:")):
        raise ValueError("the no-key fixture base_url must be loopback HTTP")
    if not config.token:
        raise ValueError("token must not be empty")
    client: ClientConfig = {
        "base_url": config.base_url.rstrip("/") + "/v1/",
        "auth": {"type": "bearer", "token": config.token},
        "paginator": {
            "type": "cursor",
            "cursor_path": "next_cursor",
            "cursor_param": "cursor",
        },
    }
    if not config.request_retries:
        client["session"] = requests.Session()
    source_config: RESTAPIConfig = {
            "client": client,
            "resources": [
                {
                    "name": "orders",
                    "primary_key": "id",
                    "write_disposition": "merge",
                    "endpoint": {
                        "path": "orders",
                        "data_selector": "data",
                        "params": {"scenario": config.scenario, "limit": 2},
                        "incremental": {
                            "cursor_path": "updated_at",
                            "initial_value": config.initial_value,
                            "start_param": "updated_since",
                            "lag": 60,
                        },
                    },
                }
            ],
        }
    return rest_api_source(
        source_config,
        name="pipelineforge_rest_source",
        schema_contract={"tables": "evolve", "columns": "evolve", "data_type": "freeze"},
    )


def run_rest_incremental(config: RestRunConfig) -> tuple[dlt.Pipeline, LoadInfo]:
    """Load one provider state, merging duplicates and late corrections."""

    config.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    pipeline = dlt.pipeline(
        pipeline_name=config.pipeline_name,
        destination=dlt.destinations.duckdb(str(config.duckdb_path.resolve())),
        dataset_name=config.dataset_name,
        pipelines_dir=str(config.pipelines_dir.resolve()),
    )
    return pipeline, pipeline.run(_source(config))
