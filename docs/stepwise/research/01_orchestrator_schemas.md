# Research — How mature orchestrators model runs/tasks/state; re-run semantics

*Subagent report, 2026-08-22. Full DDL sketch adopted into [../DESIGN.md](../DESIGN.md).*

## 1. Airflow

- **`task_instance`** keyed by `(dag_id, task_id, run_id, map_index)` — **`map_index` column = fan-out in the same table** (dynamic task mapping). One state machine, one lease mechanism for parents and children.
- **States that matter and why**: `none→scheduled→queued→running` → terminal; plus `up_for_retry` (scheduler owns retry timing, not the worker), **`upstream_failed`** (never ran — poisoned; distinct from `failed`), **`skipped`** (terminal non-error, counts as done downstream), `deferred` (waiting without holding a slot), `awaiting_input` (human-in-the-loop).
- **Clear = the re-run primitive**: state set back to None, try_number incremented, prior row copied to append-only **`task_instance_history`** first. Default UI clear = task **+ all downstream** — manual topological cascade, no hash checking.
- Backfill = insert missing (dag_id, interval) run rows; identity = the interval.

## 2. Dagster (closest match)

- Everything is an **append-only event** (materializations, step start/success/fail); "which partitions are done" is *derived by querying the event log*, with caches for speed.
- **Staleness**: user-supplied `code_version` + computed **`data_version` = hash(code_version, input data_versions)** — recursive Merkle fingerprint stored on the materialization. "Unsynced" = current declared versions ≠ recorded ones. **Not transitive through unchanged data**: if upstream re-materializes to the same data_version, downstream stays fresh — cosmetic changes don't cascade.
- **Partitions = per-chapter fan-out**: one asset, partition keys (incl. **DynamicPartitionsDefinition** — keys discovered at runtime, exactly "chapter count found by A1"); backfills target arbitrary partition subsets. String `mapping_key`s (`process[ch07]`) beat integers — stable when the list changes.

## 3. Prefect

- State **type** vs **name**: `Cached` and `RolledBack` are type COMPLETED — "skipped because done" reads as success downstream. **`Crashed` ≠ `Failed`** (infra death vs code exception). `Paused` holds infra; **`Suspended` releases it** — our "parked".
- **Cache policies compose**: `INPUTS + TASK_SOURCE` ≈ our `(input_hash + code_version)`. Isolation lesson: the cache record alone doesn't prevent concurrent double-execution — an explicit lock/lease is required.
- **Transactions**: BEGIN (key lookup → Cached) → STAGE → COMMIT/ROLLBACK with hooks; a transaction runs at most once per key. = our gate + ledger-write pattern.

## 4. Temporal

- State = append-only event history, deterministically replayed; completed activities never re-execute on replay. At-least-once + **idempotency key stable across retries** = exactly-once business effect. Key = (run id, activity id) → ours: `prod:step:substep:input_hash`, passed to the paid API where supported.
- Why not run it: 4 services + persistence + capacity decisions on day one; determinism constraints on workflow code. Overkill for one Windows box.

## 5. Make / Luigi / Snakemake / Nextflow (our lineage)

- **Make**: mtime only — fails on identical rewrites and recipe changes.
- **Luigi**: `Target.exists()` IS the state store. Atomicity contract: **temp-file + rename**, else a crash leaves a half-file that counts as done. Existence alone can't distinguish done from crashed-mid-write.
- **Snakemake**: existence + sidecar fingerprints; **five rerun-triggers** on by default (mtime, input-set, params, code hash, software-env); `--rerun-incomplete`, `--touch` (bless outputs), `--forcerun`.
- **Nextflow `-resume`**: task hash over (session, name, input values, input file metadata, **script text**, container, arch) → hash NAMES the work directory; resume = hash exists + valid exit code + outputs present. Cache modes incl. *lenient* (NFS mtimes lie). Documented failure: nondeterministic collection order changes the hash — **canonicalize/sort before hashing**.

## 6. Sub-steps / hierarchy

- **Airflow SubDAGs deprecated**: the wrapper held a worker slot while children waited → deadlock. **TaskGroups** = pure namespacing (`group.task` in the id), no extra entity.
- **Lesson: a parent step is a derived aggregation state over its children** (Airflow's dag_run-from-leaf-tasks rule), never an executable that occupies a resource.

## 7. Invalidation philosophies

- **Push invalidation** (Airflow clear-downstream, Snakemake): upstream *changed* ⇒ downstream reruns, even if output identical.
- **Output-equality cutoff** (Dagster, Nextflow): downstream reruns only if upstream's *actual output* differs.
- For a money pipeline the cutoff is decisive: re-running A3 with a fixed prompt that yields byte-identical text must NOT cascade into regenerating 27 audiobooks. Requires hashing artifact **content** at completion. **Never store a "stale" flag; always derive it.**

## 8. The recommended table set

Six tables — `step_run` (mutable current state, UNIQUE(production, step, substep_key), lease columns), `step_attempt` (append-only history), `artifact` (completion record: input_hash cache key + content_hash + temp-rename contract), `ledger` (idempotency-keyed money: reserved→committed/void), `gate` (open/approved/rejected/escalated + payload), `event` (audit log). Full annotated DDL and the operation semantics (claim, resume-skip, fan-out, clear, staleness-with-cutoff, spend safety) are adopted into [../DESIGN.md](../DESIGN.md).

Key sources: Airflow tasks/dag-run/DB docs + task_instance_history; AIRFLOW-1077 SubDAG deadlock; Dagster versioning & partitions docs + event-log source; Prefect states/caching/transactions; Temporal events + idempotency blog; Nextflow cache-and-resume; Snakemake CLI rerun-triggers; Luigi tasks docs.
