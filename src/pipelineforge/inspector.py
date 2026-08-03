"""Read-only run and reconciliation inspector."""

from __future__ import annotations

import json
import re
from importlib.resources import files
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from jinja2 import Template

RUN_ID = re.compile(r"^[a-f0-9]{16}$")


def _reports(evidence_dir: Path) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for path in evidence_dir.glob("reconciliation-*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and RUN_ID.fullmatch(str(payload.get("run_id", ""))):
            reports.append(payload)
    return sorted(reports, key=lambda item: str(item["run_id"]), reverse=True)


def create_inspector(evidence_dir: Path) -> FastAPI:
    app = FastAPI(title="PipelineForge run inspector", version="1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/runs")
    def list_runs() -> list[dict[str, Any]]:
        return _reports(evidence_dir)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        if not RUN_ID.fullmatch(run_id):
            raise HTTPException(status_code=404, detail="run not found")
        for report in _reports(evidence_dir):
            if report["run_id"] == run_id:
                return report
        raise HTTPException(status_code=404, detail="run not found")

    @app.get("/", response_class=HTMLResponse)
    def index(run: str | None = Query(default=None)) -> HTMLResponse:
        reports = _reports(evidence_dir)
        if run is not None and not RUN_ID.fullmatch(run):
            raise HTTPException(status_code=404, detail="run not found")
        selected = next((item for item in reports if item["run_id"] == run), None)
        if run is not None and selected is None:
            raise HTTPException(status_code=404, detail="run not found")
        selected = selected or (reports[0] if reports else None)
        template_text = (
            files("pipelineforge").joinpath("templates/inspector.html").read_text("utf-8")
        )
        return HTMLResponse(Template(template_text).render(runs=reports, report=selected))

    return app
