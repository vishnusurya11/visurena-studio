# A — Data model: the table that drives a department

Expert A (data modeler), design round 2026-09-25, read-only. Grounded in `stages.yaml`,
`studio/db.py` (codex + events + usage; 24 066 events, 12 479 usage rows), `step_runner`
(`STEP_ID`, `GPU`, `done(ctx)`, `run(ctx)`), `judged_gate`/`deferral`/`escalate`,
`plan_ladder.Desk.resume`, the verdict files, `uploads.jsonl`, `timing.jsonl`,
`learnings.jsonl`, `audit/rows.jsonl`; WotW ep01–ep12 + ep13 deferred; Scarlet ep01–ep14.

## 0. The brick

The studio's brick is already written (`docs/ARCHITECTURE.md`): a **Step** =
`production_id + step_name + input_hash` → one artefact on disk, a known cost, a gate.
The data model is that brick as a row:

> **One `work` row per (unit, step_id).** Base case: a unit exists (a chapter, a book,
> a master, a release). Recursive rule: *a row is `ready` when every row it requires is
> `done` and its inputs are on disk; a runner claims the earliest ready row of its
> stage; the step's `done(ctx)` on disk is the truth and the row is its projection.*
> Closure: every department's table is `stages.yaml` applied to `work` — a view with one
> column per registered step. No department has a schema of its own.

Against the ask: monitoring = `SELECT` over `work`; "its own table" = one generated view
per stage; "drives the department" = the runner pulls `ready` rows of its stage; standard
I/O = every step declares `INPUTS`/`OUTPUTS`, every deliver step writes `manifest.json`;
a chapter, an episode, a trailer, a short, a release are `units` rows of different `kind`.

**Decision: generic `work` + generic `artefacts` + one view per department.** Not a
table per department: twelve episode columns would drift from the registry and kill
its rule ("adding a step = edit the yaml + add the script, nothing else changes"). Not
`work` alone: a master, a take, an upload are a different grain than a step. `events`
is **kept** as the append-only journal (24 066 rows, the runner writes it today);
`work` is *current state*, `events` is *history*. `usage` kept, gains two columns.

## 1. Tables

```sql
-- codex: unchanged. Its per-stage <stage>_status trio becomes derivable from work; dropped later.
-- units: THE production id, one row per (book, stage, unit); `home` relative to library/<book>/.
CREATE TABLE IF NOT EXISTS units (
  id          INTEGER PRIMARY KEY,
  codex_id    TEXT NOT NULL REFERENCES codex(id),
  stage       TEXT NOT NULL,                  -- a key of stages.yaml
  unit        TEXT NOT NULL,                  -- ep04 | main | feature | d8833608@youtube | scene_12 | rel_01
  kind        TEXT NOT NULL CHECK (kind IN ('book','chapter','style','target','master','release','scene','cue','arc')),
  key_json    TEXT NOT NULL DEFAULT '{}',     -- {"chapters":[4]} | {"master":"episodes/ep11/cut/master_iter2.mp4","platform":"youtube"}
  home        TEXT NOT NULL,                  -- episodes/ep04 | refs | trailer/main | publish/d8833608@youtube
  ordinal     INTEGER,                        -- sort inside the stage: episode number, cue number
  ordered_by  TEXT NOT NULL DEFAULT 'owner',  -- owner | slate | order:<units.id>  (a promo order)
  created_at  TEXT NOT NULL,
  UNIQUE (codex_id, stage, unit)
);

-- work: the WORK ORDER. One row per step of a unit, materialised from the registry when
-- the unit is created, so a department's whole queue is visible before it runs.
CREATE TABLE IF NOT EXISTS work (
  id           INTEGER PRIMARY KEY,
  unit_id      INTEGER NOT NULL REFERENCES units(id),
  step_id      TEXT NOT NULL,                 -- registry id, fixed width: 02, 09
  state        TEXT NOT NULL CHECK (state IN
               ('queued','ready','claimed','running','done','skipped','failed','deferred','escalated','stale')),
  gpu          INTEGER NOT NULL DEFAULT 0,    -- the module's GPU flag, copied at materialisation
  attempt      INTEGER NOT NULL DEFAULT 0,    -- runner passes over this row (a ladder's rungs are learnings)
  input_sha8   TEXT,                          -- fingerprint of INPUTS at the last pass (the resume key)
  output_sha8  TEXT,                          -- fingerprint of the primary OUTPUT
  run_id       TEXT,                          -- events.run_id of the last pass -> the log file
  claimed_by   TEXT,                          -- host:pid
  ready_at     TEXT, claimed_at TEXT, started_at TEXT, ended_at TEXT,
  wall_seconds REAL NOT NULL DEFAULT 0,       -- every pass summed (timing.jsonl rule: a retry is time too)
  gpu_seconds  REAL NOT NULL DEFAULT 0,       -- wall of the GPU scripts inside the step
  cost_usd     REAL,                          -- SUM(usage.cost_usd) of the row; NULL while an unpriced call exists
  verdict_path TEXT,                          -- relative to the book: episodes/ep12/plan.verdict.json
  verdict_by   TEXT,                          -- owner | judge:plan@1
  verdict_word TEXT,                          -- pass | flagged | APPROVE | DEFERRED
  terminal     TEXT NOT NULL DEFAULT '',      -- keep_best | still | flag | defer
  detail       TEXT,                          -- one line, <= 200 chars (the events rule)
  UNIQUE (unit_id, step_id)
);
CREATE INDEX IF NOT EXISTS ix_work_state ON work (state, gpu);
-- THE GPU LEASE AS A CONSTRAINT: at most one GPU row may be claimed or running, studio-wide.
CREATE UNIQUE INDEX IF NOT EXISTS ux_gpu_lease ON work (gpu)
  WHERE gpu = 1 AND state IN ('claimed','running');

-- artefacts: what a step produced, by kind, relative path and bytes.  `current` = 0
-- once superseded (master_iter1 after iter2; a redrawn panel; a displaced take).
CREATE TABLE IF NOT EXISTS artefacts (
  id       INTEGER PRIMARY KEY,
  unit_id  INTEGER NOT NULL REFERENCES units(id),
  work_id  INTEGER REFERENCES work(id),
  kind     TEXT NOT NULL,                     -- plan|verdict|rows|sheet|pack|voice|place|line|timeline|grid|panel|take|strip|bed|master|qc|manifest|metadata|upload
  path     TEXT NOT NULL,                     -- relative to library/<book>/, posix
  sha8     TEXT NOT NULL,
  bytes    INTEGER,
  current  INTEGER NOT NULL DEFAULT 1,
  made_at  TEXT NOT NULL,
  UNIQUE (unit_id, path, sha8)
);
CREATE INDEX IF NOT EXISTS ix_artefacts_kind ON artefacts (unit_id, kind, current);

-- learnings: mirror of <home>/learnings.jsonl (the file stays the truth); audit/rows.jsonl == WHERE terminal = 1.
CREATE TABLE IF NOT EXISTS learnings (
  id INTEGER PRIMARY KEY, work_id INTEGER NOT NULL REFERENCES work(id),
  ts TEXT NOT NULL, gate TEXT NOT NULL, substep TEXT, measured TEXT, threshold TEXT,
  action TEXT NOT NULL, attempt INTEGER, seconds REAL, terminal INTEGER NOT NULL DEFAULT 0,
  faults_json TEXT, note TEXT
);
CREATE INDEX IF NOT EXISTS ix_learnings_gate ON learnings (gate, terminal);

-- existing tables: two columns each, idempotent ALTERs in db._migrate
ALTER TABLE events ADD COLUMN work_id INTEGER REFERENCES work(id);
ALTER TABLE usage  ADD COLUMN unit TEXT;
ALTER TABLE usage  ADD COLUMN work_id INTEGER REFERENCES work(id);
```

**Department tables = views generated from the registry** (`db.init_db` regenerates
them; a new stage gets its view by being registered, exactly as it gets its codex trio
today). One row per unit, one column per step holding its state, plus the deliverable:

```sql
CREATE VIEW IF NOT EXISTS v_episode AS
SELECT u.codex_id, u.unit, u.ordinal, u.home,
  MAX(CASE WHEN w.step_id='01' THEN w.state END) AS bind,
  MAX(CASE WHEN w.step_id='02' THEN w.state END) AS plan,
  -- ... one such column per registry.steps('episode'): places, record, timeline,
  --     prompts, board, panels, shoot, edit, qc ...
  MAX(CASE WHEN w.step_id='12' THEN w.state END) AS deliver,
  (SELECT a.path FROM artefacts a WHERE a.unit_id=u.id AND a.kind='master' AND a.current=1) AS master,
  SUM(w.wall_seconds) AS wall_seconds, SUM(w.gpu_seconds) AS gpu_seconds, SUM(w.cost_usd) AS cost_usd,
  SUM(w.state IN ('failed','deferred','escalated')) AS attention, MAX(w.ended_at) AS last_activity
FROM units u JOIN work w ON w.unit_id = u.id WHERE u.stage = 'episode' GROUP BY u.id;
-- v_refs, v_analysis, v_screenplay, v_trailer, v_publish, v_promo ...: same template, the
-- column list is registry.steps(stage).  Two studio-wide views:
CREATE VIEW IF NOT EXISTS v_queue AS       -- what runs next, per stage, in order
  SELECT u.stage, u.codex_id, u.unit, w.step_id, w.gpu, w.ready_at
  FROM work w JOIN units u ON u.id = w.unit_id WHERE w.state = 'ready'
  ORDER BY u.stage, u.codex_id, u.ordinal, w.step_id;
CREATE VIEW IF NOT EXISTS v_attention AS   -- the amber strip of the earlier UI design
  SELECT u.stage, u.codex_id, u.unit, w.step_id, w.state, w.verdict_path, w.detail, w.ended_at
  FROM work w JOIN units u ON u.id = w.unit_id WHERE w.state IN ('failed','deferred','escalated','stale');
```

### 1.1 State machine of a `work` row

```
queued --scheduler--> ready --runner--> claimed --runner--> running --runner--> done | skipped
  (one row per registry step,                                  |                  |
   made when the unit is created)                              +--> failed | deferred | escalated --retry / verdict file--> ready
                                                                                  +--scheduler (input sha moved)--> stale --> ready
```

| transition | who | when |
|---|---|---|
| (none) → `queued` | scheduler (`studio.py`), or a runner handed a unit with no rows | unit created: slate (`series.json`), an order (`promo/…/order.json`), the CLI |
| `queued` → `ready` | scheduler tick, or the runner after the unit's previous step | every `requires` row `done`; previous step `done`/`skipped`; `RENDER_HOLD` absent for GPU rows |
| `ready` → `claimed` | runner: `UPDATE work SET state='claimed', claimed_by=?, claimed_at=? WHERE id=? AND state='ready'` | a GPU row that violates `ux_gpu_lease` raises IntegrityError = someone holds the GPU; wait |
| `claimed` → `running` | runner, once `busy()` says the ComfyUI queue is empty | `started` event |
| `running` → `done` / `skipped` / `failed` | runner: `run(ctx)` returned / `done(ctx)` true and `input_sha8` unchanged / SystemExit or crash | the matching event; outputs registered in `artefacts`; `verdict_*` copied off the signed file |
| `running` → `deferred` / `escalated` | runner: `Deferred` (a judge's terminal) / `Escalation` (legacy owner gate) | `verdict_path` = `plan.deferred.json` / the file whose presence signs it |
| `escalated` → `ready` | scheduler tick sees `verdict_path` exist | the owner signs with the sign scripts, never edits the table |
| `deferred`/`failed` → `ready` | owner (`studio.py retry <unit> <step>`) or the next scheduled pass | `attempt + 1`; the step resumes from the aside (`Desk.resume`), never from nothing |
| `done` → `stale` | scheduler tick: `fingerprint(INPUTS) != input_sha8` | ep12: the plan was edited after step 09 ran and the runner skipped on "output exists"; every downstream row goes stale in one UPDATE |

Judges never touch the table: they sign files; the runner copies the signature into
`verdict_*`. The owner never touches it either: he signs files and runs `retry`.
`RENDER_HOLD` is not a state; it is a scheduler predicate and a banner in the UI.

## 2. The standard input/output contract

Two halves, both already half-present in the tree.

**Per step (code contract, `scripts/<stage>/step_NN_*.py`):** today `STEP_ID`, `NAME`,
`GPU`, `done(ctx)`, `run(ctx)`. Add two declarations, book-neutral globs relative to
the unit's `home` (or `book:` for a book-level file):

```python
STEP_ID, NAME, GPU = "09", "shoot", True
INPUTS  = ("plan.json", "placed.json", "audio/lines/lines.json", "storyboard/shot_*.png",
           "storyboard/eye_*.json", "book:refs/refs.json", "book:refs/verdict.json")
OUTPUTS = {"take": "takes/r2v/T??.mp4", "strip": "reports/strip_*.png", "verdict": "takes/r2v/eye_*.json"}
```

The runner computes `input_sha8 = fingerprint(INPUTS)` before `done(ctx)` and registers
every `OUTPUTS` match as an `artefacts` row after `run(ctx)`; a module with no `INPUTS`
defaults to the previous step's outputs (old modules keep working). This is `stale`.

**Per department (data contract):** every stage's last step (`deliver`, or `verify` /
`verdict` in pre-production) writes **one `manifest.json` at the unit's home**, pydantic
`UnitManifest`: `codex_id, stage, unit, inputs[{path,sha8}], outputs[{kind,path,sha8}],
verdicts[{gate,path,signed_by,word,terminal}], cost{wall_seconds,gpu_seconds,usd},
steps{id:state}`. `step_12_deliver` already writes master + qc + steps + timing; this
fixes its shape. A `requires` is satisfied by the required unit's manifest row being
`done` — never by a sentence or an event alone. The manifest is what crosses a
department boundary; the folder under `home` is where it lives. Both: a manifest names
bytes, a folder holds them.

### 2.1 The episode line on the contract (unit `ep12`, kind `chapter`, home `episodes/ep12`)

| step | INPUTS (relative to home; `book:` = book-level) | OUTPUTS kind → path | verdict | gpu |
|---|---|---|---|---|
| 01 bind | `book:analysis/scenes.json`, `book:refs/refs.json` | rows → `book:refs/refs.json` (stamped) | — | 0 |
| 02 plan | `book:analysis/**`, `book:screenplay/<target>/elements.json`?, `book:refs/refs.json`, camera catalog, `book:analysis/dq_rules.json` | plan → `plan.json`; verdict → `plan.verdict.json` \| `plan.deferred.json` | judge:plan@1 | 0 |
| 03 places | `plan.json`, `book:analysis/locations/*.json` | place → `book:refs/locations/<id>/…png` (per-episode hour) | look_back | 1 |
| 04 record | `plan.json`, `book:cast/<id>/voice/*` | line → `audio/lines/*.wav` + `lines.json` | listener | 1 |
| 05 timeline | `plan.json`, `audio/lines/lines.json` | timeline → `placed.json` | misaligned() | 0 |
| 06 prompts | `plan.json`, `placed.json` | prompts → `takes/r2v/prompts.json` | lint HARD | 0 |
| 07 board | `plan.json`, `book:refs/sheets/*.png`, places | grid → `storyboard/grids/*.png`, `layout.json` | grid_layout@1 | 1 |
| 08 panels | grids, `plan.json` | panel → `storyboard/shot_NN.png`; `panel_dq.json`, `panel_content.json`; verdict → `storyboard/eye_<sha8>.json` | judge:panel_eye@1 | 1 (VLM) |
| 09 shoot | panels + eye, sheets, lines, `prompts.json` | take → `takes/r2v/T??.mp4` (+`.dq.json`, `.content.json`); strip; verdict → `takes/r2v/eye_<sha8>.json` | judge:take_eye@1 | 1 |
| 10 edit | takes + eye, `placed.json`, bed, `book:title/*` | master → `cut/master_iterN.mp4` | bed gate | 1 (bed) |
| 11 qc | the master | qc → `qc_r2v.json`; verdict → `review/eye_<sha8>.json` | judge:master_eye@1 | 1 (VLM) |
| 12 deliver | master, qc, verdicts, `timing.jsonl` | manifest → `manifest.json` | — | 0 |

### 2.2 Every other unit is the same shape

| stage | `units.kind` | `unit` | `home` | requires (manifest of) | deliverable kind |
|---|---|---|---|---|---|
| analysis | book | `main` | `analysis` | source | `qc_report.json`; the per-chapter fan-out (`extraction/ch_NN.json`) is **artefacts** of step 02, not units — the UI's partition bar is `COUNT(artefacts WHERE kind='extraction')` vs the chapter count |
| screenplay | target | `feature` | `screenplay/feature` | analysis/main | `screenplay.json` |
| refs | style | `main` | `refs` | analysis/main (05) | `refs/verdict.json` + pack; re-opened (rows → `stale`) when a plan binds an entity with no row |
| episode | chapter | `ep04` / `ch04-05` | `episodes/ep04` | analysis/main, refs/main | master |
| trailer | book | `main` | `trailer/main` | screenplay/feature, refs/main; `ordered_by = order:<promo unit>` | master |
| shorts | scene | `scene_12` | `shorts/scene_12` | screenplay, refs | master (paid: each spend a `usage` row with `unit`) |
| audiobook / song / feature / game | chapter / cue / target / arc | `ch04` / `cue_03` / `feature` / `arc_01` | `<stage>/<unit>` | per registry | master / build |
| publish | master | `d8833608@youtube` | `publish/d8833608@youtube` | the production unit's manifest (`key_json.master`) | upload row (`uploads.jsonl` line) + `youtube.json` |
| promo | release | `rel_01` | `promo/rel_01` | publish/01 of the release's masters | `order.json` → the scheduler creates the ordered units |

## 3. How the table drives the department

**Pull, with a scheduler that materialises.** Not push: finishing a row enqueuing the
next department's row would put department B's shape inside department A's runner (the
sin the future-departments debate ruled out at 1.5). Not pure pull over `requires`
evaluated at claim time: that is today's `codex_ready_for_stage` and it cannot show a
queue before it runs.

1. `studio.py tick` (also run in-process by every runner at the start and end of a
   unit): materialise missing `work` rows from `registry.steps(stage)`; `queued → ready`
   where the previous step is `done|skipped` and every `requires` manifest row is
   `done`; `done → stale` where `fingerprint(INPUTS)` moved; `escalated → ready` where
   `verdict_path` now exists; GPU rows untouched while `RENDER_HOLD` exists. Idempotent.
2. `episode.py` with no unit = claim the lowest-ordinal `ready` row of its stage and
   run the unit from that step on; `episode.py <book> <n>` = today, plus the claim.
   `refs.py`, `publish.py` identical: `step_runner.run_steps` gains claim → run → release.
3. **Single GPU:** three guards, one truth each. `ux_gpu_lease` — one GPU row in
   `claimed|running` studio-wide, enforced by SQLite, no lock file to go stale (`tick`
   reaps a `running` row whose `claimed_by` pid is dead to `failed`). `comfy.busy()` —
   jobs this table never saw; waited on as today. `RENDER_HOLD` — the owner's brake,
   read by `tick` and before every GPU step, as today.

Every department is driven by the same query, `SELECT * FROM v_queue WHERE stage = ?`.
The UI reads the views; its only writes are the CLI's own commands (`retry`, `hold`, the
sign scripts).

## 4. Idempotency and resume

- **Re-run on `done`:** `done(ctx)` true and `input_sha8` equal → `skipped`, as today;
  sha moved → the row was already `stale`, it runs; `done(ctx)` false on a `done` row
  (artefact deleted by hand) → `tick` flips it to `ready`. Disk is the key, never the table.
- **Deferred is resumed, never restarted:** the row keeps `attempt`, `verdict_path =
  plan.deferred.json`, `detail = note`; `retry` sets `ready`, `attempt+1`; `Desk.resume`
  reads the aside's `draft` and `faults` and edits — what episode 13 taught on
  2026-09-25. The table adds nothing to the step; it makes the pass count visible.
- **Failed** stays failed until `retry`. **Paid steps** write their `usage` row before
  the call (as `youtube_publish` does); a row with usage and no artefact is the
  "credits gone twice" case made visible, never re-run without `retry`.
- **Two attempt numbers on purpose:** `work.attempt` = runner passes; `learnings.attempt`
  = rungs inside a pass.

## 5. Migration from today's tables, zero loss

Nothing existing is dropped or rewritten: the four new tables are a **projection
rebuildable from disk + events**, so `studio/backfill.py --rebuild` can run any time:

1. **units** — `library/<book>/episodes/ep??` → episode units (WotW 13, Scarlet 14;
   `ep01_short` listed, not placed); `refs/` → refs `main`; `trailer/main`; `analysis`,
   `screenplay/<target>` → book units; `uploads.jsonl` rows with a `video_id` → publish
   units `<sha8>@youtube`.
2. **work.state** — per unit and registry step, **call the step module's own `done(ctx)`**:
   the truth the runner skips on. Overrides: `plan.deferred.json` → 02 `deferred`;
   `placed.json` without `plan.verdict.json` → 02 `done`, `verdict_by='owner'`
   (grandfathered, as `step_02_plan.grandfathered` reads it). Modules with no `done()`
   (analysis, screenplay, trailer) take the latest event per step.
3. **timestamps, attempts** — from `events`: `MIN(started)`, latest terminal event,
   `COUNT(started)`, last `run_id`; `events.work_id` by the same join (`unit IS NULL`
   joins to `main`).
4. **seconds** — `timing.jsonl` stage names → step ids (`bind→01, places→03, lines→04,
   respot|timeline→05, takes|take_dq|strip→09, assemble|title→10, qc|eye_review→11`);
   `usage.unit` from the run's `run_id` window, unplaceable rows stay NULL and are listed.
5. **artefacts** — every `cut/master_iter*.mp4` (`current=1` = what
   `youtube_publish.deliverable` picks), `qc_r2v.json`, `plan.json`, verdict files,
   `refs/pack.jsonl`; `uploads.jsonl` line → kind `upload`; a `privacy: public` row →
   publish step 07 `done`.
6. **learnings** — every `learnings.jsonl` line joined by `step`; `audit/rows.jsonl`
   reconciled as the `terminal=1` subset (a mismatch printed, never fixed).

The backfill prints units per stage, rows per state, masters vs episodes, uploads vs
public rows, and every file it could not place. Expected today: WotW 12 episodes at
`deliver` done-or-ready, ep13 at 02 `deferred`; Scarlet 14 with masters; 5 WotW +
Scarlet's public rows as publish units at 07 `done`.

## 6. Worked example (three units of WotW, `codex_id 20260827135508`)

**units**

| id | stage | unit | kind | key_json | home | ordinal |
|---|---|---|---|---|---|---|
| 41 | episode | ep11 | chapter | `{"chapters":[11]}` | episodes/ep11 | 11 |
| 42 | episode | ep12 | chapter | `{"chapters":[12]}` | episodes/ep12 | 12 |
| 43 | episode | ep13 | chapter | `{"chapters":[13]}` | episodes/ep13 | 13 |
| 90 | publish | d8833608@youtube | master | `{"master":"episodes/ep11/cut/master_iter2.mp4","platform":"youtube"}` | publish/d8833608@youtube | 11 |

**work** (columns not shown are NULL/0)

| unit_id | step | state | gpu | attempt | input_sha8 | verdict_path / by / word | wall s | detail |
|---|---|---|---|---|---|---|---|---|
| 41 | 02 | done | 0 | 1 | 9c1e… | — / owner / APPROVE (grandfathered) | 0 | |
| 41 | 12 | done | 0 | 1 | d883… | — | 2 | master_iter2 d8833608; 01–11 all done |
| 90 | 05 | done | 0 | 1 | d883… | — | 41 | video_id 4HHxB6zSNIo private |
| 90 | 07 | done | 0 | 1 | d883… | uploads.jsonl#L20 / owner / public | 3 | 2026-09-25T01:20Z |
| 42 | 02 | done | 0 | 31 | 56bd… | episodes/ep12/plan.verdict.json / owner / APPROVE | 0 | re-signed after edits |
| 42 | 08 | done | 1 | 29 | c7e3… | storyboard/eye_c7e3eb93.json / judge:panel_eye@1 / flagged (keep_best) | 3 140 | 531 faults, landmark |
| 42 | 09 | **running** | 1 | 16 | 3f9b… | — | 2 970 | claimed_by host:18244, run 20260925225734 |
| 42 | 10 | stale | 1 | 3 | 1e0c… | — | 610 | input moved: takes re-rendered |
| 42 | 11 | stale | 1 | 4 | — | — | 402 | last pass failed |
| 42 | 12 | queued | 0 | 0 | — | — | 0 | |
| 43 | 02 | **deferred** | 0 | 13 | 0b77… | episodes/ep13/plan.deferred.json / judge:plan@1 / DEFERRED (defer) | 0 | passes 6; battery lines kept in the aside; 01 done, 03–12 queued |

`ux_gpu_lease` holds exactly one row (42/09). `v_episode`: ep11 twelve `done`,
`master=episodes/ep11/cut/master_iter2.mp4`; ep12 `shoot=running`, `edit=stale`,
`attention=1`; ep13 `plan=deferred`. `v_queue` for episode is empty until 42/09 ends;
for `publish` it lists ep12's master the moment 42/12 is `done`.

## 7. Three doubts for the debate

1. **Views or tables per department?** The owner said "its own table". A view is the
   registry made visible and cannot drift, but cannot hold a hand column (an owner note,
   a planned air date); the honest answer for those is `unit_notes(unit_id, key, value,
   at)`, not a column per department. Debate whether that satisfies the ask or whether
   a materialised table per stage is what he pictures in a DB browser.
2. **`events` kept beside `work`, or `work` derived from `events`?** I keep both because
   the disk (`done(ctx)`) is the truth and events are not (24 066 rows say what ran,
   not what exists). The cost is a dual write in `step_runner`. The alternative — drop
   `events`, make `work` + `learnings` the whole ledger — loses the "a run finished
   once" history unless `work_history` is added, which is `events` under another name.
3. **Grain of the fan-out inside a step.** A take, a panel, a chapter extraction are
   `artefacts` rows and their ladders are `learnings`, so per-take status (third seed on
   `T07`) is derived, not stored. If the UI must show it live during a 2-hour step 09,
   either the step reports into `work.detail`, or takes become `work` sub-rows
   (`09_01#T07`), which the fixed-width id rule forbids. The monitoring wanted decides.

Not designed here: the paid-credit reserve→commit ledger for `shorts` (a `spend` table
keyed on `work_id`, `reserved|committed|released`) — the money side's.
