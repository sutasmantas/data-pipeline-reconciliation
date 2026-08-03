"""Credential-free provider fixture with auth, cursors, drift, and failure modes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any, Literal

from fastapi import FastAPI, Header, HTTPException, Query

DEMO_TOKEN = "pipelineforge-local-token"
Scenario = Literal["initial", "incremental", "late", "schema", "failure_once", "failure"]

_INITIAL: list[dict[str, Any]] = [
    {
        "id": 1,
        "customer": "Northwind",
        "order_date": "2026-07-28",
        "updated_at": "2026-08-01T09:00:00Z",
        "amount": 100,
    },
    {
        "id": 2,
        "customer": "Acme",
        "order_date": "2026-07-29",
        "updated_at": "2026-08-02T09:00:00Z",
        "amount": 200,
    },
    {
        "id": 3,
        "customer": "Globex",
        "order_date": "2026-07-30",
        "updated_at": "2026-08-03T09:00:00Z",
        "amount": 300,
    },
]
_INCREMENTAL = {
    "id": 4,
    "customer": "Initech",
    "order_date": "2026-08-03",
    "updated_at": "2026-08-04T09:00:00Z",
    "amount": 400,
}
_LATE_CORRECTION = {
    "id": 2,
    "customer": "Acme",
    "order_date": "2026-07-29",
    "updated_at": "2026-08-05T09:00:00Z",
    "amount": 250,
}
_SCHEMA_CHANGE = {
    "id": 5,
    "customer": "Umbrella",
    "order_date": "2026-08-05",
    "updated_at": "2026-08-06T09:00:00Z",
    "amount": 500,
    "sales_region": "EU",
}


def fixture_records(scenario: Scenario) -> list[dict[str, Any]]:
    """Return deterministic cumulative provider state for a scenario."""

    rows = [dict(row) for row in _INITIAL]
    if scenario in {"incremental", "late", "schema", "failure_once", "failure"}:
        rows.append(dict(_INCREMENTAL))
    if scenario in {"late", "schema", "failure_once", "failure"}:
        rows = [row for row in rows if row["id"] != 2]
        rows.append(dict(_LATE_CORRECTION))
    if scenario in {"schema", "failure_once", "failure"}:
        rows.append(dict(_SCHEMA_CHANGE))
    return sorted(rows, key=lambda row: (str(row["updated_at"]), int(row["id"])))


def create_app() -> FastAPI:
    """Create an isolated fixture app; state is not shared between tests."""

    app = FastAPI(title="PipelineForge fixture API", version="1.0")
    app.state.forced_outage = False
    failures_seen: dict[str, int] = {}

    @app.get("/health")
    def health() -> Mapping[str, str]:
        return {"status": "ok"}

    @app.get("/v1/orders")
    def orders(
        scenario: Scenario = "initial",
        cursor: Annotated[int, Query(ge=0, le=10_000)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 2,
        updated_since: str = "1970-01-01T00:00:00Z",
        authorization: Annotated[str | None, Header()] = None,
    ) -> Mapping[str, Any]:
        if authorization != f"Bearer {DEMO_TOKEN}":
            raise HTTPException(status_code=401, detail="invalid bearer token")
        if app.state.forced_outage:
            raise HTTPException(status_code=503, detail="forced provider outage")
        if scenario == "failure":
            raise HTTPException(status_code=503, detail="forced provider outage")
        if scenario == "failure_once" and failures_seen.get(scenario, 0) == 0:
            failures_seen[scenario] = 1
            raise HTTPException(
                status_code=429,
                detail="forced transient rate limit",
                headers={"Retry-After": "0"},
            )

        eligible = [
            row for row in fixture_records(scenario) if str(row["updated_at"]) >= updated_since
        ]
        page = eligible[cursor : cursor + limit]
        next_cursor = cursor + limit if cursor + limit < len(eligible) else None
        return {
            "data": page,
            "next_cursor": next_cursor,
            "source_count": len(eligible),
            "source_amount": sum(int(row["amount"]) for row in eligible),
        }

    return app


app = create_app()
