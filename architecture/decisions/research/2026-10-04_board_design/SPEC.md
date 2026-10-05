# The board, premium — the ruling over ten reports

**Status: PROPOSED 2026-10-04 — for the owner's review with the mockups.** Nothing is built.
Owner's ask: "research in UX and UI .. to be like premium studio tracking UI and graphics ...
research and plan it first". Scope ruled by the owner: the whole board; all four looks blended;
plan + clickable mockups before any build. Ten reports (01–10) in this folder; this file rules
their disagreements. Build plan: `PLAN.md`. Mockups: `mockups/index.html`.

## The brick

**One table, many zooms, one voice.** Every studio tracker the reports studied (ShotGrid, ftrack,
Kitsu, Frame.io, Dagster, Linear) is one table — entity × step → state, with versions and notes —
shown at different zoom levels (01). The board already has that table (`work_orders` ×
`work_steps`, masters/takes as versions, verdicts/learnings as notes); what it lacks is *one voice*:
six step-bar implementations, thirteen colour families, a state drawn three colours on three pages
(06, 10). The redesign is therefore not new data — it is one component set, one token set, one
state vocabulary, drawn at five zooms: **studio (home) → book → department → unit → shot**.

**The identity rule (06):** *paper is the office, the stage is the screening room, ink is the
voice, colour means state and nothing else.* Everything you read stays on warm paper (light or
dark); every picture, take and master sits on a neutral-dark `--stage` well in both themes.
Barlow Condensed for display, IBM Plex Sans for text, Plex Mono for ids and numbers.

## Bugs the research found (fixed first, whatever else is decided)

| # | bug | found by | page |
|---|---|---|---|
| B1 | Unit page loads full PNGs for 120 px tiles: **36.4 MB, 954 ms** on ep12; 18 of 24 take tiles render blank. `/thumb/` already serves 18 KB WebP. | 02, 08, 10 | unit |
| B2 | Home "Needs you (0)" while ep12–ep16 are published with 4–37 faults: flagged units never count. | 07 | home |
| B3 | `--ink-3` fails WCAG AA (4.11:1 paper, 3.77:1 paper-2) — all muted text, th, eyebrows. | 06, 10 | all |
| B4 | Deferred is purple / blue / amber on three surfaces; stale red vs spec'd dashed. | 06 | all |
| B5 | Done and failed bar segments have 1.01 luminance contrast — identical to colour-blind eyes. | 06 | dept, book, unit |
| B6 | "Notify me" never fires in a background tab (polling stops when hidden); `new Notification` throws on mobile; no hysteresis; a dead board keeps "ticking". | 09 | unit |
| B7 | `/b` 404s behind every "Books" crumb; `/org` is a dead end. | 07 | book, org |
| B8 | Department re-sends a 77 KB table every 10 s, closing open menus and losing scroll. | 09, 10 | dept |
| B9 | Queued `○` and blocked `◌` look identical at 12 px; escalated `✋` is a colour emoji on Windows. | 03, 06 | all |

## Rulings

| point | positions | ruling |
|---|---|---|
| Dark vs paper | 02 dark well; 06 paper + stage; dark-by-default seat | **Paper office + dark stage** (06). Light default, the dark theme is the "screening room". Only media sits on `--stage`. |
| Status salience | 01/06: done is quiet; ops: saturated fills | **Done is quiet** (outline / thin green), fill is spent on running and attention states; attention states carry a **pattern** in bars (failed hatch, deferred dotted, held neutral hatch, flagged lighter amber) so colour is never alone. 15 of 31 department rows are done; they must recede. |
| State colours | 01: 5 fixed states; 06: 11 states × fg/bg/bar | **11 shown states on 06's token table** (`--st-<state>`, `-bg`, `-bar`), grouped for summaries into 01's five families (idle, live, review, done, fail). Flagged becomes true amber `#8a5a00`. |
| Icons | Unicode glyphs today | **Vendored 24-icon Lucide sprite** behind one `icon()` macro (06); Unicode kept only for plain-text contexts. |
| Type | 23 sizes today | **9 roles** (06 §4.3), 10 px floor, tabular numbers everywhere numbers align. |
| Navigation | 07 top bar; sidebar seat | **Top bar** + a **GPU pill on every page** (`● ep17 02 plan · ~21:40`) + **inbox badge** + **⌘K palette** (navigate, and this page's actions through the confirm dialog) + keyboard map (`g`-chords, `j/k`, Space peek, `?` sheet replaces the legend footer) (03, 07). Phone: one-line bar + bottom tabs Now · Inbox · Books · Search. |
| Landing | 07 Now; 04 GPU-went; 01 3-lane board | **`/` is "Now"**: the GPU lane card (running unit, finish range), **Needs you** (inbox rule incl. flagged-not-acknowledged), **Up next** (3), **Where the GPU went, 7 days** (productive vs burned on failure: today 48 of 113 GPU-h burned, 04), and a quiet "shipped with flags" lane. |
| Inbox | B2 | One rule (07): failed, escalated, deferred, stale, looping (≥3 of last 4 runs same step), and **flagged not yet acknowledged**. Needs a new `acknowledge` order kind — a one-word addition to `orders.kind` (owner's hand, no judge change). |
| Unit — running | 03: finish time hero; 04: p50–p90 range; live-card big clock | **One header**, no duplicate h1: id · title · state · actions. Hero = **"done around 21:40"** with the range shown under it ("p50 21:40 · p90 22:55", amber past p90); elapsed is secondary (04 + 03, both kept: the hero is the p50, the range is labelled). |
| Unit — finished | 02: media first | **Screening room** on top for a unit with a master: square player on stage, lanes under it (shots from `qc_r2v.edit.segments`, faults mapped to frames, lines), the judges' stamps, a **version stack** `v7 ▾` deduped by hash (iter5 = iter7 today) with compare (side-by-side / wipe / flip). |
| Unit — layout | 01 tabs; 03 sidebar; paper single scroll | **One scroll + a 264 px sticky properties sidebar** (state, step, attempt, GPU, cost, times, lease, gates, files, orders) with section jump-links; collapses to a 2-column `<dl>` under 900 px. No tabs: a glance must not need a click (03 wins over 01). |
| Unit — history | 04 run matrix; 05 run strip; 01 activity stream | **Run matrix** (12 steps × every run from `events`, skipped hollow, a duration strip on top, **loop brackets** `↻ ×4 at 09 shoot · 6h12`) replaces the Health chips; a click on a run opens its **waterfall** (05's run strip at run grain). Below: **Activity** = the run log grouped by step (failing group open, level chips, search) + verdict rounds as threads + orders (01 + 04). |
| Unit — pictures | 02 one shot strip; 08 every stage side by side | **One shot strip** (24 cards; per card: panel thumb, the take's own frame when a take exists, ✓/⚑/○ per stage, try count). The lightbox becomes the **shot view**: panel → take → its segment of the master, ↑/↓ across stages, ←/→ across shots, `R` redo, ghost "queued" card after a redo (02, 08). |
| Department | 01 12 named step tags + thumbs; 03 dense, group by status, `!n` gates | Rows grouped **by book, then by status** (Running / Needs you / In progress / Done collapsed). Step bar kept with **patterns**; the six gate columns become **one "gates" cell** showing only non-pass gates (`plan !18 · panels !531`); **unit title on every row**; a **40 px face** (poster) only where a poster exists — never an empty box. Shared blocking reason once on the group header (`7 waiting on refs/04`). Actions inline on hover, `⋯` on touch. |
| Book | 01 rows = units; 07/08 season wall | **Season wall** of master posters on top (scrub the existing contact sheets; zero video), then the **season matrix** units × 12 steps (05, 16 px glyph cells), then refs/cast strip. `/books` shelf added (fixes B7). |
| Floor → Queue | 04 GPU lane; 07 rename | **`/queue`**: one GPU lane timeline (24 h back, now line, 12 h forward; queued work as hatched p50 ghost bars → a queue ETA; idle strip), then the queue **grouped by department with counts**, actions behind `⋯` (2,681 → < 600 DOM nodes). `/floor` redirects. |
| Charts | 05/10 hand SVG; library seat | **Server-drawn SVG Jinja macros, 0 KB** (`viz.py` + `_viz.html`), with four validated `--viz-1..4` tokens (GPU rust, judgement blue, CPU ochre, waiting violet) for step classes; status keeps its own tokens. uPlot (21.7 KB) held in reserve for a dense GPU trace. No KPI deltas until ≥ 4 comparable weeks. Cost stays a number. |
| Live | 09 pulse + morph; SSE seat | **`/api/pulse.json`** (≈1 KB fingerprints + events since a cursor) polled every 2 s visible / 10 s hidden (Worker timer); sections refresh on `pulse:<section>`, 204 when unchanged; **idiomorph** morph swaps keep menus, focus and scroll (fixes B6, B8). No SSE, no skeletons, no optimistic state. |
| Motion | 09/03 one loop; polish seat | **One looping animation per viewport**; terminal states never animate; no rolling digits or row re-sort animation; a "still" toggle + reduced-motion (WCAG 2.2.2); one cross-document view transition (the unit name). |
| Notifications | 09 table; notify-all seat | Notify on: done (silent), dead/failed (sticky), refused, flagged, stalled (2-pulse hysteresis, 15 min cooldown), looping, GPU idle. Never on step events. Title + favicon carry state and the needs-you count. A "since 14:02" strip is the inbox of everything else. |
| Approve button | 02 none; review-tool convention | **None.** Judges sign; the owner's hand is acknowledge / redo / hold / bump / retry. An owner "accept" verdict would be a separate owner decision. |
| URLs | 07 book-first slugs | **Phase 3**: `/b/<slug>/episode/ep17` canonical, old `/d/…` 301-redirects; deep links `/…/shot/05`, `/…/take/T05`, `/…/gate/PLAN`, `/…/run/<id>` rendered server-side. |
| Fonts | 10 self-host | **Self-host** Barlow Condensed + Plex Sans/Mono (offline + deterministic screenshots). |
| Engineering | 10 | Commit 0 turns markup-pinned tests into answer-pinned; CSS out of `base.html` into cached `static/css/{tokens,components,pages}.css` with `@layer`; `components/` macros (mark, pill, step_bar, gate_cell, frame, tile, sparkline, run_matrix) each with a test; one `data-tone` map; a `@pytest.mark.local` screenshot + axe + budget harness with the gstack browse binary. |

## What needs the pipeline, not the board (separate, architecture-page changes)

The web process stays read-only and never decodes video (08). These belong to step scripts and are
architecture changes (decision file + Future tab when built):
1. `poster.jpg` per unit (master frame, else newest take, else contact sheet) — `deliver` / `edit`.
2. Take sprites (12 cells) and a 1 s master sprite + WebVTT — `take_strip.py`, `qc`.
3. `cut/master_iterN.cut.json` per iteration, so "iter1 vs iter7" names the changed shots — `edit`.
4. `timing.jsonl` rows carry `step` and UTC; the runner writes `work_steps.seconds` (all 0 today).
5. Learnings keep `faults` as a list (the board parses notes today).

Until they land, the board falls back (no poster → no face; no sprite → the 3 content frames).

## Budgets (10)

Unit page media < 2 MB (36.4 MB today); ≤ 1,500 DOM nodes on department/unit (floor 2,681 today);
JS ≤ 80 KB per page (htmx 2.0.4 + idiomorph + board.js + palette); pulse ≤ 1 KB; every route < 50 ms.

## Publishable artefacts (EB-1)

Four pieces generalise beyond this repo; each is a small standalone package with a write-up:
1. **`htmx-pulse`** — fingerprint pulse + morph for htmx boards over files another process writes (09).
2. **`<review-player>` / shotlane** — a dependency-free web component: native `<video>` with shot and
   judge-fault lanes, linked compare, sprite scrub (02, 08).
3. **`css-token-contrast`** — a stdlib pytest helper that reads CSS custom properties in both themes
   and asserts WCAG pairs (06).
4. **Tone-based Jinja component set + screenshot/axe harness** for htmx boards (10).
