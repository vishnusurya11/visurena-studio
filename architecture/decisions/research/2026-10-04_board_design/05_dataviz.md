# 05 — Data visualisation & graphics for the board

Researcher 05, 2026-10-04. Scope: which charts earn a place on the board, given the
ledger and library as they are today. All numbers below come from read-only queries on
`db/visurena_studio.db` and from `library/20260827135508_the-war-of-the-worlds/episodes/ep12..ep17`
`learnings.jsonl` / `timing.jsonl`.

## 0. Verdict in five lines

1. **Hand-written SVG from Jinja macros is the only chart library this board needs: 0 KB.**
   The board already draws its signal trace this way (`_live_vital.html`). Every chart below has
   at most ~600 marks, renders on the server, swaps with htmx, and takes its colours from CSS tokens.
2. Four forms earn a place: a **status matrix** (season progress), a **run strip**
   (the Gantt, shaped like Grafana's state timeline), **ladder small multiples** (faults per
   gate across passes), and a **GPU-day column strip** with a 24 h ceiling. Everything else is a number.
3. **Cost per unit is not a chart.** It runs $0.35–$4.11 per unit and covers LLM spend only. Show it as text.
4. **Judge flag *rate* is not a chart yet.** The taste gates flagged 14 of 15 signatures on ep12–16,
   so a rate line would sit flat at about 100 %. Show the gate × unit fault matrix instead.
5. The token inks (`--think`, `--accent`, `--qc`…) **fail the validator as chart marks**. They are
   text colours. Section 3 gives four chart tokens per theme that pass the validator.

## 1. The data as it is (and the traps that would break a naive chart)

| Fact | Value | Consequence |
|---|---|---|
| Episode units with real step/ladder data | 6 (ep12–ep17, WotW); 20 older units carry only `progress` like `5/12` | Small-n. Use small multiples and dot plots, not trend lines |
| Runs per unit (`events.run_id`) | ep12 32 · ep13 52 · ep14 34 · ep15 37 · ep16 32 · ep17 4 | One unit is many runs, so the Gantt's rows are **runs** |
| Wall time first→last event | ep15 11 h · ep12 23 h · ep14 44 h · ep16 53 h · ep13 60 h | A 5× spread, so an ETA must be shown as a range |
| GPU-ish hours per unit (timing.jsonl GPU stages) | ep14 33.6 · ep13 20.8 · ep12 9.6 · ep16 3.1 · ep15 2.9 · ep17 0.3 | A 10× spread, so a ranked bar reads it well |
| GPU-ish hours per day | 09-29 **20.9** · 09-27 13.6 · 09-28 10.5 · 09-25 8.1 · 09-26 7.2 · others < 3.2 | The 24 h ceiling is real (one GPU), so plot against it |
| Where ep14's time went | takes 1130 min · take_dq 279 · take_content 274 · panel_content 121 · grids 82 | Takes dominate; this is a part-to-whole by step class |
| LLM cost per unit (`usage`) | ep13 $0.76 · ep14 $2.80 · ep15 $4.11 · ep16 $2.69 · ep17 $0.44 | Too small and too few for a chart |
| Ladder rungs (`learnings.jsonl`) | ep13 PLAN 58 rungs, EYE_TAKES 33; ep14 PLAN 60, EYE_TAKES 44 | A chart per gate is legible; one combined chart would be noise |
| Fault values | PLAN is bimodal: 1–7 vs 43–66 within one ladder (ep14: 3→55→1→1). EYE_PANELS ep12 = **531** | Needs a sqrt scale plus an overflow caret, never a linear axis |
| `budget` gate rows | `measured` is negative seconds (−12 037) | A different unit. Keep it out of the fault charts |
| Gate outcomes ep12–16 | PLAN APPROVE 5/5; EYE_PANELS flagged/keep_best 5/5; EYE_TAKES flagged 4/5; MASTER flag 5/5 | A rate is uninformative. Show counts and terminal kinds |
| Failure reasons (`events.detail`) | DEFERRED PLAN 29 · qc FAIL 22 · takes_r2v exit 20 · panel 8 | A ranked list. Text with inline bars, not a pie |

**Traps the chart code has to handle:**
- **T1 — `work_steps.seconds` is 0 on every row**, and `work_steps.started_at/ended_at` span the whole
  unit (ep14 step 01 runs 09-28 → 09-30 "skipped"). A Gantt built from `work_steps` would be wrong.
  Pair `events` `started` with `completed`/`failed`/`deferred` per `run_id` + `step_id` instead
  (verified on ep16: step 02 at 19:38:15→19:51:15 = 13 min).
- **T2 — two clocks.** `timing.jsonl` is naive local time (UTC−7). The ledger is UTC with `Z`. ep17's
  bind is `2026-10-04T17:21:12` in timing.jsonl and `2026-10-05T00:21:11Z` in work_orders. Normalise
  to UTC on read and render in local time. (The 4c42ca6 commit fixed this for the rail. The charts need the same fix.)
- **T3 — `work_orders.gpu_seconds` vs timing.jsonl** agree within ~15 % (ep16 2.7 h vs 3.1 h). Choose one
  source per chart and say which in the caption. Ledger for totals, timing for breakdowns.
- **T4 — Study in Scarlet units** `ep10–ep14` are `blocked` but carry 3–5 GPU-hours from an older
  regime. A season chart must not count them as progress.

## 2. What the outside world teaches, applied here

| Source | Lesson | Applied to |
|---|---|---|
| Tufte, *Sparklines: theory and practice* — https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/ | Word-sized graphics, inline with text, at the resolution of the type. No axes. Mark the end value and the extremes | GPU-day strip on home; per-unit GPU sparkline in dept rows |
| Tufte, *Envisioning Information* (1990), ch. "Small Multiples" | The same frame repeated, so the eye compares the data, not the frames | Ladder panels per gate; mini status matrices per book |
| Stephen Few, *Bullet Graph Design Spec* — https://www.perceptualedge.com/articles/misc/Bullet_Graph_Design_Spec.pdf | One measure against a qualitative range and a target, in a small space | GPU-hours/24 h meter; plan-duration vs median |
| Few, *Practical Rules for Using Color* — https://www.perceptualedge.com/articles/visual_business_intelligence/rules_for_using_color.pdf | Use soft, natural colours by default. Keep bright colour for what needs attention | Paper look: ink ramp for magnitude, accent only for "now" and "stuck" |
| Grafana **State timeline** — https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/state-timeline/ | One row per entity, state bands over time, value text inside the band only when it fits | The run strip (rows = runs, bands = steps) |
| Grafana **Status history** — https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/status-history/ | A grid of entity × time bucket coloured by state | Season status matrix (units × steps) |
| Grafana **Stat** — https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/stat/ | One big value with an optional sparkline behind it, coloured by threshold | KPI row: GPU today, queue depth, next finish |
| Datadog **Query value** — https://docs.datadoghq.com/dashboards/widgets/query_value/ | A single number with conditional formatting, no chart | Cost per unit, taste-gate clean count |
| Datadog **Heatmap** — https://docs.datadoghq.com/dashboards/widgets/heatmap/ | Distribution over time when there are many series | Rejected here: n is too small (see §5) |
| Observable Plot — https://observablehq.com/plot/ (cell, tickX, barX marks) | The grammar of marks: cell = status matrix, barX with x1/x2 = Gantt, line + dot = ladders | Shapes the Jinja macro names; we don't ship the library |
| Linear Insights — https://linear.app/docs/insights | Charts sit beside the work they describe. Click a bar to get the issues behind it | Every chart mark links to its unit/run (htmx) |
| Vercel Analytics — https://vercel.com/docs/analytics | One quiet area/column chart, a KPI row above it, a ranked list below it | Home layout: KPIs → GPU-day strip → "where time went" ranked list |
| uPlot — https://github.com/leeoniya/uPlot | 50 KB min / **21.7 KB gz** time-series library built for 100k+ points | Kept in reserve (§4) |
| `dataviz` skill (bundled) | Choose the form first, then validate colour, then mark specs. One axis only. Status gets a glyph | Every card in §5 |

## 3. Colour — chart tokens that pass, derived from the paper palette

I ran the skill's validator (`scripts/validate_palette.js`) on the existing tokens used as
categorical marks (`--think,--accent,--qc,--invent,--ok` on `--paper`). It **FAILS**: lightness out
of band, chroma below floor, `--qc`↔`--accent` ΔE 0.5 under protanopia. These are ink colours, built
for text on paper. Add a separate chart family to the `:root` block next to them:

```css
/* light, validated on --paper #f6f3ec: band, chroma, CVD ΔE 19.7 protan / 14.3 tritan, normal ≥27, contrast ≥3:1 */
--viz-1:#c4492c;  /* rust   = GPU render (takes, grids, panels)      */
--viz-2:#2b6cb0;  /* blue   = model judgement (plan LLM, VLM eyes)  */
--viz-3:#a98516;  /* ochre  = CPU / ffmpeg (assemble, qc, lines mux) */
--viz-4:#7b4fa8;  /* violet = waiting (deferred, queued, lease)     */
/* dark, validated on --paper #181613: all PASS (tritan 7.1, inside the legal 6-8 floor band → labels required) */
--viz-1:#d8603f; --viz-2:#4a88c8; --viz-3:#a8861c; --viz-4:#9a72c8;
```
- On `--paper-2` the ochre drops to 2.87:1 (WARN). Put charts on `--paper` only, or label the ochre marks.
- **Sequential (magnitude), one hue:** `--rule` → `--line` → `--ink-3` → `--ink-2` → `--ink` (the
  warm-grey ink ramp the page already has). Heat cells, GPU columns and per-unit bars use it.
  Colour is not spent on magnitude.
- **Emphasis:** a single mark in `--accent` (the running unit, today's column, the stuck step), the rest in the ink ramp.
- **Status (reserved, never a series colour):** done `--ok`, flagged/kept `--qc`, failed/refused
  `--accent`, deferred `--viz-4`, running `--think`, queued/blocked `--rule-2` outline. **Every status cell
  carries the existing legend glyph** (✓ ⚑ ✕ ↩ • ○ ‖ ~ –) so colour is never the only channel.
- **Texture:** loops and keep_best get 45° hatching (`<pattern>` in one shared `<defs>`), which matches the
  rail's diagonal stripes for "loop". It also covers print and `forced-colors`.
- Dark mode is **selected, not flipped**. The `--viz-*` dark steps above are their own values, validated on the dark paper.

## 4. Library decision

| Option | Measured size (min / gzip, jsDelivr 2026-10-04) | Verdict |
|---|---|---|
| **Hand SVG via Jinja macros** | 0 KB, plus ~1.5 KB shared hover JS | **Default for every chart here** |
| uPlot 1.6.31 `uPlot.iife.min.js` + css | 50.3 KB / 21.7 KB + 1.9 KB | Reserve. Use only if a dense zoomable series appears (e.g. per-second GPU VRAM/util trace from nvidia-smi, 86 400 pts/day) |
| Observable Plot 0.6.17 UMD | 209 KB / 68.8 KB **+ d3 7.9 279.7 KB / 92.4 KB** | Reject: 490 KB for marks we can write as 20-line macros |
| Chart.js 4.4.7 UMD | 205.9 KB / 69.6 KB | Reject: canvas, so no CSS tokens, no htmx partials, no print, no `<title>` tooltips |
| ECharts 5.6 full | 1 034 KB / 334 KB | Reject: 20× htmx's 51 KB for a single-user local board |

Why hand SVG wins *for this board specifically*:
1. **Server truth.** The page is FastAPI + Jinja + htmx with no build step. SVG built in a macro
   is part of the partial that htmx swaps, so there's no client chart state to reconcile on a 2 s poll.
2. **Tokens for free.** `fill="var(--viz-1)"` follows `data-theme` and `prefers-color-scheme` with no
   JS re-render. Canvas libraries need a theme object rebuilt on toggle.
3. **Tests can't spend money and must be cheap.** A macro is a pure function of rows → string, so pytest asserts
   `'<rect' in out` and the counts (CLAUDE.md: every function tested). Library charts need a browser.
4. **Accessibility.** Every mark gets a `<title>` (native tooltip plus screen-reader name). Every chart
   gets a `<details><table>` twin (the skill's "table view exists" rule).
5. Scale check: the largest chart is the season matrix at 30 books × 5 depts = 150 cells, or the run
   strip at 52 runs × ≤12 steps ≈ 600 rects. That is trivial for the DOM.

Proposed module: `studio/command_center/viz.py` (pure functions: scale, ticks, `sqrt_scale`, `pairs_from_events`)
and `templates/_viz.html` (macros: `col_strip`, `bar_rank`, `status_matrix`, `run_strip`, `ladder_panel`,
`meter`, `stack1`). One shared `static/viz.js` (~40 lines) draws the crosshair/hover readout. The page
still works without it, because `<title>` is the fallback.

## 5. Chart cards — the seven asked for, decided

Global mark spec (from the skill, sized for this board): text 11 px `--ink-3` tabular-nums for axes,
12 px `--ink-2` for labels. Gridlines 1 px solid `--rule`, horizontal only. Lines 2 px. Dots r=4
with a 2 px `--paper` ring. Bars ≤ 14 px thick (a dense board), 2 px `--paper` gap, 3 px rounded data end.
Every chart has a sentence-case title that states the finding ("GPU busy 20.9 h on 29 Sep"), not the metric name.

### 5.1 Season progress: **status matrix** (Grafana status history / Plot `cell`) — EARNS IT
- **Book page `/b/{codex}`:** rows = units ep01…epNN in reading order, columns = the 12 steps
  bind…deliver. Cell 16×16 px, 2 px gap, so 12 cols = 214 px wide and 17 rows = 306 px. Fits a 400 px phone with
  the unit label column (48 px). Cell fill = status token at 22 % opacity (`color-mix(in oklab, var(--ok) 22%, var(--paper))`),
  glyph 10 px in the status ink centred. The running cell gets a 2 px `--accent` outline. A row's right edge
  shows `12/12` text and the master's iteration (`iter6`).
- Fields: `work_steps.state` per (order, step) where it exists. Otherwise fall back to `work_orders.progress`
  (`5/12` → first 5 cells done, rest hollow) with a dotted border meaning "inferred, pre-ledger" (trap T4).
- **Home `/`:** the same macro one level up: rows = 30 books, columns = 5 departments, cell = `codex.<dept>_status`.
  150 cells in 5×18 px columns, 96 px wide. It answers "where is the season" in one glance.
- Click a cell → `/d/{stage}/{codex}/{unit}` (Linear: the mark is the link). Hover → `<title>` "ep14 · 09 shoot · flagged keep_best · 18 attempts".
- Light/dark: cells use status tokens, which already have dark values. No colour is used for magnitude.

### 5.2 Step durations: **run strip** (Grafana state timeline as a Gantt) — EARNS IT
- **Unit page, below the live card, in a "runs" disclosure.** Rows = runs (`run_id`, newest at top),
  12 px tall with 4 px gap. ep13's 52 runs = 832 px, so show the last 12 rows and add "show 40 more" (htmx).
  x = wall clock, shared across rows, local time. Ticks at day boundaries plus 6 h, in `--ink-3`.
- Segment per step, from `events` pairs (trap T1). Fill = step class (`--viz-1` GPU, `--viz-2` judgement,
  `--viz-3` CPU), with the outcome on the segment's right end as a 2 px cap: `--ok` completed,
  `--accent` failed/refused, `--viz-4` deferred. Skipped steps draw nothing (they took 0 s).
  The step id is written inside the band only if the band is ≥ 22 px (Grafana's rule).
- Row label (64 px, left): run start `HH:MM` + the ending word (`refused`, `deferred`, `done`), the same words as
  the HEALTH chips already on the page, so the two read as one system.
- Why rows = runs: the unit's story *is* the retry pattern. ep16 on 01 Oct went plan→deferred three times
  in an hour, then refused at 04 record, 05 timeline, 06 prompts ×2, then ran 07→09 and deferred at 09 shoot.
  A per-step Gantt would merge all of that into one bar.
- Second view on the same data (dept page): **median step duration**, horizontal bars ranked, one per step
  (12 rows × 14 px), ink ramp, with the current unit's value as a `--accent` tick (a bullet-graph idea from Few).
  This is also the source of the rail's `median_s`, so the rail and the chart cannot disagree.

### 5.3 Fault count per gate across passes: **ladder small multiples** — EARNS IT
- **Unit page, GATES section:** one panel per gate that has a ladder (PLAN, EYE_PANELS, EYE_TAKES, MASTER).
  Panel 168×84 px with the same frame each time (Tufte). x = rung 1…5 (`attempt`). y = faults on a **sqrt** scale, 0–60
  fixed across panels. Values > 60 are pinned to the top with a ▲ caret and the number (ep12 EYE_PANELS 531,
  ep14 PLAN 55–66).
- Each ladder (the sequence of rungs ending in a terminal row) is a 1.5 px `--ink-3` polyline. The latest
  ladder is 2 px `--accent` with direct labels on the first and last value. Its end marker shows how it ended:
  filled dot = passed, hollow ⊘ = kept-not-passed (`keep_best`/`still`/`flag`), ↩ = defer. These are the same glyphs as
  the ladder chips in `_live_ladder.html`.
- What it shows that the chips can't: ep14 PLAN's ladders saw-tooth 3→55→1→1 again and again. The gate is
  not converging, it is flipping between two batteries. That is a finding the owner can act on (it is the "a fix that
  changes nothing" lesson, made visible).
- `budget` rows are excluded (trap: different unit). Budget shows as a `meter` (§5.5).
- Hover: a vertical crosshair on a rung shows `action`, `seconds`, and the first 120 chars of `note`.

### 5.4 Judge flag rates: **gate × unit fault matrix**, not a rate — CHANGED
- **Department page `/d/episode`:** rows = units, columns = PLAN · EYE_PANELS · EYE_TAKES · MASTER · RENDER.
  Cell = the signed fault count (from `work_orders.verdicts.*.faults`) as a number, with its background on the ink
  ramp (sqrt binned 0 / 1–5 / 6–20 / 21+), plus the terminal glyph (✓ pass, ⊘ kept, ⚑ flag).
  The number is always visible, so colour is never the only channel.
- Above it, one Datadog-style query value: **"taste gates clean: 1 of 15"** (ep12–16). This is the honest
  rate, as text. A rate line becomes worth drawing when N ≥ 20 signatures per gate, which is about 5 more episodes.
- This matrix is also the "a terminal is not a pass" check the owner's memory asks for before upload.

### 5.5 GPU hours per day / per unit: **column strip with a 24 h ceiling** + ranked bar — EARNS IT
- **Home and floor:** 30 day-columns (6 px wide, 2 px gap = 238 px; it fits beside a stat on a phone), height 40 px
  where the top edge **is 24 h** (one GPU, so a day can't exceed it). That makes the column a utilisation meter
  without a second axis. Ink-ramp fill. Today's column is `--accent`. Label only the max ("20.9 h, 29 Sep")
  and today (Tufte's end value and extreme). Each column stacks by step class (`--viz-1/2/3`) only when the
  strip is the focus (floor page, 120 px tall). On home it stays single hue.
- Paired **stat** to its left: "GPU today 0.3 h · 7-day 39.9 h of 168" (Grafana stat with the strip as its sparkline).
- **Dept page:** per-unit GPU hours as a horizontal ranked bar column inside the units table (a data bar,
  max 120 px, value at the tip): ep14 33.6 … ep17 0.3. Source: `work_orders.gpu_seconds` (trap T3: say so in the header tooltip).
- **Unit page:** a single **stack1** bar of where the GPU went (ep14: takes 55 % · take_dq 14 % · take_content 13 % · panel_content 6 % · other), 
  direct-labelled for the top 3 and the rest folded into "other". Never a pie.

### 5.6 Queue / ETA: **forecast lane** — EARNS IT, but drawn as a range
- **Floor and home, top:** one horizontal lane, now → +72 h, 28 px tall. The running unit is a solid block from its
  start to its server-given ETA (the live card's "done around 21:40"). Its *range* (20:25–22:55, already computed)
  is a 4 px whisker. Each queued unit (ep01, ep02, ep05) is a hatched ghost block, as long as the median finished-unit
  wall time, with a p25–p75 whisker (today ~11 h to ~53 h). The whiskers will be honestly wide.
- Holds and the owner's `orders` show as `‖` ticks on the lane. Deferred-and-waiting-for-GPU shows as `--viz-4`.
- No ETA arithmetic in the browser (progress.js already holds to this). The server sends `start, eta_lo, eta, eta_hi`
  per block and the macro only scales them.
- On a phone (< 560 px) the lane folds into a list: "ep17 · ~21:40 (20:25–22:55) · then ep01 ~+1–2 d".

### 5.7 Cost per unit: **a number** — NO CHART
- `$0.35` already sits in the unit meta line. Add it to the dept units table as a right-aligned tabular-num
  column, plus a book total on `/b/{codex}` ("LLM spend $10.72 across the 5 units that logged spend", `work_orders.cost_usd`). Visual weight on $3 spreads
  would mislead about what matters. The scarce resource is GPU-hours, not dollars.

### Rejected forms (and why)
- **Pie/donut** for anything (part-to-whole goes in `stack1`). **Dual-axis** GPU-hours + cost (two charts instead).
- **Datadog-style heatmap of step durations over time**: 6 units can't fill a distribution. Revisit at ~30 units.
- **Line chart of faults over calendar time**: ladders are per-attempt, not per-day, so the x-axis would lie.
- **Animated / live-updating charts** beyond the existing rail sheen. The owner glances. Motion should mean
  "running" and nothing else.

## 6. Interaction contract (all charts)
- Hover: `<title>` on every mark is the baseline. `viz.js` adds a crosshair + readout box for `col_strip`,
  `run_strip` and `ladder_panel` (hit target = the full column/row band, not the 6 px mark).
- Click: every mark is an `<a>` to the unit/run, or `hx-get` into the unit page's detail panel. Never a modal.
- Keyboard: charts are `role="img"` with an `aria-label` that states the finding, followed by
  `<details><summary>table</summary><table>…` with the same rows.
- Re-render: charts live inside the existing htmx partials (`_floor.html`, `_unit_live.html`). They are never
  polled on their own. The live card's 2 s poll does not re-draw the run strip (it changes only on a run boundary).

## Top 10 recommendations for this board
1. Ship all charts as hand-SVG Jinja macros (`_viz.html` + pure `viz.py`), 0 KB vendored. Keep uPlot (21.7 KB gz) in reserve only. (all pages)
2. Add validated `--viz-1..4` chart tokens per theme to the `:root` block, and never use `--think/--qc/--accent` as series colours. (all pages; `architecture/index.html` too, because a test holds the tokens equal)
3. Build the Gantt from `events` started/terminal pairs per `run_id`, never from `work_steps.seconds` (all 0). (unit)
4. Normalise `timing.jsonl` naive local time to UTC on read, before any chart uses it (7 h skew vs the ledger). (unit, floor)
5. Season status matrix units × 12 steps, 16 px glyph cells, inferred pre-ledger rows dotted. (book)
6. Run strip: rows = runs, step-class fill + outcome cap, last 12 runs then "show more". (unit)
7. Ladder small multiples per gate on a fixed sqrt 0–60 scale with ▲ overflow and ⊘/●/↩ end markers. (unit)
8. Replace "flag rate" with a gate × unit fault-count matrix + "taste gates clean: 1 of 15" stat. (department)
9. 30-day GPU column strip whose top edge is 24 h, with today in `--accent` and the max labelled. Use the stacked variant on the floor page. (home, floor)
10. Forecast lane showing running ETA + range and queued units as hatched median blocks with p25–p75 whiskers. Cost stays a number. (floor, home)

## 3 disagreements I expect with other researchers
1. **"Use a real chart library for polish" (likely from the SaaS / Grafana researchers).** I say no: the board's
   largest chart is ~600 marks, and server-rendered SVG with tokens beats a 70–330 KB canvas library on theming,
   htmx swaps, tests and print. The polish comes from the mark spec, not the library.
2. **"A KPI row of big numbers with deltas on home" (Vercel/Linear style).** Most of this board's numbers have
   n ≈ 6. A "+340 %" delta on GPU-hours vs last week would be noise posing as a trend. I'd allow 3 stats (GPU today,
   queue, next finish) with sparklines, and no deltas until there are ≥ 4 comparable weeks.
3. **Colour coding by department/book (film-tool researchers: ShotGrid/Kitsu colour every task type).** Categorical
   colour here is spent on *step class* (GPU / judgement / CPU / waiting) because that is what explains where time went.
   Departments and books are identified by position and label, and status by glyph + reserved status colour.
   Kitsu-style rainbow task colours would collide with status under CVD (the validator showed `--qc`↔`--accent` ΔE 0.5).
