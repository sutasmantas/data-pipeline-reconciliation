# PipelineForge GitHub implementation audit

Date: 2026-08-05

Purpose: reuse maintained connector, CDC, quality, lineage and orchestration components before writing consequential pipeline logic. Licenses are intentionally ignored; runtime fit, maintenance, limitations and glue/upgrade cost decide adoption.

## Current seams

- `rest_pipeline.py`, `file_pipeline.py` and `sql_pipeline.py` own source profiles through dlt.
- `operations.py` owns bounded contract/quarantine/reconciliation evidence.
- `scheduler.py` owns optional Airflow exposure.

Keep these seams. New components must emit the same stage/run/contract/reconciliation evidence rather than replace the project with a platform showcase.

## Repository comparison

| Repository and inspected pin | Health | Reusable component | Important boundary | Decision |
| --- | --- | --- | --- | --- |
| [dlt-hub/dlt](https://github.com/dlt-hub/dlt) `227413b` | active 2026-08-04; 436 open issues | existing embedded sources/state/schema/destinations | local source/state semantics still require crash/delete tests | retain baseline and inspect a source before custom connector logic |
| [airbytehq/airbyte](https://github.com/airbytehq/airbyte) `bed1670` | active 2026-08-05; 2245 issues | broad connector platform | large control plane and variable connector-specific behavior | conditional existing-platform/source fit, never co-install by default |
| [meltano/meltano](https://github.com/meltano/meltano) `3b58441` | active 2026-08-04; 148 issues | Singer tap/target project integration | plugin health and state conventions differ | component audit option for missing dlt sources |
| [debezium/debezium](https://github.com/debezium/debezium) `1397c91` | active 2026-08-04; 118 issues | database CDC/resume/tombstones | at-least-once duplicates and connector operations | P2 candidate, not custom binlog/WAL reader |
| [OpenLineage/OpenLineage](https://github.com/OpenLineage/OpenLineage) `4d61610` | active 2026-08-04; 354 issues | standard run/job/dataset/facets | emission is not completeness; backend/namespace governance remain | P4 thin emitter/completeness experiment |
| [unionai-oss/pandera](https://github.com/unionai-oss/pandera) `106a663` | active 2026-08-04; 447 issues | dataframe schema/value checks and property generation | backend/import/static-typing differences documented | P3 first Python-local semantic quality candidate |
| [sodadata/soda-core](https://github.com/sodadata/soda-core) `b2e571e` | active 2026-08-04; 202 issues | SQL/data-source quality and contract checks | broader connector/runtime; contract surfaces evolve | compare if warehouse-native checks dominate |
| [fivetran/great_expectations](https://github.com/fivetran/great_expectations) `1c34439` | active 2026-08-04; 38 issues | expectations/checkpoints/results/docs | heavier project context and ownership transition | defer until Pandera/Soda leave a declared gap |
| [bitol-io/open-data-contract-standard](https://github.com/bitol-io/open-data-contract-standard) `f5bfbb8` + [datacontract CLI](https://github.com/datacontract/datacontract-cli) `9876b7d` | active 2026-08-05/04 | current standard plus lint/test/import/export | organization/exchange layer does not replace runtime controls | preferred future contract standard |
| [datacontract/datacontract-specification](https://github.com/datacontract/datacontract-specification) | officially deprecated for ODCS; support to end 2026 | migration reference | near-term migration and duplicate standard | reject new adoption |
| [apache/airflow](https://github.com/apache/airflow) `9a85faa` | active 2026-08-05; 1855 issues | existing optional DAG/schedule/backfill | orchestration does not prove data quality/CDC | retain optional control |
| [dagster-io/dagster](https://github.com/dagster-io/dagster) `8e7f0b7` | active 2026-08-04; 2613 issues | asset/partition/check orchestration | platform migration cost | conditional asset-governance profile only |
| [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect) `f3e3cd5` | active 2026-08-04; 827 issues | Python flows/events/retries | new control plane; not a data correctness component | conditional dynamic-flow profile only |
| [dbt-labs/dbt-audit-helper](https://github.com/dbt-labs/dbt-audit-helper) `71817f0` | active 2026-05-19; 11 issues | relation/query comparison macros | dbt/SQL only | reuse in client dbt region |
| [datafold/data-diff](https://github.com/datafold/data-diff) `1410c6c` | archived; last push 2024-05 | historical diff algorithms | abandoned dependency | reject; use maintained SQL/domain comparison |
| [apache/flink](https://github.com/apache/flink) `3c8740f` | active 2026-08-04; 373 issues | stateful stream/checkpoint runtime | end-to-end exactly-once requires cooperative sink; large runtime | specialist streaming profile only |
| [apache/iceberg](https://github.com/apache/iceberg) `7377afa` | active 2026-08-04; 857 issues | atomic snapshots, evolution, branches/WAP | catalog/storage/engine and maintenance cost | specialist lakehouse profile only |
| [Shopify/toxiproxy](https://github.com/Shopify/toxiproxy) `94d6d4b` | active 2026-08-04; 104 issues | network fault injection | not a process/database/semantic fault tool | reuse in P0/P1/P2 harness |

## Reuse map before custom logic

| Need | First reuse source | Thin PipelineForge ownership |
| --- | --- | --- |
| new connector | dlt source, then Airbyte/Singer audit | source-specific normalization and acceptance fixtures |
| database CDC | Debezium | target merge/dedupe/tombstone and reconciliation adapter |
| semantic dataframe checks | Pandera | domain schemas and quarantine/evidence mapping |
| warehouse checks | Soda or existing dbt tests | result normalization and release policy |
| data contract exchange | ODCS + Data Contract CLI | project mapping and client-specific SLA/ownership |
| lineage | OpenLineage | exact run/dataset/column mapping and completeness scorer |
| SQL reconciliation | dbt-audit-helper when dbt exists | business totals and non-SQL stages |
| network faults | Toxiproxy | stage kill/restart and truth reconciliation |

## Explicit non-adoptions

- Do not write a WAL/binlog reader, connector platform, checkpoint engine, quality framework or lineage standard from scratch.
- Do not add Airbyte/Meltano beside dlt without a source the existing substrate cannot reasonably support.
- Do not add Pandera, Soda and Great Expectations together; one measured operating region selects a component.
- Do not adopt the deprecated Data Contract Specification or archived data-diff.
- Do not call Flink operator-state exactly-once an end-to-end sink guarantee.
- Do not add Dagster/Prefect merely to make the orchestration list longer.

## Minimal integration checks

1. Preserve current REST/file/SQL full/incremental and no-key regression results.
2. Crash before/after source read, staging write, contract validation and publish; reconcile source, staged, accepted, quarantined and target rows.
3. Test equal/late watermarks, updates, deletes/tombstones, schema add/drop/type change and replay.
4. Compare structural and semantic faults separately; report quarantined reasons and false blocks.
5. Validate every emitted lineage edge/facet against a frozen expected graph.
6. Keep every CDC/quality/lineage/orchestrator profile removable while the dlt control remains runnable.

