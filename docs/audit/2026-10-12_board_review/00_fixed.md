# 00 — What the fixer did with the four board reviews (2026-10-12)

Inputs: `01_bugs.md`, `02_data_truth.md`, `03_ux.md`, `04_speed.md` in this folder. Every item was
checked against its file:line before it was touched. Nothing was posted to the live board, the board
was not restarted, no runner or autopilot was run, and **the live DB was not written** (the ledger
projection was proved on a copy in the session scratchpad instead; see P1).

## Commits

| group | commit | what |
|---|---|---|
| P0 money / isolation | `91841e1` | the session guard: no test writes the live DB, resolves a remote host or spawns the claude CLI |
| P1 data truth | `e190c2d` | `[arch]` the ledger settles book stages; the disk, the channel and the engine on the board |
| P2 bugs | `43e5f90` | B01–B13, S1, the acknowledge proof |
| P3 UX | `95fee44` | list A (the rest of it), the org chart on Studio dark |
| P4 speed | `49b8159` | mmap, mtime caches, no sibling renders, light unit partials, prune, real-data budget |
| this file | the last commit | S10 (sidebar title) and this report |

## P0 — money and isolation: what was found

- **The writer.** `tests/test_autopilot_cli_brain_wiring.py::test_run_brain_briefs_from_disk_and_maps_the_verdict`
  faked `brain.turn` but not `ledger_conn`, so `scripts/episode/autopilot.py::ledger_brain` opened
  `db.get_connection()` — the relative `db/visurena_studio.db`, the **live** DB from the repo root — on every
  suite run. Its fake turn returns `total_cost_usd: 0.2`, which is the $0.20 on the early rows.
- **No money was spent.** The turn was faked: every row has 0 input and 0 output tokens. No test path reached a
  paid API in this session's runs: the paid surfaces are `studio/llm.py` (OpenAI client to the providers),
  `studio/brain.py` (claude_agent_sdk spawns the `claude` CLI) and `scripts/episode/{cast_cards,storyboard,title}.py`
  (gpt-image); all now trip under pytest.
- **The guard** (`tests/guards.py`, installed by `tests/conftest.py` for every test): a write-capable
  `sqlite3.connect` of the live DB raises `LiveDbRefused` (a `mode=ro` URI is allowed); `socket.getaddrinfo` of any
  host but this machine raises `PaidCallRefused` (every paid API is a remote host); `SubprocessCLITransport.connect`
  raises (the brain's CLI). The ComfyUI trap now also covers the board's new `/queue` reader. Proved by
  `tests/test_no_test_reaches_a_paid_api_or_the_live_db.py` (11 tests). The full suite ran under the guard: see Test counts.
- **The live rows, listed, not deleted.** 33 rows in `usage`, `codex_id = '20990101000000'`, `stage = 'brain'`,
  `step_id = 'triage'`, `unit = 'ep02'`, 0 tokens each:
  ids 13096, 13097, 13099, 13100, 13107, 13117, 13118, 13374 (`claude-sonnet-5-5`, $0.20 each = **$1.60**,
  2026-10-06 17:33Z .. 10-07 14:09Z); ids 13381, 13422 (`claude-sonnet-5-5@subscription`, NULL), 13563 and
  13723–13744 (`claude-sonnet-5@subscription`, NULL), 2026-10-07 14:39Z .. 10-12 14:11Z. The review saw 32; one more
  landed at 14:11Z before the guard. To remove them, after a backup:
  `DELETE FROM usage WHERE codex_id = '20990101000000' AND stage = 'brain';` (owner's call; the codex id is not a book).

## Every item

Legend: **fixed** (commit) · **dropped** (why) · **deferred** (why, what it needs).

### 01_bugs.md

| item | outcome |
|---|---|
| B01 side-panel files 404 on book units | fixed `43e5f90` — the list shows only names the unit's index holds |
| B02 state chips ignore `?book=` | fixed `43e5f90` |
| B03 unit stamps in UTC | fixed `43e5f90` — `.astimezone()` as the shell does |
| B04 "Today" is the UTC day | fixed `43e5f90` — `views.local_day_start` |
| B05 "Up to" a 404 | fixed `43e5f90` — `app.error_parent`: the department, the shelf, or no button |
| B06 JSON routes answer an HTML 404 | fixed `43e5f90` — `/api/ /json/ /viewer/ /log/` answer `{"detail": …}` |
| B07 palette remembers error pages | fixed `43e5f90` |
| B08 "1 takes fault" | fixed `43e5f90` — "1 fault, flagged" after the template's `GATE:` |
| B09 "1 units", "1 files", "1 need you" | fixed `43e5f90` |
| B10 empty wall slot in a pass title | fixed `43e5f90` |
| B11 a rise read "stuck" | fixed `43e5f90` — improving / stuck / worse. The per-gate "higher is better" flip is not done: every measured gate today is a fault count or an overrun (lower is better) |
| B12 ep14 first on /b, last on /d | fixed `e190c2d` — one key, `views.unit_order` |
| B13 red "0" | fixed `43e5f90` (server and pulse) |
| S1 thumbs without `?v=` cached a year | fixed `43e5f90` — immutable only with `?v=`, else `no-cache` |
| S2 loose palette fuzzy match | dropped — the reviewer's own verdict: noise, the exact hit ranks first |
| S3 `?rows=` on a plain .json | dropped — harmless, nothing asks for it |
| S4 cold first loads | partly fixed by P4 (`49b8159`); the cold thumb path (#10 below) deferred |
| S5 "Masters 2" vs 3 files | deferred — not verified as a fault (the Viewer may separate r2v from iterations); needs the Viewer owner's intent |

### 02_data_truth.md — confirmed

| # | outcome |
|---|---|
| 1 screenplays all "queued" | fixed `e190c2d` — `tick.settle_from_events` (`studio/ledger_settle.py`). Proven on a DB copy: Dracula, P&P, Dubliners, Jekyll **failed** (into Needs you), Scarlet **done ⚑1** (a 08-30 re-run failed at 03), 25 **queued at 05 verify** (01–04 completed, 05 never ran). The live rows change on the next tick |
| 2 trailers "queued" | fixed `e190c2d` — Scarlet done ⚑1 (re-run failed at 03 on 09-07); Jekyll done from its file (`deliverable: trailer/main/TRAILER-*.mp4`, no ledger) |
| 3 Scarlet refs "queued at 03" first in line | fixed `e190c2d` — `tick.settle_consumed`: "legacy: consumed by 14 published episodes"; the idle card no longer says "the GPU waits for a runner" (no runner polls the queue) |
| 4 GPU card idle while ComfyUI runs | fixed `e190c2d` — `comfy_tap`: GET `/queue`, 0.5 s timeout, 5 s cache, refreshed on a thread so no page waits; the process table names the script ("GPU busy outside the runner: refs/looks_table.py · Jekyll") |
| 5 ep08/ep01 play an unpublished master | fixed on the board `e190c2d` — a published unit plays the file whose sha8 is the live upload's (the QC'd one when its own sha8 matches, else hashed once per process). **Deferred:** the tick re-pointing a done row's `deliverable`: it would hash every published master on every tick |
| 6 ⚑N on published tiles | fixed `e190c2d` — `row_view` carries `flags_open` (the `flags_open` rule) |
| 7 "GPU-h" counts LLM steps | fixed `e190c2d` — only steps `timing_sum.STAGES` marks as GPU; "most lost" instead of "lever" |
| 8 dead runs' open timers | fixed `e190c2d` — open only in the live run; else "no end (run died)", no wall |
| 9 "no runs yet" on book units | fixed `e190c2d` — `COALESCE(unit,'book')` |
| 10 stale LOOK shown passed | partly fixed `e190c2d` — the unit page re-checks PLAN and LOOK at render and names a moved one `stale`. **Deferred (owner ruling):** wiring `tick.verify` into the tick flips published units stale and floods Needs you. The WotW refs row's `flags=1` over a 0-fault verdict is not touched |
| 11 "Moved 20 h" | fixed `e190c2d` + `95fee44` — Moved is the newest event, else finished |
| 12 making / no picture / unit counts | fixed `e190c2d` — making = an episode not done; poster fallbacks (board panels, reference takes, contact sheets); /b counts rows like /books |
| 13 ep14 NULL sequence | fixed on every page `e190c2d` (`unit_order` falls back to the unit's number). **Deferred:** backfilling `number`/`sequence` in the live DB and making the run's upsert apply `unit_grammar` (a live write) |
| 14 spend.jsonl hidden behind $0 | fixed `e190c2d` — unit pages show the priced part with "+ N unpriced", and the book's spend.jsonl total ($41.02 for Scarlet). **Deferred:** importing spend.jsonl into `usage` (a live write) |
| 15 published units "step 11 of 13" | fixed `e190c2d` — a done row stands at its last step without progress |

### 02_data_truth.md — suspected

| # | outcome |
|---|---|
| S1 a deleted upload counts | fixed `e190c2d` — `backfill.deleted_ids` |
| S2 WotW ep16 has three public uploads | deferred — needs a channel check (no API call was made) |
| S3 the board never reads the autopilot | fixed `e190c2d` (A22) — "complete · still paused in series.json (two parked in a row: ep22, ep23)" for WotW today |
| S4 compilations have no row | deferred — needs a stage in stages.yaml (an architecture proposal) |
| S5 two "todays" | fixed `43e5f90` (B04) |
| S6 fake-codex rows | P0 `91841e1` — rows listed above, not deleted |
| S7 "queued" overstates | fixed `e190c2d`/`95fee44` — the meaning, the idle card and the queue subtitle say nothing polls the queue. The `v_queue` order (by stage name) is unchanged: a view in the live schema |
| S8 stale `codex.<stage>_status` | mitigated `e190c2d` — the ledger settles before the column is read; the columns themselves are untouched (live write) |
| S9 GPU-h per unit undercounts | deferred — `timing_sum.STAGES` vs `eta.py` names need the owner's call on the eyes' second-vote reads |
| S10 sidebar title says the count twice | fixed (this report's commit) |

### 03_ux.md — list A

| item | outcome |
|---|---|
| A1 false LOOPING | fixed `95fee44` |
| A2 Watch on YouTube | fixed `e190c2d` |
| A3 ep14 first | fixed `e190c2d` |
| A4 "no picture yet" | fixed `e190c2d` |
| A5 stale in done-green | fixed `95fee44` |
| A6 plain meanings | fixed `95fee44` |
| A7 red 0 | fixed `43e5f90` |
| A8 sidebar counts under AA | fixed `95fee44` |
| A9 no focus ring on the filter | fixed `95fee44` |
| A10 step 13 wraps | fixed `95fee44` |
| A11 "12 deliver" chip on done | fixed `95fee44` |
| A12 Redo the brightest button | fixed `95fee44` |
| A13 "Look_state" | fixed `95fee44` |
| A14 "1 units" | fixed `43e5f90` (B09) |
| A15 lower-case crumb | fixed `95fee44` |
| A16 "when / taken by" | fixed `95fee44` — "ago", "status", "21 h ago" |
| A17 "lever" | fixed `e190c2d` |
| A18 queue subtitle | fixed `95fee44` |
| A19 raw codex on the shelf | fixed `e190c2d` (kept in the link title) |
| A20 unit titles | fixed `95fee44` — department rows, season wall, Ctrl K |
| A21 empty Up-next boxes | fixed `95fee44` |
| A22 autopilot line | fixed `e190c2d` — Home's idle card and the GPU card |
| A23 beige org chart | fixed `95fee44` — Studio dark `#0f1012` default, Graphite light on `?theme=light` |
| A24 red QC on a published master | fixed `e190c2d` — "QC 4 of 5 checks passed", the shortfall in the title |

### 04_speed.md

| # | outcome |
|---|---|
| 1 mmap on read connections | fixed `49b8159` |
| 2 memoised publish lookups | fixed `49b8159` — uploads.jsonl and the library listing once per mtime. Judging `flags_open` once per request is not done (the two caches remove its disk reads) |
| 3 partials compute only their section | fixed `49b8159` — head/tails/orders/live skip pictures, master and files: 57 → 19 ms on WotW ep18 |
| 4 sibling prefetch, moderate speculation | fixed `49b8159` |
| 5 204 before compute | fixed `49b8159` |
| 6 palette embedded in every page | fixed `49b8159` — pages, books and departments embedded; units and actions fetched on first open |
| 7 memoise `event_marks` | deferred — after #1 the scan reads mapped pages; worth it only if the pulse grows |
| 8 fingerprint N+1 | deferred — the byte-identical fingerprint contract needs its own test pass |
| 9 poster cache per unit | deferred — the library listing is cached (#2); the per-row globs remain (/d/episode is 35 ms warm now) |
| 10 thumb route off the event loop | deferred |
| 11 prune `.cache/thumbs` | fixed `49b8159` — 256 MB cap, oldest first, at start |
| 12 hidden-tab section refetch | deferred |
| 13 real-data budget test | fixed `49b8159` — `tests/test_the_board_meets_its_budget_on_real_data.py`, `local`, skipped without library/ or the DB |
| 14 restart :8700 | owner action (below) |
| side: orders CHECK lacks 'acknowledge' | **does not hold up as a fault**: `work_orders._insert_order` waives the old CHECK for that word; a new test posts `/act/acknowledge` through the route against an old-CHECK DB and reads the row back (`43e5f90`) |
| side: /docs, /redoc served | dropped — 127.0.0.1 only; harmless |

Real data, warm (`-m local`), before → after: `/` 37 → 20 ms (74 → 49 KB), pulse 16.4 → 12.6 ms,
`/d/episode` 53 → 35, `/b/<WotW>` 56 → 26, WotW ep18 91 → 78, unit partials 57 → 19.

## The B list (03_ux.md), ranked for the owner

1. **B2 "On YouTube" shelf + links on the season wall** — high value, S effort: `backfill.live_upload` now gives the video id per episode.
2. **B1 autopilot panel** — high value, M: A22's reader is in place (`views.autopilot_lines`); add events.jsonl's last 10 and the parked list.
3. **B5 one table for one-unit-per-book departments** — medium value, S: /d/refs is 5,933 px of 30 one-row cards.
4. **B4 queue grouped by department** — medium value, S–M: 89 flat rows become one line per department with its count.
5. **B9 order controls behind ⋯** — medium value, S: free-text hold inputs leave the page headers.
6. **B8 tap-to-explain pills** — medium value, S: `title=` never shows on a phone.
7. **B6 finished-episode layout** — medium value, M: lead with YouTube, master and judges; fold Runs/Files.
8. **B3 GPU lane timeline + 30-day history** — high value, M–L: needs a GPU/VRAM sampler the board does not keep yet.
9. **B7 viewer screening lanes** — medium value, M–L.
10. **B10 books shelf with faces** — low–medium value, M (A19 and the unit-count fix took the cheap half).
11. **B11 spec drift (/floor 301, book-first URLs)** — low value, S / M.

Publishable (EB-1 note): `tests/guards.py` is a generic, dependency-free pytest guard ("no test touches the
production DB, the network or an agent CLI") that would ship as a small pytest plugin; `comfy_tap.py` plus
`views.autopilot_lines` is the read-only "engine + supervisor status card" the 03 review already flagged.

## Test counts

- New tests: 135 in 15 new files (`tests/test_no_test_reaches_a_paid_api_or_the_live_db.py`, …,
  `tests/test_the_board_meets_its_budget_on_real_data.py`, 11 of them `local`) + 3 added to existing files;
  16 existing tests updated because they pinned the faults fixed here.
- Board subset (99 files): 1345 passed, 2 skipped after P4; P3/P4/S10 test files 17 + 12 passed after the last change.
- Baseline full suite before any change (no guard): 10825 passed, 7 failed (3 were this work's tests written first).
- Full suite **under the new guard** (started 08:29, it straddled the P2-P4 commits): 10900 passed, 4 skipped,
  8 xfailed, 10 failed, 25 min. **No failure was a `LiveDbRefused` or `PaidCallRefused`**: no other test touches
  the live DB, the network or the claude CLI. 6 of the 10 were old tests it had loaded before they were updated
  in P2-P4; rerun now, those files pass (116 passed).
- **Pre-existing failures, not touched** (they fail in the baseline too): `tests/test_canon.py::TestTier::test_the_canon_is_asked_of_its_own_thinking_tier`,
  `tests/test_llm.py::test_resolve_tier_returns_provider_and_model`, `tests/test_llm.py::test_resolve_tier_carries_params`
  (all three expect the API-key providers and `reasoning_effort` that `models.yaml` dropped when every tier moved
  to the subscription, 2fc2c29), and `tests/test_episode_tail.py::test_a_part_the_join_silently_drops_is_refused`.

## What the owner must do

1. **Restart the board on :8700.** It runs code from before 181e7e1 (04's first finding); none of these commits
   show until it restarts.
2. **Run a tick** (`uv run python studio.py tick`, or let the next runner's first act do it) to project the ledger
   onto the live rows: screenplays failed/queued-at-05, Scarlet refs/screenplay/trailer done, Jekyll trailer done.
   A peer's refs runner held the Jekyll refs row during this work; the tick never touches a running row.
3. **Republish the architecture page's claude.ai copy** (`architecture/index.html` changed in `e190c2d` and
   `95fee44`; the link is in `architecture/README.md`). Not republished here, as asked.
4. **Rule on:** wiring `tick.verify` into the tick (02 #10); deleting the 33 fake-codex usage rows (P0); the WotW
   ep16 triple upload (02 S2); a compilation stage (02 S4).
