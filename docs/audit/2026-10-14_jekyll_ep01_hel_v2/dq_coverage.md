# Jekyll HEL ep01 v2: DQ coverage, take by take (2026-10-14)

Master: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/cut/master_iter1.mp4`
(RTX VSR 4x ULTRA, 3072x3072, 148.08 s, sha8 bb1c6410). QC: **PASS**. The QC line was -14.1 LUFS / -2.0 dBTP,
cuts 22/22, lines heard 21/21, longest gap 5.43 s against the 6.0 s wall. The master eye read **flag**: story, content
on shots 10/14/22, and take_identity advisories on T01/T02/T19. v1 was set aside to
`episodes/superseded/ep01_2026-10-14_hel_v1` (master_iter1 and master_iter2 kept).

Tables: `audit_tables.py` (this folder) reads them off `takes/r2v/T??.dq.json`, `T??.content.json` and `shots.json`.

## The clock

- Machine clock: 12,099 s, which is **3.36 h** (`autopilot/status.json`, clock_spent_s). It stayed under the 5 h ceiling throughout.
- Wall time: launch 1:32 pm Seattle; master built 5:45 pm; delivered (manifest) 6:05 pm. That is **4 h 33 min**.
- What was in the gap between clock and wall:
  - two record parks (l15) before the fix;
  - two G-DEAD refusals before the fixes;
  - about 20 min of WAIT_TREE while a peer session's scheduler work held the tree;
  - the GPU idle while CPU checks ran between renders (the owner's 4:55 pm finding). The binding owner rule since is renders back to back.

**No check was cut for time.** The budget never had to refuse a measure: there is no `reserve` or `terminal: budget` row
in `learnings.jsonl`. Every take was re-measured under the code that judged it: `MEASURES` now covers `stillness.py`
and `identity_gate.py`.

## Coverage by check

| check | ran on | result | notes |
|---|---|---|---|
| plan battery (`plan_check`) | final plan | VERDICT: clean | G-PRESENT clean (was 3 appearances in v1). Advisories: G-TWICE (6), G-MOTION walk-in-wide (shots 0, 22) |
| plan critic (judge:plan) | 3 drafts | keep_best, flagged | turn read on shot 6 (the trampling), marked 13. The writer's improve rung rewrote line 0's hook and shot 7 (family framed out) |
| panel DQ + panel content | 23/23 | 21/23 clean; shot 2 (Enfield's shoulder lost), shot 5 (Enfield's foreground shoulder counted as an undeclared figure) | |
| panel eye | 3 reads | keep_best (redraw_grid_seed, reprose) | rungs ran out, not time. Faults: missing on 2 and 4, people on 5, G-FRAME framing advisories |
| take DQ (all rows) | 23/23 + every retake | see the table | 9-10 HARD rows ran per take |
| frozen-whole, **house rule** (drawn relaxations removed) | 23/23 | first pass failed T10, T13, T18, T19 | cured by move type: T13 (5 %), T18 (55 %), T19 (26 %); T10 is now 33 % static |
| **G-GAIT** | 23/23 asked; measured where the plan walks a subject with feet in frame | T03 PASS (4.0 steps/s, **0.122** heights a step; v1 was 0.027), T04 PASS (0.074), T06 PASS (0.059), T22 FAIL then cured (0.003 shuffle -> re-render, now "no step rhythm") | unmeasured: T05 (depth: the girl runs toward the corner), T15/T16 (feet out of frame), T22 retake (no rhythm) |
| **identity (sheets in, advisory)** | 22/23 measured (T05: not measured) | DRIFT advisories on Enfield in T01 (0.74), T02 (0.72) and T19 (0.52); 0 STRANGER | read by the master eye as `take_identity` (low) |
| take content (VLM) | 23/23 + retakes | FAIL T10, T14, T16 "text or lettering" | T10's cheque carries writing (the book's own prop). T14/T16 show shop lettering behind |
| lip-sync / G-TAIL | 4/4 dialogue | T14 FAIL on 4 renders | WER 0.56 and tail words "of the name of Hyde" at -22 dB on every seed: the render says the line late, a voice fault and not the picture |
| take eye (EYE_TAKES) | 2 batched rounds + 1 retake by the ladder's entry point | keep_best, flagged | see "cured / kept" below |
| G-DEAD | master | cut [] (nothing dead) | refused twice first (below) |
| QC | master | PASS | ran in full |
| master eye | master | flag | story, 3 content, 3 identity advisories |

## Each take: cured or kept

| take | first pass | cure | final |
|---|---|---|---|
| T10 | frozen-whole 81 % HARD | move type (tilt -> track) | 33 % PASS. The content fault (the cheque's lettering) was stilled at 6.75 s, then retired (G-DEAD); the take ships, **flagged content** |
| T13 | frozen-whole 69 % | move type | 5 % PASS |
| T14 | lip-sync WER 0.56 + G-TAIL + content | 3 reseeds (2 by the ladder, 1 by its entry point at the coordinator's order) | **keep_best**: the same fault on 4 renders. G-DEAD now reads it as a voice fault, not dead picture |
| T16 | content (lettering) | reseed | content still FAIL. A 3.9 s still was retired; the take ships, **flagged** |
| T18 | frozen-whole 96 % | move type | 55 % PASS |
| T19 | frozen-whole 82 % | move type x2 (the first cure's aim was garbled) | 26 % PASS |
| T22 | G-GAIT shuffle 0.003 | move type | PASS (unmeasured: no step rhythm) |
| T01/T02 | identity DRIFT (advisory) | none (advisory) | flagged by the master eye |

## Faults met and fixed this run (test-first, each in its own commit)

| commit | fault |
|---|---|
| `adf0dc4` | the owner's four rulings: drawn-look stillness relaxations dropped; identity row measured with sheets (advisory); Hyde clean-shaven; G-GAIT in GATES/LESSONS |
| `e8a0806` | the record step gave a refused line 2 tries a run while keep_best needs 8, so l15 parked the episode twice |
| `fcf5b21` | the move-type cure's aim was garbled ("tracks beside the lawyer across to the door's"). A frozen follow went to a lock; a frozen take never got its second move type; the terminal stilled panels G-DEAD refuses |
| `fb20016` | the ladder's live stills kept a still longer than 2.5 s |
| `ff82e6c` | assemble read stills.json itself and cut the 6.75 s still anyway |
| `f64d865` | G-DEAD counted a voice-only failure (T14) as dead picture, so the master could never be built |
