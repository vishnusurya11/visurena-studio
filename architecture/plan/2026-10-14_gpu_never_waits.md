# 2026-10-14 — The GPU never waits on a check (step 09, two lanes)

Status: **BUILT 2026-10-14** — the two-lane scheduler, the early round, `take_dq --cpu-only`,
the replay. First live episode under it: the next one launched after the commit.
Decision: `architecture/decisions/2026-10-14-gpu-never-waits-for-checks.md`.
Owner rule: "it shouldn't wait, the GPU needs running, and the DQ checks should be done after
all videos are done, or in parallel if the GPU is not needed."

## Commits

- [x] `studio/take_schedule.py` — the GPU queue's policy (render > retake > gpu_checks; checks
      wait for an idle CPU lane, never preempt) and the wall-clock projection (serial,
      overlap_only, overlapped); `tests/test_the_gpu_never_waits_on_a_check.py`
- [x] `take_dq.py --cpu-only` — no ComfyUI job beside a render; a deferred leak is never cached
      nor current; `tests/test_a_cpu_check_never_queues_on_comfy.py`
- [x] `studio/take_overlap.py` — the two lanes run for real: landed takes checked as they land,
      the early round (ladder.json `early: true`, joined, learned), boundary, busy engine, the
      `takes` row with its CPU rows `within`; `StageContext.spawn`;
      `tests/test_take_lanes_run_side_by_side.py`
- [x] step 09 + `take_ladder.retake` on the lanes, the GPU window after them
- [x] `scripts/episode/take_schedule_replay.py` — the projection off an episode's own clock;
      `tests/test_the_take_schedule_replays_an_episodes_clock.py`
- [x] skill (SKILL/GATES/LESSONS), the architecture page, README, DECISIONS
- [ ] read the first live episode's `take_dq` rows `within: takes`: per-check seconds beside a
      render (CPU contention, per-process model loads) against the 29 s / 60 s the replay used

## Log

- 2026-10-14: built while the drawn-book remake ran step 09 live under the autopilot;
  committed only after that episode left steps 09-11, so no code moved under a running step.
- Replay of that episode's own clock (`take_schedule_replay.py`): serial model 5455 s,
  two lanes 4232 s — 1223 s saved (22 %), GPU idle 1464 s → 302 s. 5 of round 1's 7 retakes
  were dq-borne and would have rendered during the first pass.
