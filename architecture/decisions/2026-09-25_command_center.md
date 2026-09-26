# The Command Center: departments driven by their tables, and the board that shows them

**Status: DECIDED 2026-09-25 — the owner ruled "looks good"; building** (was PROPOSED the same day) (`architecture/index.html`, tab
*Command Center*). Five reports under `research/2026-09-25_command_center/` (A data model,
B execution model, C production office, D operations UI, E codebase migration); this file is
the chair's ruling over them. Tracker: `architecture/plan/2026-09-25_command_center_build.md`.

## The ask

> a general local ui i can use to monitor the progress on jobs .. also each department should
> have its own table .... and that should drive the departments ... come up with the data model
> for that .. how each department is driven .. we need to have standard inputs for departments
> and outputs

## The brick

**One WORK ORDER row per (book, department, unit).** Base case: a row is `queued` when every
row it `requires` (the registry's edge) is `done` and its declared inputs exist on disk.
Recursive rule: a runner claims the earliest queued row of its department, runs the
registry's steps for that unit, and the row's state is whatever the run's last event says;
the department's last step writes the unit's `manifest.json`, which is the next
department's declared input. Closure: every department's table is `stages.yaml` applied to
`work_orders` — a department that needs a column the row lacks is mis-cut. The disk stays
the truth of a step (`done(ctx)`); the events table stays the journal; the row is their
projection, written from one place, rebuildable from disk at any time.

## The debate, ruled

| point | positions | ruling |
|---|---|---|
| Grain of the row | A: one row per (unit, step). B, C, D, E: one row per (department, unit), sub-rows for detail | **Unit grain.** The owner asked for a department's table; a coordinator's row is a unit. A's per-step row survives as `work_steps` under the order (timing, attempt, verdict per step) — the unit page's chips, never the queue's grain. |
| "Each department its own table" | A, E: one table + a generated VIEW per department. A's doubt: a view holds no hand columns | **One `work_orders` table, one view per registered department** (`episode_orders`, `refs_orders`, …, generated from the registry the way the codex status columns are). The hand columns (priority, hold, redo, note) live on the row, so the view has them. A physical table per department loses: twelve DDLs drifting from the registry. |
| Where standard inputs/outputs are declared | A: `INPUTS`/`OUTPUTS` on the step module + a `UnitManifest`. C, E: `in:`/`out:` per step in `stages.yaml`. | **The registry declares** (`in:`/`out:` per step, `{unit}`-templated, book-relative globs) — one declaration, and the org chart is the source; a drift-guard test asserts every `out:` is a path its step's `done()` reads. **The manifest crosses the boundary**: a department's last step writes `manifest.json` (pydantic `UnitManifest`: inputs, outputs, verdicts, cost, steps); a `requires` is satisfied by the upstream manifest's row being `done`, never by a sentence. A's module constants lose (two declarations of one fact). |
| Push, pull or scheduler | all: materialize on a tick from `requires`, pull by one worker | **Tick + pull.** `studio.py tick` (also run in-process at the top of every runner) inserts rows from the registry and the slate, promotes `blocked → queued`, mirrors `RENDER_HOLD`, sweeps expired leases. Push loses (refs/04 fans out to N episodes; episode/01 orders refs back upstream). |
| Explicit invocation | E: must keep working | **Unchanged.** `uv run python episode.py <book> <n>` claims that one row. The no-unit form (`episode.py <book>`, and later `studio.py work`) drains queued rows in `priority, sequence` order. The UI never runs a step; it writes orders. |
| The GPU | A: a partial unique index; B: lease columns; E: keep the live ComfyUI read | **All three.** `claimed_by`/`lease_until` (15 min, renewed by the writes the runner already makes); `UNIQUE INDEX ON work_orders(gpu) WHERE gpu=1 AND state='running'` so a second GPU claim is an IntegrityError; `comfy.busy()` and the `RENDER_HOLD` file stay as they are (the file is the owner's one-second brake from any shell; the tick mirrors it into `holds`). |
| States | B: 9; A: 10 (+stale); C: 11 coordinator words; D: 11 glyphs | **Nine stored states**: `blocked, queued, running, stale, held, deferred, escalated, failed, done`. `flagged` is a count (`flags`, from audit rows) on a done row, not a state; `published` is the publish department's own row; `grandfathered` is `source='backfill'` with no verdict. C's words are the UI legend over these; D's glyphs and the one-glance colour rule stand (red = a developer, black = the owner, amber = nobody now, purple = the next pass). |
| Sub-units (takes, panels) | B: `items` rows; A: artefacts + learnings; D: a progress column | **A `progress` column the runner writes** (`18/25 · T10 attempt 3 move_type`) in v1; `items` rows in v2 when the take loop stops being a subprocess. Nothing globs the disk on a poll. |
| Deferred units | B: wait for a bump or a changed input | **Wait.** Episode 13 burned six identical ladders unattended. A deferred row is resumed only by an order (`retry`) or a changed `input_sha8`, and the resume EDITS the kept draft (`Desk.resume`). |
| Owner actions | D: an `orders` table; C: `redo.jsonl` | **One writer: `orders`** (`hold, lift, redo, bump, retry, requeue`, with a note and a `taken_by_run`). The runners take orders at the top of each loop; a redo's note also goes to the casebook through `scripts/audit/note.py`. A second redo on the same class is a bench case, not a third render (C). |
| Events vs rows | E's doubt: a second truth | **Events stay the journal; the row is upserted inside `db.add_event`** (one place, zero runner edits). `studio.py verify` diffs rows against disk and marks `stale`; it never auto-resolves. |
| UI stack | D: FastAPI; E: Starlette (installed, transitive) | **FastAPI + Jinja2 + htmx**, pinned with `==` (`uv add`, then `uv sync --all-groups`), port 8700, `uv run python command_center.py`. Read-only SQLite from the web process, one short read per request; artefacts served from `library/` behind a resolved-path check and a suffix allowlist; tests use `TestClient` in-process and never spawn a server. |
| The org-chart page | D: keep it, link it | `architecture/index.html` stays the self-contained document, served at `/org`; the Command Center copies its tokens (test-enforced). |

## The data model

```sql
-- the department table: one row per (book, department, unit)
CREATE TABLE IF NOT EXISTS work_orders (
  id           INTEGER PRIMARY KEY,
  codex_id     TEXT NOT NULL REFERENCES codex(id),
  stage        TEXT NOT NULL,                        -- a key of stages.yaml
  unit         TEXT NOT NULL DEFAULT 'book',         -- ep04 | main | feature | <sha8>@youtube
  number       INTEGER,                              -- the runner's <n>, when the unit has one
  kind         TEXT NOT NULL DEFAULT 'book',         -- book|chapter|style|target|master|release|scene
  home         TEXT NOT NULL,                        -- episodes/ep04 (book-relative, posix)
  state        TEXT NOT NULL CHECK (state IN ('blocked','queued','running','stale','held',
                                              'deferred','escalated','failed','done')),
  step_id      TEXT,                                 -- the step the state is about
  progress     TEXT,                                 -- '18/25 · T10 attempt 3 move_type'
  priority     INTEGER NOT NULL DEFAULT 0,           -- lower first; 0 = bumped
  sequence     INTEGER,                              -- slate order (ep12 before ep13)
  gpu          INTEGER NOT NULL DEFAULT 0,           -- the current step's GPU flag
  attempts     INTEGER NOT NULL DEFAULT 0,           -- `started` events on this unit
  flags        INTEGER NOT NULL DEFAULT 0,           -- audit rows (terminal signatures)
  input_sha8   TEXT, blocked_on TEXT,                -- resume key; 'refs/04' while waiting
  claimed_by   TEXT, lease_until TEXT, run_id TEXT,
  requested_at TEXT, started_at TEXT, updated_at TEXT NOT NULL, finished_at TEXT,
  gpu_seconds  REAL NOT NULL DEFAULT 0, cost_usd REAL,   -- NULL while an unpriced call exists
  deliverable  TEXT, verdicts TEXT,                  -- book-relative path; JSON {gate:{word,by,sha8,faults}}
  hold_reason  TEXT, redo TEXT, note TEXT,           -- the hand columns
  source       TEXT NOT NULL DEFAULT 'run',          -- run | queue | backfill
  UNIQUE (codex_id, stage, unit)
);
CREATE INDEX IF NOT EXISTS ix_work_orders_queue ON work_orders (stage, state, priority, sequence);
CREATE UNIQUE INDEX IF NOT EXISTS ux_gpu_lease ON work_orders (gpu) WHERE gpu = 1 AND state = 'running';

-- the unit page's chips: one row per (order, step)
CREATE TABLE IF NOT EXISTS work_steps (
  order_id INTEGER NOT NULL REFERENCES work_orders(id), step_id TEXT NOT NULL,
  state TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0, run_id TEXT,
  started_at TEXT, ended_at TEXT, seconds REAL NOT NULL DEFAULT 0, gpu INTEGER NOT NULL DEFAULT 0,
  verdict_path TEXT, verdict_by TEXT, verdict_word TEXT, terminal TEXT NOT NULL DEFAULT '',
  outputs TEXT, detail TEXT,                         -- JSON [book-relative paths]; <= 200 chars
  PRIMARY KEY (order_id, step_id)
);

-- the owner's intent, one writer; runners take rows at the top of each loop
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY, ts TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('hold','lift','redo','bump','retry','requeue')),
  scope TEXT NOT NULL CHECK (scope IN ('studio','book','unit')),
  codex_id TEXT, stage TEXT, unit TEXT, step_id TEXT,
  note TEXT, by TEXT NOT NULL DEFAULT 'owner', taken_ts TEXT, taken_by_run TEXT
);
CREATE TABLE IF NOT EXISTS holds (                   -- RENDER_HOLD mirrored; book and unit holds
  id INTEGER PRIMARY KEY, scope TEXT NOT NULL, codex_id TEXT, stage TEXT, unit TEXT,
  reason TEXT NOT NULL, held_by TEXT, held_at TEXT NOT NULL, lifted_at TEXT
);

-- one per registered department, generated from registry.stage_names():
CREATE VIEW IF NOT EXISTS episode_orders AS SELECT * FROM work_orders WHERE stage = 'episode';
-- studio-wide: v_queue (queued, in priority, sequence order), v_attention (failed|deferred|escalated|stale)

-- existing tables, idempotent ALTERs: events.order_id, usage.unit, usage.order_id
```

`timing.jsonl` rows become `work_steps.seconds` (a stage-name → step-id map, since the file's
names predate the registry); `usage` gains `unit` so a unit's paid cost is answerable;
`learnings.jsonl` and `audit/rows.jsonl` stay files (the UI tails them).

### The state machine

`blocked → queued → running → done | failed | deferred | escalated`, plus `held` (a hold at
any scope), `stale` (the input sha moved after `done`, or a lease expired mid-run). The
scheduler's tick materializes and promotes; the runner claims and settles (`add_event` does
it: `started → running`, the final step's `completed → done`, `failed/escalated/deferred →
the word`); judges and the owner only sign files and write orders — nobody types a state.

## The standard department contract

| department | unit | turnover IN (declared `in:`) | deliverables OUT (declared `out:`; the manifest names them) | final when | progress |
|---|---|---|---|---|---|
| analysis | book | `source/*`, the codex row | `analysis/book.json`, `chapters/`, `extraction/ch_NN.json`, `scenes.json`, `characters/`, `locations/`, `qc_report.json` | `06 verify` done | chapters / chapters |
| screenplay | (book, target) | analysis manifest, `targets.yaml` row | `screenplay/<target>/{plan,screenplay,elements}.json`, `.fountain`, `qc_report.json` | `05 verify` done | beats / beats |
| refs (the bible) | (book, style) | analysis manifest, the cast list | `refs/refs.json`, sheets, `pack.jsonl`, `cast/<id>/voice/*`, `refs/verdict.json` | `judge:look@1` signs the pack sha | bound / needed |
| episode (production) | (book, chapter) | analysis + refs manifests, rows stamped for the unit | `plan.json`+verdict, lines, `placed.json`, panels+eye, takes+eye, `cut/master_iterN.mp4`, `qc_r2v.json`, `review/eye_*.json`, `manifest.json` | `12 deliver` done: every verdict's sha8 matches the master | takes judged / shots |
| trailer | (book, main) | screenplay + refs manifests | story, metre, clips, `master.mp4`, `qc.json`, `manifest.json` | `10 deliver` done | clips / setups |
| publish (future) | (master sha8, platform) | a production manifest, the master eye, the series policy | `publish/<sha8>/<platform>.json`, bundle, `uploads.jsonl` row | the platform's live status read back | items / 5 |
| promo (future) | release | a publish row, an analytics reading | campaign, orders, key art, cutdowns, posts | every order delivered and posted | orders / orders |

Same seven columns every time; the registry already carries three (`unit`, `requires`, the
steps). The office adds `in:`/`out:` and the counter, so the row is generated, not typed.

## How a department is driven

```
tick(conn):    rows from the registry × the slate (INSERT OR IGNORE); blocked → queued when
               requires are done and in: exist; RENDER_HOLD → holds; expired leases → stale
claim(conn):   UPDATE work_orders SET state='running', claimed_by=?, lease_until=now+15m
               WHERE id = (SELECT id FROM v_queue WHERE stage=? LIMIT 1) RETURNING *
run:           step_runner.run_steps(ctx, steps)      -- unchanged; add_event upserts the row
settle:        the last event's word; outputs, gpu_seconds, cost from what the run wrote
orders:        taken at the top of each loop: hold/lift → holds; bump → priority 0;
               retry → deferred|failed → queued; redo → the named step re-runs although done()
```

## The board (v1, read-only; v2 adds the order buttons)

Six pages, the studio home as landing: **On the floor** (the one GPU's row, live progress),
**Needs you** (failed · escalated · deferred · stale, oldest first), department lanes with
counts and glyphs, today's timeline. Then `/floor` (NOW · NEXT · WAITING ON · HELD · TODAY),
`/d/{stage}` (the department's table: state, unit, step · progress, last, attempts, gpu,
verdict strip, action), `/d/{stage}/{codex}/{unit}` (step chips, master player, verdicts,
panel and take thumbnails from files the steps already write, learnings and log tails,
timing), `/b/{codex}` (units across, departments down, ▲ for a public upload), `/org` (this
page). htmx partials on a 2 s poll for the floor and running cells, 10 s for tables; a JSON
twin per partial. Wireframes: report D §5.

## Migration, zero loss

`scripts/audit/backfill_work_orders.py` derives rows from disk and events (dry-run, then
`--write`, `source='backfill'`, never a row with a live `run_id`): `plan.verdict.json` signed
→ plan done; `cut/master_iterN.mp4` → edit done; `qc_r2v.json.passed` → qc done;
`youtube.json`/`uploads.jsonl` → the publish row; `plan.deferred.json` → deferred. Verified
on disk (report E §3): 25 of 27 episode folders derive without judgement; ep12 is ambiguous
(a hand-signed verdict and a live run) and is listed for the owner; `ep01_short` is outside
the unit grammar.

## Not built, on purpose

Crew scheduling, revision colours, VFX version trees, per-line budgets, Kanban, @mentions,
ETA models, Approve/Reject on judged gates (a redo + a note replaces them), any daemon,
executor, replay engine or pool. A worker loop that starts a five-hour GPU job unattended is
one commit away and is NOT in this decision: a `queued` row is a request until the owner
says it is an instruction.

## Open for the owner

1. Is a `queued` row an instruction (a worker loop drains it) or a request (a runner
   invocation takes it)? The plan builds the request; the loop waits for the word.
2. The publish department: does the board show a Distribution lane from `uploads.jsonl`
   before a `publish` stage exists in the registry (a file-read lane breaks "no state a
   runner did not write"), or does it wait for the stage?
3. `flagged` as a count on a done row (this ruling) or as a state of its own (D's doubt).
