# 2026-10-12 — The events ledger settles the book-level departments

Status: **BUILT 2026-10-12**, decided by the board-review fixer on the owner's behalf
(his standing "decide, don't ask" order), open to veto.
Evidence: `docs/audit/2026-10-12_board_review/02_data_truth.md` (#1, #2, #3, #10) and
`docs/audit/2026-10-12_board_review/00_fixed.md`.

## The fault

The board only knew what a runner wrote into `work_orders`. Rows for analysis,
screenplay, trailer and refs were materialized on 2026-09-26, after most of their work
had run, so:

- all 30 screenplays and trailers read `queued, step – of N` over hundreds of events;
- Dracula, Pride and Prejudice and Dubliners failed at screenplay 02/03 and Jekyll at 05
  verify, and none of them was in Needs you;
- Scarlet's trailer delivered (10 completed, 2026-09-07) and read queued;
- Scarlet's legacy refs (no `pack.jsonl`, no verdict, 0 refs events) sat first in the
  queue forever, though 14 published episodes were built from them.

`tick.settle_skipped` needs a stage `deliverable:`; only episode declared one.
`tick.settle_from_ledger` trusts `codex.<stage>_status`, stale since August.

## Is a `deliverable:` per stage the right mechanism?

**Only half of it.** The disk cannot say whether a screenplay was verified: Jekyll has a
`qc_report.json` written by a 05 verify that FAILED (56 blocking findings), and 25 books
have `screenplay.json` from steps 01-04 but never ran 05. A file-only rule would call
Jekyll done. The ledger can say it. So:

1. **The ledger first** (`studio/ledger_settle.py`, `tick.settle_from_events`): a blocked or
   queued book-level row with terminal step events is what they say —
   `done` when the stage's last step completed (flags 1, with the failure in the note, when a
   later re-run failed: Scarlet's trailer and screenplay); `failed` when nothing delivered and
   the newest terminal event failed (lands in Needs you); otherwise only its cursor moves to the
   step after the newest completed (25 screenplays: queued at 05 verify).
2. **The disk only where the ledger is silent** (`settle_skipped`, now with a declared
   `deliverable:` for every stage): `analysis/qc_report.json`,
   `screenplay/feature/qc_report.json`, `trailer/main/TRAILER-*.mp4` — the trailer itself,
   so the pre-runner Jekyll trailer (two masters, no events, no manifest) settles done.
3. **Consumption** (`tick.settle_consumed`): an upstream book-level row the episode `requires`,
   with no ledger and no deliverable on disk, is done once an episode built on it is on the
   channel ("legacy: consumed by 14 published episodes").

A running, held, failed, deferred or done row is never touched: the tick still moves only
blocked and queued rows.

## Not done here (deferred to an owner ruling)

`tick.verify` (the only caller of `db.mark_stale_verdicts`) is still not called by the tick.
Wiring it would flip finished, published units to `stale` whenever a later step rewrote a
signed file (WotW refs LOOK: signed pack 4b0a9ecd, the per-episode looks rewrote it to
57f5f814) and flood Needs you. The unit page re-checks the cheap signatures (PLAN, LOOK) at
render and names a moved one `stale` without changing the row.

## What the owner sees after the next tick

Screenplay: 4 failed (Needs you), Scarlet done ⚑1, 25 queued at 05. Trailer: Scarlet done ⚑1,
Jekyll done (from its file), 28 queued. Refs: Scarlet done (consumed). The rows change when a
tick runs (any runner's first act, or `uv run python studio.py tick`); this fixer did not
write the live DB.
