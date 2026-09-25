# B — Execution model for a table-driven studio

Expert B (pipeline orchestration), design round 2026-09-25. Read-only; nothing here is built.
Grounded in `stages.yaml`, `studio/{db,step_runner,stage_run,episode_run,judged_gate,deferral,
ladder,take_ladder,plan_ladder,comfy,approval,spend,episode_clock,learnings}.py`, `gates.yaml`,
`docs/db/EVENT_MODEL.md`, `docs/stepwise/DESIGN.md`, `docs/command_center/DESIGN.md`, the
2026-09-24 departments decision, and `library/<wotw>/episodes/ep12` (24 kept takes, 10 displaced
attempts, eye signed) and `ep13` (`plan.deferred.json`, six PLAN ladders in `learnings.jsonl`).

## 0. The brick, and what already exists

The brick is unchanged from the 2026-09-24 decision: a **Step** `(stage, unit, step_id)`, one
artefact on disk, a known cost, a gate. The owner asks for the row above it: a **work order** =
one unit of one department, `(stage, codex_id, unit)`. Today that row is implied by `events`
and by the runner's argv (`episode.py <codex> 12`). Every mechanism it needs already exists:

| need | exists today as |
|---|---|
| readiness from `requires` | `refs.ready()` -> `db.codex_ready_for_stage` (pull, at runner start, book grain only) |
| resume / idempotency | `step.done(ctx)`: output on disk + `take_currency.is_current` (bytes of prompt and pictures) |
| GPU mutual exclusion | `StageContext.wait_free()` polling `comfy.busy()` every 20 s, cap 7200 s; `GPU = True` on the step |
| brake | `RENDER_HOLD` file; `run_steps` refuses a GPU step while it exists |
| terminals | `judged_gate.clear` -> `keep_best | still | flag | defer`; `Deferred` / `Escalation` exceptions -> `deferred` / `escalated` events |
| attempts of a sub-unit | `takes/r2v/attempts/T10_fail2.mp4`; `--retake=10,19 --why=move_type: cut, jump` in `timing.jsonl` notes |
| GPU seconds | `timing.jsonl` rows `{stage, started, ended, seconds, ok, note}` with CONTENDED detection |
| paid tokens | `usage` table (`codex_id, stage, step_id, tier, model, tokens, cost_usd`) — **no `unit` column** |
| rungs taken | `learnings.jsonl` `Learning(step, substep, gate, measured, threshold, action, attempt, seconds, terminal)` |
| non-idempotent POST | `comfy.submit` re-checks `/queue` by `save_prefix` after a timeout (ep04: take 11 queued 7x) |

So the execution model is three new tables and one loop over what is there — not a scheduler.
## 1. Pull vs push vs scheduler-materialized: **materialize, then pull**

Three ways a row appears for the next department when a unit finishes:

- **Push** (the finishing runner inserts downstream rows): wrong grain. `refs/04` completing for
  a book should yield N episode rows from `series.json`, not one; `episode/01 bind` can order a
  `refs` row back upstream (a new entity). Push makes every runner know its consumers.
- **Pull** (what `refs.ready()` does): correct but invisible. A row that does not exist cannot be
  shown as `blocked` or `ready`, cannot be held, cannot carry a priority. The owner said the
  table should *drive* the department; a pulled row is driven by the runner's argv.
- **Materialize** (a tick reads `stages.yaml` + the slate and upserts one row per `(stage, unit)`
  with `state = blocked|ready`; a worker pulls the top ready row): rows exist before work, so
  the UI shows the whole season as a grid the day the book is registered; `requires` edges are
  evaluated in one place; the tick is idempotent (`INSERT OR IGNORE` on the unique key).

Recommendation: **materialize on a tick, pull by one worker**. The tick is a function, not a
daemon — the worker calls it before every claim, the UI on load. Unit enumerators per stage:
`analysis/screenplay/trailer` -> `main`; `refs` -> `(book, style)` plus just-in-time rows
ordered by `episode/01`; `episode` -> the slate's ordered unit list; `publish` -> every
`deliver` completion `(sha8@platform)`. One GPU means one worker; a CPU-only lane (plan,
prompts, timeline) is a later column (`lane`, derived from the steps carrying `GPU = True`).

## 2. Claiming, leases, crash recovery, the brake

```sql
CREATE TABLE orders (               -- one row per unit of one department
  id           INTEGER PRIMARY KEY,
  stage        TEXT NOT NULL,       -- registry stage = the department
  codex_id     TEXT NOT NULL REFERENCES codex(id),
  unit         TEXT NOT NULL,       -- 'ep12', 'main', '<sha8>@youtube'
  state        TEXT NOT NULL,       -- see §4
  priority     INTEGER NOT NULL DEFAULT 100,   -- lower first
  sequence     INTEGER,             -- position in the slate (ep12 < ep13)
  lane         TEXT NOT NULL DEFAULT 'gpu',
  input_sha8   TEXT,                -- hash of the upstream artefacts requires resolves to
  inputs_json  TEXT,                -- [{stage, step, relpath, sha8}] the contract in
  outputs_json TEXT,                -- [{relpath, sha8, verdict_relpath}] the contract out
  step_reached TEXT,                -- '09'
  progress_json TEXT,               -- {"done":18,"total":25,"item":"T10","attempt":3}
  attempts     INTEGER NOT NULL DEFAULT 0,      -- runner runs on this row
  flags        INTEGER NOT NULL DEFAULT 0,      -- audit rows from terminal rungs
  claimed_by   TEXT, lease_until TEXT, heartbeat_at TEXT,
  hold_reason  TEXT,                -- per-row hold; NULL = none
  retry_after  TEXT,                -- scheduler-owned backoff; never sleep in a worker
  gpu_seconds  REAL NOT NULL DEFAULT 0, llm_usd REAL, llm_tokens INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  UNIQUE (stage, codex_id, unit)
);
CREATE INDEX ix_orders_ready ON orders (state, lane, priority, sequence);
CREATE INDEX ix_orders_updated ON orders (updated_at);
```

**Claim** is one statement, which SQLite's single writer serialises (Python 3.12 ships SQLite
with `RETURNING`):

```sql
UPDATE orders SET state='running', claimed_by=?, lease_until=?, heartbeat_at=?, attempts=attempts+1
 WHERE id = (SELECT id FROM orders
             WHERE lane=? AND hold_reason IS NULL AND (retry_after IS NULL OR retry_after < ?)
               AND (state='ready' OR (state='running' AND lease_until < ?))
             ORDER BY priority, sequence, unit LIMIT 1)
RETURNING *;
```

**Lease**: 15 minutes, renewed by every write the runner already makes (`tracker.event`,
`episode_clock.stamp`, `ctx.learn`, the 20 s `wait_free` poll) routed through one
`ctx.beat(progress=...)`. An H3 take is ~11 min between writes, so 15 min is the floor.

**Crash**: a lease that expires is not requeued blindly. The tick moves the row to **`stale`**
and the *sweep* decides: (a) `comfy.busy()` and `already_queued(save_prefix)` say the crashed
run's job is still on the engine -> stay `stale`, wait; (b) the engine is idle -> `ready`, with
`retry_after = now + 60 s`. Resume then costs nothing: `step.done(ctx)` and `take_currency`
skip every artefact whose bytes are current. That is **at-least-once claims with
content-addressed idempotency**, which is as close to exactly-once as a GPU step gets; a true
exactly-once claim would need the engine to be transactional and it is not (ep04's seven
queued takes are the proof). Paid tokens: local tiers are $0 and the plan ladder is the only
LLM spender in the line; a paid tier gets the reserve->commit ledger from `docs/stepwise` only
when the `shorts` line registers (credits). Not before.

**`RENDER_HOLD` stays a file.** It is the one brake that works from another shell, another
session, another repo, while a runner is mid-take; a row cannot be written from anywhere in one
second. The tick mirrors it: `studio` singleton row `(hold_reason, hold_since)` for the UI and
the claim query refuses every GPU-lane row while it is set. The UI's Hold button writes the
file and never only the row; deleting the file lifts it (unchanged owner rule, 2026-09-12).
Per-book hold = `codex.hold_reason`; per-row hold = `orders.hold_reason`. Three scopes, one
column name.

## 3. Idempotency keys and sub-units

- **Work order key** = `(stage, codex_id, unit)`. A re-run of a completed row with the same
  `input_sha8` is a no-op at every step (existing `done(ctx)`); a changed `input_sha8` (a new
  refs verdict, a re-planned cell) flips the row to `ready` with `step_reached` cleared to the
  first step whose output is no longer current — the runner already computes that per step, the
  row only records it.
- **Sub-units are `items`, never orders.** A take, a grid, a panel, a line, a sheet:

```sql
CREATE TABLE items (
  order_id INTEGER NOT NULL REFERENCES orders(id),
  kind TEXT NOT NULL,   -- take | grid | panel | line | sheet | version
  key  TEXT NOT NULL,   -- 'T10', 'hill_2x1', 'shot_04', 'L07'
  state TEXT NOT NULL,  -- pending | rendering | judging | passed | flagged | still | failed
  attempt INTEGER NOT NULL DEFAULT 0, rung TEXT,         -- 3, 'move_type'
  artefact TEXT, verdict_sha8 TEXT,                       -- relpath under the book; eye sha8
  seconds REAL NOT NULL DEFAULT 0, faults_json TEXT, updated_at TEXT NOT NULL,
  PRIMARY KEY (order_id, kind, key)
);
```

`attempts/T10_fail1.mp4`, `T10_fail2.mp4` stay on disk as the truth (the displaced attempt is
evidence the retrospect reads); the item row is the index: `attempt = 3, rung = 'move_type'`.
A re-shoot of one take is `UPDATE items` plus a `learnings` row, never a new order and never
a new `attempts` count on the order (that counts runner runs). Deadline's job/task split and
Airflow's `map_index`, with a string key (Dagster's `mapping_key`) because take numbering has
holes (`shots.json` is indexed by first shot).

- **Attempt history of the order** = the existing `events` rows joined on `run_id`; no new table.

## 4. States, ladders and terminals

Order states (nine, each a verb the UI can name):

```
blocked  requires unmet (tick keeps re-evaluating)
ready    claimable
running  claimed; lease live
stale    lease expired; sweep decides
held     hold_reason set (row, book or studio); never claimed
escalated  a human gate (gates.yaml state: human) parked it; the verdict file lifts it
deferred a judge's battery terminal (plan.deferred.json exists); NOT auto-claimable (§ uncertain 3)
failed   crash or REFUSED exit; retry_after set, attempts capped at 3, then stays failed
done     every step completed; flags > 0 means done-with-audit-rows, not a separate state
```

`upstream_failed` (Airflow) is not needed: a `blocked` row shows its upstream's state through
the join; `skipped` is an event, not an order state. Ladders map without new machinery: every rung taken is already a `Learning`; the runner writes
the same fact to `items` (`attempt`, `rung`, `faults_json`) and bumps `orders.progress_json`.
Terminals: `keep_best`/`still`/`flag` -> the item `flagged`/`still`, `orders.flags += 1` (the
audit row `judged_gate.audited` already writes); `defer` -> order `deferred`, `outputs_json`
points at the `.deferred.json` draft (ep13: 5 battery passes kept, resumable). What the UI
needs from a ladder, per row: `step_reached`, `attempts`, `flags`, the last `Learning`
(`gate`, `action`, `measured`, `threshold`), and per item the rung and faults.

## 5. Cost and time per row

- `usage` gains `unit` and `order_id` (it has `codex_id, stage, step_id` only; per-unit LLM cost
  is unanswerable today). `llm.set_spend_context` carries the row id.
- `episode_clock.stamp` keeps writing `timing.jsonl` and *also* inserts a `timings` row
  `(order_id, item_key, stage_name, started, ended, seconds, ok, note, contended)`; the UI never
  parses JSONL. GPU seconds = `SUM(seconds)` over rows of GPU steps; wall = last end - first
  start; `contended` is the existing overlap test.
- Denormalised on the order at every step end: `gpu_seconds`, `llm_usd` (NULL if any call was
  unpriced — never zero, `spend.py`'s rule), `llm_tokens`. Per department = `SUM` by `stage`;
  per book = `SUM` by `codex_id`; a view `v_department` gives the department table its footer.

## 6. Priorities and ordering

`ORDER BY priority, sequence, unit` inside the claim. `sequence` is the slate position (ep12
before ep13 is ordering, not a dependency; one GPU serialises anyway). A book before another =
`codex.priority` folded in by the tick (`priority = codex.priority * 1000 + stage_rank`). A hold
on a book = `codex.hold_reason`. A manual bump = `UPDATE orders SET priority = 0` from a UI
button; a running row is never pre-empted (`comfy.interrupt` is unreliable — run 18's
eleven-hour VLM read — and a take is only ~4 GPU minutes).

## 7. Long-running steps and progress

Two layers: `items` is the truth of a shoot (25 rows, one per take); `orders.progress_json` is
the one-write summary updated at each item boundary (`{"done":18,"total":25,"item":"T10",
"attempt":3,"rung":"move_type"}`) so the list page reads one row per order. Polling: htmx every
2 s (`DESIGN.md`) against `GET /orders?since=<updated_at>` on `ix_orders_updated`; a dozen rows,
no joins. The drill-down is an htmx table over `items WHERE order_id = ?` (Dagster's partition
bar -> table, not 25 nodes). The step reports through `ctx.beat(progress=...)`; the runner owns
the connection, so departments still import neither Strands nor the ledger (invariant).

## 8. Reference designs — take, skip

| system | take | skip |
|---|---|---|
| Dagster | partition = `unit`; a materialization = our `completed` event carrying the artefact sha; the partition status bar | the asset-reconciliation daemon and sensors; the tick is enough |
| Prefect | task run = `items`; `Paused`/`Suspended` releases resources = `escalated`/`deferred` never hold the lease | the flow-run state graph (14 states) |
| Temporal | event history = `events`; heartbeat on long activities = `ctx.beat` | replay determinism; nothing here replays code |
| Deadline | job/task tables, task progress %, *requeue task*, *suspend job*, a limit of 1 on the GPU pool | slaves, pools, plugins |
| Airflow | `task_instance` current-row + history; `map_index`; `next_retry_at` owned by the scheduler | the scheduler and executors |

The **simplest thing that works** for one maintainer, SQLite and htmx: three tables (`orders`,
`items`, `timings`) beside `codex`/`events`/`usage`; one worker loop (tick, claim, `run_steps`,
settle); the UI writes three things only — hold (the file), priority, requeue. No daemon.

## 9. The worker loop

```python
def work(conn, lane="gpu", once=False):                    # uv run python studio.py work
    while True:
        tick(conn)                                         # materialize rows; requires -> blocked|ready; mirror RENDER_HOLD; sweep stale
        order = claim(conn, lane, worker_id(), lease=15 * 60)
        if order is None:
            if once: return 0
            time.sleep(20); continue                       # the only sleep, and it is the scheduler's
        ctx = context_for(order)                           # EpisodeContext/RefsContext from registry unit grammar
        ctx.beat = lambda **p: heartbeat(conn, order.id, lease=15 * 60, **p)   # renews lease + progress_json
        try:
            outcome = step_runner.run_steps(ctx, step_runner.load_steps(order.stage))   # unchanged
        except SystemExit as held:                         # HELD or REFUSED
            settle(conn, order, "held" if ctx.held() else "failed", str(held)); continue
        except Exception as exc:
            settle(conn, order, "failed", repr(exc), retry_after=backoff(order.attempts)); continue
        settle(conn, order, {"completed": "done", "escalated": "escalated", "deferred": "deferred"}[outcome])
        if once: return 0

def settle(conn, order, state, note="", retry_after=None):
    conn.execute("UPDATE orders SET state=?, claimed_by=NULL, lease_until=NULL, retry_after=?, "
                 "outputs_json=?, gpu_seconds=?, llm_usd=?, updated_at=? WHERE id=?",
                 (state, retry_after, outputs_of(order), gpu_of(order), usd_of(order), now(), order.id))
    conn.commit()
```

`tick` is four statements: per stage in file order, `INSERT OR IGNORE` each enumerated unit;
`UPDATE ... SET state='ready' WHERE state='blocked' AND every requires row is done`; the hold
mirror; the stale sweep.

## 10. Worked example (the two rows the owner would see tonight)

```
orders
id stage    unit  state    step priority seq attempts flags progress                                  gpu_s   llm_usd
41 episode  ep12  running  09   100      12  3        2     {"done":18,"total":25,"item":"T10",       9 812   0.00
                                                              "attempt":3,"rung":"move_type"}
42 episode  ep13  deferred 02   100      13  6        0     {"passes":5,"draft":"episodes/ep13/          0   NULL (local tier, unpriced)
                                                              plan.deferred.json"}
43 publish  <sha8>@youtube blocked -  100  12  0      0     requires episode/12 -> row 41 running          0   -

items (order 41, kind = take)                      timings (order 41, tail)
key state     attempt rung          seconds          stage    seconds ok note                         contended
T09 passed    1       -             229              takes    1 965   1  --retake=0,2,10,11,17,19    0
T10 rendering 3       move_type     -                          --why=seed: content, cut, ...
T11 passed    2       seed          458              take_dq    315   1  0 2 10 11 17 19 --attempts  0
T16 flagged   3       shorter_take  690              takes      771   1  --retake=10,19 --why=move_type 0
T19 passed    3       move_type     ...              takes      467   1  --retake=16 --why=shorter_take 0
```

Row 41 is `running` with a live lease (`claimed_by = host:pid:run_id`, `heartbeat_at` within
20 s); the list page shows `shoot 18/25 · T10 attempt 3 (move_type)`; the drill-down lists 25
items. Row 42 has `plan.deferred.json` (best draft, `passes: 5`) as its output and is not
claimable until bumped; the six PLAN ladders in `learnings.jsonl` are its attempt history via
`events.run_id`. Row 43 exists already, blocked on 41 — the season reads as a grid.

## 11. Three things I am unsure of (for the debate)

1. **Who writes `items` — the step or a disk scanner?** The invariant says departments hand
   back typed artefacts and import nothing. `ctx.beat()` keeps that letter, but the take loop
   lives in `takes_r2v.py` under a subprocess (`ctx.run_script`), which cannot reach `ctx`. The
   alternative is a scanner the runner runs between steps (glob `T??.mp4`, `.dq.json`,
   `attempts/`, the eye) — truth stays on disk, but progress inside the slow step is then only
   as fresh as the last file written (every ~4 min for a take; fine for the UI, useless for a
   per-frame bar). I lean scanner-first, `beat` when the render loop moves in-process.
2. **`stale` -> `ready` automatically, or by hand?** Automatic after the engine-idle check is
   what a farm does; but a crash mid-round can leave the `ComfyUI/input` staging and a half
   `graph.json` (commit 82c291c: "a graph newer than its video proves nothing"), and
   `take_currency` handles that case today. I recommend automatic with `attempts <= 3`, and
   I would like the codebase expert to confirm every GPU step's `done()` is safe on a
   half-written artefact.
3. **Is `deferred` auto-retried?** The next pass "authors again" by design, but ep13 burned
   six ladders (about 2.5 h of local LLM) producing the same battery refusal. A deferred row
   that is claimable again the moment the worker is idle would burn the night. I recommend
   `deferred` waits for a bump (or a changed `input_sha8`: a new brief, a rule edit), and the
   debate should decide whether a retry cap on the same `input_sha8` belongs in the ladder or
   in the table.

Smaller open point: a second CPU-lane worker means two writers on one SQLite file; WAL mode and
`busy_timeout` suffice, but the claim must key on `lane` so a CPU worker never takes a `gpu` row.
