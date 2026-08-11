# PipelineForge research decision

Date: 2026-08-05

## Outcome

The systematic evidence gate is `PASS`. Experiment and overall technique-ceiling gates remain `PARTIAL`: P0-P4 are frozen designs, not results.

The current dlt batch/incremental profiles remain the baseline. P0 is the exact first experiment, followed by dlt crash/scale validation in P1. Debezium, Pandera/Soda and OpenLineage are maintained candidates for observed gaps; streaming, lakehouse and alternative orchestrators remain conditional.

## Retained decisions

| Family | Disposition |
| --- | --- |
| dlt REST/file/SQL full + watermark | mandatory control |
| TPC-DI subset + exact stage reconciliation | P0 |
| dlt crash/scale/watermark/delete matrix | P1 |
| Debezium | P2 only for freshness/deletion region |
| Pandera first, Soda for SQL region | P3; choose one winner/profile |
| ODCS/Data Contract CLI | future inter-team contract profile; deprecated predecessor rejected |
| OpenLineage | P4 completeness experiment |
| Airflow | retain optional scheduler control |
| Dagster/Prefect | only for explicit asset/dynamic-flow requirement |
| Flink/Iceberg | specialist admission only |
| custom connector/CDC/quality/lineage framework | rejected before component evidence |

## Exact next controlled work

1. P0 common workload, fault manifest and mutation-sensitive reconciliation.
2. P1 current dlt profiles under crash, watermark, deletion and scale cases.
3. P2 only if P1 cannot meet declared freshness/deletion needs.
4. P3 only on semantic faults current contracts miss.
5. P4 after stage/run truth is stable.

No experiment, implementation, polish, merge, push or publication occurred.

## Eleven systematic evidence gates

| Gate | Status | Evidence |
| --- | --- | --- |
| Problem decomposition | PASS | capture through evaluation layers in `TECHNIQUE_TAXONOMY.md` |
| Search protocol | PASS | nine dated iterations |
| Survey coverage | PASS | pipeline-tools and pipeline-quality surveys plus primary standards |
| Benchmark coverage | PASS | TPC-DI subset and P0-P4 local fault/scale design |
| Existing-answer search | PASS | CDC/orchestration/lineage/quality roles separated |
| Technique-family saturation | PASS | iterations 7 and 8 added no top-level family |
| Candidate comparison | PASS | `EVIDENCE_MATRIX.csv` |
| Contrary evidence | PASS | obsolete/no-result workload, at-least-once CDC, archived/deprecated tools and incomplete lineage |
| Implementation evidence | PASS | exact pins and reuse map in `GITHUB_IMPLEMENTATION_AUDIT.md` |
| Portfolio fit | PASS | distinct data reliability evidence while reusing DeliveryGuard/AdapterProof boundaries |
| Review status | PASS | conclusions explicitly labelled |

## Claim boundary

Defensible now: bounded dlt ingestion/contracts/quarantine/reconciliation and a systematic pinned plan for crash recovery, CDC, semantic quality, lineage and scale.

Not defensible now: CDC correctness, deletion completeness, production scale/SLA, semantic-quality engine performance, complete lineage, streaming exactly-once, lakehouse behavior or orchestrator superiority.

