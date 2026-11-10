# Jekyll ep07 retro: tracker

Owner, 2026-11-10: "do a retro on episode 7 and please fix the skills and framework".
Scope chosen: medium (lead + 4 Sonnet experts + 1 Opus skeptic). Covers shipped flaws, time and loops, publish blockers, and the owner's own catches (none typed yet). GPU proofs are built now and run after the PCIe fix.

## Jobs
- [x] A loops/autopilot (Sonnet): out/A_loops.md -- clock_loop outranks named parks; "told" proves no delivery; brain redo 09 a no-op x3; plan unchecked at preflight; F1-F5
- [x] B people-gate false refusals (Sonnet): out/B_people.md -- G-WHO 0/7 precision; shot_07 block = one master frame, no confirm at ship_block; fix master_blocks needs 2 frames
- [x] C shipped motion flaws (Sonnet): out/C_motion.md -- gait 4.0 steps/s is an alias (8 Hz render pulse read at 12 fps); rolls were seed rerolls; F1-F6
- [x] D time (Sonnet): out/D_time.md -- take_dq 125 of 180 min hidden under renders; refusal loop runs 13-17 = 84 min; projection 7.08 h -> ~5.3 h
- [x] E skeptic (Opus) over A-D: out/E_skeptic.md -- S1-S11 specs, rejections, GPU proof list
- [x] lead: S1-S11 built test-first; skill (LESSONS 17-18, GATES, OPERATOR, archive); commits 6e04708b + 4f0449b5; FINAL.md

## Log (Seattle time)
- 11-10 ~11:00: evidence gathered (EVIDENCE.md); experts launched.
- 11-10 afternoon: experts back (A, B, C, D), skeptic E; S1-S8 committed 6e04708b, S9-S11 4f0449b5; 3926 affected tests pass.
- OPEN: GPU proofs (FINAL.md) after the PCIe/BIOS fix.
