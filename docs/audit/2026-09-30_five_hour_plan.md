# The five-hour episode: five-expert verdict (2026-09-30)

Owner's question: the fast era shipped episodes in <= 5 h wall; WotW ep12-14 took 23-92 h.
Five experts (timing archaeologist, GPU economist, process engineer, flow engineer,
production executive) read the past ~28 runs — every timing.jsonl, drive.jsonl,
learnings.jsonl, ladder.json, attempts/, superseded/ and the ComfyUI logs. Unanimous.

## The finding

**The work did not grow. The loops did.** Shots x1.07, runtime x1.04 — logged hours x11.
The seven runs that shipped <= 5 h (SiS ep06-09/12/13, WotW ep10) were all ONE PASS:
one render, at most one batched retake, one QC, nothing redrawn. The new quality layers
(grids, one-room, judges, content gates) cost only ~70 min in a single pass; the other
~29 h of an ep14-shaped run was every stage running 5-30x. WotW ep10 drew 31 grids in
0.3 h and shipped in 5.0 h — the layers are not the problem; re-running them is.

## The seven mechanisms (each measured, each with its owner)

1. **The 5-h ceiling resets on every resume.** `Budget.t0` is per PROCESS
   (run_budget.py; episode_run.py:31); ep14 had 31 driver runs on 23 commits, each with
   a fresh 5 h. The episode as a whole never had a clock. — up to ~29 h on ep14
2. **A reprose leaves the plan signature stale** (LIVE BUG: ep14's plan.json is
   `0f71db24`, its verdict signs `1eb1993f`): every restart between a panel reprose and
   the first take re-ran the whole plan ladder, regrid, re-read. — 3.5 h on ep14;
   after all 6 panel terminals on ep13
3. **Panel work is unbounded across resumes and re-read whole.** `Climb.redrawn` is
   memory-only (waterloo 9 redraws vs CAP=2); every rung re-reads the FULL board
   (RUNG_SECONDS=1900 vs ~300 s incremental; ep13: 28 full passes = 7.2 h, 107 grid
   draws). — 2-10 h per bad run
4. **Model loading is ~4.6-6.7 h per run.** Weights live on the D: HDD. H3 re-stages
   ~115 s of weights EVERY take (41% of a 277 s take; 40 GB staged per prompt, LoRA
   re-patched); the VL judge paid 39-40 disk loads x 214 s (ep13 also 1408 RAM reloads
   = 3.3 h); panel_eye and the master eye don't use model_kept; master eye uncached.
5. **The plan ladder oscillates with no memory.** 12 full 4-rung ladders on ep14
   (3.3 h), battery counts going 56→1→46→1; critic re-read every restart; most refusals
   mechanical (splits, "slowly", span labels) — fixable without a writer call. Plan runs
   on the API (CPU): it could overlap the previous episode's renders entirely.
6. **Fixed costs re-run per resume.** QC 8x (1.2 h), assemble 9x, title on the critical
   path 17-25 min (twice on ep14); QC re-runs on an unchanged failed master (done()
   discards a failed report whose sha8 matches). ep13 then waited 32.4 h to ship.
7. **Mispricing.** TAKE_S=228 vs 265 measured (can_afford approves rounds that overrun);
   panel rung priced 1900 s; EPISODE_SHARES give judges 15 min vs 38 measured; ~2.6 h
   of eye reads per run are invisible to timing.jsonl.

Already fixed this week (verified in the data, not re-litigated): the 9:16 era (~22 h,
G-ASPECT), the rung-serial ladder (batched cures, ROUNDS_CAP=2, circuit-breaker), judge
false alarms, take_dq/content byte caches (38 min a resume → 18 s), G-CROWD, Shorts wall.

## The 5-hour budget for ep15 (30 shots, square), after the P0 fixes

| stage | min | evidence |
|---|---|---|
| bind + plan (hard 10-min share; mechanical fixes first) | 11 | ep14 cycles were re-litigations, not writing |
| places + cast + lines | 31 | ep14: 5.5+5.8+20 |
| timeline/prompts | 2 | ~0 everywhere |
| grids one pass + one panel read + <=1 scoped rung | 40 | ep12: 14 draws 17 min; first read 13 min; scoped rung ~5 min |
| round 0 render (30 takes) | 95-110 | 106 measured; −~40 min once staging is fixed |
| round-0 judges | 35 | 13+25 measured, one VL window |
| batched ladder <= 2 rounds + judges | 45 | 40+51 measured per round, routed subsets |
| title (pre-baked) + assemble + one QC + confirm | 25 | SiS ep13: 7.6+1.4+8.1 |
| deliver + upload on QC pass | 5 | ep14 shipped 4 min after its last row |
| **total** | **~290** | |

## The build list

**P0 — before ep15 (each test-first, small):**
1. **One clock for the whole episode**: `Budget.t0 = now − sum(timing.jsonl)`; drive
   refuses auto-resume past the ceiling; a step out of budget takes its terminal, never
   a fresh 5 h. (The only change that GUARANTEES 5 h.)
2. **Idempotent picture stage**: frame-only plan edits re-sign (step_03's resign
   pattern); `storyboard/ladder.json` persists redrawn grids + rungs (CAP=2 across
   resumes, mirroring takes/r2v/ladder.json); a redraw re-reads ONLY its own panels.
3. **Fixed costs cached**: QC done() hands a matching-sha8 failed report to the ladder
   without re-running; one QC + one confirm; pre-bake title/epNN.mp4 for eps 15-27 in
   one batch off the critical path.
4. **Weights to the NVMe** (zero code; ComfyUI idle; symlinks): ~45-60 min/ep of cold
   loads back. C: has 338 GB free vs ~77 GB needed.
5. **VL judge kept resident**: model_kept + cached_text in panel_eye and the master
   eye; one VL window per round (take_dq DINO + content + eye together).
6. **Honest prices + clocks**: TAKE_S=265; timing stamps for plan, panel eye, take eye,
   master eye; upload fires on QC pass.
7. **Code freeze rule**: one pinned commit per episode run; bugs fixed after the ship
   (ep14 ran across 23 commits; the skill carries the rule).

**P1 — benched, after ep15 ships:** merged turbo-LoRA UNET + encode-all/sample-all
batching (A/B first: ~10 GPU-min; targets the 115 s/take staging, ~1 h/ep); plan ladder
mechanical-first + monotone acceptance + critic cache + plan.ladder.json; ep N+1's plan
written (API, CPU) while ep N renders — a plan deferral then costs zero wall; take_dq
CPU metrics streamed beside the render (ep10 collision contained: DINO off-queue).

**Resolved in debate:** ROUNDS_CAP stays 2 (the archaeologist's cap-1 was measured
pre-batching; the router + circuit-breaker already refuse a third look at an
unprogressed fault). The storyboard keeps its ladder (no parking, per the 09-24
decision) but bounded: persisted cap, scoped re-reads, ~20 min worst case.

**Projection with P0 only:** GPU ~4.1 h + non-GPU ~0.8 h ≈ **4.9 h wall**, matching the
measured anatomy of SiS ep12/13 (3.3-3.9 h) plus the one storyboard pass they never had.

Full expert reports: session record 2026-09-30. Prior verdicts extended, not repeated:
2026-09-27_episode_speed_plan.md (items 1, 9, 10 were never built — now P0.4/P1),
2026-09-29_ep14_time_debate.md, 2026-09-30_rounds_debate.md.
