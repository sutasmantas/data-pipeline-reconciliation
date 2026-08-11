# PipelineForge benchmark design

Date: 2026-08-05

Status: design only. No CDC, quality-engine, lineage, scale or streaming experiment was run.

## Questions closed by external evidence

| Question | Closed decision |
| --- | --- |
| Should every source use CDC? | no; snapshot/watermark remain simpler controls and CDC must earn freshness/deletion value |
| Do row counts prove a correct load? | no; use keys, aggregates, hashes, domain totals and deletion checks |
| Does orchestration make the data correct? | no; schedule/retry/backfill and data contracts/reconciliation are separate |
| Does an emitted lineage event prove complete lineage? | no; compare emitted edges/facets with known transformations |
| Should new pipeline logic be written before GitHub component audit? | no; reuse connector/CDC/quality/lineage components unless glue exceeds the bounded logic |

## Common workload and evidence contract

Adapt a declared TPC-DI 1.1 subset rather than claim a compliant benchmark: customer/account/trade/security-style historical plus incremental data across CSV/XML/SQL shapes, errors and warehouse aggregates. Add small local REST/file/SQL twins for fast CI. Freeze scale factors 1/10/100, source keys, expected transforms/deletes/late updates and a stage graph.

Each run stores source snapshot/offset/watermark, input file/hash, extracted/staged/accepted/quarantined/published counts and key digests, contract/quality results, destination commit/version, reconciliation totals, lineage events, start/end/recovery timestamps and resource use. All timing profiles repeat five times; exact correctness gates apply every time.

## P0 — workload, fault and reconciliation harness (exact first experiment)

Map current dlt runs and the TPC-DI subset to one stage/result contract. Inject a dropped row, duplicate key, compensating aggregate error, late update, hard delete, wrong lineage edge and stranded staging batch; the scorer must catch all seven. Add Toxiproxy plus process/database kills. PASS requires deterministic rebuild, exact mutation sensitivity and unchanged current focused tests.

Budget: local CPU/containers, six hours, no cloud spend.

## P1 — dlt batch/incremental scale and crash matrix

Compare full snapshot and watermark incremental across scale factors and DuckDB/Postgres. Kill before/after extraction, state advance, staging, validation and publish. Test equal timestamps, overlap/lookback, late updates and deletions.

Hard gates: zero unexplained lost/duplicate target keys after replay, exact quarantine accounting, state never advances beyond durable publish, full rebuild matches incremental target, and p95/runtime/memory/storage are reported. Retain the simplest profile meeting the declared refresh SLA.

## P2 — watermark versus Debezium CDC

Run only on the Postgres source. Compare polling/lookback with Debezium for inserts, updates, deletes, transaction bursts, connector restart and schema changes. Measure change-to-visible p95, duplicates, missed changes, source load, recovery time, operational components and tombstone handling.

Promote CDC only if it uniquely meets the freshness/deletion gate and every at-least-once duplicate is reconciled. Existing Debezium/Kafka infrastructure can lower the operational threshold; absent it, the improvement must pay for the new control plane.

## P3 — semantic quality engine admission

Keep current structural contract as control. Seed 30 semantic faults: range/domain, cross-column, uniqueness, referential, freshness, distribution shift and business-total errors. Compare hand SQL/current checks, Pandera and Soda; add Great Expectations only if both leave a declared reporting/oracle gap.

Promotion requires at least 90% seeded semantic-fault recall, zero missed hard business invariants, under 5% false blocks on clean mutations, useful row/batch failure evidence and less than 20% runtime overhead at scale factor 10. A standard ODCS contract is evaluated separately for portability and generated checks, not as a replacement oracle.

## P4 — lineage and orchestration completeness

Emit OpenLineage for the frozen stage graph and compare run/job/dataset/column/quality facets with expected edges across success, retry, quarantine and failure. PASS requires 100% required dataset/run lifecycle edges and at least 95% reviewed column-expression edges, with no stale success after failure.

Retain optional Airflow as scheduler control. Compare Dagster or Prefect only when a real asset-partition/ownership or dynamic-event requirement is declared; the challenger must reduce operator steps or recovery time without changing data correctness.

## Specialist admission

Flink is admitted only for continuous stateful processing whose latency cannot be met by micro-batch. Iceberg is admitted only for large lake tables needing atomic snapshots, multi-engine access, time travel or write-audit-publish. Both reuse the same P0 truth contract and must state end-to-end sink/retention limits.

## Stopping rules

- Stop after P1 if batch/incremental meets the declared SLA and deletion semantics.
- Do not compare every platform; introduce one challenger only for an observed requirement.
- Keep ingestion, transformation, quality, publish and lineage metrics separate.
- Reconcile after every failure, not only at the final successful run.
- Prefer importing a maintained connector/check/emitter over custom logic unless the adapter is demonstrably larger or riskier than the bounded behavior replaced.

