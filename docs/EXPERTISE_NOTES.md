# PipelineForge expertise notes

**Verification:** [claim-to-artifact map and rerun commands](https://sutasmantas.github.io/evidence/#pipelineforge) · [machine-readable receipt](https://sutasmantas.github.io/evidence/receipt.json)

Date: 2026-08-05

No P-series experiment ran in this dossier slice. The notes distinguish externally closed architecture decisions from project-local results that remain open.

## Reconcile source and destination after every recovery boundary

- **Trigger:** a batch/incremental/CDC pipeline can fail after reading, advancing state, staging, validation or publishing.
- **Failure:** a successful retry can hide rows lost before a state advance, duplicates after replay, compensating aggregate errors or a stranded staging batch.
- **Decision:** record source position and stage counts/key digests, then reconcile source, staged, accepted, quarantined and published truth after every injected failure. Counts are only one layer; include keys, aggregates, hashes, business totals and deletions.
- **Control:** P0/P1 seed seven mutations and crash at every stage boundary; state may never advance beyond durable publish.
- **Boundary:** P0/P1 have not run and current reconciliation is bounded.
- **Evidence:** `TECHNIQUE_TAXONOMY.md` and P0/P1 in `BENCHMARK_DESIGN.md`.
- **Proposal-safe insight:** I treat recovery as a data-correctness test, not simply “the job eventually turned green.”
- **Central index disposition:** add card **Reconcile source and destination after every recovery**.

## Choose CDC only when freshness or deletion handling pays for it

- **Trigger:** polling misses deletes/late updates or cannot meet a change-latency requirement.
- **Failure:** adopting CDC by default adds privileges, connector infrastructure, schema/tombstone behavior and at-least-once duplicates without necessarily improving the paid outcome.
- **Decision:** retain snapshot/watermark as control; compare Debezium on the same insert/update/delete/restart workload and promote it only for a required freshness/deletion win with complete reconciliation.
- **Control:** P2 measures change-to-visible p95, missed/duplicate changes, source load, recovery and operational components.
- **Boundary:** no PipelineForge CDC result exists.
- **Evidence:** Debezium official semantics, `GITHUB_IMPLEMENTATION_AUDIT.md`, and P2.
- **Proposal-safe insight:** CDC is an operating-region choice, not a badge; it earns its control plane by fixing a measured latency or deletion gap.
- **Central index disposition:** add card **Choose CDC only when freshness or deletion needs justify it**.

## Separate structural contracts from semantic data quality

- **Trigger:** a table has the right columns/types but values or relationships can still be wrong.
- **Failure:** schema checks miss range, uniqueness, referential, cross-column, freshness, distribution and business-total errors; adding three quality frameworks creates overlapping glue.
- **Decision:** keep structural admission separate, seed semantic faults, and compare the current checks with Pandera first and Soda for warehouse-native cases. Add no second broad framework unless it catches a declared gap.
- **Control:** P3 uses fault recall, false blocks, evidence usefulness and runtime overhead.
- **Boundary:** P3 has not run; no quality-engine winner is claimed.
- **Evidence:** P3 in `BENCHMARK_DESIGN.md` and the pinned component audit.
- **Proposal-safe insight:** I use contracts to control shape/evolution and a measured semantic engine for business-data failures; neither substitutes for reconciliation.
- **Central index disposition:** add distinct card **Separate structural contracts from semantic data quality**.


## Audit maintained connectors before writing a new source by hand

- **Trigger:** a new source has to be ingested and writing a bespoke extractor looks faster than evaluating what exists.
- **Failure:** hand-rolled extractors reimplement pagination, typing, incremental state and retry semantics that maintained frameworks already carry, and the cost arrives later as glue and upgrade work rather than at the moment of writing.
- **Decision:** audit the source against dlt first, because it is the best local fit for Python embedding and typed destinations; consider Airbyte where a broad managed connector platform is wanted and Singer/Meltano where tap/target composability is. Custom code is justified only for a small unmatched seam whose glue and upgrade cost is genuinely lower.
- **Control:** the component audit is dated and pinned, and P1 exercises dlt across scale factors and both DuckDB and Postgres rather than accepting it on reputation.
- **Boundary:** P1 has not run, so dlt is the audited fit rather than a measured winner.
- **Evidence:** `GITHUB_IMPLEMENTATION_AUDIT.md`, the connector-framework family in `TECHNIQUE_TAXONOMY.md`, and P1 in `BENCHMARK_DESIGN.md`.
- **Proposal-safe insight:** I check what is maintained before writing an extractor, and I justify custom code by the seam it fills rather than by preference.
- **Central index disposition:** add card **Audit maintained connectors before writing a source**.

## Read "exactly once" as a statement about state, not about delivery

- **Trigger:** a latency or continuity requirement makes stateful streaming look like the obvious upgrade from micro-batch.
- **Failure:** Flink documents that its exactly-once guarantee covers managed operator state unless the sink cooperates, so treating the phrase as end-to-end silently assumes a property the sink may not have — duplicates then appear at the destination while the framework's own guarantee remains satisfied.
- **Decision:** keep micro-batch as the control, admit Flink only for continuous stateful work whose latency micro-batch cannot meet, and require any streaming arm to state its end-to-end sink and retention limits explicitly rather than inheriting the framework's headline.
- **Control:** specialist admission requires the streaming arm to reuse P0's truth contract, so its reconciliation is judged on the same stage and result evidence as batch.
- **Boundary:** no streaming arm has run here; this is a reading of the framework's own documentation, not a local measurement.
- **Evidence:** Flink official checkpointing and state documentation, the batch-versus-streaming family in `TECHNIQUE_TAXONOMY.md`, and the specialist admission gate in `BENCHMARK_DESIGN.md`.
- **Proposal-safe insight:** I ask which component owns a delivery guarantee before quoting it, because "exactly once" is usually scoped to state and the sink decides what the destination sees.
- **Central index disposition:** add card **Read exactly-once as a state guarantee, not a delivery one**.

## Treat a deprecated standard as evidence, not as a detail

- **Trigger:** a data-contract format has to be chosen, and several specifications appear to be live options.
- **Failure:** adopting the Data Contract Specification would have meant building on a repository that is deprecated in favour of ODCS 3.1 — a choice that reads as current at the moment of selection and becomes migration work later.
- **Decision:** express structural compatibility, ownership, semantics, quality and service levels in ODCS, and record the deprecation as the reason rather than as a footnote. Keep the contract's role bounded: a standard aids exchange and can generate checks, but it does not execute every semantic rule and does not prove pipeline correctness.
- **Control:** P3 evaluates an ODCS contract separately for portability and generated checks, explicitly not as a replacement oracle for the semantic-fault suite.
- **Boundary:** P3 has not run, so no claim is made about how many seeded faults a generated contract catches.
- **Evidence:** the ODCS 3.1 repository and the deprecation notice on the older specification, the structural-contract family in `TECHNIQUE_TAXONOMY.md`, and P3.
- **Proposal-safe insight:** I record the maintenance state of a standard as part of the decision, because "deprecated in favour of" is the cheapest possible warning and it is free to read.
- **Central index disposition:** add card **Treat a deprecated standard as selection evidence**.

## An emitted lineage event is not evidence of lineage coverage

- **Trigger:** a pipeline emits OpenLineage events and lineage is therefore reported as solved.
- **Failure:** emission proves the integration works, not that the graph is complete. Missing column-expression edges, incorrect run lifecycle transitions, stale successes after a failure and duplicate events all leave a lineage view that looks populated and is wrong where it matters.
- **Decision:** measure coverage against an expected graph rather than counting events: required dataset and run lifecycle edges at 100%, reviewed column-expression edges at 95% or better, and no stale success recorded after a failure.
- **Control:** P4 emits OpenLineage for the frozen stage graph and compares run, job, dataset, column and quality facets across success, retry, quarantine and failure paths.
- **Boundary:** P4 has not run; the current lineage claim is emission, not coverage.
- **Evidence:** the OpenLineage specification's run/job/dataset facet model, the lineage family in `TECHNIQUE_TAXONOMY.md`, and P4.
- **Proposal-safe insight:** I treat lineage as a recall measurement against an expected graph, because an event stream that is present but incomplete is harder to detect than one that is absent.
- **Central index disposition:** add card **Measure lineage coverage, not lineage emission**.

## Keep the orchestrator out of the correctness argument

- **Trigger:** connector, CDC or contract problems appear during a migration and switching orchestrator is proposed as the remedy.
- **Failure:** Airflow, Dagster and Prefect solve scheduling, retries, backfills and operations. None of them fixes a missed delete, an unreconciled duplicate or a semantic fault, so an orchestrator migration undertaken for a data-correctness problem spends the budget in the wrong place.
- **Decision:** retain the existing optional Airflow as the scheduling control, and compare an asset-centric or event-driven challenger only when a real asset-partition, ownership or dynamic-flow requirement is declared. The challenger must reduce operator steps or recovery time **without changing data correctness**, which is measured separately.
- **Control:** P4 holds the correctness evidence fixed while the scheduler varies, so a scheduling change cannot be credited with a data outcome.
- **Boundary:** no orchestrator comparison has run, and none is scheduled without a declared requirement.
- **Evidence:** the orchestration family in `TECHNIQUE_TAXONOMY.md` and the retention rule in P4.
- **Proposal-safe insight:** I separate scheduling from correctness, so an orchestrator is chosen for operations and never credited with fixing data.
- **Central index disposition:** add card **Keep the orchestrator out of the correctness argument**.

## Use an obsolete benchmark as a workload, never as a leaderboard

- **Trigger:** a data-integration workload is needed and TPC-DI is the industry option.
- **Failure:** TPC-DI is now listed as obsolete and has no published results, so citing it as a benchmark implies a comparison that does not exist. Equally, discarding it loses the only specified workload with historical and incremental loads, multiple formats, transformations and deliberate errors.
- **Decision:** use a declared TPC-DI subset as the workload shape and generate the evidence locally, stating the subset. Reconciliation and fault injection supply the verdict; the benchmark supplies only realism.
- **Control:** P0 maps the TPC-DI subset and the current dlt runs onto one stage and result contract, then requires the scorer to catch all seven seeded mutations — a dropped row, duplicate key, compensating aggregate error, late update, hard delete, wrong lineage edge and stranded staging batch.
- **Boundary:** P0 has not run, so the harness's mutation sensitivity is specified rather than demonstrated.
- **Evidence:** the TPC-DI specification and its obsolete listing, `TECHNIQUE_TAXONOMY.md`, and P0.
- **Proposal-safe insight:** I separate where a workload comes from from where a verdict comes from, so an unmaintained benchmark can still buy realism without lending unearned authority.
- **Central index disposition:** add card **Use an obsolete benchmark as a workload, not a leaderboard**.
