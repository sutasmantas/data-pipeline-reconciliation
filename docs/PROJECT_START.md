# PipelineForge foundation and identity record

Completed before portfolio-owned product implementation on 2026-08-03. These
are private working projects; license was not researched or used as a filter.

## 1. Restart boundary

- repository: `portfolio_demos/pipeline_forge`
- baseline branch and commit: `main` at upstream `a5e3fced5860c22b6ed439030b2d189791edacdb`
- implementation branch: `agent/pipelineforge-p4`
- assigned isolated worktree: `portfolio_demos/worktrees/pipelineforge_p4`
- owner/session: current Codex session only
- repositories/worktrees that are read-only: DeliveryGuard and AdapterProof;
  ContextSidecar is excluded and must not be inspected
- exact next action: replace the old BigQuery-only demo configuration with a
  current, tested dlt 1.29.1 DuckDB vertical slice while preserving the
  inherited SQL extraction behavior

Never share this worktree or switch its branch.

## 2. Client outcome and non-duplication

- one client-purchased outcome this project proves: reliably move and
  reconcile changing data from REST APIs, files, and PostgreSQL into a local or
  PostgreSQL warehouse, with incremental recovery and a client-readable report
- existing portfolio evidence closest to it: AdapterProof proves individual
  HTTP adapter contracts; DeliveryGuard proves durable action delivery
- mechanism or deliverable that is genuinely new: stateful multi-source data
  movement, schema evolution, migration, warehouse reconciliation, and an
  Airflow entry point
- why this is better coverage than deepening an existing project: it closes the
  non-AI data-pipeline/API-integration/migration/reporting delivery surface
  without misrepresenting the narrower adapter projects as data platforms

## 3. GitHub foundation comparison

No candidate was researched, filtered, or ranked by license.

| Candidate | Repository | Activity/version checked | Central behavior reusable for this MRE | Adaptation cost/risk | Decision |
| --- | --- | --- | --- | --- | --- |
| PostgreSQL to BigQuery pipeline demo | `dlt-hub/postgresql_bigquery_pipeline_demo` | pinned `a5e3fced5860c22b6ed439030b2d189791edacdb`; last upstream change 2023-05-24 | real SQLAlchemy database reflection, selected-table incremental hints, merge/replace modes, and deployed-pipeline files | old dlt/BigQuery pins and defects in example control flow require a bounded upgrade | **adopt repository foundation and refit** |
| dlt OpenAPI demo | `dlt-hub/dlt-init-openapi-demo` | pinned `6b21898ad1caf8883b05ae96da4ddd783b986663`; last upstream change 2024-04-13 | generated OpenAPI client and DuckDB pipeline | generator demonstration is stale and does not provide file migration, reconciliation, or operational evidence | reject as foundation; retain as REST-generation comparison |
| dlt verified sources | `dlt-hub/verified-sources` | pinned `3957506893a7da821dbcc6acd51c7ca4475d1f53`; checked 2026-08-03 | broad historical connector corpus | current generic REST and filesystem files are redirect placeholders; inheriting it would not inherit working central behavior | reject as foundation |
| Airbyte | `airbytehq/airbyte` | v2.0.0; head `6bd89053b4c7722a923a3893754a17875e8ebcc7` | large connector catalog and declarative connectors | separate control plane/runtime, deployment, and connector protocol would dominate this small Python starter | reject as foundation; consult connector patterns only |
| Meltano | `meltano/meltano` | v4.2.2; head `6a34713da405597b8cf355a7b242f29b780980dd` | Singer plugin orchestration and catalog | duplicates dlt extraction/state/load responsibilities and adds plugin/runtime boundaries | reject as foundation; consult Singer taps only when a paid job needs one |

Selected foundation:

- repository URL: `https://github.com/dlt-hub/postgresql_bigquery_pipeline_demo`
- pinned tag/commit: `a5e3fced5860c22b6ed439030b2d189791edacdb`
- exact code/package/contracts reused: repository history, `sql_database`
  source package, SQLAlchemy reflection, incremental cursor hints, and
  merge/replace pipeline shapes
- upstream history/identity preservation: cloned with its two upstream commits;
  remote renamed to `upstream`; portfolio work begins on a separate branch
- why this is faster/safer than starting blank: one of the two required
  adaptations begins from an exercised database-source pipeline, while current
  dlt supplies the state, normalization, schema, and destination contracts

## 4. Component-level GitHub reuse audit

| Proposed component | GitHub candidates checked | Decision | Exact reused surface or custom boundary | Integration cost and reason |
| --- | --- | --- | --- | --- |
| extraction, normalization, incremental state, schema evolution, loads | `dlt-hub/dlt` 1.29.1 / `412b4deab6908ec8665c42833ec6c6d01327d1b0`; Airbyte 2.0.0; Meltano 4.2.2 | **adopt dlt** | REST API, SQL database, filesystem/readers, incremental cursors, merge disposition, schema contracts, DuckDB and Postgres destinations | dlt removes the whole responsibility in-process; combining connector runtimes would create integration and upgrade burden |
| orchestration | Apache Airflow 3.3.0 / `1438ea3587031417cc85d74323235cf087a058fb`; Prefect 3.8.1 / `05c045c68360e723560d61d5231824b55b811db1`; Dagster 1.13.16 / `0ddc19cf5d3613f79a6229d2fb959210e8a7f56c` | **refit Airflow boundary** | scheduler-independent `run` command plus one thin Airflow DAG/task entry point; Airflow remains an optional environment | Airflow matches the market evidence; embedding any orchestrator in the core would add a second state machine |
| typed/schema contracts and quarantine | dlt 1.29.1 schema/data contracts; Soda Core v4.19.0 / `0416a3d0a47d04c112dd8f8d8b7b5cc017888c57`; Pandera v0.32.1 / `e649b0d76e3ecb3b6ca916bdd5807c64eddd7603` | **adopt dlt; custom bounded quarantine routing** | dlt contract modes and column hints enforce load schema; rejected rows receive a small PipelineForge reason envelope | Soda adds datasource/YAML/scan runtime; Pandera adds a dataframe engine and duplicate schema. Neither removes a responsibility not already covered for the fixed cases |
| source/target reconciliation and quality checks | Soda Core v4.19.0; Great Expectations 1.19.1 / `04b53b2c1e8691523b3afa263a901a5b36e7d3b5`; archived Datafold data-diff v0.11.1 / `1410c6cd0b915ae24a15e03a7de15ff41beebaf0` | **custom bounded SQL** | exact counts, key uniqueness, required-field completeness, freshness, stable row digests, and mismatch samples over DuckDB/Postgres | the exit gate needs a small fixed cross-engine metric set, not another validation runtime or an archived database-diff CLI; SQL results remain directly auditable |
| mapping canonical records | AdapterProof `6dd45c0`, package 0.1.0; dlt transforms | **adopt AdapterProof where flat dot-path mapping fits** | consume `AdapterManifest`/`map_event` through its wheel; dlt handles normalization; no copied code | reuses an already tested portfolio package without turning its HTTP conformance runner into pipeline orchestration |
| retries, idempotency, dead letters, replay, alerts | DeliveryGuard `4fd8eaa`, package 0.1.0; dlt pipeline retry/deployment patterns | **adopt DeliveryGuard** | consume `DeliveryExecutor`, `DeliveryStore`, stable keys, bounded retries, dead letters, replay, and redaction through its wheel | removes the durable action state machine; adapters remain PipelineForge-owned and narrow |
| HTTP fake source and inspection API | FastAPI 0.136.3 / Airflow 3.3.0 compatibility boundary; Flask | **adopt FastAPI** | credential-free paginated/rate-limited/failing fixture API and read-only run/report endpoints | one typed ASGI runtime serves both test source and bounded inspector; the pin remains installable beside optional Airflow |
| structured logs and run history | dlt trace/state; structlog 26.1.0 / `7b04229f3e569d03f5b8a7ae919355a3a0e0abb2`; OpenLineage | **adopt dlt trace; custom JSON log adapter** | persist selected stable dlt trace fields plus newline JSON events and report metadata | structlog/OpenLineage add dependencies and schemas without removing the small stable adapter needed by this MRE |
| client-facing HTML report | Jinja 3.1.6 / `5ef70112a1ff19c05324ff889dd30405b1002044`; hand-built HTML | **adopt Jinja** | deterministic report template over reconciliation data | templating removes escaping/layout plumbing with little glue |
| bounded run/reconciliation UI | Tabulator 6.5.2 / `efc2b324317c6c0211415ce4e044ee48667f708f`; TanStack Table / `00bccc405fb8e366a436f3434c9cb9d0034ccc07`; native HTML table | **custom native table** | server-rendered run selection and source/target comparison only | either grid imports a JS framework-sized upgrade surface for sorting a small fixed table; native semantics are smaller and testable |
| local metadata persistence | dlt state/trace; SQLModel/SQLAlchemy | **adopt dlt plus bounded SQLite schema** | only portfolio run, check, quarantine, and replay evidence not already held by dlt | a second ORM would exceed the fixed schema and obscure reconciliation SQL |

- component audit completed before implementation: **yes**
- selected reusable components and pins: dlt 1.29.1, DeliveryGuard 0.1.0
  at `4fd8eaa`, AdapterProof 0.1.0 at `6dd45c0`, FastAPI 0.136.3,
  Jinja 3.1.6, optional Airflow 3.3.0
- deliberately custom components and decision evidence: fixed SQL
  reconciliation, quarantine envelope, JSON-log adapter, four-table evidence
  store, and native comparison screen; each is smaller than integrating the
  rejected general-purpose runtime
- overlapping candidates rejected to avoid integration/upgrade burden:
  Airbyte, Meltano, Prefect, Dagster, Soda, Pandera, Great Expectations,
  data-diff, Tabulator, and TanStack Table

## 5. Distinct visual direction

Rendered working-state screenshots were inspected, not covers or logos.

| Existing project | Screenshot inspected | Spatial model | Navigation | Palette family | Typography character | Geometry/surface model | Dominant interaction | Candidate differences |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Relay | `docs/screenshots/relay-case-workspace.png` | three-column case workspace | dark left sidebar and tabs | white/navy/teal | compact product sans | rounded cards | approve proposed actions | no sidebar/cards; horizontal stages and paired data ledger |
| Atlas | `qa_library.png` | sidebar plus KPI/table canvas | dark left sidebar | pale blue/navy/violet | compact product sans | rounded dashboard cards | browse documents | report-sheet spatial model and source/target comparison |
| LedgerLens | `docs/screenshots/review-queue.png` | sidebar plus review table | dark left sidebar | white/navy/orange | compact product sans | rounded dashboard cards | choose a review item | square ruled dossier; horizontal navigation |
| LeadDock | `docs/leaddock-1440.png` | appointment ledger with top intake rail | top rail | violet/coral | condensed/mono operations | boxed paper ledger | select and book slot | paired warehouse columns, editorial report type, blue/red marks |
| Printline | `docs/screenshots/printline-workstation-1440.png` | artboard plus right control deck | top/status bands | charcoal/lime/coral | industrial mono/sans | square technical panels | edit recipe/render | light dossier rather than dark workstation; reconciliation is primary |
| Gauge | `docs/screenshots/gauge-station-1440.png` | central optical stage and rails | top infeed rail | cream/black/yellow | heavy industrial display/mono | square machine console | inspect/disposition image | text-and-table evidence sheet, editorial rather than machine-HMI scale |

- comparison projects/screenshots reviewed: Relay, Atlas, LedgerLens,
  LeadDock, Printline, and Gauge
- product/audience metaphor: a signed migration/reconciliation dossier used by
  a data engineer and client during handoff
- layout structure: full-width sticky header; horizontal pipeline-stage rail;
  below it a large source-versus-destination ledger with a narrow vertical run
  spine and an attached reconciliation-sheet footer; no persistent sidebar
- palette: warm newsprint, charcoal ink, ultramarine source marks, vermilion
  mismatch marks, restrained green only for passed checks
- typography character: editorial serif headings paired with monospaced data
  values and a neutral sans for controls
- primary interaction pattern: select a run/stage on the horizontal rail, then
  inspect paired counts, fields, and mismatch samples in the ruled ledger
- explicit patterns avoided because another project already uses them: dark
  left navigation, rounded KPI cards, chat/case three-column layout, purple
  appointment ledger, and dark industrial control deck
- 1440/1024/390 first-viewport evidence: **PASS** at
  `docs/screenshots/pipelineforge-1440.png`, `pipelineforge-1024.png`, and
  `pipelineforge-390.png`; all reconciliation columns remain visible at 390px
- closest visual neighbor and why this is not a reskin: LeadDock also uses a
  ledger metaphor, but PipelineForge uses a horizontal process route plus
  paired source/destination report columns, editorial type, newsprint/blue/red,
  and read/compare interaction rather than a violet calendar and approval flow

## 6. Minimum referenceable evidence contract

| Gate | Observable acceptance evidence | Status |
| --- | --- | --- |
| Central similarity | inherited SQL incremental pipeline exercised against dlt 1.29.1 by `tests/test_foundation_sql.py` | PASS |
| Component-level reuse decisions | every substantial subsystem audited above before implementation | PASS |
| Working vertical slice | REST-to-DuckDB plus file/Postgres migration and report | PASS |
| No-key deterministic proof | fixed authenticated fake API through local DuckDB, including cursor pagination | PASS |
| Invalid input and abuse behavior | mapping, cursor, path, endpoint limits, missing destination credentials, and quarantine tested | PASS |
| Provider/tool failure and retry/refusal/handoff | forced 429 and 503, durable dead letter, cycle-2 replay, duplicate suppression, payload conflict refusal, and redacted alert evidence | PASS |
| Focused mechanism tests | initial/incremental/late/schema/failure/replay/mismatch cases | PASS |
| Clean-checkout quickstart | detached clean worktree at `56eb87f`: 19 passed, 1 deselected, 92% coverage; CLI PASS; wheel/sdist Twine PASS | PASS |
| Cover-letter claim ledger | exact supported claims and test references in `docs/CLAIMS.md` | PASS |
| Honest unsupported-claim boundary | no production scale, exactly-once, CDC, hosted scheduler, managed-service, or client-data claims | PASS |

Only all `PASS` closes P4. Stop before decorative polish.

## 7. Verification and handback

- static/type/lint command: `.venv/Scripts/python -m ruff check .` and
  `.venv/Scripts/python -m mypy`
- focused tests: full live-Postgres run: 20 passed at 93% branch coverage;
  clean no-key run: 19 passed, 1 Postgres test deselected, at 92% coverage
- integration/demo command: `pipelineforge migrate-files --work-dir
  .pipelineforge`; deterministic `PASS`, 5 rows, amount 1550, 2 quarantined
- build/package command: `python -m build` and `python -m twine check dist/*`;
  wheel and sdist pass
- reused-component contract tests and pin/upgrade boundary: checksum tests pass
  for AdapterProof/DeliveryGuard/fixtures; Airflow 3.3.0 digest-pinned image lists
  `pipelineforge_file_migration` locally with zero import errors
- branch and implementation commit: `agent/pipelineforge-p4` at `56eb87f`
- clean state: branch worktree has no uncommitted implementation changes;
  detached proof worktree reproduced the committed quickstart
- known boundaries: no managed warehouse, production-scale throughput,
  distributed exactly-once, CDC, hosted scheduler, or named SaaS connector
- exact next portfolio action: finish P4 all-PASS gate, merge locally, then P5
  voice; no polish or ContextSidecar work
