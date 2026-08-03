"""Small scheduler-independent command surface."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

import uvicorn

from pipelineforge.file_pipeline import FileRunConfig, run_file_migration
from pipelineforge.inspector import create_inspector


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="pipelineforge")
    commands = root.add_subparsers(dest="command", required=True)
    migrate = commands.add_parser("migrate-files")
    migrate.add_argument("--source-dir", type=Path, default=Path("fixtures/catalog"))
    migrate.add_argument(
        "--manifest", type=Path, default=Path("contracts/catalog_orders.json")
    )
    migrate.add_argument("--destination", choices=("duckdb", "postgres"), default="duckdb")
    migrate.add_argument("--postgres-url")
    migrate.add_argument("--work-dir", type=Path, default=Path(".pipelineforge"))
    serve = commands.add_parser("serve")
    serve.add_argument("--evidence-dir", type=Path, default=Path(".pipelineforge/evidence"))
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "migrate-files":
        work_dir: Path = args.work_dir
        _, _, report = run_file_migration(
            FileRunConfig(
                source_dir=args.source_dir,
                mapping_manifest=args.manifest,
                destination=args.destination,
                postgres_url=args.postgres_url,
                duckdb_path=work_dir / "migration.duckdb",
                pipelines_dir=work_dir / "pipelines",
                evidence_dir=work_dir / "evidence",
            )
        )
        print(json.dumps(asdict(report), sort_keys=True))
        return 0 if report.gate == "PASS" else 2
    uvicorn.run(
        create_inspector(args.evidence_dir),
        host=args.host,
        port=args.port,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
