# 2026-10-18 -- The run stream and the run truth

Status: APPROVED (owner, 2026-10-18: batches 1-4 of the page-experts list; "write the decision
first, build after their commit"). The board half is BUILT (`69fcdea`); the runner half waits for
the session holding `step_runner.py` to commit.
Evidence: `docs/audit/2026-10-18_page_experts/` (five experts; `00_ranked.md` is the list,
`03_live_integration.md` §2-§4 the contract this decision adopts).
Tracker: `architecture/plan/2026-10-18_run_stream_and_truth.md`.

## Why

The board reverse-engineers a run from log banners and file mtimes (`legacy_progress.py`).
`studio/progress.py` documents `progress.jsonl` and folds it, but nothing writes it. Measured on
Jekyll ep01, 2026-10-18:

- The lease (900 s) renews only on a step event. The LLM plan step wrote none for 15+ min, so
  the head said "~ stale lease" beside a LIVE card while the run's own clock beat every 60 s.
- Three silence detectors use three rules, and none sees LLM work. The card said "stalled", the
  drive sent a false 20-min Telegram, and the autopilot has its own hang check.
- "On the GPU" was shown during an LLM step: the GPU sat loaded but idle.
- A plain `open('a')` from four processes lost 12.7 % of lines and tore 86 (measured);
  `FILE_APPEND_DATA` lost none at 0.37 ms per append.

## Decision

1. **The run stream.** `studio/progress_event.py` is a pydantic union keyed on `ev` (run, end,
   step, sub, plan, item, round, call, job, beat, stall, park). It uses UTC epoch `t` only and
   refuses an absolute path. One writer, `studio/progress_sink.emit`, appends with
   `FILE_APPEND_DATA` and is a no-op unless the run sets `VISURENA_PROGRESS`. Eleven emit sites
   are shared services and the runner (03 §2.4); no department imports Strands or the runner to
   emit. The DB `events` table stays the journal; where the two disagree, the DB wins.
2. **The run truth.** `studio/run_truth.py` (pure, `now` passed in) holds the stall, activity
   and lease rules. The board shows it, `drive.py` writes the one stall event, and the autopilot
   acts only at its higher threshold. The stall budget follows what runs: a GPU job, an LLM call,
   or the step's full-run median.
3. **The heartbeat renews the lease.** `run_clock`'s 60 s beat renews the work order's lease.
   The 45-min mtime heuristics (`vitals.files_alive`, `views._files_carried`) retire after one
   full episode on it.
4. **Transport.** The live card moves to SSE: native `EventSource`, the byte offset as the event
   id, a 15 s keepalive, a 204 at the run's end, and the poll as the fallback. The 2 s pulse stays
   for the shell. Polling was measured cheap (pulse 16 ms after D4); its fault is latency.
5. **Legacy retires by parity.** The dual source and the parity test come first, then the default
   flip after one full episode on the stream; only then are the banner regexes deleted.

## Not decided here

Per-take redo (a take-level order) stays a separate proposal (the media expert's E4, size L).
