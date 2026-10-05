# P06 — Data visualisation: charts that earn their place, and update live without flicker

Panelist P06, 2026-10-04. Read-only. Sources: the live board (:8700, ep17 running at 04:00), the
mockups (:8710, snapshot 19:21), `studio/command_center/` (templates, `static/progress.js`),
`mockups/assets/unit.js`, `mockups/index.html`, `mockups/queue.html`, and the prior rulings
`2026-10-04_board_design/05_dataviz.md` (which forms and colours) and `09_liveness_motion.md` (pulse + morph).
Screenshots: `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\9340346d-60b6-4248-b569-c5a6fe035ef8\scratchpad\board_v3\mockups\shots\panel\`
(`p06_mock_home.png`, `p06_mock_queue.png`, `p06_live_ep17.png`, `p06_live_home.png`).

## 0. The brick

Report 05 settled what to draw. Report 09 settled how the page learns about a change. Nobody has yet
settled **how a chart behaves when it is refreshed**, and the owner's request ("more dynamic, refresh
and updating") is exactly about that. The rule I propose:

> **A chart is a pure function of (rows, now rounded to its resolution). It is re-rendered on the
> server only when that pair changes, and patched into the page by key, never redrawn.**

The rest follows from it. The resolution is the pixel size of one unit of time. On a 24 h axis 1 000 px
wide, one minute is 0.7 px, so redrawing it more often than once a minute changes no pixel. The
fingerprint is `hash(rows_fp, floor(now / resolution))`. Stable keys on the marks let the morph change
attributes and leave nodes in place: no flicker, no lost hover, no lost tooltip. "Now" comes from
the server, so the client does no chart arithmetic. That keeps progress.js's rule "no ETA math here".

## 1. What is on screen today (observed)

| Where | Chart | Drawn by | Refresh | Finding |
|---|---|---|---|---|
| Live unit `#live` | vital trace 240×24 px polyline, 30 min | Jinja first, then `progress.js tracePoints()` | 2 s JSON, attribute patch | **Good pattern.** Already patch-in-place. No stall-budget reference on it, though: "quiet 2m" vs "stalled" can't be seen on the trace |
| Live unit rail | step segments with `--p` fill | Jinja + `patchRail` | 2 s | Good. Patches class and `--p` only |
| Live unit PLAN line | `2 ▸ 31 ▸ 18 ▸ 16 ▸ 14 ▸ 15 → stuck` | text | 3 s head swap (`outerHTML`) | Text, not a ladder. The whole head is replaced every 3 s |
| Live home / floor / dept | none | — | `innerHTML` every 2–10 s | No charts yet. Every planned chart will land inside these swaps |
| Mock home KPI "GPU today" | 7-point line + area, `preserveAspectRatio="none"` | inline JS, static array | never | Joins daily totals with a line, which implies continuity between days. Today's 1.5 h at 19:21 is drawn against full days |
| Mock home "Where the GPU went" | stacked columns, 24 h dashed ceiling, hatch for burned | inline JS, width read from `clientWidth` **once** | never; no resize handler | Honest ceiling (good). Today is a partial day drawn as if complete. `clipPath id="cp0..6"` and `hatchF` are page-global ids |
| Mock home ETA band | 420-wide SVG, 10 px text, scaled into ~210 px | static | never | Text renders at ~5 px in the 1440 screenshot (`p06_mock_home.png`, "now 19:21", the tick labels): illegible |
| Mock queue "The GPU" lane | runs + running + p50 ghosts, 24 h/3 d/7 d | JS `draw(range)`, resize-debounced | never | "now 19:21" label overlaps the "18:00" tick label (`p06_mock_queue.png`). Ghosts are "p50 of a clean pass (2 h 38)" |
| Mock unit ladder (`unit.js:246`) | sqrt 0–60, `Math.min(v, 60)` | JS | never | **Clamps silently.** ep12 EYE_PANELS 531 is drawn at the same height as 60, and nothing marks the clamp. Report 05 required a ▲ caret plus the value |
| Mock unit run matrix (`unit.js:328`) | runs × 12 steps, pattern-filled cells, run-time bars | JS | never | Strong. Uses ids `pf ph pd pg` (global) |

Also seen on the live ep17 page: the hero says **22/22 panels, "done around 23:20 at the 5 h ceiling"**,
and all 22 panel tiles render as empty beige boxes in the headless capture. The ETA is clamped (the same
honesty issue as the ladder: a clamped value must look clamped). The empty tiles may be a headless
lazy-load artefact. The thumbnail lens should verify that, not me.

## 2. Outside practice that applies

| Source | Lesson | Here |
|---|---|---|
| idiomorph — https://github.com/bigskysoftware/idiomorph ; htmx morph ext — https://htmx.org/extensions/idiomorph/ | Morph matches nodes by `id`, then by structure. Ids give it a stable identity | Every mark gets an `id` built from its key (`gpu-d-2026-10-04-burn`), so a morph patches `height`/`y` in place |
| Grafana dashboard refresh / "min interval" — https://grafana.com/docs/grafana/latest/panels-visualizations/query-transform-data/#query-options | A panel never queries more finely than one pixel's worth of time | Per-chart resolution: 24 h lane = 60 s, 7-day columns = 5 min, 30-min trace = 2 s |
| uPlot streaming demo — https://leeoniya.github.io/uPlot/demos/stream-data.html | Only dense per-second series need a client chart. Everything else is a static picture refreshed rarely | The only 1 Hz chart is the vital trace, and it already works |
| Tufte, sparklines — https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/ | Mark the end value and the extremes; word-sized | KPI strips: label today and the max, nothing else |
| Few, bullet graph spec — https://www.perceptualedge.com/articles/misc/Bullet_Graph_Design_Spec.pdf | One measure against its range and target | ETA band (p10–p90 range, p50 tick, now marker); today vs elapsed-day ceiling |
| FlowingData, bar baselines — https://flowingdata.com/2015/08/31/bar-chart-baselines-start-at-zero/ | Bars must start at zero, and a truncated or clamped value needs a visible break | Ladder overflow caret; ETA "capped" ceiling drawn as a wall |
| MDN `contain` — https://developer.mozilla.org/en-US/docs/Web/CSS/contain ; web.dev CLS — https://web.dev/articles/cls | A swapped region with a reserved box and `contain: layout paint` cannot shift the page | Every chart box gets a fixed `aspect-ratio`/height before data arrives |
| MDN `font-variant-numeric` — https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric | `tabular-nums` stops digits jittering as values change | All chart value labels and KPI digits (09 already bans rolling digits) |
| W3C WCAG 2.2.2 — https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html | Auto-updating content needs a pause control | Charts obey 09's "still" toggle: frozen at the last render, caption says "paused" |
| Grafana "No data / stale" states — https://grafana.com/docs/grafana/latest/panels-visualizations/configure-standard-options/#no-value | A panel must say when its data is old, rather than look current | `data-stale` greys every chart and prints "as of 04:02" |

## 3. The live-chart contract (applies to every chart from report 05)

1. **Server-drawn SVG, in a Jinja macro, from a pure `viz.py` function.** The mockups' inline-JS
   charts (`index.html` went/sparks, `queue.html draw()`, `unit.js ladderSvg/renderRuns`) are ported
   to macros. JS is kept only for hover readouts. This lets pytest assert the marks at $0.
2. **Fixed viewBox, CSS width.** One viewBox per chart (e.g. 640×220) with `width:100%`. No
   `clientWidth` read at draw time, so no redraw on resize and no first-paint size guess. Text that must
   stay legible (axis ticks, ETA labels) goes in **HTML positioned by %** over the SVG, or the chart uses
   `vector-effect:non-scaling-stroke` and a minimum rendered width. Never scale 10 px SVG text by 0.5.
3. **Keyed marks.** `id="{chart}-{key}-{part}"` on every rect/line/text. Pattern and clip ids are
   prefixed with the chart key (`went-hatch`, `ep17-runs-pf`). Shared patterns go in **one** `<svg
   width=0 height=0>` `<defs>` in `base.html`, so two charts never declare the same id and a morph
   never finds two.
4. **Resolution-bucketed fingerprint.** `viz.fp(rows_fp, now, res_s)`. The pulse (report 09) carries
   one fp per chart section. Unchanged → 204 → no swap.

   | Chart | res | Changes when |
   |---|---|---|
   | vital trace | 2 s | runner signal (already client-patched) |
   | GPU lane 24 h, ETA band | 60 s | run boundary, or the minute ticks |
   | 7/30-day columns, KPI sparks | 300 s | run boundary, or 5 min of running |
   | run matrix, ladders, fault matrix, season matrix | ∞ | run boundary / signature only |
5. **Motion inside a chart**: none on refresh. The morph changes geometry instantly. With 60 s
   resolution, a growing column moves < 1 px per update, so a tween adds nothing and would break 09's
   "one loop per viewport" rule. The only animation on a chart is 09's 1.6 s change wash on a mark
   that **appeared** (a new run column, a new ladder rung), via `.chg` on the new id.
6. **Reserved box.** `.chart{aspect-ratio:640/220; contain:layout paint}`, with the table twin in
   `<details>`. CLS stays 0 when a chart arrives or grows.
7. **Staleness.** If the pulse fails, `<html data-stale>` makes charts `opacity:.55` and
   `filter:grayscale(1)` and swaps each caption's `as of HH:MM` to `--accent`. The "now" line stops
   where the data stops. It never keeps walking on the client clock.
8. **Done means measured.** A browse script on ep17: tag `#went-d-today-ok` with an expando, wait for
   3 pulses, and assert the expando survives (node kept). A `PerformanceObserver('layout-shift')` sum of
   0 over 10 min. Bytes per minute per tab ≤ 15 KB with charts (today `/d/episode` alone is 77.5 KB
   per 10 s, from 09).

## 4. Honest-scale fixes (the charts must not lie as they update)

- **Today is a partial day.** On every daily column chart, draw today's ceiling as the hours elapsed so
  far (19.35 h at 19:21): a dotted cap in `--rule-2`, labelled "today so far". Never compare today's
  1.5 h against full days without that mark. The KPI says "1.5 h of 19.4 elapsed".
- **Clamped values look clamped.** Ladder points above the sqrt scale's 60 sit on the top edge with a ▲
  and their value (`531`). The live hero's "at the 5 h ceiling" becomes a visible wall on the ETA band,
  and the p50 tick turns into an open bracket `]` at the wall.
- **Clean pass vs as run.** Queue ghosts and the "Episode lane clears ~05:29 Mon" KPI use "p50 of a
  clean pass (2 h 38)". Report 05 measured finished units at 11–60 h wall first→last event. A big
  single time on home, with no qualifier in the digits, will be wrong by days. Show both: the ghost
  block at the clean p50, plus a faint whisker to the as-run p50 for the same step mix. The KPI reads
  `~Mon 05:29 if clean · as run Tue–Thu`.
- **Lines only for continuous series.** The GPU-today spark becomes 7 columns with a 24 h ceiling,
  the same marks as "Where the GPU went". The spark then previews the chart it links to.
- **Shared scales across small multiples.** Ladders stay on fixed 0–60 sqrt in every panel. KPI sparks
  keep max=24 h, never auto-max: an auto-scaled spark makes a quiet week look as busy as the busiest.

## 5. New small charts that earn a place on the live board

- **Stall-budget marker on the vital trace** (unit `#live`, and the floor row). Draw a dashed
  vertical at `now − stall_budget` and shade it in `--rule` 30 %. It reads directly from
  `p.vital_reason`'s budget (`quiet 22m · budget 10m`). When the last spike falls left of the
  line, the owner sees *why* the word says "stalled". Patched by `tracePoints` (one more attribute).
- **Micro-trace on floor/home "On the GPU" card**: the same 30-min trace at 120×16, from the pulse's
  `running[].trace` (add the field, ≤ 30 floats). It is the one live graphic on home, and it replaces
  any pulsing dot, as 09 requires.
- **Run matrix on the live unit page** (port `unit.js renderRuns`). A new run appends a column with
  the change wash. ep17's 7 runs (killed, deferred, refused ×3) are the story HEALTH chips now tell in a row.
- **PLAN ladder panel beside the text** `2 ▸ 31 ▸ 18 ▸ 16 ▸ 14 ▸ 15 → stuck`. Keep the text, since it
  is the table twin, and add the 168×84 panel from 05 §5.3.

## Proposals

| id | page | change | effort | files |
|---|---|---|---|---|
| P06.1 | all | Live-chart contract: charts are Jinja-macro SVG from pure `viz.py`, keyed mark ids, refreshed by a resolution-bucketed fingerprint in the pulse, morphed (never `innerHTML`/JS redraw) | M | `views.py` (fp), new `viz.py`, new `templates/_viz.html`, `base.html`, pulse.js (09), tests `tests/command_center/test_viz.py` |
| P06.2 | home, floor, queue | Today's column/KPI gets an "elapsed so far" ceiling; the GPU-today spark becomes 7 columns on a fixed 24 h max | S | `viz.py` `day_columns()`, `_viz.html col_strip`, `home.html` |
| P06.3 | unit | Ladder panels with ▲ overflow + value (fix the silent `Math.min` clamp of `unit.js:246` in the port); PLAN text stays as the twin | S | `viz.py sqrt_scale/ladder`, `_viz.html ladder_panel`, `_unit_head.html` |
| P06.4 | home, queue | Clean-pass vs as-run ETA: ghost at clean p50 plus as-run whisker; KPI text carries "if clean" and the as-run range | M | `views.py` queue ETA, `viz.py lane()`, `home.html`, queue template |
| P06.5 | home, unit | ETA band rebuilt as HTML/CSS (%-positioned range, p50 tick, now, ceiling wall) so labels stay 11 px at any width; morphs by `style` | S | `_live_hero.html`, `_viz.html eta_band`, `static/css` |
| P06.6 | unit, floor, home | Stall-budget marker on the vital trace; 120×16 micro-trace on the On-the-GPU card from `pulse.running[].trace` | S | `_live_vital.html`, `progress.js tracePoints`, `progress_view.py`, `_floor.html` |
| P06.7 | all | Stale state for charts: `data-stale` greys them, caption "as of HH:MM" in `--accent`, the now line stops | S | `base.html` css, pulse.js, every chart caption |
| P06.8 | all | Chart-scoped ids for clipPaths/patterns; one shared `<defs>` sprite in `base.html` | S | `base.html`, `_viz.html` |
| P06.9 | all | Reserved chart boxes (`aspect-ratio`, `contain:layout paint`), `tabular-nums` labels; measured CLS = 0 over 10 min | S | `static/css`, `_viz.html` |
| P06.10 | unit | Run matrix ported to the live unit page; new run column arrives with the 1.6 s wash, nothing else moves | M | `viz.py runs_from_events()` (events pairs, 05 trap T1), `_viz.html run_matrix`, `unit.html` |
| P06.11 | queue | Tick-label collision rule: hide any axis label within 36 px of the now label (fixes "18:00" under "now 19:21") | S | `viz.py ticks()`, `_viz.html lane` |

Verification for all of them: a browse script that checks node identity across 3 pulses, the
layout-shift sum, bytes per minute, and a screenshot pair (fresh and `data-stale`) in `shots\panel\`.

## I will argue against

1. **Tweened or animated chart updates (bars growing, numbers counting up, a sliding now-line) "to
   feel dynamic".** At the right resolution a live chart changes by under a pixel per refresh, so a
   tween only animates noise. It also adds a second loop to the viewport, which 09 banned. "Dynamic"
   should mean *current and trustworthy* (fresh "as of", stale state, a change wash on new marks), not
   moving pixels.
2. **A 1 Hz GPU utilisation/VRAM line chart (nvidia-smi) on home "because studios have one".** It
   looks alive and answers no question the owner acts on. The vital trace already says whether the
   run is breathing, and the GPU lane says where the hours went. If ever needed, it goes on `/floor`
   only, via uPlot, behind a disclosure.
3. **Adopting Chart.js/ECharts/Recharts for "polish" or easier live updates.** A canvas chart redraws
   whole on every update, can't be morphed by key, ignores CSS tokens on theme toggle, and can't be
   asserted in a $0 pytest. The polish problems seen here (illegible scaled text, a silent clamp, id
   collisions, partial-day bias) are mark-spec bugs, and a library fixes none of them.
