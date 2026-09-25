# D — The floor: UI design for the command center

*Expert D (operations-dashboard UX), design round 2026-09-25. Read-only; nothing built. Prior
art improved, not obeyed: `docs/command_center/DESIGN.md` (v0.1, 2026-08-22) and its research
file. Since then: judges sign taste gates pass|flagged and the owner audits after the fact
(`gates.yaml`), `events` gained a `unit` column, and departments are tables of units, not a DAG.*

## 0. The brick of this UI

One row per (department, unit); every screen is a projection of it. A home lane is one
department's rows counted by state; a department page is the rows in full; a unit page is
one row opened with its folder read from disk; the call sheet is the rows sorted by what the
one GPU does next. No second brain: the UI never computes a state a runner did not write.

The earlier proposal put a graph library at the centre. The DAG already exists as a document
(`architecture/index.html`) and the fan-out that matters (24 takes, 23 panels, 27 chapters) is
homogeneous, which the research file itself says wants a table. So: **tables and strips; no
Cytoscape in v1.** A unit's step timeline is twelve chips in a row, drawn from `stages.yaml`.

## 1. Information architecture

| page | route | answers at a glance |
|---|---|---|
| **Studio home** (landing) | `/` | Is the GPU busy, on what, how far? What needs *me* (escalated, failed, held)? Per department: how many units in each state, which ones are flagged? |
| Call sheet (the floor) | `/floor` | What runs now, what runs next, in what order, and why (priority, hold, blocked-by); today's timeline of finished steps with seconds. |
| Department | `/d/{stage}` | ITS table: every unit of this department across books, sortable by attention, with step progress, last event, attempts, cost, artefacts, verdict chips, action buttons. |
| Unit | `/d/{stage}/{codex}/{unit}` | The unit opened: step timeline, the plan, panel thumbnails, take strips, the master playable, gate verdicts with their faults, learnings tail, log tail, the timing ledger. |
| Book | `/b/{codex}` | One book down every department: an Airflow-grid of units × departments with state cells; the book's cost, its published episodes, its audit sheet and casebook links. |
| Org chart | `/org` | The existing `architecture/index.html`, served as-is (see §6). |

**Landing = Studio home, not the call sheet.** With one GPU, "what is running" is *one line*
and fits as the home page's first strip ("On the floor"); the call sheet earns its own page
only for the queue order and the day's timeline. A glance must answer "running? stuck? needs
me?" in the first 120 px, then "how is each department doing". A department-first landing
buries the one running job under five tables; a call-sheet landing hides the flagged pile.
Breadcrumb on every page: `Studio › Episode › War of the Worlds › ep12`; book and department
are two cross-cuts of the same rows and link to the same unit page.

## 2. Status vocabulary and visual language

Derived, never invented: the state is the row's `state`, written by the runner from the same
words `studio/db.py` already CHECKs, plus what the gate files and the owner's orders add.

| state | glyph | colour token (from the org-chart page) | meaning, in one line | who it needs |
|---|---|---|---|---|
| queued | `○` | `--ink-3` grey, hollow | deps met, waiting for the GPU or its turn | nobody |
| blocked | `◌` | grey, dotted border | a `requires` unmet (refs/04 unsigned, analysis/06 missing); names the blocker | the blocker's row |
| running | `●` pulsing | `--think` blue | a step started and has not ended; shows live progress `takes 18/25` | nobody |
| passed | `✓` | `--ok` green | step completed, every gate signed pass | nobody |
| flagged | `⚑ n` | `--qc` amber (the judge's colour) | a judge signed with n faults; a deliverable exists; work goes on | the owner's audit, later |
| deferred | `↩` | `--invent` purple | a judge's terminal set the unit aside (`plan.deferred.json`); nothing broke; the next pass re-authors | the next pass |
| failed | `✕` | `--accent` red | an exception, a stop, an exit 1 outside any ladder; no artefact | a developer |
| escalated | `✋` | `--ink` black, bold 2 px border | parked for the owner's signature: money or publish only | **the owner** |
| held | `⏸` | striped `--rule-2` | the owner's hold on a unit or a book; the scheduler skips it | the owner to unhold |
| stale | `~` | hollow green, dashed | output older than its input (an unfinished render is not current: commit 82c291c) | a re-run |
| skipped | `–` | grey, thin | the format skipped this word (episode has no `sound`) | nobody |

The one-glance rule for the four confusable states: **red = the code needs a developer; black
= it needs the owner; amber = it needs nobody now (audit later); purple = it needs the next
pass.** Each has its own glyph, border style and word, so colour alone never carries it.

Row colour never fills the row (Deadline's green-to-red drift is unreadable on paper); state
lives in one left cell plus the segmented progress bar (green passed, amber flagged, blue
running animated, grey not yet). The verdict strip is the gates of `gates.yaml` in order,
`PLAN ✓ · LAYOUT ✓ · PANELS ⚑3 · TAKES ⚑5 · MASTER ○`, each chip linking to its faults.
Typography and theme are the org-chart page's: IBM Plex Sans / Mono, Barlow Condensed,
`--paper` / `--ink` tokens, light and dark by the same `data-theme` rule; numbers tabular.

## 3. Live-ness

- **What polls**: only what changes. The "On the floor" strip and the running row's progress
  cell are `hx-get` partials with `hx-trigger="every 2s"`; department and book tables swap
  every 10 s; a unit page's log and learnings tails every 3 s while running, and the server
  drops the `hx-trigger` once the state is terminal. The artefact grid reloads on a click only.
- **htmx partials over JSON**: the same Jinja partial serves the first paint and every swap
  (`_floor.html`, `_rows.html`, `_progress.html`): one template, one test. A `/api/*.json`
  twin per partial (same view-model, `response_model=` pydantic) is free once the model exists.
- **Reads that never block the runners**: `studio.db` opened `file:...?mode=ro`, WAL already
  the journal, `busy_timeout=250`, one short read per request. Progress (`18/25`) is a column
  the runner writes on its row every take, so no poll globs `takes/`; the unit page counts
  files only on load.
- **Artefacts as static files**: `/lib/{codex}/{relpath}` is a `StaticFiles` mount rooted at
  `library/` behind one guard: the resolved path must start with the resolved root and its
  suffix must be in `{png, jpg, mp4, wav, json, jsonl, html, txt}`; a `..`, a symlink out or a
  `.py` is a 404, never a 403. Videos stream with Range (Starlette), so `master_iter2.mp4`
  seeks in a `<video>` tag. The web process generates no thumbnails (no ffmpeg from a
  request): the pipeline already writes `storyboard/contact.png`, `reports/strip_*.png` and
  `shot_NN.png`; takes use those plus `<video preload="metadata">` on hover. A thumb cache is
  v2 and belongs to a step (`11_04 dossier`), not the UI.
- Logs: the unit page tails `logs/{codex}/{stage}/{run_id}.log` (the row's `run_id`), a
  bounded read of the last 64 KiB parsed as JSONL, WARN and ERROR coloured.

## 4. Actions (v2; affordances designed now)

Every action is **one POST that appends one row to an `orders` table** (`ts, kind, codex_id,
stage, unit, note, by, taken_ts, taken_by_run`). The web process never imports a runner,
spawns a subprocess or edits a file under `library/`. The runner (or the future scheduler)
reads untaken orders at the top of every loop and stamps `taken_ts`; until then the row shows
the order as a chip (`↑ priority 1 · ordered 09:14`), so a click visibly lands even when
nothing is running.

| affordance | where | POST | row it writes | what the runner does with it |
|---|---|---|---|---|
| Run / Resume | unit row, unit page header | `/orders` kind=`run` | one row | the scheduler runs it next in priority order; resume is the default (outputs on disk are the resume key) |
| Hold / Unhold | book page header, unit row | kind=`hold` / `unhold` | one row | the scheduler skips held units; state shows `⏸` |
| Redo with a note | unit page, beside a verdict chip | kind=`redo`, `note` required, `gate` in payload | one order row **and** an audit note through `scripts/audit/note.py` (the owner's finding goes to the casebook, never a hand-signed verdict) | the ladder re-runs from that gate on the next pass |
| Bump priority | unit row (`↑`), call sheet drag | kind=`priority`, `value` | one row | the queue re-sorts; the call sheet shows the new order at the next poll |
| Approve / Refuse (money, publish) | the escalated row only | kind=`approve` / `refuse`, `note` | one row | the step that parked reads the answer; nothing else may consume an approval (`studio/approval.py` remains the only reader) |

Each form is an htmx `hx-post` (`hx-confirm` on redo and refuse) answered with the row's partial plus the order chip; hidden in v1, the routes 404 until `orders` lands.

## 5. Wireframes, components, stack

### 5a. Studio home `/`

```
┌ Visurena Studio ─────────────── Home · Floor · Books · Org chart ── ◐ ┐
│ ON THE FLOOR  ● Episode › WotW › ep13 · 09 shoot · takes 18/25         │
│               attempt 2 · gpu 1h42 of 5h · started 14:02 · next: ep14  │
│ NEEDS YOU (2) ✋ Shorts › s07 · approve render 340 cr  [Approve][Refuse]│
│               ✕ Refs › Dracula › style krea2 · 02 sheets · KeyError … ▸│
├──────────┬──────────┬──────────┬──────────┬──────────┬────────────────┤
│ ANALYSIS │SCREENPLAY│ REFS     │ TRAILER  │ EPISODE  │ DISTRIBUTION   │
│ 3 units  │ 2 units  │ 2 units  │ 1 unit   │ 13 units │ 11 published   │
│ ▮▮▮      │ ▮▮       │ ▮▮       │ ▮        │ ▮▮▮▮▮▮▮▮▮▮▮▮● │ ▮▮▮▮▮▮▮▮▮▮▮ │
│ ✓3       │ ✓2       │ ✓1 ✕1    │ ✓1       │ ✓5 ⚑6 ●1 ↩1 │ ✓11           │
│          │          │          │          │          │                │
│ WotW  ✓  │ WotW  ✓  │ WotW  ✓  │ WotW  ✓  │ ep13 ● 18/25 │ ep11 public │
│ Dracula ✓│ Dracula ✓│ Dracula ✕│          │ ep12 ⚑5 iter2│ ep10 public │
│ Frankst ✓│          │          │          │ ep14 ↩ defer │ ep09 public │
│          │          │          │          │ ep10 ⚑2      │ …           │
│ open ▸   │ open ▸   │ open ▸   │ open ▸   │ open ▸   │ open ▸         │
├──────────┴──────────┴──────────┴──────────┴──────────┴────────────────┤
│ TODAY  07:40 ep12 qc 412s ✓ · 08:45 ep12 prompts 2s ✓ · 15:52 ep12     │
│        bind ✓ · 15:52 ep12 takes 3s ✓ · 20:54 ep13 PLAN ↩ · 22:20 …    │
│ legend  ○ queued ◌ blocked ● running ✓ passed ⚑ flagged ↩ deferred      │
│         ✕ failed ✋ escalated ⏸ held ~ stale – skipped                   │
└────────────────────────────────────────────────────────────────────────┘
```

Lanes are the departments in `stages.yaml` order plus Distribution (from `uploads.jsonl` /
`youtube.json`, not a registry stage yet). Each lane: count, segmented bar by state, count
line, then the three rows that matter (running, then escalated/failed, then flagged newest).
Polls: floor strip 2 s, lanes 10 s.

### 5b. Call sheet `/floor`

```
┌ Studio › Floor ─────────────────────────────────── GPU: RTX 4090 ─ ◐ ┐
│ NOW   ● Episode WotW ep13 · 09 shoot · round 2 · take T18 of 25         │
│       ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮░░░░░░░ 72% · 1h42 of 5h ceiling · ETA 16:40   │
│       run 20260827135508_episode_20260925140212 · [log tail ▾]         │
│                                                                        │
│ NEXT  1  Episode WotW ep14        02 plan     ↑ priority 1   [hold]     │
│       2  Refs  Dracula krea2       02 sheets   after fix ✕    [hold]    │
│       3  Episode WotW ep15        01 bind     queued          [↑][hold]│
│       4  Trailer Dracula           03 music    ◌ needs refs/04          │
│ HELD  ⏸ Episode Frankenstein *    all         owner 09-24: "after ref"  │
│                                                                        │
│ TODAY ─ 07:40 ─── 08:45 ── 15:52 ─── 20:54 ──── 22:20 ─── now         │
│   ep12 ▮qc 412s ▮prompts ▮bind ▮takes   ep13 ▮plan ↩  ▮plan ↩  ●shoot │
│   gpu busy 3h11 · idle 9h02 · steps 9 · flagged 1 · deferred 2         │
└────────────────────────────────────────────────────────────────────────┘
```

NEXT is the scheduler's order: priority, registry order, unit order; a blocked row names and
links its blocker. Until a scheduler exists the list is queued rows sorted the same way, labelled *derived*.

### 5c. Department `/d/episode`

```
┌ Studio › Episode ───────────── 13 units · 5h ceiling per unit ─── ◐ ┐
│ filter [all books ▾] [state ▾] [flagged only □]   sort: attention ▾   │
├─────┬────────┬──────┬────────────────────┬────────┬─────┬──────┬──────┤
│ st  │ book   │ unit │ step · progress    │ last   │ att │ gpu  │ verd │
├─────┼────────┼──────┼────────────────────┼────────┼─────┼──────┼──────┤
│ ●   │ WotW   │ ep13 │ 09 shoot ▮▮▮▮░ 18/25│ 14:02  │ 2   │ 1h42 │ ✓✓⚑○○│ [hold]
│ ✋  │ WotW   │ ep16 │ 09 shoot · render  │ 13:10  │ 1   │ 0    │ ✓✓✓○○│ [Approve]
│ ↩   │ WotW   │ ep14 │ 02 plan · deferred │ 22:20  │ 5   │ 0    │ ↩    │ [run]
│ ✕   │ Drac   │ ep01 │ 04 record · Error  │ 09-24  │ 1   │ 0:04 │ ✓○○○○│ [run]
│ ⚑ 5 │ WotW   │ ep12 │ 12 deliver ✓ iter2 │ 15:52  │ 5   │ 4h58 │ ✓✓⚑⚑✓│ [redo]
│ ⚑ 2 │ WotW   │ ep10 │ 12 deliver ✓ iter1 │ 09-23  │ 3   │ 3h20 │ ✓✓⚑✓✓│
│ ✓   │ WotW   │ ep11 │ 12 deliver ✓ public│ 09-22  │ 3   │ 4h01 │ ✓✓✓✓✓│
│ ○   │ WotW   │ ep15 │ 01 bind            │ –      │ 0   │ –    │ ○○○○○│ [↑]
│ ◌   │ Drac   │ ep02 │ needs refs/04      │ –      │ 0   │ –    │      │
│ ⏸   │ Frank  │ ep01 │ held 09-24         │ –      │ 0   │ –    │      │
├─────┴────────┴──────┴────────────────────┴────────┴─────┴──────┴──────┤
│ row hover: thumbnails strip (contact.png) · click unit → unit page      │
│ footer: ✓5 ⚑6 ●1 ↩1 ✕1 ○… · gpu this week 21h · legend                 │
└────────────────────────────────────────────────────────────────────────┘
```

`att` is the ladder attempt (highest `attempt` of the current gate in `learnings.jsonl`);
`verd` is the `gates.yaml` strip. Default sort "attention": escalated, failed, running,
deferred, flagged, queued, passed. Every department renders this same table with its own
gate list and cost unit (`credits` for shorts, `gpu` for the local lines, `tokens` for analysis).

### 5d. Unit `/d/episode/20260827135508/ep12`

```
┌ Studio › Episode › War of the Worlds › ep12 "Weybridge and Shepperton" ┐
│ ⚑ 5 flagged · 12 deliver ✓ · master_iter2 · 4h58 gpu · 5 attempts     │
│ [run/resume] [redo ▾ with note] [hold] [audit sheet ▸] [dossier ▸]      │
├────────────────────────────────────────────────────────────────────────┤
│ STEPS  01 ✓ 02 ✓ 03 ✓ 04 ✓ 05 ✓ 06 ✓ 07 ✓ 08 ⚑ 09 ⚑ 10 ✓ 11 ✓ 12 ✓      │
│        bind plan places record timeline prompts board panels shoot …   │
│        click a chip → its timing row, its log slice, its gate faults   │
├──────────────────────────────────┬─────────────────────────────────────┤
│ MASTER  ┌──────────────┐         │ VERDICTS                            │
│         │ ▶ master_iter2│ 160 s  │ PLAN   ✓ judge:plan@1  56bd2e17     │
│         │   1:1  -14.1  │ LUFS   │ LAYOUT ✓ grid_layout@1              │
│         └──────────────┘         │ PANELS ⚑ panel_eye@1 c7e3eb93       │
│  iter1 · r2v  · qc: 23/23 cuts,  │   landmark at shot_00 (x28) ▸       │
│  23/23 lines heard, gap 5.8/6.0  │ TAKES  ⚑ take_eye@1 21227f91        │
│                                  │   face-at-end T16 0.74 · lag T16 ·  │
│ PLAN  Q: "Can the guns stop      │   cut T19 · jump T19 → still        │
│ them?" · answer shot 19 · 24     │ MASTER ○ not yet signed             │
│ shots · 23 lines · 3 beds ▸json  │ [redo PANELS with note]             │
├──────────────────────────────────┴─────────────────────────────────────┤
│ PANELS (contact.png)   TAKES (strip_*.png)                             │
│ [00][01][02][03][04]   [T00][T01][T02]…[T16⚑][T17][T18][T19⚑ still]   │
│ [05][06][07]…  ▸ all   hover: <video preload=metadata>; click: lightbox│
├────────────────────────────────────────────────────────────────────────┤
│ LEARNINGS (tail 5)                 │ LOG run …140212 (tail, WARN+)     │
│ 14:09 09 EYE_TAKES keep_best ⚑ …  │ 22:20 WARN plan_check refused: …  │
│ 14:09 09 EYE_TAKES replan_cell 5   │ 22:19 WARN PLAN: measured 24.0 →  │
│ 14:08 09 EYE_TAKES head_cut 4      │ …                                 │
├────────────────────────────────────┴───────────────────────────────────┤
│ TIMING  bind 0.1s · plan 31s · … · shoot 2h50 · edit 6m · qc 412s      │
└────────────────────────────────────────────────────────────────────────┘
```

Everything here is a file the row points at (`plan.json`, `plan.verdict.json`, the two
`eye_<sha8>.json`, `qc_r2v.json`, `cut/master_iterN.mp4`, `learnings.jsonl`, `timing.jsonl`,
the run's log). A verdict whose `sha8` no longer matches its artefact shows `~ stale`.

### 5e. Book `/b/20260827135508`

```
┌ Studio › Books › The War of the Worlds ── H. G. Wells · 27 chapters ── ┐
│ [hold book] [audit sheet ▸] [casebook ▸] [org chart ▸]                  │
│ analysis ✓ · screenplay ✓ (target: episode) · refs ✓ style krea2 ·     │
│ trailer ✓ · episodes 13 of 27 · published 11 · gpu total 41h            │
├──────────┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──────────────┤
│ unit     │01│02│03│04│05│06│07│08│09│10│11│12│13│14│15│16│  …27         │
├──────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──────────────┤
│ episode  │✓ │✓ │✓ │✓ │✓ │⚑ │⚑ │✓ │⚑ │⚑ │✓ │⚑ │● │↩ │○ │✋│ ○○○○○○○○○○○  │
│ publish  │▲ │▲ │▲ │▲ │▲ │▲ │▲ │▲ │▲ │▲ │▲ │  │  │  │  │  │              │
├──────────┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──────────────┤
│ REFS  cast 9 sheets ✓ · 2 props ✓ · 6 voices ✓ · LOOK ✓ look@1 (pack sha)│
│ [sheet thumbs: narrator][artilleryman][curate][…]                       │
│ ANALYSIS 01✓ 02✓ 03✓ 04✓ 05✓ 06✓ · SCREENPLAY 01✓ 02✓ 03✓ 04✓ 05✓        │
│ TRAILER 01✓ … 10✓ · master ▶                                             │
│ AUDIT  rows 41 · open notes 3 · last owner note 09-24 ▸                 │
└────────────────────────────────────────────────────────────────────────┘
```

The grid row is the Airflow grid the research file named, reduced to what this studio has:
units across, departments down. Cells link to unit pages; `▲` is a public upload.

### 5f. Components

`app.py` (FastAPI, ~12 routes) · `views.py` (pure rows → view-models; the tested layer) ·
`library_paths.py` (the `/lib` guard) · `templates/base.html` (nav, tokens, legend) · partials
`_floor`, `_lanes`, `_rows`, `_progress`, `_verdicts`, `_gallery`, `_tail` (each also a poll
target) · pages `home`, `floor`, `department`, `unit`, `book` · `static/studio.css` (the
org-chart page's `:root` block copied; a test asserts byte equality) · `static/htmx.min.js`
(vendored) · `static/studio.js` (≤ 60 lines: lightbox, theme, hover video). No graph library.

### 5g. Stack

| option | verdict |
|---|---|
| **FastAPI + Jinja2 + htmx** | **Recommended.** `response_model=` pydantic classes make the view-model the contract (the repo's rule); `TestClient` runs in-process so no test spawns a server; Jinja partials are the poll unit; htmx is one vendored file; zero build. Adds `fastapi`, `uvicorn`, `jinja2`, `python-multipart`, all pinned `==`. |
| Starlette only | Same runtime, loses `response_model` and the OpenAPI page for free; saves one dependency. Not worth it. |
| NiceGUI | Pure Python, but it owns the page through a websocket and its own component tree: harder to test without a browser, harder to keep in the org-chart page's design language, and it fights the "rows and files" reading. Fallback only. |
| Static HTML that fetches JSON | Every page becomes client-side state; `file://` breaks fetch; two renderers (JSON + DOM) to keep in step; tests need a browser. No. |

Tests (pytest; no server, GPU or network): `views.py` against an in-memory SQLite seeded via
`studio/db.py` plus a `tmp_path` library with a fixture unit derived from the contract (a
plan, two verdicts, an empty `takes/`); `TestClient(app)` per route asserting the row's glyph
and the `hx-trigger`; the `/lib` guard against `..`, symlinks and `.py`; CSS token equality;
and a grep test that the web process imports nothing from `scripts/`. Launch: `uv run studio
ui` on `http://localhost:8700` (`--open` raises the browser); Datasette on 8701 optional.

### 5h. Columns the UI needs on the work-order row (for experts A/B)

`stage`, `codex_id`, `unit`, `state` (§2), `step_id` + `step_name` (the cursor),
`progress_done/total/label`, `attempt`, `cost_kind` (`gpu_seconds` | `credits` | `tokens`),
`cost`, `ceiling`, `started_ts`, `last_ts`, `last_event` (one line), `run_id`, `priority`,
`hold_note`, `blocked_by`, `deliverable` (relative path), `iteration`, `publish_state`, and a
`verdicts` JSON column (`{gate: {verdict, judge, sha8, faults}}`) so the strip needs no file
read on a poll. Artefact paths are relative to the book, never absolute.

## 6. What `architecture/index.html` becomes

A **link, served unchanged at `/org`**; the design language flows the other way (the UI copies
the page's tokens and fonts; a test keeps them equal). Not a tab, because the page has three
duties the UI must not inherit: one self-contained file published to claude.ai, changed in
the same commit as every architecture change, describing a *proposed* future beside the built
present. Fold it in and either the UI becomes a document or the document grows a server. The
nav reads Home / Floor / Books / Org chart, so the owner reads the company from one chrome:
the chart is who reports to whom, the floor is what they are doing now. A department header
links to its subtree (`/org#episode`); the chart's department cards gain one link back
(`/d/episode`), the only edit the page needs.

## 7. Three doubts for the debate

1. **Is "flagged" a state or a decoration?** I made it a row state (amber, needs nobody now).
   If A/B keep `state` to the events CHECK set and put flagged only in `verdicts`, the home
   lane loses its amber count and the owner's audit pile goes invisible at a glance. The
   owner should rule on which reading he wants at 07:00.
2. **Progress as a row column vs. read from disk.** The runner writing `18/25` every take is
   the cheap poll but one more write inside the render loop, and wrong if a step crashes
   between the file and the row; globbing `takes/T??.mp4` is always true and costs a glob
   every 2 s. I chose the column, with the glob as the unit-page truth; expert C may not.
3. **Does Distribution deserve a lane before it is a registry stage?** `youtube.json` and
   `uploads.jsonl` exist, but `stages.yaml` has no `publish` stage, so no runner writes its
   rows. A lane read from files breaks "the UI never computes a state a runner did not
   write"; hiding it hides the one number the owner counts weekly.
