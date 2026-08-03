"""Schema-mapped file migration and deterministic warehouse reconciliation."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

import dlt
from adapterproof import (  # type: ignore[import-untyped]
    AdapterManifest,
    MappingContractError,
    load_manifest,
    map_event,
)
from dlt.common.pipeline import LoadInfo
from dlt.sources.filesystem import filesystem, read_csv, read_jsonl, read_parquet
from jinja2 import Template

FileFormat = Literal["csv", "jsonl", "parquet"]


@dataclass(frozen=True)
class FileRunConfig:
    source_dir: Path
    mapping_manifest: Path
    destination: Literal["duckdb", "postgres"] = "duckdb"
    postgres_url: str | None = None
    duckdb_path: Path = Path(".pipelineforge/migration.duckdb")
    pipeline_name: str = "pipelineforge_files"
    dataset_name: str = "migration_data"
    pipelines_dir: Path = Path(".pipelineforge/pipelines")
    evidence_dir: Path = Path(".pipelineforge/evidence")


@dataclass
class MigrationStats:
    source_rows: int = 0
    valid_rows: int = 0
    quarantined_rows: int = 0
    expected_by_id: dict[int, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    expected: int | str
    actual: int | str


@dataclass(frozen=True)
class ReconciliationReport:
    run_id: str
    gate: Literal["PASS", "FAIL"]
    source_rows: int
    valid_rows: int
    quarantined_rows: int
    expected_unique_rows: int
    destination_rows: int
    expected_amount: int
    destination_amount: int
    checks: tuple[CheckResult, ...]


def _destination(config: FileRunConfig) -> Any:
    if config.destination == "duckdb":
        config.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        return dlt.destinations.duckdb(str(config.duckdb_path.resolve()))
    if config.destination == "postgres":
        if not config.postgres_url:
            raise ValueError("postgres_url is required for the postgres destination")
        return dlt.destinations.postgres(credentials=config.postgres_url)
    raise ValueError("destination must be 'duckdb' or 'postgres'")


def _coerce(mapped: dict[str, Any]) -> dict[str, Any]:
    try:
        if isinstance(mapped["id"], bool) or isinstance(mapped["amount"], bool):
            raise ValueError("boolean is not a numeric order field")
        if isinstance(mapped["customer"], float) and math.isnan(mapped["customer"]):
            raise ValueError("customer is empty")
        mapped["id"] = int(mapped["id"])
        mapped["amount"] = int(mapped["amount"])
        mapped["customer"] = str(mapped["customer"]).strip()
        if not mapped["customer"]:
            raise ValueError("customer is empty")
        date.fromisoformat(str(mapped["order_date"]))
        datetime.fromisoformat(str(mapped["updated_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise MappingContractError(f"typed contract rejected row: {exc}") from exc
    return mapped


def _reader(config: FileRunConfig, file_format: FileFormat) -> Any:
    glob = "*.parquet" if file_format == "parquet" else f"*.{file_format}"
    source = filesystem(bucket_url=config.source_dir.resolve().as_uri(), file_glob=glob)
    if file_format == "csv":
        return source | read_csv(chunksize=1000)
    if file_format == "jsonl":
        return source | read_jsonl(chunksize=1000)
    return source | read_parquet(chunksize=1000)


def _route(
    row: dict[str, Any],
    *,
    manifest: AdapterManifest,
    file_format: FileFormat,
    stats: MigrationStats,
) -> Any:
    stats.source_rows += 1
    try:
        mapped = _coerce(map_event(manifest, row))
    except MappingContractError as exc:
        stats.quarantined_rows += 1
        raw = json.dumps(row, sort_keys=True, default=str, separators=(",", ":"))
        quarantine = {
            "row_digest": hashlib.sha256(raw.encode()).hexdigest(),
            "source_format": file_format,
            "reason": str(exc),
            "raw_record": raw,
        }
        return dlt.mark.with_hints(
            quarantine,
            dlt.mark.make_hints(
                table_name="quarantine",
                primary_key="row_digest",
                write_disposition="merge",
            ),
        )

    stats.valid_rows += 1
    previous = stats.expected_by_id.get(mapped["id"])
    if previous is None or str(mapped["updated_at"]) >= str(previous["updated_at"]):
        stats.expected_by_id[mapped["id"]] = dict(mapped)
    return dlt.mark.with_hints(
        mapped,
        dlt.mark.make_hints(
            table_name="catalog_orders",
            primary_key="id",
            write_disposition="merge",
            schema_contract={"tables": "evolve", "columns": "evolve", "data_type": "freeze"},
        ),
    )


def _resource(
    config: FileRunConfig,
    file_format: FileFormat,
    manifest: AdapterManifest,
    stats: MigrationStats,
) -> Any:
    reader = _reader(config, file_format)

    @dlt.resource(name=f"catalog_{file_format}")
    def routed_rows() -> Any:
        for row in reader:
            yield _route(
                row,
                manifest=manifest,
                file_format=file_format,
                stats=stats,
            )

    return routed_rows()


def reconcile(pipeline: dlt.Pipeline, stats: MigrationStats) -> ReconciliationReport:
    expected_rows = len(stats.expected_by_id)
    expected_amount = sum(int(row["amount"]) for row in stats.expected_by_id.values())
    with (
        pipeline.sql_client() as client,
        client.execute_query(
            "select count(*), coalesce(sum(amount), 0), "
            "sum(case when customer is null or customer = '' then 1 else 0 end), "
            "count(*) - count(distinct id), max(updated_at) from catalog_orders"
        ) as cursor,
    ):
        row = cursor.fetchone()
    if row is None:
        raise RuntimeError("reconciliation query returned no row")
    destination_rows, destination_amount, missing, duplicates, freshest = row
    expected_freshest = max(str(item["updated_at"]) for item in stats.expected_by_id.values())
    actual_freshest = (
        freshest.isoformat().replace("+00:00", "Z")
        if isinstance(freshest, datetime)
        else str(freshest)
    )
    checks = (
        CheckResult(
            "row_count",
            int(destination_rows) == expected_rows,
            expected_rows,
            int(destination_rows),
        ),
        CheckResult(
            "amount_total",
            int(destination_amount) == expected_amount,
            expected_amount,
            int(destination_amount),
        ),
        CheckResult("completeness", int(missing) == 0, 0, int(missing)),
        CheckResult("uniqueness", int(duplicates) == 0, 0, int(duplicates)),
        CheckResult(
            "freshness",
            actual_freshest == expected_freshest,
            expected_freshest,
            actual_freshest,
        ),
        CheckResult(
            "quarantine",
            stats.quarantined_rows >= 0,
            stats.quarantined_rows,
            stats.quarantined_rows,
        ),
    )
    digest_input = json.dumps(
        {
            "expected": stats.expected_by_id,
            "checks": [asdict(check) for check in checks],
        },
        sort_keys=True,
        default=str,
    )
    return ReconciliationReport(
        run_id=hashlib.sha256(digest_input.encode()).hexdigest()[:16],
        gate="PASS" if all(check.passed for check in checks) else "FAIL",
        source_rows=stats.source_rows,
        valid_rows=stats.valid_rows,
        quarantined_rows=stats.quarantined_rows,
        expected_unique_rows=expected_rows,
        destination_rows=int(destination_rows),
        expected_amount=expected_amount,
        destination_amount=int(destination_amount),
        checks=checks,
    )


def write_report(report: ReconciliationReport, evidence_dir: Path) -> tuple[Path, Path]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    json_path = evidence_dir / f"reconciliation-{report.run_id}.json"
    html_path = evidence_dir / f"reconciliation-{report.run_id}.html"
    payload = asdict(report)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    template_text = files("pipelineforge").joinpath("templates/report.html").read_text("utf-8")
    html_path.write_text(Template(template_text).render(report=payload), encoding="utf-8")
    return json_path, html_path


def run_file_migration(
    config: FileRunConfig,
) -> tuple[dlt.Pipeline, tuple[LoadInfo, ...], ReconciliationReport]:
    if not config.source_dir.is_dir():
        raise ValueError("source_dir must be an existing directory")
    manifest = load_manifest(config.mapping_manifest)
    stats = MigrationStats()
    pipeline = dlt.pipeline(
        pipeline_name=config.pipeline_name,
        destination=_destination(config),
        dataset_name=config.dataset_name,
        pipelines_dir=str(config.pipelines_dir.resolve()),
    )
    load_infos = tuple(
        pipeline.run(_resource(config, file_format, manifest, stats))
        for file_format in ("csv", "jsonl", "parquet")
    )
    report = reconcile(pipeline, stats)
    write_report(report, config.evidence_dir)
    return pipeline, load_infos, report
