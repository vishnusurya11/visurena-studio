# 2026-10-18 -- The run stream and the run truth (and the honest episode page)

Status: **IN PROGRESS** -- the board half is BUILT in `69fcdea`. The runner half waits for the
session holding `step_runner.py` / `stages.yaml` to commit (shared checkout, no stash).
Decision: `architecture/decisions/2026-10-18_run_stream_and_truth.md`.
Findings: `docs/audit/2026-10-18_page_experts/00_ranked.md`.

## Board half (built, `69fcdea`)

- [x] C1 Seattle time everywhere (one local filter, a no-slice lint test, NaN feed and ladder times)
- [x] A1/A2 the honest timeline: full-run norms (`eta.full_runs`), rule W (`eta.will_run` over
      in:/out:), `eta.project`, "episode done ~HH:MM", "<step> ends ~HH:MM", a window per later step
- [x] A3 a re-make shows the old make as earlier; a gate whose file is gone is "earlier", no 404 link
- [x] B3 the WHY line (`legacy_progress.why_of`, a gate report reduced to what refused); B4 "↗ worse"
- [x] B1 board side: a lapsed lease with a fresh beat reads "beating"; the card's liveness is the beat
- [x] D1 the live card never freezes; D2 elapsed from this run; D3 gates/runs/props on the pulse
- [x] D4 file stamps in the unit fingerprint, a one-query orders partial, `open_flag_keys`
- [x] E1 the delivered master opens on its judged item

## Runner half (after the peer's commit; one small test-first commit each)

- [ ] C1 `studio/progress_event.py` -- the contract; round-trip every kind; refuse an absolute path
- [ ] C2 `studio/progress_sink.py` -- no-op without the env; 4 processes x 500 lines, 0 lost, 0 torn
- [ ] C3 the Tracker hook + `episode.py` run/end + the env
- [ ] C4 heartbeat `beat` + lease renew (`test_a_twenty_minute_step_never_lapses_its_lease`)
- [ ] C5 `timed` / `capture_script` subs; `learn` rounds with `of`
- [ ] C6 `llm.structured` calls (FakeModel); `comfy` jobs (fake HTTP)
- [ ] C7 `takes_r2v` plan/item; panel plan/item
- [ ] C8 `studio/run_truth.py` + delegate `vitals`, `episode_drive.silent`, `autopilot.hung`
- [ ] C9 `progress_view` reads the stream (dual source) + the GPU card via `activity`
- [ ] C10 the projection reads stream rounds (rule R widens hi)
- [ ] C11 the SSE route + `EventSource` in progress.js
- [ ] C12 retire the legacy regexes (after one full episode on the stream)
- [ ] `registry._load` keyed on stages.yaml's mtime (a running board missed steps added since 10-12)
- [ ] architecture page: Platform "Run stream" / "Run truth" flip to built; Current tab rows

## Log

- 2026-10-18 13:20-15:40 PDT: five experts audited the page (reports 01-05); the owner chose
  batches 1-4. The board half was built test-first; the live board restarted after each change
  (it reads templates live but Python at start: one restart missed = a TemplateAssertionError on
  the page, 14:00). Committed by the peer session as `69fcdea` on the owner's "commit as-is".
