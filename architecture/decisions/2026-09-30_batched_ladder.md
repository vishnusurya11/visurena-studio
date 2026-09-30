# 2026-09-30 — Every cure rides one batched round

**Trigger.** The owner, on ep14's timing table (takes 18.8 h over 32 rounds): "why 32
rounds .. before you were able to do in 3-4 rounds max 5 .. use 5 sub agents .. debate
and come up with solution." Five subject-matter experts debated; the verdict of record
is `docs/audit/2026-09-30_rounds_debate.md`.

**Finding.** The rung-serial ladder (seed → move_type → shorter_take → head_cut →
replan_cell, one round per rung, re-judging between rungs) multiplied rounds against
the measured cure rates: seed ~0% solo (3.6 GPU-h spent), shorter-on-lag 0/15,
replan-content 3/21 — while move_type ran 89–100% at ~8 min a cure. 86% of ep14's
take faults were input-borne (panel/prompt), incurable by any render. The old process
(ep10 synthesis F1) was ONE person-chosen batched round per master; automation lost
the batching, not the taste.

**Decision (three phases).**
- **A — the judges tell the truth** (committed `b5e41e3`): beard rows read per face,
  a declared crowd waives the count, print scoped to sizes where it reads, dusk joins
  the daylight words, pass-through demoted to advisory pending a WotW bench.
- **B — the batched ladder** (this build): one `batched_cures` rung, tries 2.
  `cure_of` routes each faulted take to its measured cure (move_type; free
  timeline_trim for lag; free head_cut for a covered leak; input-borne kinds and
  repeated/never-seed rows to the terminal). `route` drops capped takes and, on the
  second try, takes whose fault signature did not progress (the circuit-breaker).
  The union renders in ONE round; free cures cost no round. `ROUNDS_CAP = 2` across
  resumes in `takes/r2v/ladder.json`, which now records each round's fault
  signatures. The old rung constants stay defined for their prices and tests.
- **C — the plan tells the truth first**: G-CROWD refuses crowd prose under a
  wide/full shot with `extras=0` at plan time (11 ep14 shots were born
  self-contradictory); the battery lists the expects-text set.

**Expected.** ep14's fault stream replayed under A+B ≈ 5 rounds / ~3 GPU-h instead of
19 / ~10; a 30-shot episode's takes land in round 0 (~2 h) + ≤ 2 batched rounds +
terminal.

**Follow-ups (tracker).** A content → panel-redraw-then-one-render rung
(`retake_shot` as code, today content routes terminal); wardrobe-prose text-prop lint
on the refs side; panel_place calibration over ep06/ep09-13; a shadow-bench promotion
path for demoted judges (pass-through's PASS_WALL first).
