# Event Model — codex + events + logs (owner-directed design)

**Status: DRAFT per owner direction 2026-08-22.** To be refined together, step by step, when we
build the analysis stage. Supersedes the 6-table stepwise sketch as the storage shape;
[../stepwise/DESIGN.md](../stepwise/DESIGN.md) stays as the reference for gate/ledger/staleness
*ideas*, which can layer onto this model later if needed.

## The three pieces

```
1. codex   — master table: one row per book (see SCHEMA.md)
2. events  — ONE append-only table: every pipeline event, timestamped
3. logs    — NOT a table: Python-logging / AWS-Glue-style log files
             (timestamps + messages + errors; greppable)
```

Plus a **step-registry folder** in the repo that defines every stage's steps and ids — the
DB never defines the pipeline, it only records what happened (this matches how Databricks,
Dagster, and every event-sourced system splits definition from record).

## 2. The `events` table

One row per thing-that-happened. Current status of anything = **derived** from the latest
event per key (event-sourcing pattern; standard SQL: `ROW_NUMBER() OVER (PARTITION BY
codex_id, stage, step_id ORDER BY event_ts DESC) = 1` — Databricks' pipeline event log uses
exactly this).

| Column | Type | Notes |
|---|---|---|
| `event_ts` | TEXT | ISO-8601 UTC with microseconds — ordering key |
| `codex_id` | TEXT | THE id from the codex table |
| `stage` | TEXT | `analysis`, `music`, `video`, … — same vocabulary as the codex stage columns |
| `step_id` | TEXT | hierarchical id from the registry, **fixed-width 2-digit segments**: `01`, `01_01`, `02_03`, `01_01_01`, … |
| `event` | TEXT | `started` / `completed` / `failed` / `skipped` / … (small CHECK'd set — finalize together) |
| `run_id` | TEXT | correlation id linking to the log file for this run (proposed) |
| `detail` | TEXT | tiny optional payload (artifact path, cost, error *summary* — one line max; full detail lives in logs) |

**What it deliberately does NOT contain:** stack traces, LLM outputs, long messages — that's
what logs are for, exactly as you said.

### `step_id` sorting — SOLVED (owner decision 2026-08-22)

**Fixed-width 2-digit segments, zero-padded**: `01`, `01_01`, `01_02`, `01_01_01`. With every
segment the same width, lexicographic order = hierarchical order at every depth:

```
01 < 01_01 < 01_02 < 01_10 < 02 < 02_01      -- plain ORDER BY step_id is correct
```

**Growth rule (owner's)**: a level never exceeds 2 digits (99). If a step is accumulating too
many substeps, that's the signal to restructure it into another sub-level instead of growing
the list.

**Insertion rule**: to add work between `01_01` and `01_02`, give it a sub-level
(`01_01_01`) rather than renumbering — ids are stable once events reference them.

The registry file remains the source of truth for what exists, names, and the DAG shape; the
padded ids just mean sorting also works directly in SQL with no join.

## 3. Logs — files, not tables

Modeled on AWS Glue/CloudWatch conventions (log **stream per job run**) + Python structured
logging practice:

```
logs/<codex_id>/<stage>/<run_id>.log        # one file per run — Glue's stream-per-run
```

- Line format: **JSONL** — `{"ts": …, "level": "ERROR", "codex_id": …, "stage": "analysis",
  "step_id": "1_2", "msg": …}` — structured lines make "find all errors for book X step 1_2"
  a one-line grep/jq, which is the whole point you stated.
- Standard `logging` module with a JSON formatter + a context filter injecting
  codex_id/stage/step_id automatically — code just calls `log.info("...")`.
- The `events.run_id` column is the join: event says *what/when*, the log file says *why/how*.
- Rotation/retention: logs are disposable evidence; events are the permanent record.

## 4. The step registry — ONE file: `stages.yaml` (owner decision 2026-08-22)

All stages, steps, and substeps live in a single repo-root file (originally a folder of
per-stage files; owner simplified to one file for easy scanning):

```yaml
# stages.yaml
stages:
  analysis:
    steps:
      - id: "01"
        name: ingest
        script: step_01_ingest       # module in scripts/analysis/
        desc: Read the source book, split into chapters/scenes.
      # ... 02 registry, 03 extract, 04 timeline, 05 consolidate, 06 verify
  # audiobook: / music: / video: — same shape, scripts in scripts/<stage>/
```

Rules:
- **File order = execution order.** The DB never knows the pipeline shape; runners load
  their stage from this file and refuse to run if a script's STEP_ID disagrees with the yaml.
- ids are stable once used (events reference them); names/descriptions free to evolve.
- The command-center UI renders its DAG straight from this file and colors nodes from
  the latest events — no schema change ever needed to add steps.

## Resume rule (owner-confirmed 2026-08-23)

> **A step's resume key is its OUTPUT's existence — never the events table.**
> - Output on disk → check file exists + content hash matches input (step 01: book.json
>   sha vs epub; step 02: per-chapter extraction files).
> - Output in the world (upload, paid generation) → the recorded row IS the artifact;
>   the table becomes the resume key.

Division of labor: **events** pick work at the book level (`codex_pending_stage`) and
keep the record; **files+hashes** decide whether to redo work within a step. An event
row says "a run finished once"; a hash-matched file says "the output exists right now
and matches the current input" — only the latter is safe before skipping paid work.

## Open refinement points (for our step-by-step session)

1. Final `event` vocabulary (started/completed/failed/skipped — plus retries? approvals?).
2. `run_id` format (proposal: `<codex_id>_<stage>_<yyyymmddhhmmss>`).
3. Where cost lands (proposal: `detail` on completed events now; dedicated column/ledger later if money steps need reserve/commit safety — see stepwise DESIGN §money).
4. Substep fan-out ids for per-chapter work: `03_01` per chapter vs a `03_01_ch07`-style suffix.
5. YAML vs Python for registry files.
6. Where the analysis A0-A9 proposal maps onto `01, 01_01, …` numbering — we'll do this together.

Sources: [materialized-path sorting pitfall](https://bojanz.github.io/storing-hierarchical-data-materialized-path/) · [event-sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) · [Databricks pipeline event log schema](https://docs.databricks.com/aws/en/ldp/monitor-event-log-schema) · [AWS Glue reliable-pipeline logging](https://docs.aws.amazon.com/ja_jp/whitepapers/latest/aws-glue-best-practices-build-secure-data-pipeline/building-a-reliable-data-pipeline.html) · [structured logging w/ correlation ids](https://medium.com/@connorbutch/how-to-implement-structured-logging-in-aws-fc3f80929750)
