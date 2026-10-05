# Episode Progress Tracker: the chair's spec

No deliverable this pass. This is the spec, and nothing in the repo has changed yet.

This spec settles the disagreements between the ten lenses and the two critics. Where it overrules a lens, it says so in one line, and the reason is a fact I measured or one that a critic re-checked against the repo, the database and the process table.

## 0. Rulings

| Disagreement | Ruling | Why |
|---|---|---|
| Was ep17 healthy or dead? | **Dead.** PID 22060 is gone and `drive.jsonl` has only a `start` row. | Checked by the engineering critic. The page's first job is to say "dead" truthfully. |
| Where progress is stored | **An append-only file, `episodes/epNN/progress.jsonl`.** `work_orders.progress` only gets a one-line mirror, written at step boundaries by the process already writing the tracker. | The database is in rollback-journal mode (not WAL), and the board reads it with a 250 ms busy timeout, so writes every 2 s would contend. |
| Should progress beats renew the lease? | **No.** The lease is the GPU lock (decision of 2026-09-25), and `queue.renew` does not check `run_id`. When the PID is alive, the board shows the "stale lease" pill as grey text instead of red. | Changing the lease is a separate owner decision. |
| Liveness signal | **First the PID is alive, then the newest runner-written signal.** A PID counts only if its process started no later than `started_at`. A runner-written signal is a `progress.jsonl` line, the runner log, or a ComfyUI event. File mtimes elsewhere never count. | `ep17/plan.json` was written 7 minutes after the runner died. |
| Transport | **v1 polls JSON every 2 s** into page nodes that stay in place. No SSE and no websocket to the browser. | Nothing new to depend on, and it matches the server-computed, test-first design. Animation is driven by the client clock, so motion does not depend on the poll rate. |
| htmx swap | **The live card sits outside `#head`'s `outerHTML` swap.** | htmx is 2.0.4 and idiomorph is not bundled. Swapping the card would restart every animation every 3 s. |
| ComfyUI `/ws` | **Server-side bridge, in the last commit, optional.** The browser cannot connect: `server.py` sends a 403 on an origin from a different port. The sampler has **8 steps**, so the display is "sampler k/8", then "decoding". | Needs `uv add websockets==<pin>` followed by `uv sync --all-groups`. |
| ETA display | **One rounded finish time** ("done around 02:45"), plus a smaller line with the range and the run count. It updates at most once a minute. Past p90 it reads "running long" and shows no number. | Points from both critics. |
| tqdm | **Only in `scripts/episode/watch.py`.** Pin `tqdm==4.70.0`, the version already in `uv.lock`; the telemetry lens's 4.67.1 would downgrade it. | stdout goes to a log file, so `\r` progress bars would clutter it. |
| Previews | **v1 shrinks images inside the board process** with PIL, keeps them in an LRU cache, and serves versioned URLs. Posters and loops written by the pipeline come after the episode, in a commit of their own. | The `app.py` rule says no route spawns a process or writes a file. Memory says no mid-run commits. |
| CSS tokens | **The new motion tokens go in a second `:root{}` block after `*{box-sizing`.** | `tests/test_the_board_copies_the_org_charts_tokens.py` requires the first block to match byte for byte. |
| History source | Use the **`events` table**, `timing.jsonl` and `shots.json`. Never use `drive_runNN.log`. | `drive.py` overwrites `drive_run01.log` on every launch. |

**Cut from v1:** SSE hub, BroadcastChannel, the nvidia-smi "wedged" heuristic, master sprite scrubber, orphan counter, lifeline, and pipeline-written posters and loops.

**Kept in v1:** the Now card, the darkroom contact sheet, the signal trace, ladder chips, a time-proportional step rail, title and favicon, and completion handing over to the master player.

---

## 1. The progress event file

**Path:** `library/<book>/episodes/epNN/progress.jsonl`. It is append-only, one JSON object per line.

**Writer:** `studio/progress.py`.

- `emit(home: Path, ev: str, **fields) -> None` is best-effort. It wraps everything in `try`, does `open('a')`, `write`, `flush` and `os.fsync`, and never raises.
- `run_id` and `pid` come from `os.environ["STUDIO_RUN_ID"]` and `os.getpid()`.
- `episode.py` sets `STUDIO_RUN_ID` and `STUDIO_EP_HOME` before steps run. Subprocesses started by `stage_run.run_script` (via `subprocess.run`) inherit them.
- Timestamps are always UTC epoch floats (`"t"`). This removes the local-time problem in `timing.jsonl` at the source.

**Schema (v1):**

```json
{"v":1,"t":1759624861.2,"run":"2026..__episode__20261005002109","pid":41212,
 "ev":"step|sub|plan|item|round|end",
 "step":"09","name":"shoot",             // step + sub
 "state":"start|done|skip|fail|deferred|refused|escalated",
 "sub":"takes",                           // sub
 "items":[["T01",192],["T02",88]],        // plan: id, weight (frames for takes, cells for grids, 1 otherwise)
 "kept":["T00"],                          // plan: already-current items (resume)
 "item":"T05","weight":192,"secs":182.0,"prompt_id":"..","note":"192f 8.00s",   // item
 "gate":"PLAN","measured":6.0,"threshold":null,"action":"fresh_brief","terminal":false,"round":2,"cap":2,  // round
 "outcome":"completed|deferred|refused|failed"   // end
}
```

**Write sites.** Each is a small call with a test.

| # | Site | Emits |
|---|---|---|
| W1 | `studio/step_runner.py:82–98` (`run_steps`) and the failure branches at lines 69–77 | `step` start, done, skip and fail, with `total=len(steps)`. |
| W2 | `studio/episode_clock.py:67` (`timed`) | `sub` start and done. This one hook covers takes, take_dq, take_content, strip, assemble, qc and master_eye. |
| W3 | `scripts/episode/takes_r2v.py:1020`, right after the `queueing N takes` print | `plan`: `items` = the kept takes plus `jobs`, weight = frames. This is the only true total, because `shots.json` only grows as takes land. |
| W3b | `takes_r2v.py:1022` (`keep()`) | `item` done, with `secs = render_s` from ComfyUI history and `prompt_id`. |
| W3c | `takes_r2v.py:780` (the `LOST` branch) | `item` fail. |
| W4 | `scripts/episode/grids.py:329/351`, plus the step 03, 07 and 08 loops that call it | `plan` with cells at loop start, then `item` done at the line-351 print. |
| W5 | `studio/episode_run.py:46`, where every ladder rung is already logged as `GATE: measured X vs Y -> action` | `round`. This covers PLAN, panels, takes and master in one place. Set `terminal` from the action suffix. |
| W6 | `scripts/episode/drive.py` | `end` with the outcome. The silence check also uses `progress.jsonl`'s mtime, not only the drive log's size. Rename the run log to `drive_<launchts>_runNN.log` so a relaunch no longer overwrites it. |
| W7 | `episode.py`, at step boundaries only | Mirror one line into `work_orders.progress`, e.g. `09 shoot · 5/26 · ~02:45`, from `fold()`. |

Land W1–W7 **between episodes**, never while a drive is running (`drive.py` warns when code moves mid-run).

---

## 2. Elapsed time and ETA

All of this lives in **`studio/eta.py`** as pure functions. `now` is always passed in, and no ETA logic runs in JavaScript.

**Elapsed** is a fact:

- **Run elapsed** = now − the first `t` of this run in `progress.jsonl`.
- **Step elapsed** = now − the latest `step start`.
- **Episode work-clock** = `run_budget.spent_before(home)` + run elapsed, measured against the 5 h ceiling `EPISODE_CEILING_SECONDS=18000`.
- Wall time across refused and deferred runs is shown separately, never mixed in.
- Fallback for runs before `progress.jsonl` existed: `events.started` (UTC), with any `timing.jsonl` time passed through `unit_parse.local_to_utc`.

**Step history.** `step_history(conn, last_n_episodes=8) -> {step: [secs]}` takes the started→completed pairs within one `run_id` from `events`.

Measured medians (s) are:

| Step | Median (s) |
|---|---|
| 01 bind | 0 |
| 02 plan | 413 (p90 908) |
| 03 places | 525 |
| 04 record | 111 |
| 05 timeline | ~0 |
| 06 prompts | ~1 |
| 07 board | 530 |
| 08 panels | 2611 |
| 09 shoot | 3764 |
| 10 edit | 93 |
| 11 qc | 1346 |
| 12 deliver | 20 |

`band(xs) -> (p10, p50, p90)`. When n<5, the confidence is `"estimate"`.

**Counted steps (03, 07, 08, 09):**

- Take prior: `TAKE_FIXED + TAKE_PER_FRAME·frames`, with `TAKE_COLD` added once (`episode_clock.py:44`: 300, 60, 1.2).
- Correction: `r` = an EWMA (α=0.3) of `secs/prior` over this run's done items. It is seeded at **0.75**, because recent runs measure 173–209 s against a modelled 262 s.
- Remaining = `r · Σ prior(remaining items)` ± `1.4826·MAD(ratios)·prior_mean·√n`.
- With fewer than 3 items done, the basis is `"norm"`. With 3 or more it is `"measured"`.
- Retake allowance: if `round` events exist, add P(cure) × failed × mean take time, as a separate segment. The bar never moves backwards.

**Loop steps (02, 11, ladders):** `remaining_unknown(elapsed, xs)` returns the median of `{x − elapsed : x > elapsed}`. It returns `None` once elapsed > p90, which the page shows as "running long".

**Episode ETA:**

- p50 = the running step's remaining time + Σ p50 of the steps still to run.
- The band is √(Σ variances) around it, using an IQR-derived σ per step, not summed maxima.
- The band is capped at the ceiling, and the label says so.

**Display rules:**

- The finish time is rounded to 5 minutes and recomputed at most every 60 s. The server holds it; the client caches it.
- The secondary line, e.g. "range 02:30–03:10 · 22 runs", uses `--ink-2`, never `--ink-3` (4.11:1 contrast).

---

## 3. Server endpoints and transport

All are read-only and live in `studio/command_center/app.py`.

| Route | Purpose |
|---|---|
| `GET /api/progress/episode/{codex}/{unit}.json` | `response_model=models.Progress`. Built by `studio/command_center/progress_view.py::progress(home, conn, now, comfy=None)`, the only function here that touches disk. It caches history by mtime. Budget: under 30 ms, under 6 KB. |
| `GET /thumb/{codex}/{w}/{path}?v={mtime_ns}` | `w ∈ {160, 320}`. PIL WebP at q75 in an in-process LRU keyed `(rel, mtime_ns, size, w)`, capped at 64 MB. Sent with `Cache-Control: public,max-age=31536000,immutable`. Add `.webp` to `SUFFIXES` in `library_paths.py`. |
| `/lib/...` | Change `app.py:223` from `no-store` to `no-cache`, so ETags give a 304. |
| (commit 7) ComfyUI bridge | `studio/command_center/comfy_tap.py`: one asyncio task started on app startup. It connects to `ws://127.0.0.1:8188/ws?clientId=cc-<pid>` and keeps `{prompt_id: (value, max, node, t)}` in memory. It reconnects with backoff 1→30 s. Completion comes from `execution_success`. It is passed into `progress()` as `comfy=`. |

`command_center.py` gets `timeout_graceful_shutdown=3`.

**`models.Progress`:**

```
vital: live|quiet|stalled|dead|refused|deferred|done ; vital_reason ; quiet_s ; budget_s
run_started, step_started, now (epoch) ; elapsed_s ; work_s ; ceiling_s
steps: [{id,name,state,secs,median_s,retries}]           # rail
now_step: {id,name,kind: counted|loop, done,total,weight_done,weight_total,
           current, sampler:{k,of,phase}|null, rounds:[{gate,measured,action,terminal}]}
items: [{id,state: waiting|rendering|landed|failed|retake, panel_url, poster_url, secs, round}]
eta: {finish_at, lo, hi, basis, n_runs, long: bool}
trace: [epoch...]   # runner-signal timestamps, last 30 min
last_words: str     # last runner-log line or round note
title: "● 09 shoot 11/26 · ~02:45 · ep17"
```

**Client.** Inline `static/progress.js`, about 120 lines:

- polls `fetch` every 2 s while the tab is visible and stops at `done` or `dead`;
- patches `data-*` attributes and CSS custom properties on nodes that stay in place;
- ticks the clocks every 1 s from `run_started` and `step_started`, corrected by `now` against `Date.now()` for clock skew;
- sets `document.title` and a canvas favicon ring.

`localStorage` is used only for "notify me", wrapped in try/catch.

---

## 4. Page layout

`unit.html`: a new `_unit_live.html` sits above `#head`, which is now shown in a compact form. It is rendered server-side so it works without JavaScript; JavaScript then takes over.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ep17 · The Exodus                       ● LIVE  last sign 4s  ⌁⌁╱╲⌁⌁⌁╱╲⌁⌁⌁╱╲  │ ← vital + signal trace
│                                                                              │
│   11/26           09 SHOOT · take T12 · sampler 5/8                          │ ← hero: 72px Barlow
│   takes           done around 02:45                                          │
│                   range 02:30–03:10 · 22 runs · 41m in step · 2h31m / 5h     │
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌──    │ ← darkroom contact sheet
│ │T00 ││T01 ││... ││T10 ││T11 ││▒T12││ ░  ││ ░  ││ ░  ││ ░  ││ ░  ││ ░  ││      │   landed=ink, T12 develops,
│ └────┘└────┘└────┘└────┘└────┘└────┘└────┘└────┘└────┘└────┘└────┘└────┘└──    │   waiting=ghost panel
├──────────────────────────────────────────────────────────────────────────────┤
│ ✓01│✓02×3────│✓03──│✓04│·│·│✓07───│✓08 panels──────│▶09 shoot ████▒▒▒░░│10│11 qc──│12│ ← time-proportional rail
├──────────────────────────────────────────────────────────────────────────────┤
│ PLAN 11 → 26 → 6 fresh_brief → ⊘ keep_best (kept, not passed)                │ ← ladder chips (rounds)
│ last words: "plan_check refused: G-LIGHT setup 'london_pool' …"              │
└──────────────────────────────────────────────────────────────────────────────┘
  #head (existing, compacted: umeta folded into <details>) · Health · Gates · Pictures · Master …
```

**Phone (≤600 px, 16 px gutter):**

- vital line;
- hero number;
- finish time;
- the contact sheet as a 6-column grid that scrolls vertically;
- the rail collapsed to "step 9 of 12" in a `<details>`;
- ladder chips wrapping onto new lines.

**The hero changes by step kind:**

- **Counted steps (03, 07, 08, 09):** the big number is done/total.
- **Loop steps (02, 11):** the big number is elapsed `mm:ss`. The ladder chips move up under it with the last refusal sentence, so the owner watches the loop argue with itself.
- **DEAD:** the whole card becomes one ink sentence, "Run stopped at 00:37. Last words: …", with the existing `/act/retry` button. Nothing moves.
- **DONE:** the contact sheet hands over to the master player (`preload=metadata`, muted, first frame) with the QC verdict beside it.

**Components:**

| Component | Template partial |
|---|---|
| Vital line | `_live_vital.html` |
| Signal trace | Inline SVG polyline, 30 min across 240 px. Each blip is a 6 px spike; with no signals the line is flat. |
| Hero | `_live_hero.html` |
| Contact sheet | `_live_sheet.html`; the same component serves steps 03, 07 and 08 using panels or places. |
| Rail | `_live_rail.html`. Width ∝ median, with a minimum of 18 px. The running segment expands to hold its item ticks. |
| Ladder | `_live_ladder.html` |

---

## 5. Motion and visuals

Everything goes in the second `:root` block in `base.html`, and the dark-mode overrides go in both dark blocks. No new colours: running is `--think`, done `--ok`, flagged `--qc`, failed `--accent`.

```css
:root{--ease-out:cubic-bezier(.22,1,.36,1);--ease-std:cubic-bezier(.4,0,.2,1);
 --d1:120ms;--d2:240ms;--d3:480ms;--d4:900ms;--breathe:2.8s;--sheen:2.4s;--stripe:1.6s;
 --think-glow:color-mix(in srgb,var(--think) 35%,transparent);
 --sheen-hi:color-mix(in srgb,#fff 55%,transparent)}
/* dark blocks: --sheen-hi 22%, --think-glow 45% */
@property --p{syntax:'<number>';inherits:true;initial-value:0}
@property --dev{syntax:'<number>';inherits:true;initial-value:0}
```

**Rules:**

- **Only one thing moves**, and only while `vital=live`: the running rail segment plus the single developing tile. Any other vital sets `data-still` on the card, which stops all animation.
- **Rail fill:** `i::before{width:calc(var(--p)*100%);transition:width var(--d4) var(--ease-out)}`. A counted step's `--p` is weight_done/weight_total; a loop step uses diagonal stripes instead: `repeating-linear-gradient(-45deg,var(--think) 0 6px,color-mix(in srgb,var(--think) 70%,var(--paper)) 6px 12px)` animated by `background-position` over `--stripe`.
- **Sheen** on the running segment: `linear-gradient(100deg,transparent 30%,var(--sheen-hi) 50%,transparent 70%)/200% 100%`, keyframes `150%→-50%` over `--sheen` linear. Animation phase is pinned with `animation-delay: calc(var(--age) * -1s)`, so a re-render never restarts it.
- **Developing tile (the darkroom):**
  - Two layers: the panel thumbnail and, under it, the take poster when there is one, else the panel at full ink.
  - The ghost layer gets `filter: grayscale(1) contrast(calc(.4 + .6*var(--dev))); opacity: calc(.25 + .75*var(--dev))`.
  - `--dev` comes from the client: elapsed in this take ÷ (prior·r), capped at .92, and snapped to `k/8·.85` on sampler events.
  - A 3 px conic ring masks the edge: `conic-gradient(var(--think) calc(var(--dev)*1turn),var(--rule) 0)` with 8 notch ticks.
  - When a take lands, the poster comes in with `clip-path: inset(0 100% 0 0)→inset(0)` over `--d3 --ease-out`, plus a 1 px `--ok` inset that fades over 2 s.
- **Waiting tiles:** panel at 25% opacity, dashed `--rule` border, no motion. A failed tile gets a `--accent` 3 px inset and a static ✕. A retake gets an "r2" corner badge.
- **Vital dot:** a `box-shadow` halo `0 0 0 0 var(--think-glow)→0 0 0 6px transparent` over `--breathe`. The animation is re-armed by toggling a class on each **new** signal only. The text never blinks; the existing `pulse` opacity on `.st.blue`, `.sbar`, `.pill` is replaced by this halo.
- **Step completes:** the fill reaches 100% over `--d3`, the sheen fades over `--d2`, the colour changes to `--ok` over `--d2 --ease-std`, and an SVG check draws (`stroke-dashoffset 24→0` over 320 ms). Total time is under 800 ms.
- **Episode completes:** a sweep of `--ok` across the rail, staggered 40 ms per segment, then the hand-over to the master player.
- **Numbers:** `font-variant-numeric: tabular-nums` on all figures, in IBM Plex Mono. The hero number is Barlow Condensed 72 px (44 px on phones). No rolling digits.
- **Reduced motion:** `@media (prefers-reduced-motion:reduce){.live *{animation:none!important;transition-duration:1ms!important}}`. The values still update; the vital reads `● live` / `○ quiet 2m` in words.
- **Accessibility:**
  - `role=progressbar` on the hero, with `aria-valuetext` = "take 11 of 26, done around 02:45";
  - one `aria-live=polite` region holding only the step name and the vital, never the clocks.

---

## 6. Live media

- Every tile uses `/thumb/.../160/...?v=mtime_ns`: the panel `storyboard/h3/shot_NN.png`, and the take poster.
- **v1 take poster:** the panel thumbnail, plus the `.mp4` with `<video preload=none>`, and hover loads the full take. The 1.7 MB file is fetched only on hover.
- **After the episode, in its own commit:** `studio/media_preview.py` with `poster()` and `loop()`, about 0.1 s per take, called from `keep()` and best-effort. Tests use a `FakeRunner` that records the ffmpeg argv.
- Item states are computed in `progress_view` from `progress.jsonl`:
  - `landed` = an `item done` in this run, or an mp4 with mtime later than run start;
  - `rendering` = the bridge's prompt_id → take, else the first not-landed item in plan order while sub=takes;
  - `retake` = a second `item done` for the same id.
- Fixed `aspect-ratio:1` and `decoding=async` on every tile, so nothing shifts as tiles land.
- Opening the page drops from about 77 MB to about 0.6 MB.

---

## 7. Failure and stall states

`studio/command_center/vitals.py` holds pure functions. Checks run in priority order and the first match wins.

| Vital | Rule | Shows |
|---|---|---|
| `done` | An `end completed` event, or `=== EPISODE completed`. | Master player. |
| `dead` | The row is running, and either `pid_alive(claimed_by)` is false or the process started after `step_started`. Checked via ctypes `OpenProcess` + `GetProcessTimes`, wrapped behind an injectable `proc_info` function. Also, no `end` event. | Red sentence, last words, retry action. Every animation stops. |
| `refused` / `deferred` | The last `end` or drive.jsonl `run.outcome` says so. | Red for refused, `--think` for deferred. The reason is the runner log's `plan_check refused:` line. |
| `stalled` | PID alive, and `quiet_s > budget(step)`. | Amber, "quiet 22m · budget 10m", and a bar filling toward the budget. |
| `quiet` | PID alive, and `60 s < quiet_s ≤ budget`. | Grey dot, still. |
| `live` | Otherwise. | Breathing halo. |

**Runner signals** are `progress.jsonl` lines carrying this `run`, the runner log `logs/<codex>/episode/<run_id>.log`, and bridge events for a known prompt_id. Nothing else counts.

**Budgets:**

- Step 09: `2·(TAKE_FIXED+TAKE_PER_FRAME·frames)` for the current item, plus `TAKE_COLD` on the first item. This is 580 s for a 192-frame take, above the 538 s worst case seen.
- Step 02: 600 s since the last runner signal.
- Everything else: `2·norm_for(stage)`.

**Other states:**

- A terminal ladder rung gets a hollow ⊘ chip reading "kept, not passed", never a ✓.
- The "stale lease" pill becomes grey text when the PID is alive.
- Browser notifications are opt-in through a button and fire only on a *transition* into dead, stalled, refused or done, with `tag=unit:vital`.
- The drive's Telegram `notify()` stays as it is; it reads `progress.jsonl`'s mtime too (W6).

---

## 8. Build order

Tests come first in every commit. All tests are free: no network and no GPU. The fixtures are frozen real files in `tests/fixtures/progress/`:

- ep16 `drive_run02.log`, `timing.jsonl`, `shots.json` (26 rows) and its mp4 mtimes;
- ep17 `drive.jsonl`, the runner log and `learnings.jsonl`;
- a synthetic `progress.jsonl` replaying ep16;
- an `events` table extract (SQLite).

No drive letters appear in the fixtures.

1. **`studio/progress.py`, the emitter and `fold()`.**
   - Tests: `emit` appends one parseable line containing `run` and `pid`; `emit` never raises on an unwritable path; `fold` skips a torn last line; `fold` of the replay gives the step, done/total and weights; `plan` sets the total including `kept`.
2. **Write sites W1–W6** (pipeline; land them between episodes).
   - Tests:
     - `run_steps` with fake steps emits start, done, skip and fail in order;
     - `timed` emits a sub start and done pair;
     - `takes_r2v` plan/keep/LOST hooks are tested through extracted helpers `plan_row(kept, jobs)` and `item_row(c, record)`;
     - `grids` emits a cell item;
     - `episode_run` emits `round` with `terminal`;
     - `drive.py` silence considers `progress.jsonl`'s mtime, and the log name is launch-unique.
   - Same commit: `architecture/index.html` (shared service: the progress channel), `architecture/decisions/2026-10-04_episode_progress_channel.md`, `architecture/README.md`, and a `docs/DECISIONS.md` line.
3. **`studio/eta.py`.**
   - Tests:
     - `step_history` takes only same-run pairs from the last 8 episodes;
     - `band` on a known list;
     - `take_remaining` with the 0.75 seed moving to the EWMA after 3 items;
     - replaying ep16 line by line, the ETA never rises when a take lands (excluding round events);
     - `remaining_unknown` returns None past p90;
     - the episode band is capped at the ceiling;
     - mixed UTC and naive-local inputs normalise.
4. **`vitals.py`.**
   - Tests: ep17 replay gives `dead`; a reused PID (process started later) gives `dead`; `plan.json` touched by an outsider is not a signal; budget for a 192 f take is 580 s; terminal rung renders as kept; ep16 replay mid-shoot gives `live`.
5. **`progress_view.progress()`, `models.Progress`, the `/api/progress` route and the `/thumb` route.**
   - Tests: TestClient on `make_library` + fixtures; the contract entry in `test_command_center_api_contract.py`; under 30 ms and under 6 KB; thumb LRU key changes with mtime; the immutable header; `/lib` sends `no-cache`.
6. **Page:** `_unit_live*.html`, `static/progress.js`, the second `:root` block, keyframes, the reduced-motion block, `umeta` folded into `<details>`.
   - Tests:
     - the token-copy test still passes;
     - the WCAG contrast test (≥4.5:1, both themes) on every pair the card uses;
     - the markup has `role=progressbar` and `aria-valuetext`;
     - `aria-live` holds no clock;
     - every `@keyframes` use is gated behind no-preference;
     - the card renders with JavaScript off;
     - the dead state renders no animated class.
   - Then a visual pass with `/browse` against `scripts/command_center/replay_progress.py`, which writes the ep16 replay at 60× into a temporary library. That check is `@pytest.mark.local`.
7. **ComfyUI bridge and `watch.py`.** `uv add websockets==<pin> tqdm==4.70.0`, then `uv sync --all-groups`.
   - Tests: `comfy_tap` fed recorded frames through a fake socket (progress, execution_success, reconnect); the sampler shows "k/8" then "decoding"; the snapshot is still correct when the bridge is down; `watch.py` renders bars from `fold()` output using an injected tqdm.

**Later, in its own commit after an episode:** pipeline-written posters and 3 s loops (`studio/media_preview.py`), the lifeline, and the master sprite scrubber.

**Publishable:** "a crash-safe JSONL progress channel + frame-weighted EWMA ETA + PID-first liveness for long GPU pipelines, with an htmx/vanilla live card" can be split out as a standalone package. The ComfyUI `/ws` tap alone could ship as a ComfyUI-Manager-listed utility.

**Files touched:**
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\progress.py` (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\eta.py` (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\vitals.py` (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\progress_view.py` (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\comfy_tap.py` (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\static\progress.js` (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\templates\_unit_live.html` and the `_live_*.html` partials (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\episode\watch.py` (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\command_center\replay_progress.py` (new)
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\step_runner.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\episode_clock.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\episode_run.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\episode\takes_r2v.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\episode\grids.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\episode\drive.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\app.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\models.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\library_paths.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\templates\base.html`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\templates\unit.html`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\templates\_unit_head.html`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\command_center.py`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\architecture\index.html`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\architecture\README.md`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\DECISIONS.md`