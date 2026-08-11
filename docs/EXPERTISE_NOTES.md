# PipelineForge expertise notes

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

