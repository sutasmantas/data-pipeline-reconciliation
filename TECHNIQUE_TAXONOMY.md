# PipelineForge technique taxonomy

Date: 2026-08-05

Status: systematic research dossier; no implementation or experiment is authorized here. Conclusions use `established`, `provisional`, `contested`, or `unknown`.

## Decision boundary

PipelineForge currently demonstrates dlt-based REST, file and SQL ingestion into DuckDB/Postgres with full and watermark-incremental modes, bounded schema contracts, quarantine, aggregate reconciliation, DeliveryGuard lifecycle evidence and optional Airflow. It does not prove log-based CDC, deletion handling, stage-level crash recovery, semantic data quality, complete lineage, distributed scale, streaming latency or a production SLA.

The paid outcome is data that arrives completely, on time, with explainable transformations and recoverable failures. Ingestion, change capture, state/commit semantics, contracts, reconciliation, lineage and orchestration must be evaluated separately.

## Problem decomposition

| Layer | Decision | Serious families | Current boundary |
| --- | --- | --- | --- |
| source/change capture | obtain full and changed data | snapshot; file/API incremental; watermark polling; log CDC; event stream | snapshot + watermark |
| connector substrate | avoid rebuilding source clients/state | dlt; Singer/Meltano; Airbyte; bespoke connector | dlt |
| processing mode | choose latency/state model | bounded batch; micro-batch; stateful streaming | batch/incremental batch |
| commit/recovery | prevent loss/duplication across stages | local state; transactional staging/swap; checkpoint; replay/dedupe; WAP branch | dlt state + bounded lifecycle |
| schema contract | control structural evolution | code schema; ODCS; registry/table-format schema; strict/evolve/quarantine | bounded custom contract |
| semantic quality | test values/relationships/distributions | SQL assertions; Pandera; Soda; Great Expectations; dbt tests | bounded hand checks |
| quarantine | preserve invalid data and reason | fail-fast; row reject; batch hold; audit branch/write-audit-publish | row/batch evidence |
| reconciliation | establish completeness/correctness | counts; aggregates; hashes; key/row diff; business totals; delete/tombstone checks | counts/aggregates |
| lineage | explain source-transform-output | manual manifest; OpenLineage run/job/dataset; column lineage; query extraction | partial local evidence |
| orchestration | schedule/retry/backfill/ownership | cron; Airflow task DAG; Prefect flows; Dagster assets | optional Airflow |
| storage/table semantics | support evolution/time travel/atomic publish | database tables; files; Iceberg/Delta/Hudi | database tables |
| scale engine | execute large/bounded/stateful work | DuckDB/Postgres; Spark; Flink; warehouse-native | DuckDB/Postgres |
| evaluation | measure correctness and operating cost | TPC-DI workload; seeded faults; fault injection; scale/recovery/lineage completeness | focused fixtures only |

## Technique families and operating regions

### Full snapshot and watermark incremental — `established controls`

Full loads are a simple reconciliation/reset control; watermark polling is appropriate when updates are monotonic and deletions are handled explicitly. Late updates, equal timestamps, source clock drift and hard deletes create known gaps. Keep both as baseline rather than assuming CDC is always superior.

### Log-based CDC — `established conditional family`

Debezium captures committed row changes with resume state and broad database-specific connectors. It reduces polling lag and handles deletes, but adds database privileges, connector operations, schema/tombstone semantics and at-least-once duplicates. Adopt when freshness/deletion volume justifies those costs or the platform already exists.

### Connector frameworks — `established reuse family`

dlt is already the best local fit for Python embedding and typed destinations. Airbyte provides a broad managed connector platform; Singer/Meltano provides tap/target composability. A new source should first be audited against these implementations. Custom code is justified only for a small unmatched seam with lower glue/upgrade cost.

### Batch versus stateful streaming — `established operating regions`

Flink checkpoints operator state and replay positions and documents that “exactly once” applies to managed state unless the sink cooperates. Streaming is appropriate for continuous stateful/low-latency workloads; it is not a free upgrade to this bounded batch demo. Micro-batch remains the control.

### Structural contracts and ODCS — `established distinct role`

Structural compatibility, ownership, semantics, quality and service levels can be expressed in the Open Data Contract Standard. The older Data Contract Specification repository is deprecated in favor of ODCS 3.1, which is important negative implementation evidence. A standard contract aids exchange; it does not execute every semantic rule or prove pipeline correctness.

### Semantic data-quality engines — `established family`, `unknown local winner`

Pandera offers code-first dataframe validation/property generation; Soda offers dataset/warehouse contract checks; Great Expectations offers rich expectations/checkpoints/docs. All are maintained and broader than the current checks. Compare only faults the current contract misses, plus integration/runtime/reporting cost. Do not adopt all three.

### Reconciliation — `established invariant`

Counts alone miss compensating errors. Use source/destination keys, nulls, aggregates, checksums and domain totals at each recovery boundary; detect deletions/tombstones explicitly. dbt-audit-helper is a maintained SQL comparison component. `datafold/data-diff` is archived and is negative evidence against new adoption.

### Lineage — `established standard`, `coverage-dependent`

OpenLineage models run/job/dataset and extensible facets, including column lineage and data-quality assertions. Emitting a lineage event is not proof of complete transformation lineage. Measure known-edge and column-expression recall, lifecycle correctness and stale/duplicate events.

### Orchestration — `established alternatives`, `conditional`

Airflow is task/DAG oriented and already optional; Dagster is asset-centric; Prefect is Python-flow/event oriented. These solve scheduling, retries, backfills and operations, not connector correctness, CDC or data contracts. Retain Airflow unless an asset/ownership or dynamic-flow requirement produces a measured advantage.

### Table formats/write-audit-publish — `established specialist`

Iceberg provides atomic snapshot commits, schema/partition evolution, time travel and branches that can support write-audit-publish. It adds catalog/storage/engine complexity and is inappropriate for the current small Postgres/DuckDB boundary unless reproducible rollback, large lake tables or multi-engine access are required.

### Fault evaluation and workload realism — `established need`

TPC-DI is the available industry data-integration workload with historical and incremental loads, multiple formats, transformations, errors and warehouse consistency. It is now listed as obsolete and has no published results, so use a declared subset as a workload—not a leaderboard. Add Toxiproxy/process/database faults and exact stage reconciliation.

## Search protocol

- Search date: 2026-08-05.
- Sources: the 2024 pipeline-tools survey, 2023 pipeline-quality taxonomy, TPC-DI specification/paper, Debezium/Flink/Iceberg/OpenLineage/ODCS official material, maintained GitHub implementations and current defects.
- Included negative evidence: TPC-DI's obsolete/no-results status, at-least-once CDC, incomplete lineage, archived data-diff and deprecated Data Contract Specification.
- Excluded: vendor rankings, popularity-only selection and all license research/ranking.

| Iteration | Query family | New decision-relevant family |
| ---: | --- | --- |
| 0 | pipeline tools/quality surveys | ingestion, processing, orchestration and quality taxonomy |
| 1 | TPC-DI and data-integration benchmarks | representative workload/reconciliation evaluation |
| 2 | dlt, Airbyte, Meltano, orchestration implementations | connector/orchestrator operating regions |
| 3 | CDC and lineage | Debezium CDC and OpenLineage |
| 4 | semantic quality/data contracts | Pandera/Soda/GX and contract standards |
| 5 | 2025-2026 pipeline reliability/lineage | no top-level family; refined lineage completeness |
| 6 | streaming checkpoint and table-state semantics | Flink and Iceberg specialist regions |
| 7 | current quality-engine docs | no top-level family; refined integration boundaries |
| 8 | ODCS and lineage facets | no top-level family; corrected deprecated contract candidate |

Iterations 7 and 8 added no top-level family after streaming/table formats were included. Saturation is `PASS` for the dated scope.

## Primary anchors

- [Survey of Pipeline Tools for Data Engineering](https://arxiv.org/abs/2406.08335)
- [Data Pipeline Quality](https://arxiv.org/abs/2309.07067)
- [TPC-DI 1.1.0](https://www.tpc.org/tpc_documents_current_versions/pdf/tpc-di_v1.1.0.pdf)
- [Debezium delivery semantics](https://debezium.io/documentation/reference/3.5/configuration/eos.html)
- [Flink fault tolerance](https://nightlies.apache.org/flink/flink-docs-stable/docs/learn-flink/fault_tolerance/)
- [OpenLineage](https://openlineage.io/docs/)
- [Open Data Contract Standard](https://github.com/bitol-io/open-data-contract-standard)
- [Apache Iceberg](https://iceberg.apache.org/docs/latest/)

