# 04 — Pipeline / orchestration monitors, applied to the board

Researcher 04, 2026-10-04. Sources: Dagster, Prefect, Temporal Web UI, Airflow, GitHub Actions,
Buildkite, CircleCI Insights, Argo Workflows (URLs in §9). Real data: the ledger
`db/visurena_studio.db` (read-only), `logs/<codex>/episode/*.log`, `library/<book>/episodes/epNN/`.

## 0. What the ledger actually holds (the data every proposal below reads)

- `events(event_ts, codex_id, stage, step_id, event, run_id, detail, unit)`: one row per
  started / completed / failed / skipped / deferred / escalated. **This is the run history.**
  `work_steps` is keyed `(order_id, step_id)` so it keeps only the *latest* attempt of each step;
  every multi-run view must be built from `events` grouped by `run_id`.
- War of the Worlds **ep13: 52 distinct run_ids** (`work_orders.attempts = 52`, 21.1 GPU-h,
  $0.76, 20 flags) between 09-25 17:40 and 09-28 06:10. (The brief's "29 runs" is likely the count
  that reached step 08+; the ledger says 52.) Its shape, in three acts:
  1. 09-25 20:18–22:12: 7 runs that end at 02 (`deferred` ×4, `failed` ×1, killed) — a plan loop.
  2. 09-26 22:55 → 09-27 16:08: ~12 runs alternating `08 ✗` / `09 ✗` — the panels/shoot loop.
  3. 09-27 22:02 → 09-28 05:47: ~10 runs dying at `11 qc ✗` (6 fails) before `12 ✓`.
  Most runs begin with a column of `skipped` (cache hits for 01–07). Several runs start mid-chain
  (`09:star` alone) — out-of-band re-runs of one step.
- Run logs are **structured JSONL**: `{ts, level, codex_id, stage, step_id, msg}`; the "ladders"
  pseudo-step logs every gate decision (`PLAN: measured 16.0 vs None -> improve`).
  `learnings.jsonl` (118 rows for ep13) holds `{gate, measured, action, attempt, seconds, terminal}`.
- Durations across all episode runs (minutes, from `events` started→ended):

  | step | completed n / median / p90 | failed+deferred n / time burned |
  |---|---|---|
  | 02 plan | 43 / 7.1 / 15.1 | 32 / **10 h** (deferred med 24 min) |
  | 08 panels | 22 / 43.5 / 90.2 | 16 / 5 h |
  | 09 shoot | 23 / 62.7 / 123.8 | 31 / **30 h** |
  | 11 qc | 11 / 22.4 / 27.4 | 24 / 3 h |

  **~48 of ~113 measured GPU-hours went into runs that ended failed or deferred.** No current page
  says that. It is the single most decision-relevant number in the ledger.

## 1. What each tool does that matters here

**Airflow Grid** (3.x). Columns = runs, rows = tasks, each cell a status square; above the grid a
bar per run whose height = run duration. Hover = details, click = side panel with logs. 3.1 folded
the Gantt into the grid's side panel. Task Duration view: per-task duration line across the last
N runs to "find outliers". Task instances carry a **Try Number** column.
→ The run × step matrix is the exact shape of "12 steps × 52 passes". A loop is visible as a
horizontal stripe of red in row 08/09 — no explanation needed.

**Buildkite waterfall**. One row per step, bar split into three segments: **grey = waiting for an
agent, yellow = agent assigned → started, green/red = execution**. Parent rows (group/matrix)
draw a solid bar spanning children, red if any child failed. Hover gives the three durations.
Logs: `---` collapsed group, `+++` expanded, `~~~` collapsed *and de-emphasized*; since 2026-09
system groups are folded by default into compact rows, **search reaches inside folded groups**,
links to a line open its group, toolbar has Expand/Collapse visible groups.
→ The waiting segment is the floor's missing concept: on one GPU, time waiting for the lease is
real and invisible today.

**Temporal Web UI**. Event History has three views: **Compact** (event groups left→right, parallel
ones stacked), **Timeline** (row per event group: Scheduled+Started+Completed collapse into one bar
spanning the activity; first row = whole workflow duration; green completed, red failed; points
for markers/signals; zoom +/−, Fit button, hover gives start/end/duration to the ms), and the
full **event table**. Retrying activities show **a retry icon with the current attempt number**.
The summary page has **Pending Activities**: type, attempt, attempts remaining, **last failure**,
last heartbeat. v2.26 added a live feed of event history.
→ The "now" card for a running step should be Temporal's Pending Activity, not a progress bar:
attempt n, last failure text, heartbeat age.

**Dagster**. Run page: Gantt in the upper pane, structured event log below, toggle to raw
stdout/stderr, level filter that shows **"n of m levels selected"**, re-execute button, related
runs panel. Overview → **Run timeline**: one row per job, runs as bars on a wall-clock axis with
a now line; hover lists run ids and timings. Assets: **partitions health bar** (green
materialized / red failed / grey missing), per-group status. → The partitions bar maps one-to-one
to "units of a department": the home cards' segmented bars already are this; make them honest
(one segment per unit, state glyph on hover/focus, click = unit).

**Prefect**. Flow-run page leads with a **flow run graph / timeline** (task runs as bars in time,
nested subflows), zoomable; a "radar" for hierarchy; logs tab with level filter. Lesson from its
issue tracker (#8750, #14709): graphs that cannot be range-zoomed become unreadable past a few
dozen nodes — ep13's 52 runs × 12 steps is that size.

**GitHub Actions**. Run page = job list left, log right. **Failed steps auto-expand**; others stay
folded with duration at right. `::group::` folding. Search only covers expanded steps (a known
weakness Buildkite fixed). Line-number anchors give permalinks. Re-runs create **"Attempt #n"**
selectable from a dropdown; "re-run failed jobs" retries only the red ones.

**CircleCI Insights**. Per workflow: runs, **success rate** (excl. cancelled), **p50 / p95
duration**, credits; trend arrows vs previous window; **flaky tests** = passed and failed on the
same commit. → "Flaky" maps to *a step that fails and passes on the same inputs* — `input_sha8`
exists on `work_orders`; 09 shoot is the studio's flaky test.

**Argo Workflows**. DAG graph with node-state icons; a retried step becomes a **retry node** with
children `(0)`, `(1)`, `(2)` per attempt; workflow-level retry is a CLI action (issue #12022).
Community complaint (#4203): node kinds indistinguishable. → Retry-as-children is the right
mental model for "attempt n of a step inside a run", but the node-link DAG is wrong for a linear
12-step chain.

## 2. Unit page — the run matrix (Airflow Grid × Temporal compact)

Component **`run-matrix`**, placed directly under the step rail, replacing the "HEALTH" chip row
(`06:26 08 error · 06:40 08 error …`), which today shows ≤14 runs as text chips and "+18 earlier".

- Grid: 12 rows (01 bind … 12 deliver, labels left in mono 11 px), one **10 px column per run**,
  oldest left. 52 runs = 520 px; wraps to a horizontal scroller with the newest pinned in view
  (`scroll-snap-align:end`). Cell = 10×10 square, 2 px gap.
- Cell glyph + colour (never colour alone; glyph on ≥10 px, title attribute always):
  completed `--ok` filled; failed `--accent` filled + ✕ at zoom; deferred `--qc-bg` with `--qc`
  border; skipped (cache hit) **hollow 4 px dot in `--rule-2`** — this is what makes a loop pop,
  because the left 6–7 rows of a looping run go quiet and only the live rows are ink;
  running `--think` with a 1.2 s opacity pulse (respect `prefers-reduced-motion`); not reached =
  empty.
- **Top strip**: one bar per run, height ∝ run wall-time (max 40 px), fill = the outcome of the
  run's last step. ep13's three acts read instantly: tall red bars in act 2 (1–2 h shoots dying).
- **Day ticks** under the strip (`09-26`, `09-27`) where the date changes; a gap > 2 h between
  runs draws a 4 px spacer column so nights read as nights.
- **Loop detection, drawn**: consecutive runs whose *last non-skipped step* and outcome match
  (e.g. 4× `09 ✗`) get a bracket under the columns: `↻ ×4 at 09 shoot · 6h12 · 3 different
  failures`. Reads `events` only. This replaces the text "no loop" / "loop" badge with evidence.
- Click a column → selects that run: the rail above and the gantt below (§3) re-render for it via
  `hx-get /d/episode/{codex}/{unit}/run/{run_id}` (htmx swap of `#run-detail`). Click a row label
  → step history (§5). Keyboard: ←/→ moves the selected run; the URL carries `?run=`.
- Phone (400 px): matrix rotates — runs become rows (newest first, 12 squares each = 144 px
  wide), which is GitHub's attempt list in grid form.

## 3. Unit page — the selected run as a waterfall (Buildkite × Temporal timeline)

Component **`run-waterfall`** in `#run-detail`: one row per step *that the run touched* (skipped
steps collapse into a single folded row `01–07 skipped · cached` — Buildkite's `~~~`).
- Row 0 = the run itself, spanning its whole duration (Temporal's first row).
- Each bar has up to three segments: **waiting** (`--rule` hatched: run started → step started
  while another unit held the GPU lease; derived from the floor's lease rows), **working**
  (`--ink-3`), **outcome cap** 4 px at the end (`--ok` / `--accent` / `--qc`).
- Inside a step, gate retries from `learnings.jsonl` (same `step`, rising `attempt`) render as
  ticks on the bar with the attempt number — Temporal's retry icon + Argo's `(0)(1)(2)` children,
  expandable to sub-rows: `PLAN attempt 1 measured 5 → improve · 41 s`.
- Axis: run-relative (`+0`, `+30m`, `+1h`) with absolute start in the header; hover/focus tooltip
  gives start, end, duration, and **"vs typical: p50 62.7m · p90 123.8m"** for that step.
- Fit button only; no free zoom (the Prefect lesson: zoom that is not range-select is noise).

## 4. Live view — the running step as a Pending Activity (Temporal) with an honest ETA

The current hero (`11:44 IN PLAN · done around 21:40 · range 20:25–22:55 · 43 runs measured`)
is already the right idea. Sharpen it with Temporal's fields and a measured-percentile bar:

- Line 1: `09 SHOOT · attempt 3 of run 41 · take T14/23` (the step's own progress counter where
  one exists: takes on disk vs `plan.json` shots — `G_unit_data.md` sources).
- **Elapsed bar** 100% width, 8 px: fill = elapsed; two ticks at **p50** and **p90** of that
  step's *completed* durations across all episodes (09: 63 m / 124 m). Past p90 the fill switches
  to `--qc` and the caption reads `longer than 9 of 10 past shoots`. Never a fake percentage.
- ETA text: `ends ~14:20 (p50) · by 15:21 (p90)` — the step ETA, and a second line for the run:
  remaining steps' p50 summed = `episode done ~18:40`. The current "range" already does this;
  label which percentile each end is.
- **Last failure** (Temporal): the previous attempt's `detail`, first line, mono, truncated with
  a disclosure — today's "LAST WORDS" row, but labelled by what it is.
- **Heartbeat**: age of the newest log line for this run (`quiet 6m` today). Turns `--qc` at
  > 2× the step's median gap between log lines, `--accent` at the lease expiry (`lease_until`).
- Live update: htmx `hx-trigger="every 10s"` on this card only (Temporal's live feed); the
  matrix's newest column polls at 30 s. The rest of the page is static until reload.

## 5. Step history and duration insight (Airflow Task Duration × CircleCI)

Click a step label in the matrix → a drawer `step-history` for that step on this unit, and a
link to the same step across all units of the department:
- Duration dot plot: x = run index, y = minutes, dot = outcome glyph; horizontal rules at the
  department-wide p50/p90. Outliers are the dots above p90.
- Counters in a row: `23 ✓ · 31 ✕ · 30 h burned on failures · success 43%` (CircleCI's success
  rate excl. killed). **"Flaky"** flag when the same `input_sha8` both failed and passed.
- Failure reasons grouped: the first line of `detail` normalised (strip paths/numbers), counted:
  `REFUSED takes_r2v.py exit 1 ×9 · EYE_TAKES flagged ×6 …` — GitHub's annotations, counted.

## 6. Logs UX (Dagster structured log × Buildkite folding × GitHub auto-expand)

Today the unit page offers `RAW … log 4 lines` as a link. Proposed **`run-log`** panel under the
waterfall, for the selected run:
- Groups = `step_id` (incl. the `ladders` pseudo-step shown as "gates"). **The failing step's
  group opens automatically; skipped steps fold to one de-emphasised line**; others are folded
  with line count + duration at right (GitHub).
- Level chips with counts: `INFO 4 · WARNING 6 · ERROR 0` — Dagster's "n of m" — toggling via a
  query param, server-filtered (no JS framework). Default: WARNING+.
- Search box filters across **folded** groups too and auto-opens matching groups (Buildkite's fix
  over GitHub). Matches highlighted with `<mark>` in `--qc-bg`.
- Multi-line `msg` (the `plan_check refused:\nCONTRACT OK…` blocks) folds after 3 lines.
- Line anchors `#L<ts>` — permalink a refusal into a note or an order.
- Toggle **structured / raw** (Dagster): raw = the `.log` file verbatim with a download link.
- Gate lines (`PLAN: measured 16.0 vs None -> improve`) render as a mini table
  `gate · measured · action`, since they are data, not prose.

## 7. The floor — one GPU's queue as a timeline (Dagster run timeline × Buildkite waiting)

The current floor is a 92-row call sheet where rows 4–92 are `refs main` / `screenplay book` /
`trailer book` at priority 0 — a list, not a schedule. One GPU is a single lane; draw it:
- **GPU lane** 48 px tall, axis = last 24 h ← **now line** (`--accent`, 2 px) → next 12 h.
  Past: bars per run coloured by department (5 hues max, plus a 3-letter label inside: `EP17`),
  outcome cap at the right end. Future: queued work orders as **hatched ghost bars** whose width
  = p50 of that department's run time (episodes from `events`; refs/screenplay from their own
  history), so the owner reads "ep01 starts ~03:10, ep02 ~07:40" — an ETA for the queue.
- Under the lane, a thin **idle strip**: GPU idle time per hour in `--rule`, so 6 idle hours at
  night (no run holding the lease) is visible as lost capacity.
- Holds draw as a vertical barrier on the future side (`II studio hold: why…`).
- The queue table stays but **groups by department with counts** (`refs · 29 queued · next:
  A Study in Scarlet`) and expands on click — Airflow's grid collapses task groups the same way.
  Row actions (↑, hold) remain inside the expanded group only.

## 8. The home page — insights, not lists (CircleCI × Dagster asset health)

- Keep `ON THE FLOOR` as the first line, but render it as the compact live card of §4 (one line:
  `EP17 · 02 plan · attempt 3 · 11m of p50 7m · ends ~02:20`).
- Department cards keep the partitions bar (one segment per unit, Dagster) with state glyph
  counts; add one line per card: `7d: 5 runs · 60% ✓ · 14 GPU-h (6 wasted)`.
- A **"Where the GPU went (7 days)"** strip: stacked horizontal bar per step: productive
  (`--ok`) vs burned on failed/deferred (`--accent` hatched) — today's 48/113 h finding as a
  standing chart. Below it, a "flakiest steps" leaderboard (top 3): `09 shoot 31✕/23✓ · 11 qc
  24✕/11✓ · 02 plan 32↩/43✓`. These are the owner's levers.
- `TODAY` stays as a feed, but each item gets a 10 px matrix cell glyph instead of trailing ✓/✕.

## 9. The DAG view — where it belongs, and where it does not

- **Not on the unit page.** 12 steps in a fixed chain are a line; a node-link DAG (Argo,
  Dagster asset graph) would spend a screen saying "01→02→…→12". The step rail is the DAG.
- **On the book page / org chart**: the cross-department lineage (analysis → screenplay →
  trailer, refs → episode) per book is a real graph with fan-out; Dagster's asset graph pattern
  fits there: node = department × book, border = state, a "stale" badge when an upstream
  `input_sha8` changed after the downstream finished (`work_orders.state='stale'` exists).

Sources:
- Temporal Timeline view: https://temporal.io/blog/lets-visualize-a-workflow
- Temporal updated timeline / compact: https://temporal.io/change-log/updated-event-history-timeline-view-is-now-available ; https://temporal.io/changelog/temporal-web-ui-v2-26-0 ; https://docs.temporal.io/web-ui
- Temporal pending activities: https://docs.temporal.io/activity-operations
- Airflow UI (Grid, Gantt, task duration, try number): https://airflow.apache.org/docs/apache-airflow/stable/ui.html ; https://airflow.apache.org/blog/airflow-3.1.0/ ; https://www.astronomer.io/docs/learn/airflow-ui
- Buildkite waterfall: https://buildkite.com/docs/pipelines/insights/waterfall
- Buildkite log groups: https://buildkite.com/docs/pipelines/configure/managing-log-output ; https://buildkite.com/resources/changelog/413-see-the-important-parts-of-job-logs-first/
- Dagster webserver/run page/logs: https://dagster.io/docs/guides/operate/webserver ; https://docs.dagster.io/guides/log-debug/logging ; https://docs.dagster.io/about/changelog
- Dagster partitions: https://docs.dagster.io/guides/build/partitions-and-backfills/partitioning-assets ; https://dagster.io/blog/dagster-1-4-material-girl
- Prefect flow runs / graph zoom issues: https://prefect-284-docs.netlify.app/ui/flow-runs/ ; https://github.com/PrefectHQ/prefect/issues/8750 ; https://github.com/PrefectHQ/prefect/issues/14709
- GitHub Actions logs: https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs
- CircleCI Insights glossary: https://circleci.com/docs/guides/insights/insights-glossary/ ; https://circleci.com/blog/how-the-insights-team-uses-insights-to-optimize-pipelines/
- Argo retries / UI issues: https://argo-workflows.readthedocs.io/en/latest/retries/ ; https://github.com/argoproj/argo-workflows/issues/12022 ; https://github.com/argoproj/argo-workflows/issues/4203

## Top 10 recommendations for this board

1. **Unit:** add the `run-matrix` (12 steps × every run_id from `events`, skipped = hollow dot, run-duration strip on top) in place of the HEALTH chip row.
2. **Unit:** draw loops as brackets under the matrix (`↻ ×4 at 09 shoot · 6h12`), computed from consecutive runs with the same last step + outcome.
3. **Unit (live card):** elapsed bar with p50/p90 ticks from completed durations of that step; turn amber past p90; label which percentile each ETA is.
4. **Unit (live card):** Temporal's pending-activity fields — attempt n, last failure (first line of `detail`), heartbeat age vs `lease_until`.
5. **Unit:** selected-run waterfall with waiting/working/outcome segments and gate attempts from `learnings.jsonl` as ticks with attempt numbers.
6. **Unit:** structured `run-log` panel — grouped by step, failing group auto-open, skipped folded, level chips with counts, search across folded groups, line anchors, raw toggle.
7. **Home:** "Where the GPU went (7 days)" — productive vs burned-on-failure hours per step (today 48 of 113 h burned), plus a top-3 flakiest-steps leaderboard.
8. **Floor:** one GPU lane timeline (24 h back, now line, 12 h forward) with queued orders as hatched p50-width ghost bars giving a queue ETA; an idle strip under it.
9. **Floor:** collapse the 92-row call sheet into department groups with counts; actions live inside the expanded group.
10. **Book / org:** put the only node-link DAG at the cross-department lineage per book with stale badges; never a DAG for the 12-step chain.

## 3 disagreements I expect with other researchers

1. **Density vs editorial calm.** The film-studio and paper-look researchers will want large thumbnails and whitespace; I want a 10 px-cell run matrix and dot plots on the unit page. I hold that 52 runs is the unit's real story and only a dense grid tells it in one glance; thumbnails belong below it.
2. **Percentile ETAs vs a single "done at" time.** SaaS-polish researchers (Linear/Vercel) will prefer one confident timestamp. Shoot durations span 63 → 124 min at p50 → p90; a single time is a lie half the time, so I want both ends labelled.
3. **No DAG on the unit page.** Ops-monitor peers (and the brief's "the DAG view") may push an Argo/Dagster-style graph per unit. A linear chain gains nothing from node-link drawing; the rail + matrix already are the graph. The DAG earns its space only at book/department lineage.
