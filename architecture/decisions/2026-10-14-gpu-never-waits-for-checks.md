# 2026-10-14 -- the GPU never waits on a check: step 09 runs two lanes

Status: BUILT 2026-10-14 (owner rule of the day; built test-first, committed once the live
episode had left steps 09-11). Tracker: `architecture/plan/2026-10-14_gpu_never_waits.md`.

## The rule (owner, 2026-10-14)

> "it shouldn't wait, the GPU needs running, and the DQ checks should be done after all videos
> are done, or in parallel if the GPU is not needed."

Seen live: the drawn-book remake's step 09 sat at 6 % GPU while the CPU measured its takes.

## What step 09 did

    render ALL  ->  take_dq ALL (CPU)  ->  take_content ALL (VL on ComfyUI)  ->  strip  ->  take_eye
                ->  one batched retake round  ->  take_dq  ->  take_content  ->  take_eye  -> ...

Every stage waited for the one before it. The CPU measures (pose, face, gait, Whisper, the
frame rows; ~29 s a take, ~60 s a retake with its attempts) ran with the GPU idle, and a cure a
CPU row already proved (a frozen take, a shuffling walker) waited for the VL read and the eye
before anything rendered it.

## The brick

**A job runs on the lane its hardware names, the moment its input exists; a GPU job never
waits on a CPU job unless the CPU job can still change what the GPU does next.**

Everything below is that rule applied to step 09's jobs.

## What it does now

Two lanes, polled every 5 s (`studio/take_overlap.py`; the policy, pure, in
`studio/take_schedule.py`):

| lane | runs | rule |
|---|---|---|
| GPU | one `takes_r2v.py` process at a time | the first renders back to back (one process queues them all on ComfyUI, weights loaded once); then any retake a check ordered |
| CPU | one `take_dq.py --cpu-only` process at a time | every take that has LANDED (its bytes complete: `shots.json` is written after the video) and carries no verdict by this measuring code; a check that dies is tried once more, then left to the serial pass |

The GPU queue holds three kinds of job, in this order:

1. **render** -- the first renders.
2. **retake** -- behind every first render still queued; ahead of any GPU check; retakes ordered
   while one waits join it (one process, warm weights).
3. **gpu_checks** -- the reads that need ComfyUI (the VL content read; a deferred DINO leak). Only
   when no render is queued AND the CPU lane is idle. They never preempt a render. They wait for
   a running CPU check because that check may still order a retake, and a retake after the VL
   batch pays the video weights' reload (TAKE_COLD 300 s priced) -- more than any one check
   (29-60 s). In practice that is "after the renders", which is the owner's first option.

### The early round

A take whose dq rows ALONE route to a render cure -- `take_ladder.route` on a dq-only verdict,
cure `move_type` or `seed` (frozen, held, pass-through, camera-move, gait, ...) -- is queued as a
retake the moment its check ends. These retakes are the take ladder's **round 1**: written to
`ladder.json` with `early: true` when the first job of the round LAUNCHES (never when ordered, so
a pause strands nothing), and every later early job in the same pass joins that round. The
plan edit for a move cure goes through `write_plan` at launch too. A learning row
(`EYE_TAKES early_cures`) is written like any rung's.

Not early, by construction: content, clones, twin, identity, unread (the VL read and the eye
find them); the free cures (timeline trim for lag, head cut for leak) -- they stay with the
ladder after the window, where they always cost nothing.

After the lanes go idle step 09 runs the GPU window -- take_dq's serial pass (cache hits, any
check that died, a deferred leak measured with its embedder) and `take_content_check` (one VL
load) -- then the strip and `judge:take_eye`, whose ladder takes round 2 (`ROUNDS_CAP` 2,
unchanged). The ladder's own retake round runs on the same two lanes (`take_ladder.retake`):
renders back to back, each retake's `--attempts` check beside them, no early ordering.

### `--cpu-only`

`takes_r2v` queues every take on ComfyUI in one go, so a check that put a job on ComfyUI would
wait behind every render and its model load would evict the H3 stack between takes. `take_dq
--cpu-only` therefore never calls ComfyUI: when the `image_embed` workflow is installed, the leak
row is read by the embedder-free step measure and the verdict is marked `deferred: ["leak"]`;
the cache never serves a deferred verdict and step 09 never counts one current, so the GPU
window measures that take again with the embedder. With no embedder installed (production
today: every Jekyll and WotW verdict reads the step leak) nothing is deferred and the verdict
is byte-for-byte the serial one.

## Every guarantee kept

| guarantee | how |
|---|---|
| batched cure round cap (2) | the early round IS round 1 in `ladder.json`, counted once however many jobs carry it; opened only when no round was taken since the clock's reset; the ladder's `still_curable`/`progressed` read it unchanged |
| MAX_TAKE_ATTEMPTS (3) | `take_ladder.route` filters the early cures exactly as it filters the ladder's |
| honest clock | one `takes` row around the whole two-lane pass; the CPU rows are stamped `within: "takes"` and the outer row net of them, so every reader that sums `seconds` counts the wall once (the master-upscale contract); the budget reads wall time, untouched |
| downstream reserve | an early job must pass `leaves_reserve` AND `take_ladder.can_afford` for its own takes; no budget, no early round |
| a check is never cut while the clock has room (24ba65b) | the CPU lane carries `dq_flags(ctx)` exactly as the serial pass does |
| idempotent resume | the disk is the state: a landed take with a current verdict is never measured again; an early round already recorded is joined, its takes never cured early twice; takes_r2v renders only missing or stale takes |
| renders before checks for model residency (five-hour P0) | the CPU lane never touches ComfyUI; the VL read waits for the GPU queue to empty |
| G-GAIT / G-DEAD / G-PRESENT / every take row | unchanged: the same `take_dq` code measures them, in another process at another time |
| ComfyUI shared with another production | the render job waits for an idle engine (2 h cap, as `run_script`); the CPU lane does not wait |
| boundary pause | once the boundary is asked no job launches on either lane; the running ones finish and the pause is raised when the lanes stop; an early retake ordered but never launched is not recorded as a round |

## Measured: the replay

`uv run python scripts/episode/take_schedule_replay.py <book> <n>` reads the episode's own
`timing.jsonl`, `phases.jsonl` (each render's seconds) and `ladder.json`, and projects the same
renders and the same checks three ways. On the drawn-book remake (ep01, 2026-10-14: 23 first
renders, round 1 of 7 retakes, round 2 of 2):

| arm | wall | GPU idle |
|---|---|---|
| measured rows (the step-09 cycles of the day) | 5573 s | -- |
| serial model (today's order, same costs) | 5455 s | 1464 s |
| overlap only (today's rounds, checks beside their renders) | 4393 s | -- |
| **two lanes + early round (this decision)** | **4232 s** | **302 s** |

**1223 s saved (22 %), GPU idle 1464 -> 302 s.** Sensitivity to the one unmeasured input, the VL
load per batch: 30 s -> 1193 s saved, 120 s -> 1283 s. Five of round 1's seven retakes
(four frozen, one gait) were ordered by the CPU lane during the first renders; the other two
(content, lip-sync) waited for the window, as designed.

What the model does not count, either way: CPU contention between the checks and the render's
own decode/save, and the per-process model loads of a check spawned per landed take (Whisper,
FaceMesh, YOLO; a take lands every ~100 s, a check costs ~30 s, so the lane keeps up). Both
are read off the first live episode's `timing.jsonl` (`take_dq` rows `within: takes`).

## Rejected

- **A check job between renders on ComfyUI ("in the gaps").** There are no gaps: takes_r2v
  queues the whole round at once, so a ComfyUI check either waits behind it or, submitted at
  the front, evicts the video weights -- the 2026-09-12 measurement (407-583 s back to back vs
  742-998 s interleaved).
- **A second takes_r2v process beside the first.** Two writers of `shots.json`; the retake joins
  the GPU queue and launches the moment the running job exits, on warm weights.
- **Retaking content faults early.** They need the VL read, which needs the GPU: they ride the
  window and then round 2.
