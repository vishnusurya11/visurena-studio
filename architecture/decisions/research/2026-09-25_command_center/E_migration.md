# E — Codebase integrator: the migration path to a table-driven studio

Read-only research, 2026-09-25. Every claim below was checked against the tree on
`master` at 82c291c and the live `db/visurena_studio.db` (30 codex rows, 24 066 events,
`usage` table). Paths are repo-relative; the repo is
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio`.

## 0. The brick

The studio already has its brick: **`stages.yaml` is the org chart, `events` is the
ledger, `done()` on disk is the truth of a step.** Everything the owner asks for — a
table per department, standard inputs and outputs, a monitor — is a *projection* of those
three, not a fourth source of truth. The migration therefore adds ONE derived table and
ONE registry key, and touches the one door every event already walks through. Nothing
existing is renamed, moved or re-keyed; every runner still runs exactly as typed today.

## 1. Inventory: what is already a department table in disguise

| today | where | what it records | what it lacks |
|---|---|---|---|
| `events` | `studio/db.py` (`add_event`, `unit_status`) | per (codex, stage, step, unit): started/completed/failed/skipped/escalated/deferred, run_id, 200-char detail | no **row per unit**: state is a GROUP BY at read time; no priority, no hold, no redo, no cost, no artefact list |
| `codex.<stage>_status/_started_at/_updated_at` | `db.mark_stage` | the book-level trio per stage | book grain only: WotW `episode_status='running'` says nothing about which of 13 episodes |
| `done()` | every `scripts/<stage>/step_NN_*.py` | the output on disk, currency-checked (sha8-bound verdicts, mtime vs inputs) | only answerable by importing the module with a context; not queryable |
| verdict files | `plan.verdict.json`, `plan.deferred.json`, `refs/verdict.json`, `storyboard/eye_<sha8>.json`, `takes/r2v/eye_<sha8>.json`, `review/eye_<sha8>.json`, `qc_r2v.json` | gate outcomes bound to a sha8 | scattered; the deferred file carries `passes` (attempt count) nowhere else |
| `timing.jsonl` | `studio/episode_clock.py` | wall seconds per stage run, retries counted, `ok`, note | episode only; not in the DB; no stage name matches a registry step id (`takes`, not `09`) |
| `usage` | `studio/spend.py` via `llm._record_spend` | tokens + USD per (codex, stage, step) | **no `unit` column**; `spend_context` takes no unit; `episode.py`/`refs.py` never open a spend context |
| `learnings.jsonl` | `studio/learnings.py` | one row per ladder rung (gate, measured, threshold, action, terminal) | per unit folder; the attempt count of a gate lives here |
| `uploads.jsonl` | `studio/youtube_publish.record` | video_id, privacy, sha8 per upload | the only record of *published*; per book, not queryable |
| `audit/rows.jsonl` | `studio/audit_rows.py` | one row per terminal rung | read by `scripts/audit/sheet.py` only |
| `RENDER_HOLD` | `studio/approval.HOLD`, `StageContext.held()` | studio-wide brake | no scope (book/unit), no reason field beyond free text, no lift record |
| ComfyUI `/queue` | `studio/comfy.busy` | the one-GPU guard | not a table and should not be: it is the engine's truth |

Missing, in one sentence: **a row that says where a unit stands, what it was asked to
produce, what it produced, what it cost, and whether anyone is holding it.**

## 2. The smallest schema change: one table, one view per department

Real per-department tables generated from `stages.yaml` were rejected: five DDLs, five
migrations, a UNION for every cross-department query, and `events` — which already keys
on `stage` — would have to split too. A **VIEW per stage** over one table gives the owner
"each department has its own table" in the UI and in `sqlite3`, from one DDL, and the
registry still decides which departments exist (`db.STAGES` already does this for the
codex trio).

```sql
CREATE TABLE IF NOT EXISTS work_orders (
  id           INTEGER PRIMARY KEY,
  codex_id     TEXT NOT NULL REFERENCES codex(id),
  stage        TEXT NOT NULL,
  unit         TEXT NOT NULL DEFAULT 'book',   -- 'ep04', 'main', 'book'
  number       INTEGER,                         -- the runner's <n>, when the unit has one
  state        TEXT NOT NULL CHECK (state IN ('blocked','queued','running','escalated',
                 'deferred','failed','held','done','published','grandfathered')),
  step_id      TEXT,                            -- the step the state is about
  priority     INTEGER NOT NULL DEFAULT 0,      -- higher first
  attempts     INTEGER NOT NULL DEFAULT 0,      -- `started` events on this unit
  redo         TEXT,                            -- JSON list of step ids to run although done()
  blocked_on   TEXT,                            -- 'refs/04' while a requirement is not done
  requested_by TEXT, requested_at TEXT, started_at TEXT, updated_at TEXT NOT NULL, finished_at TEXT,
  run_id       TEXT,                            -- the live run, joins logs/<codex>/<stage>/<run_id>.log
  inputs       TEXT,                            -- JSON {name: book-relative path}, from the registry
  outputs      TEXT,                            -- JSON {step_id: [book-relative paths that exist]}
  cost_usd     REAL NOT NULL DEFAULT 0.0,
  gpu_seconds  REAL NOT NULL DEFAULT 0.0,
  source       TEXT NOT NULL DEFAULT 'run',     -- 'run' | 'queue' | 'backfill'
  note         TEXT,
  UNIQUE (codex_id, stage, unit)
);
CREATE INDEX IF NOT EXISTS ix_work_orders_queue ON work_orders (stage, state, priority DESC, requested_at);

CREATE TABLE IF NOT EXISTS holds (
  id        INTEGER PRIMARY KEY,
  scope     TEXT NOT NULL CHECK (scope IN ('studio','book','unit')),
  codex_id  TEXT, stage TEXT, unit TEXT,
  reason    TEXT NOT NULL, held_by TEXT, held_at TEXT NOT NULL, lifted_at TEXT
);
-- one per registered stage, generated in _migrate_work_orders from registry.stage_names():
CREATE VIEW IF NOT EXISTS episode_orders AS SELECT * FROM work_orders WHERE stage = 'episode';
```

The migration, in `studio/db.py` next to `_migrate_events` and called from `_migrate`:

```python
def _migrate_work_orders(conn) -> None:
    """The unit table and the holds table, and one view per registered stage
    (idempotent: a present table is left alone, a new stage gets its view)."""
    conn.executescript(_WORK_ORDERS_DDL)
    for stage in STAGES:
        conn.execute(f"CREATE VIEW IF NOT EXISTS {stage}_orders AS"
                     f" SELECT * FROM work_orders WHERE stage = '{stage}'")
```

`STAGES` is already `tuple(registry.stage_names())`, so a stage added to `stages.yaml`
gets its view the next time `init_db` runs — the same rule the codex trio follows.
Tested the way `test_init_db_brings_an_old_db_forward_without_losing_a_row` is: build a
DB under today's DDL, `init_db`, assert the table, the views and every old event.

**Standard inputs and outputs live in the registry, not the table.** Add two optional
keys per step in `stages.yaml`, the way `unit:` and `requires:` were added on 2026-09-24:

```yaml
      - id: "10"
        name: edit
        script: step_10_edit
        in:  [episodes/{unit}/placed.json, episodes/{unit}/takes/r2v/T??.mp4, title/{unit}.mp4]
        out: [episodes/{unit}/cut/master_r2v.mp4]
```

`registry.inputs_of(stage, step_id)` / `outputs_of(...)` return the globs with `{unit}`
filled. The runner records which `out` paths exist on `completed` into `work_orders.outputs`;
the UI links them; the backfill derives step state from them. `done()` stays the
authority on *currency* (a sha8-bound verdict, a master newer than its takes); `out:` is
the *declaration* the department is held to. A guard test asserts every `out:` of a
step is a path `done()` reads (grep the module for the file's basename), so the two
cannot drift.

## 3. Backfill from disk

`scripts/audit/backfill_work_orders.py <codex_id | all> [--write]` (dry-run prints the
derived rows; `--write` upserts with `source='backfill'` and **never touches a row whose
`run_id` is set** — a live run owns its row). Timestamps come from `events` where a unit
has any (WotW ep01/ep12/ep13, refs main, every analysis/screenplay/trailer book), else
from file mtimes, marked `note='ts:mtime'`.

Derivation, in order; the first matching rule sets the unit's state:

| stage | rule | state |
|---|---|---|
| episode | `uploads.jsonl` has a row for the number with a `video_id` | `published` (step 12) |
| episode | `cut/master_r2v.mp4` + `qc_r2v.json` with `passed` and `sha8 == sha8(master)` (`youtube_publish.deliverable`) | `done` (step 12 when `manifest.json`, else 11) |
| episode | latest event is `deferred` or `plan.deferred.json` newer than `plan.json` | `deferred` (02) |
| episode | `plan.json` + `placed.json` and no `plan.verdict.json` (`step_02_plan.grandfathered`) with no master | `grandfathered` (02) |
| episode | `plan.json` only | `queued` (01), attempts from `plan.iterN.json` count |
| refs | `refs/verdict.json` with `pack_sha8 == sha8(pack.jsonl)` (`refs_verdict.current`) | `done` (04) |
| refs | `refs/refs.json` and no `pack.jsonl` | `grandfathered` (legacy bible) |
| analysis | event `completed` on step 06 (`codex_pending_stage` logic) | `done` |
| screenplay | event `completed` on 05; else latest step completed | `done` / `running`-turned-`failed` if the last event is `failed` |
| trailer | event `completed` on 10 | `done` |

Per-step `outputs` are filled from `out:` globs that exist; per-step timestamps from the
last `completed` event of that step, else the newest file's mtime.

**Which of the existing episodes backfill cleanly (checked on disk 2026-09-25):**

- WotW ep01–ep11: **clean, `published`** — every one has a public row in `uploads.jsonl`,
  `master_r2v.mp4`, `qc_r2v.json`. Their middle steps are `grandfathered` (no
  `plan.verdict.json`, no `storyboard/eye_*.json`; ep01–ep04 predate `storyboard/`
  altogether). Only ep01 has step events (a 12-step "skipped" pass on 2026-09-25).
- WotW ep12: **ambiguous** — `plan.verdict.json` is hand-signed (`signed_by` absent,
  note "Re-signed by Claude"), the events say step 11 `failed` at 14:47 then step 09
  `started` at 22:57 (a live run); the backfill must skip it (`run_id` rule).
- WotW ep13: **clean, `deferred`** — five `deferred` events, `plan.deferred.json`
  `passes: 5`; `attempts` = 5 straight from the events.
- Scarlet ep03–ep14: **clean, `published`** — `qc_r2v.json` + `uploads.jsonl` rows; zero
  events, so every timestamp is an mtime.
- Scarlet ep01, ep02: **ambiguous** — published (`video_id` present) but no `qc_r2v.json`
  (`findings.json`/`dq_report.md` era); `deliverable()` refuses. Rule 1 still says
  `published`; the qc step stays `unknown`, noted.
- Scarlet `ep01_short`: outside the `ep\d\d` grammar (`episode_run.unit_of`); listed,
  not a row.
- Refs: WotW `main` is `done` (judge:look@1, pack_sha8 4b0a9ecd); Scarlet has
  `refs.json` and no `pack.jsonl` → `grandfathered`.
- Analysis: all 30 books `done` from events; screenplay: 29 have events, Scarlet's trio
  says `running` (stopped at `RUN_UNTIL_STEP`) — the backfill records what the events
  say and the note names the gap.

So 25 of the 27 episode folders derive without a judgement call; two need a note, one is live.

## 4. Runners write the rows with one change

Every runner already goes through **`db.add_event`** — `Tracker.event` (episode, refs,
trailer via `StageContext`), and `analysis.py`/`screenplay.py` call it directly. So the
upsert lives *inside* `add_event`, and no runner changes:

```python
def add_event(conn, codex_id, stage, step_id, event, *, run_id=None, detail=None, unit=None):
    ...INSERT INTO events...
    upsert_work_order(conn, codex_id, stage, unit or "book", step_id, event, run_id, event_ts)
    conn.commit()
```

`upsert_work_order` (new, ~20 lines): `INSERT ... ON CONFLICT(codex_id, stage, unit) DO
UPDATE`; the event decides the state — `started`→`running` (+1 attempts, set `started_at`
once, `run_id`), `skipped`→`running` (step advances), `completed`→`running`, or `done` when
`step_id == registry.steps(stage)[-1]["id"]`, `failed`→`failed`, `escalated`/`deferred`→
the word. A `done` transition also flips every `blocked` row whose `blocked_on ==
f"{stage}/{step_id}"` to `queued` (this is `requires:` becoming live).

| what | where | lines |
|---|---|---|
| `_WORK_ORDERS_DDL`, `_migrate_work_orders` | `studio/db.py` | ~30 |
| `upsert_work_order`, `STATE_OF_EVENT` map | `studio/db.py` | ~25 |
| `add_event` calls the upsert | `studio/db.py` | +2 |
| `outputs` on `completed`: `registry.outputs_of` globbed under `ctx.book_dir` | `studio/step_runner.run_steps` (the `completed` line) → `db.record_outputs` | ~12 |
| `redo`: `if _done(step, ctx) and step.STEP_ID not in ctx.redo` | `studio/step_runner.run_steps`, `StageContext.redo = ()` | +3 |
| `held()` reads the file **or** an unlifted `holds` row for the studio, the book or the unit | `studio/stage_run.StageContext.held` → `db.active_hold` | ~12 |
| `usage.unit` column + `spend_context(..., unit=None)`; `_record_spend` passes it; the upsert adds `cost_usd` | `studio/spend.py` (migration +4), `studio/llm.py` (+3) | ~10 |
| `gpu_seconds` = sum of `episode_clock.rows()` since `started_at`, written once at unit end | `episode.py.process` after `run_steps` | ~6 |
| `attempts` per gate stays in `learnings.jsonl`; the UI reads it by path | — | 0 |

Artefact paths are book-relative in `outputs` (the invariant "never store an absolute
path" holds: `episode_home.relative`). Total: about 110 lines of production code across
`db.py`, `spend.py`, `llm.py`, `step_runner.py`, `stage_run.py`, `episode.py`.

## 5. How the table drives a department without breaking `episode.py <book> <n>`

- **Explicit invocation is unchanged.** `uv run python episode.py <book> 4` builds the
  context, `run_steps` emits `started`, `add_event` upserts the row (`source='run'`).
  Same for `refs.py <book>`, `trailer.py <book>`, and every `step_NN_*.py <book> <n>`
  through `step_cli.main` (it calls the same `run_steps`).
- **`queue`** — a new leader-level command, `uv run python studio_cli.py queue episode
  <book> 14 [--priority=5] [--redo=09,10] [--note=...]` (`studio/work_orders.py`, ~40
  lines): for each `registry.requires_of(stage)` it asks the table whether that
  `stage/step` row is `done`; all yes → `queued`, else `blocked` with `blocked_on`. It
  writes `inputs` from `in:` globs. A row that already exists is updated, never
  duplicated (the UNIQUE key).
- **Draining.** `episode.py` with no unit today runs "every epNN with a plan, ascending"
  (`episode.units`). Commit 7 makes the no-argument form read
  `db.next_queued(conn, "episode")` (priority DESC, requested_at ASC) and process rows one
  at a time; `episode.py <book>` keeps the folder scan for one release, then follows.
  `refs.py`/`trailer.py`/`screenplay.py` already have a `ready()`/`scan_once()` shape —
  they swap the events query for the table query and gain nothing else. `analysis.py`'s
  `POLL_SECONDS` is the daemon shape a worker loop grows from later; **the UI process
  never runs a step** (it writes rows; a runner drains them).
- **RENDER_HOLD becomes a `holds` row with `scope='studio'`, and the file stays.** The
  file is the owner's one-second brake from anywhere (owner 2026-09-12) and needs no
  process to honour it; `held()` reads both, the UI's *Hold* button writes the row *and*
  the file for the studio scope, and lifting deletes both. Book- and unit-scope holds are
  rows only. `approval.require` keeps reading the file alone (paid pictures).
- **The ComfyUI queue guard stays where it is** (`comfy.busy`, read before every GPU
  script). The table does not lease the GPU: two runners could both read a stale row,
  while the engine's `/queue` cannot lie. The UI shows `queue_counts()` live beside the
  running row and names which row's `run_id` is on the GPU (the row with
  `state='running'` and `GPU` on its current step).

## 6. Serving the UI

`starlette 1.6.0`, `uvicorn 0.52.4`, `jinja2 3.1.6` and `httpx 0.28.1` import today, but
**none is in `pyproject.toml`** — all four arrive transitively through
`strands-agents → mcp` (`uv tree`). A strands bump could drop them silently. So the first
UI commit pins what is already resolved (no lock churn):

```
uv add starlette==1.6.0 uvicorn==0.52.4 jinja2==3.1.6
uv add --group dev httpx==0.28.1
uv sync --all-groups        # the uv-groups hazard: uv add strips music/voice groups
```

FastAPI is not needed: the pages are HTML tables and one JSON endpoint; pydantic
serialisation adds nothing over `json.dumps(dict(row))`. Adding FastAPI would be a new
framework for zero routes' worth of benefit; Starlette is the thing FastAPI wraps.

Layout — a runner sibling of `episode.py` plus a package, so the leader convention holds:

```
command_center.py                 uv run python command_center.py [--port=8765] [--db=...]
studio/command_center/app.py      make_app(conn, library=episode_home.LIBRARY) -> Starlette
studio/command_center/routes.py   / (every department, counts), /d/<stage> (its table),
                                  /u/<codex>/<stage>/<unit> (one row: steps, outputs,
                                  learnings, timing), /api/orders.json (polled every 10 s),
                                  POST /queue, /hold, /lift, /redo (form posts → studio/work_orders)
studio/command_center/templates/  Jinja2; the dossier's CSS (scripts/episode/dossier.CSS)
studio/command_center/files.py    the artefact route
```

Tests exercise routes with `starlette.testclient.TestClient(make_app(conn, library=tmp))`
— no server, no port, a tmp SQLite, a tmp library; `make_app` takes the connection and the
library root as arguments so nothing in a test touches `db/` or `library/`.

Artefacts under `library/` are served by `/lib/{codex}/{path:path}`:
`codex` must match `^\d{14}(_[a-z0-9-]+)?$` (`episode_home.book_dir` matches by prefix, so
an unanchored id would open another book); `target = (book / path).resolve()`;
refuse unless `target.is_relative_to(book.resolve())` and the suffix is in
`{.mp4,.wav,.png,.jpg,.json,.jsonl,.html,.md,.log}`; `FileResponse` with `Cache-Control:
no-store` (masters are overwritten by iteration). Test names: `a_path_that_climbs_out_of_the_book_is_refused`,
`a_codex_prefix_opens_only_its_own_book`. Bind `127.0.0.1` only.

## 7. Test plan and commit sequence

Tests, in this repo's sentence style (each pins one rule; ~24 new files):

- `test_a_finished_unit_is_one_row_in_its_departments_table.py`
- `test_an_old_db_gains_work_orders_and_a_view_per_stage_without_losing_an_event.py`
- `test_every_registered_stage_has_its_view.py`
- `test_a_started_event_makes_the_row_running_and_counts_an_attempt.py`
- `test_the_final_steps_completed_event_makes_the_row_done.py`
- `test_a_deferred_event_leaves_the_row_deferred_at_its_step.py`
- `test_a_done_requirement_unblocks_the_rows_waiting_on_it.py`
- `test_a_queued_unit_carries_its_inputs_from_the_registry.py`
- `test_a_completed_step_records_the_outputs_it_declared.py`
- `test_every_declared_output_is_a_path_its_step_reads.py` (the drift guard)
- `test_a_redo_step_runs_although_its_output_exists.py`
- `test_a_hold_row_stops_a_gpu_step_the_way_the_file_does.py`
- `test_a_lifted_hold_holds_nothing.py`
- `test_the_explicit_runner_call_still_runs_without_a_row.py`
- `test_the_runner_with_no_unit_drains_the_queue_in_priority_order.py`
- `test_spend_inside_a_unit_lands_on_its_row.py`
- `test_backfill_reads_a_published_episode_off_its_upload_ledger.py`
- `test_backfill_reads_a_deferred_episode_off_its_events.py`
- `test_backfill_never_overwrites_a_row_with_a_live_run.py`
- `test_backfill_marks_a_legacy_plan_grandfathered_not_done.py`
- `test_the_department_page_lists_only_its_own_rows.py`
- `test_the_unit_page_links_every_recorded_output.py`
- `test_a_path_that_climbs_out_of_the_book_is_refused.py`
- `test_a_queue_form_post_writes_the_row_the_cli_would.py`

Every test runs on a tmp DB and a tmp library; no ComfyUI, no model, no network.

Commits (each green, each ≤ 10 functions of 10–20 lines; architecture page updated where
the org chart changes):

1. `work_orders` + `holds` DDL, `_migrate_work_orders`, one view per stage; the migration test.
2. `upsert_work_order` inside `add_event`; state map; the four event tests. (Every runner writes rows from here on, untouched.)
3. `in:`/`out:` keys in `stages.yaml` for episode and refs; `registry.inputs_of/outputs_of`; the drift guard; `record_outputs` on `completed`.
4. `usage.unit` + `spend_context(unit=)`; `gpu_seconds` at unit end in `episode.py`.
5. `holds` in `StageContext.held()`; `redo` in `run_steps`; `studio/work_orders.queue/hold/lift/redo`; `studio_cli.py`.
6. `scripts/audit/backfill_work_orders.py`, dry-run first; the four backfill tests; then run `--write` on WotW and Scarlet and commit the printed derivation as `docs/audit/2026-09-2x_backfill.md`.
7. `episode.py` with no unit drains the queue; `refs.py`/`trailer.py` `ready()` read the table. **Architecture page: Current tab — "the desk" (the table) between the org chart and the runners; `architecture/plan/` tracker.**
8. Pin starlette/uvicorn/jinja2 (+httpx dev), `uv sync --all-groups`; `studio/command_center` read-only pages + `/api/orders.json`; `command_center.py`; TestClient tests.
9. Form posts (queue/hold/lift/redo) through `studio/work_orders`; the artefact route with its two refusals.
10. `architecture/README.md` tables, `docs/DECISIONS.md` line, republish the claude.ai copy of `index.html`.

## 8. Three doubts for the debate

1. **Is a derived table a second truth?** `work_orders.state` is written from events, but
   `done()` on disk can disagree with it (a hand-edited plan, a master deleted). The
   backfill and a `reconcile` command re-derive from disk; but if the UI shows the table
   and the runner believes the disk, the owner will one day watch a `done` row rerun. Rule
   to decide: the row is the *office's* truth (what was asked, what it cost, who holds it);
   the disk is the *department's* truth (what exists). The UI should show both and name
   the disagreement, never resolve it.
2. **`out:` in `stages.yaml` vs `done()` in the module.** Two declarations of one fact.
   The guard test keeps them from drifting, but the alternative — `step.OUTPUTS` on the
   module, read by the registry — keeps one file per step and no templating. I chose the
   registry because the owner reads `stages.yaml` and asked for standard inputs/outputs
   *per department*; the debate should weigh whether a person or the code reads it more.
3. **Who drains the queue?** This plan keeps the runners as the only executors and the
   UI as a row-writer: the owner still types `uv run python episode.py` (now with no
   unit). A worker loop (`analysis.py`'s `POLL_SECONDS` shape) is one commit away, but
   it is also the moment an unattended process starts a five-hour GPU job because a row
   said so. The `holds` row and `RENDER_HOLD` are the brakes; the debate should decide
   whether a `queued` row is an *instruction* or a *request* before anything drains it
   without a keypress.
