"""Durable run, retry, dead-letter, replay, and alert evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from deliveryguard import (
    ActionRecord,
    ActionState,
    Classification,
    DeliveryExecutor,
    DeliveryFailure,
    DeliveryResult,
    DeliveryStore,
    RetryPolicy,
    make_idempotency_key,
)

from pipelineforge.fake_api import Scenario
from pipelineforge.rest_pipeline import RestRunConfig, run_rest_incremental


class RestRunAdapter:
    """DeliveryGuard adapter that treats a full dlt run as a durable action."""

    def __init__(self, base_config: RestRunConfig) -> None:
        self.base_config = base_config

    def send(
        self,
        payload: Mapping[str, Any],
        *,
        idempotency_key: str,
        correlation_id: str,
    ) -> DeliveryResult:
        del idempotency_key, correlation_id
        scenario = str(payload.get("scenario", ""))
        if scenario not in {
            "initial",
            "incremental",
            "late",
            "schema",
            "failure_once",
            "failure",
        }:
            raise DeliveryFailure(
                Classification.CLIENT_ERROR,
                "scenario is not supported",
                retryable=False,
            )
        try:
            pipeline, info = run_rest_incremental(
                replace(self.base_config, scenario=scenario)  # type: ignore[arg-type]
            )
            with (
                pipeline.sql_client() as client,
                client.execute_query("select count(*) from orders") as cursor,
            ):
                row = cursor.fetchone()
        except Exception as exc:
            raise DeliveryFailure(
                Classification.SERVER_ERROR,
                "pipeline provider failed",
                retryable=True,
                evidence={"error_type": type(exc).__name__},
            ) from None
        return DeliveryResult(
            Classification.SUCCESS,
            response={
                "load_packages": len(info.loads_ids),
                "destination_rows": int(row[0]) if row else 0,
            },
        )


class GovernedRestRunner:
    """Public run boundary backed by DeliveryGuard receipts."""

    def __init__(
        self,
        config: RestRunConfig,
        *,
        database_path: Path,
        event_log_path: Path,
        policy: RetryPolicy | None = None,
    ) -> None:
        self.store = DeliveryStore(database_path)
        self.event_log_path = event_log_path
        self.executor = DeliveryExecutor(
            self.store,
            RestRunAdapter(config),
            policy=policy or RetryPolicy(max_attempts=3),
        )

    def _record(self, action: ActionRecord) -> None:
        self.event_log_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "event": (
                "pipeline.dead_letter"
                if action.state is ActionState.DEAD_LETTER
                else "pipeline.run"
            ),
            "action_id": action.id,
            "state": action.state.value,
            "cycle": action.cycle,
            "attempt_count": action.attempt_count,
            "classification": (
                action.last_classification.value if action.last_classification else None
            ),
            "correlation_id": action.correlation_id,
        }
        with self.event_log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")

    def deliver(
        self,
        scenario: Scenario,
        *,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> ActionRecord:
        payload = {"scenario": scenario}
        action = self.executor.deliver(
            idempotency_key=idempotency_key
            or make_idempotency_key("pipelineforge-rest", payload),
            destination="rest-to-warehouse",
            payload=payload,
            correlation_id=correlation_id,
        )
        self._record(action)
        return action

    def replay(
        self,
        action_id: str,
        scenario: Scenario,
        *,
        correlation_id: str | None = None,
    ) -> ActionRecord:
        action = self.executor.replay(
            action_id,
            payload={"scenario": scenario},
            correlation_id=correlation_id,
        )
        self._record(action)
        return action

    def evidence(self, action_id: str) -> dict[str, Any]:
        return {
            "action": asdict(self.store.get(action_id)),
            "attempts": [asdict(attempt) for attempt in self.store.attempts(action_id)],
        }
