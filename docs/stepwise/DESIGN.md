# stepwise — Proposed Design

**Status: SUPERSEDED IN PART, 2026-08-22 — owner directed a simpler 3-piece model
(codex + one events table + file logs + step-registry folder): see
[../db/EVENT_MODEL.md](../db/EVENT_MODEL.md). This doc remains the reference for the
gate / ledger / staleness-cutoff / lease ideas, to be layered in only if and when needed.**

The durable, cost-gated step runner (Layer 1 of ARCHITECTURE.md). Generic across every stage —
analysis (A0-A9), audiobook, shorts, video — one mechanism, one UI. Evidence:
[research/01_orchestrator_schemas.md](research/01_orchestrator_schemas.md) + the autopsy of our
own v1 (`d060598` `step_tracker.py`/`job_queue.py`).

## Design stance (each choice stolen from a system that proved it)

1. **Mutable current-state row + append-only history** (Airflow `task_instance` + `task_instance_history`): cheap "what's the status" queries, full audit.
2. **Fan-out = a `substep_key` column in the same table** (Airflow `map_index`, but a *string* like `ch07` — Dagster mapping_key — stable when the chapter list changes). A parent step is a **derived aggregate over its children**, never an executable holding a resource (the SubDAG-deadlock lesson).
3. **Resume = content-addressed artifacts** (Nextflow/Snakemake position): skip iff an `artifact` row exists for `(production, step, substep, input_hash)` AND the file exists with matching `content_hash`. DB is the index, disk is the truth; writers must **temp-file + rename** (Luigi's atomicity contract).
4. **Staleness is derived, never stored**, with the **output-equality cutoff** (Dagster/Nextflow): a step is *unsynced* when `hash(code_version + upstream output_hashes + params)` ≠ its recorded `input_hash`. If a re-run produces a byte-identical artifact, downstream hashes don't change → **no cascade, no re-spend**. This is the single most money-saving idea in the design.
5. **Money = idempotency-keyed ledger with reserve→commit** (Temporal/Prefect transactions): `reserved` row written before the paid call, `committed` with artifact + success in ONE transaction. A dangling `reserved` after a crash means "verify with provider before retrying" — never blind re-execution.
6. **Leases, not statuses, prevent double-work** (Prefect isolation lesson): claim via one atomic `UPDATE … RETURNING` on `(state='ready' OR lease expired)`; SQLite's single-writer serializes it; the same shape becomes `FOR UPDATE SKIP LOCKED` on Postgres.

## State machine

```
pending → ready → claimed → running → succeeded
                                    → failed (attempt < max → back to ready after backoff)
                                    → parked            (gate ESCALATE; infra released; queue moves on)
          upstream_failed  (never ran — poisoned; distinct from failed)
          skipped          (terminal non-error; counts as done downstream)
          cancelled
```

Named distinctions with pedigree: `upstream_failed` ≠ `failed` (Airflow); `skipped` counts as
done (Airflow); `parked` = Prefect *Suspended* (releases resources); a resume-skip completes as
`succeeded` with `note='cached'` (Prefect Cached-is-COMPLETED). Retry timing owned by the
scheduler via `next_retry_at`, **never `time.sleep` in a worker** (v1 bug #4).

## Tables (6)

Full DDL lives in the research file; summary:

| Table | Role | Key columns |
|---|---|---|
| `step_run` | current state, one row per (production, step, substep) | `production_id, step_name, substep_key, input_hash, code_version, state, attempt, output_hash, lease_owner, lease_expires_at` — UNIQUE(production, step, substep) |
| `step_attempt` | append-only history (written on every clear/retry) | snapshot of input_hash/code_version/state/worker/timestamps/error |
| `artifact` | completion records = resume keys | `path` (relative!), `input_hash`, `content_hash`, size, creating attempt — UNIQUE(production, step, substep, input_hash) |
| `ledger` | money | `idempotency_key` (prod:step:substep:input_hash, stable across retries), provider, units (credits/usd), amount, `state ∈ reserved/committed/void` |
| `gate` | approvals | step_run, gate_name, `open/approved/rejected/escalated`, payload (spend plan/artifact refs), decided_by/at/note |
| `event` | audit log | event_type, payload JSON, actor, timestamp |

Hierarchy beyond one fan-out level = **dot-namespacing in `step_name`** (`A3.extract`,
Airflow TaskGroup pattern) — no extra tables, arbitrary depth, and the UI's drill-down falls
out of splitting on dots.

**Same tables serve every stage.** "Analysis of book X" and "audiobook of book X" differ only
in the pipeline *definition* (a static Python/YAML DAG of step names, dependencies, executors,
gate policies — code, not DB; the Temporal anti-lesson says render/plan from definition,
overlay status from DB). `production_id` = `codex_id` for book-level stages; production folders
for shorts keep their existing ids.

## Re-run semantics (the owner's ask, explicitly)

| Want | How |
|---|---|
| Re-run one substep ("chapter 12 only") | **Clear** that `step_run` row: snapshot → `step_attempt`, state → `ready`, attempt+1. Nothing else touched. |
| Re-run a step + everything after | Clear with `--downstream`: walk the definition DAG, clear dependents. But the **cutoff** applies: dependents whose recomputed input_hash is unchanged skip instantly as cached. |
| Prompt/template changed | Bump that step's `code_version` in the definition → affected steps show **unsynced** in the UI; you choose to materialize the stale subgraph (Dagster "materialize unsynced"). |
| Crash mid-run | Lease expires → row reclaimable. Half-written files impossible to mistake for done (temp+rename + content_hash verify). Dangling `reserved` ledger rows demand provider verification first. |
| Force-accept an existing output | `--bless` (Snakemake `--touch`): record artifact as current without running. |
| Never re-spend by accident | Resume check runs **before** any paid call, and the ledger reserve makes double-spend visible even across crashes. |

## What v1 lacked → fixed

linear enum order → definition DAG · no input_hash/artifact check → content-addressed resume ·
racy claim → atomic lease · blocking sleep → `next_retry_at` · no gates/parking → `gate` +
`parked` · no staleness → derived unsynced + cutoff · orphan int job ids → `codex_id` join.

## Open questions for review

1. `stepwise` is the working package name — keep, or name it (it's the publishable artifact)?
2. Backoff policy per step type (LLM retry fast; paid-media steps maybe never auto-retry, only via gate)?
3. `event` table growth: prune/archive policy per finished production (Temporal history-cap lesson)?
4. Ledger `units`: credits + usd enough, or track tokens too?
5. Confirm: pipeline definitions live in code (Python dicts/YAML in repo), DB stores only runs.
