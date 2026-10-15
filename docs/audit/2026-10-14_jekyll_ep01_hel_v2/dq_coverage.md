# Jekyll HEL ep01 v2: DQ coverage, take by take — iter4 (2026-10-15, the girl fix)

Master: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/cut/master_iter4.mp4`
(RTX VSR 4x, 3072x3072, 147.33 s, sha8 **8c21321b**). Preview: `cut/master_iter4_preview720.mp4` (720x720, 21.8 MB).
`master_iter3.mp4` (84c15a36, the cut before the master eye's T01 retake; preview `master_iter3_preview720.mp4`),
`master_iter2.mp4` (c9265e3b) and `master_iter1.mp4` (bb1c6410) are kept. Nothing uploaded; `publish/standing.json`
does not exist.

**Why iter4 and not iter3.** Step 10 cut iter3 with the girl's new takes; step 11's QC passed it and the master eye
(`judge:master_eye`) climbed its one rung -- `retake_shot` on T01 ("faces at master") -- and recut: iter4. T05, T06,
T07 and T19 are the same bytes in both; only T01 differs.

QC on 8c21321b: **PASS** — -14.1 LUFS / -1.8 dBTP, cuts 22/22, segments 23/23, lines heard **21/21**, longest gap
5.43 s (wall 6.0), takes 23/23 pass, title card present. Master eye: **flagged** (terminal after its one retake) --
faces at master, story at master, content at shot_16 (lettering; shipped so in iter2 too), content at shot_22,
take identity T19 DRIFT 0.63 (advisory).

## The girl (owner 2026-10-15: "the girl is not accurate in some shots")

| | iter2 | iter4 |
|---|---|---|
| sheet | black lace bonnet, blonde bangs, hollow solid-black eyes, black pinafore (`superseded/sheet_2026-10-14_hellsing_v2_lace.png`) | one base sheet redrawn on the HEL drawer (seed 505, 16 candidates over 3 tag rounds): small soft grey woollen bonnet, fair plaits, blue eyes with irises, plain grey pinafore over a dark-red long-sleeved blouse, black boots |
| words | "small knitted woollen bonnet ... plain grey pinafore" (refs.json, looks.json, look.json, dossier, heads.json) | the same five files say the drawn sheet |
| SHEET-ROW (new, refs/04) | refuses 3/3: lace for knitted, black for grey, hollow eyes | passes; LOOK verdict signed `judge:look@1` (pack ef9cac00 + the restore row) |
| T05 (medium, she runs in) | grey knitted bonnet, grey pinafore, red sleeves -- the words | grey bonnet, plaits, grey pinafore, red sleeves -- the sheet; VLM list 3/3 frames match |
| T06 (full, the trample) | a white-grey heap; the panel drew her TWICE (fallen and running) | one girl (the `twin` reprose + seed bump 1 on the grid), grey bonnet and dress, face down, smaller than the owner wanted; VLM 2/3 frames grey bonnet (1 white), dress grey |
| T07 (full, Enfield hauls Hyde back) | beige bonnet, grey-brown dress | grey bonnet, grey dress, red sleeves at the cuffs, fair plaits; VLM 3/3 frames grey bonnet + dress |
| take prompt | "<Picture 2> defines this **woman** alone" | "... this **girl** alone" (`age_of` reads "a girl of about nine") |

Strips: `girl/girl_strip_iter3.jpg` (her sheet_front beside six frames of T05, T06, T07 -- iter4 holds the same takes),
`girl/girl_strip_before_iter2.jpg` (iter2's takes beside the new sheet), `girl/girl_zoom_T06_T07.jpg`,
`girl/T06_push_shuffle.jpg` (the push that framed her large and walked Hyde on the spot). Colour list:
`girl/girl_identity.json`. The take identity row reads "0 cast on screen" on all three: facenet finds no face on a
small cel child, so the VLM list stands in for it.

**T06 is the compromise.** The crane froze twice (83 % static, G-STILL had named its held high angle); the ladder's
move_type push toward the kerb framed her large and clear -- red sleeves, plaits, screaming -- but both push renders
failed G-GAIT (Hyde 4.0 steps/s at 0.041 / 0.04 heights a step, wall 0.045; by eye ~10 px of ground in two
seconds). `take_dq --attempts` kept the crane render that passed 95; the plan's motion was restored to the crane.

**T19 was re-opened, not by the girl.** iter2's T19 (87.6) was destroyed by the attempt-swap fault after iter2
shipped; the take left froze (83 %) and G-DEAD refused iter3's first assembly. Locked, push, follow and pull-back all
froze (83-89 %); plan.py's own "pushes in a hand's breadth toward Mr. Enfield's face, across the whole shot" passed
on both seeds (95, 100).

## The clock (Seattle time)

| part | wall | machine clock |
|---|---|---|
| v2 run + finishing pass (iter1, iter2), as before | | **5.62 h** |
| girl fix, iter2 -> iter4 (2026-10-15, 8:19 am - 12:25 pm) | 4 h 06 min | counted whole, as wall: **4.1 h** |
| **episode total** | | **~9.7 h, 3.7 h past the 6 h budget (owner-ordered)** |

Breakdown of the girl pass: sheet candidates 16 draws ~4 min GPU; SHEET-ROW build, tests and three real-reader
replays (~25 min of VLM reads); two LOOK step-04 ladders that redrew the pick before their faults were found and
killed (~15 min, both reverted); grids 3 + 4 seed bumps + 1 (~6 min); step 08 (~25 min, content read of all
panels); renders: T05-T07 x3, early round 2, a step-09 re-render of T06/T07 from a mispaired attempt graph (2),
T19 x5, T06 x3, the master eye's T01 (1): 16 takes ~38 min; take DQ ran on the CPU lane beside the renders in step
09, by hand `--cpu-only` after each manual retake; step 10 twice (G-DEAD refused the first) ~8 min; step 11 QC +
master eye + T01 retake + recut + QC ~35 min. The GPU sat idle while I read strips, diagnosed T19 and T06, and wrote
the fixes -- this pass was not run under the scheduler's two lanes end to end.

## Takes (iter4)

| take | verdict | attempts | hard rows ran / failed | frozen-whole | gait | identity | content | unmeasured rows |
|---|---|---|---|---|---|---|---|---|
| T00 | PASS 95.0 | 1 | 9 / 0 | PASS 1% static, run 0.04s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T01 | PASS 100.0 | 5 | 10 / 0 | PASS 10% static, run 0.04s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | pass-through, last-vs-panel, gait |
| T02 | PASS 73.9 | 2 | 10 / 0 | PASS 80% static, run 1.21s | n/m (n/a by the plan) | PASS 1 cast on screen | PASS | held, pass-through, last-vs-panel, gait |
| T03 | PASS 100.0 | 1 | 9 / 0 | PASS 0% static, run 0.0s | PASS 4.0 steps/s, 0.122 heights a step over 0.48 heig | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag |
| T04 | PASS 72.5 | 1 | 9 / 0 | PASS 0% static, run 0.0s | PASS 3.9 steps/s, 0.050 heights a step over 0.20 heig | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag |
| T05 | PASS 90.0 | 1 | 9 / 0 | PASS 7% static, run 0.04s | PASS 3.0 steps/s, 0.114 heights a step over 0.34 heig | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag |
| T06 | PASS 95.0 | 7 | 9 / 0 | PASS 34% static, run 0.75s | PASS 4.0 steps/s, 0.059 heights a step over 0.23 heig | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag |
| T07 | PASS 100.0 | 1 | 9 / 0 | PASS 3% static, run 0.04s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T08 | PASS 100.0 | 1 | 9 / 0 | PASS 31% static, run 0.67s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T09 | PASS 50.0 | 1 | 9 / 0 | PASS 9% static, run 0.08s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T10 | PASS 14.7 | 2 | 9 / 0 | PASS 33% static, run 0.96s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T11 | PASS 85.0 | 1 | 9 / 0 | PASS 0% static, run 0.04s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T12 | PASS 100.0 | 1 | 9 / 0 | PASS 0% static, run 0.0s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T13 | PASS 100.0 | 4 | 9 / 0 | PASS 10% static, run 0.67s | n/m (n/a by the plan) | PASS 1 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T14 | PASS 52.2 | 4 | 10 / 0 | PASS 89% static, run 1.58s | n/m (n/a by the plan) | PASS 1 cast on screen | PASS | pass-through, last-vs-panel, gait |
| T15 | PASS 83.1 | 1 | 9 / 0 | PASS 59% static, run 0.08s | n/m (not measured (unmeasured: feet in frame ) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T16 | PASS 90.0 | 4 | 9 / 0 | PASS 8% static, run 0.04s | n/m (not measured (unmeasured: feet in frame ) | PASS 0 cast on screen | FAIL text or lettering in the picture | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T17 | PASS 55.0 | 1 | 10 / 0 | PASS 0% static, run 0.0s | n/m (n/a by the plan) | PASS 1 cast on screen | PASS | held, pass-through, last-vs-panel, gait |
| T18 | PASS 59.0 | 2 | 9 / 0 | PASS 55% static, run 1.46s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T19 | PASS 100.0 | 1 | 9 / 0 | PASS 31% static, run 1.38s | n/m (n/a by the plan) | PASS advisory: DRIFT richard_enfield: first vs last f | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T20 | PASS 70.0 | 1 | 9 / 0 | PASS 3% static, run 0.04s | n/m (n/a by the plan) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T21 | PASS 100.0 | 1 | 9 / 0 | PASS 0% static, run 0.0s | n/m (n/a by the plan) | PASS 1 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |
| T22 | PASS 95.0 | 5 | 9 / 0 | PASS 45% static, run 0.71s | n/m (not measured (unmeasured: no step rhythm) | PASS 0 cast on screen | PASS | lip-sync, held, pass-through, last-vs-panel, lag, gait |

| shot | setup | size | present (setup cast) | faces | extras | enters | grid sheets | take sheets | panel people | take people |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | door_day | wide | L,E | L,E | 0 | - | door_day_1x1_a: L,E | L,E | 2 | 2 |
| 1 | door_day | medium_close | L,E | E | 0 | - | door_day_1x1_s01: E | E | 1 | 1 |
| 2 | door_day | medium_close | L,E | L,E | 0 | - | door_day_1x1_s02: L,E | L,E | 1 | 2 |
| 3 | night_cross_street | full | E,H,G | E,H | 0 | - | night_cross_street_1x1_a: E,H | E,H | 2 | 1 |
| 4 | night_cross_street | medium | E,H,G | H | 0 | - | night_cross_street_1x1_b: H | H | 1 | 1 |
| 5 | night_cross_street | medium | E,H,G | G | 0 | G | night_cross_street_1x1_c: G | G | 1 | 1 |
| 6 | night_cross_street | full | E,H,G | H,G,E | 0 | - | night_cross_street_1x1_d: H | H,G,E | 3 | 3 |
| 7 | night_cross_street | full | E,H,G | E,H,G | 0 | - | night_cross_street_1x1_e: E | E,H,G | 3 | 3 |
| 8 | night_door | medium | E,H | H,E | 0 | - | night_door_1x1_a: H,E | H,E | 2 | 2 |
| 9 | night_door | insert | E,H | H | 0 | - | night_door_1x1_b: H | H | 1 | 1 |
| 10 | night_door | insert | E,H | H,E | 0 | - | night_door_1x1_c: H,E | H,E | 2 | 2 |
| 11 | pavement_day | medium | L,E | E,L | 0 | - | pavement_day_2x2_a: E,L | E,L | 2 | 2 |
| 12 | pavement_day | medium | L,E | L,E | 0 | - | pavement_day_2x2_a: E,L | L,E | 2 | 2 |
| 13 | sunday_street | medium | L,E | L,E | 0 | - | sunday_street_2x2_a: L,E | L,E | 2 | 2 |
| 14 | sunday_street | medium_close | L,E | E,L | 0 | - | sunday_street_2x2_a: L,E | E,L | 2 | 2 |
| 15 | sunday_street | medium | L,E | L,E | 0 | - | sunday_street_2x2_a: L,E | L,E | 2 | 2 |
| 16 | sunday_street | insert | L,E | L | 0 | - | sunday_street_2x2_a: L,E | L | 1 | 1 |
| 17 | sunday_street | medium_close | L,E | L | 0 | - | sunday_street_1x1_b: L | L | 1 | 1 |
| 18 | pavement_day | medium | L,E | E,L | 0 | - | pavement_day_2x2_a: E,L | E,L | 2 | 2 |
| 19 | pavement_day | medium_close | L,E | E,L | 0 | - | pavement_day_2x2_a: E,L | E,L | 2 | 2 |
| 20 | pavement_day | insert | L,E | L,E | 0 | - | pavement_day_1x1_b: L,E | L,E | 2 | 2 |
| 21 | pavement_day | medium_close | L,E | L | 0 | - | pavement_day_1x1_c: L | L | 1 | 1 |
| 22 | door_day | wide | L,E | L,E | 1 | - | door_day_1x1_b: L | L,E | 3 | 3 |


---

# (history) Jekyll HEL ep01 v2: DQ coverage, take by take — FINAL (2026-10-15)

Master: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/cut/master_iter2.mp4`
(RTX VSR 4x, 3072x3072, 147.33 s, sha8 **c9265e3b**). Preview: `cut/master_iter2_preview720.mp4` (720x720, 22.6 MB).
`master_iter1.mp4` (bb1c6410) is kept. Nothing uploaded; `publish/standing.json` does not exist.

QC on c9265e3b: **PASS** — -14.1 LUFS / -1.8 dBTP, cuts 22/22, segments 23/23, lines heard **21/21**, longest gap
5.43 s (wall 6.0), takes 23/23 pass, title card present. Master eye: see "Master eye" below.

Tables were read off disk with `audit_tables.py` (this folder) from `takes/r2v/T??.dq.json` and `T??.content.json`.

## The clock (Seattle time)

| part | wall | machine clock |
|---|---|---|
| v2 run, plan through master_iter1 (2026-10-14, 1:32 pm - 6:05 pm) | 4 h 33 min | 12,099 s = **3.36 h** (`autopilot/status.json` `clock_spent_s`) |
| finishing pass, master_iter1 -> master_iter2 + QC + master eye (2026-10-15, 1:41:35 am - 3:57:14 am) | 2 h 15 min | counted whole, as wall: **2.26 h** |
| **episode total** | | **5.62 h (20,238 s), under the 6 h budget** |

Finishing-pass breakdown (my logs, `timing.jsonl` rows for the step scripts):

| step | minutes | notes |
|---|---|---|
| plan cures + timeline | 1 | shorten T14 (ladder's `shorten`), reprose shots 1/4/5, replan_cell shot 19, all through `write_plan` / `write_cured` |
| grids (Qwen-Image) | 10.2 | door_day s01 x2, s02, night_cross_street b, c |
| step 08 panels + gates + panel eye | 15.6 | two passes (content 1.8 + eye 7.1 + a first pass refused by a stale boundary flag) |
| takes (H3 renders) | 38.2 | rounds: 9 + 4 + 3 + 3 takes, plus 2 re-rendered by step 11's step-09 dependency (see faults) |
| take DQ | ~12 not overlapped | the rest ran on the CPU lane beside the renders (`--cpu-only`) |
| take content (VLM) | ~9 | |
| edit: assemble + RTX 4x | 6.4 | 2.0 net + 4.4 RTX |
| QC | 9.9 | one pass refused on two unjudged takes (T02/T16 content not yet read), then PASS |
| master eye | 2.3 | read once, no ladder (no clock left for a retake round) |
| reading, deciding, code fixes | the rest | two test-first fixes landed (below) |

**GPU idle.** ComfyUI history over the whole finishing pass, 1:41-3:57 am: 62.1 min busy, **73.0 min idle** in a
135.1 min window (to 3:20 am: 51.1 busy, 47.6 idle). Of the idle: 5.4 min before the first grid (reading), 4.4 min the RTX pass (GPU busy outside ComfyUI), and the
rest the gaps where a decision waited on a check (round 3 content read 3.2 min, round 4 setup 3.5 min, T19/T22 loss
4.5 min, round 6 checks 6.7 min, assemble/QC 11 + 9.4 min with the GPU on RTX and CPU QC, and the last 14 min of
audit writing after the master eye). The v2 run's step 09 was
serial (the two-lane scheduler, ffe11d6, landed after it): `take_schedule_replay.py` projects **24.4 min** of GPU idle
in it, 5.0 min had it run overlapped.

## Coverage by check (final state)

| check | ran on | result |
|---|---|---|
| plan battery | plan after the cures | clean before the cures; the cures are frame-lead phrases and one timing halving, both written through the contract |
| panel DQ + content | 23/23, re-read after every redraw | DQ fails 4, 5 ("missing": 0 faces detected); content fails 2 ("1 figure for 2 named") — see allowed |
| panel eye | 2 reads | keep_best, flagged (faults listed under allowed) |
| take DQ (all HARD rows) | 23/23 + every retake, `--attempts` | **23/23 PASS**, 0 hard rows failed on the takes in the master |
| frozen-whole (house rule) | 23/23 | PASS on all |
| G-GAIT | measured T03 0.122, T04 0.050, T06 0.059 heights a step | PASS; T05/T15/T16 feet out of frame, T22 no step rhythm (unmeasured) |
| lip-sync + G-TAIL | 4/4 dialogue | **all PASS**: T01 WER 0.15, T02 0.00, T14 **0.11** (was 0.56), T17; T14 tail -48.4 dB (was -22.7 with words) |
| identity (sheets in, advisory) | 22/23 | DRIFT only on T19 (Enfield 0.59) — allowed below |
| take content (VLM) | 23/23 | PASS 21/23; FAIL T01, T16 (lettering) — allowed below; **T10 now PASS** (cheque) |
| G-DEAD | master | nothing dead |
| QC | master c9265e3b | **PASS**, lines 21/21 |
| master eye | master c9265e3b | **flag** (below) |

## The owner's six flags

| # | flag | what was done | final |
|---|---|---|---|
| 1 | T14 lip-sync WER 0.56 + G-TAIL on 4 renders | the SHORTER take: coda 1.5 -> 0.75 s by the ladder's own `shorten` (141 -> 124 frames). It had never run: the ladder compared the timeline to the FILE length and read "restore" every time (fixed, ce2ddea) | **CLEARED**: WER 0.11, tail pass -48.4 dB, mux lag -0.010 s, content clean |
| 2 | shot 1 red door against shot 0's blistered brown | door_day s01 regridded twice on the room anchor (the door master's view); then the `people` cure (the lawyer had been drawn behind Enfield) | **CLEARED**: the door is the blistered brown of shot 0 in panel and take. T01 picked up a new fault — see allowed |
| 3a | T14, T16 shop lettering | T14 cleared with its new take. T16 reseeded twice more (4 renders): H3 writes "BUDLE..." on the gold shop fascia at the right edge from 2 s on, every seed; the panel itself is clean | T14 **CLEARED**; T16 **ALLOWED, flagged** (below) |
| 3b | T10 cheque writing | recorded as allowed IN CODE: a cheque is print by what it is (`panel_content.PRINTED`, 811cabb, test-first) | **CLEARED**: T10 content PASS |
| 4 | Enfield identity drift T01 0.74, T02 0.72, T19 0.52 | T01 regridded + retaken; T02 retaken (seed); T19 retaken 3 more times incl. the ladder's replan_cell (locked) | T01 **CLEARED** (no drift), T02 **CLEARED** (1 cast, no drift); T19 **ALLOWED** (below) |
| 5 | panel eye keep_best on 2, 4, 5 | 4 and 5 regridded with the ladder's reprose (`framing`, `people`); 2 regridded on a new seed | shot 5's extra figure **CLEARED** (Enfield's shoulder gone); 2/4/5 remaining rows **ALLOWED** (below) |
| 6 | master eye "story": the turn reads on 6, not 13 | cheap fix inside the takes: T13 retaken; the new take shows the lawyer's hand on Enfield's arm turning him (frames 0.5 / 3 / 6 s). No re-plan: the plan's turn IS shot 13 (the lawyer's choice), shot 6 is the inciting act | **STANDS**: the eye still reads a pre-grip frame of shot 13 (below) |

## Allowed, with the reason (each a measured repeat, not a skipped check)

| where | row | reason |
|---|---|---|
| T16 | content: lettering | 4 seeds, the same invented fascia lettering ("BUDLE...") at the right edge; the panel (sunday_street 2x2) is clean, so the take invents it. The cure is the board's (a 2x2 redraw of sunday_street with "Every surface ... plain, wordless paint" leading shot 16), which re-renders T13-T16 -- T13 and T14 just passed; no clock for it. |
| T01 | content: lettering | the regridded T01 passes every DQ row (98.8, WER 0.15, tail pass, door correct) but the reader sees a faint shop fascia at the left from ~4 s. 3 renders. A second cane appears at 6.3 s, past the cut (the shot holds 5.7 s). |
| T19 | identity DRIFT Enfield 0.59 (advisory) | 7 renders: every moving take drifts 0.52-0.75 because the plan's verb ("lowers his eyes and shakes his head") puts his face under the brim; the one locked replan froze (HARD frozen-whole). The take in the master passes every HARD row (87.6). The cure is the plan's verb, a re-plan. |
| panel 2 | content: 1 figure for 2 named | over-the-shoulder 1x1: 5 seeds, Enfield's shoulder never drawn (twice the lawyer in Enfield's hat). The TAKE stages both sheets and shows both men (content PASS, identity PASS). The fix is the plan's: a two-shot, or the OTS in a 2x2 (shots 14 and 19 drew their shoulders that way). |
| panels 4, 5 | DQ: "missing" (0 faces) + framing wide vs medium | the figure is there (Hyde walking, the girl running, full figure with the feet in frame -- what G-GAIT needs and what plan.py's own notes ask for); the face detector reads 0 faces at that size. Framing is in `REDRAW_CANNOT_CURE` (measured ep13). The takes pass content and gait. |
| T22 | master content "1 figure for 2" at the end (iter1) | the book's button: the two men walk on to the RIGHT and out; the last seconds are the door and the tramp. The take in the master is the G-GAIT-cured render (95). |

## Faults met and fixed this pass (test-first, own commits)

| commit | fault |
|---|---|
| `ce2ddea` | the shorter-take rung read the FILE length (frames_for(placed + HANDLE)) against the timeline, so every shorten was a "restore": T14's mux-lag cure was four same-length reseeds |
| `811cabb` | a cheque is print: the content gate called the book's own cheque "lettering" |

**Found, not fixed (in LESSONS):** `take_dq --attempts` swaps an older attempt into `T<NN>.mp4` with its old mtime;
`take_currency` then reads it as an unfinished render and the next `takes_r2v` (or a step 11 that re-runs step 09)
overwrites it without archiving and with `tries` reset. It destroyed T22's cured render once (re-rendered with
`--retake`, seed + 101, which reproduced it: 95) and T19's 87.6 twice; the T19 in master_iter2 is that render, but
the file on disk under `takes/r2v/T19.mp4` is now a later, failed locked render (and T01.mp4 a later 100-score
render). The master's QC (c9265e3b) was measured against the takes as they stood when it was cut.

## Master eye on c9265e3b (`review/eye_c9265e3b.json`): flag

| fault | was on iter1 | now | why it stands |
|---|---|---|---|
| story (turn shot 13: grip/swing/turn not listed) | yes | **stands** | the new T13 shows the grip (take frames 0.5/3/6 s), but the eye reads ONE frame of shot 13 in the master and listed "standing, talking / facing". The cut holds the take's opening, before the hand lands. A timing-word fix in the plan (the grip at the first frame) is a plan edit; not taken. |
| content shot 16 (lettering) | no (was 14) | stands | T16, 4 seeds, allowed above; shot 14's lettering is gone |
| content shot 22 (1 figure for 2) | yes | stands | the book's button: the men walk out of frame; allowed above |
| content shot 10 (cheque) | yes | **cleared** | 811cabb |
| take_identity T01, T02 | yes | **cleared** | |
| take_identity T19 | yes | stands (advisory) | 7 renders, allowed above. NB the eye read the T19.dq.json now on disk (a later render, 0.73), not the take in the cut (0.59): the attempt-swap fault |
| faces: shot 1 face at 0.11 of the frame (wall 0.12) | no | **new** | the regridded panel draws Enfield at mid-thigh so the door shows behind him (flag 2); the face fell 0.01 under the medium-close wall |
| identity: the girl drifts from her own median (0.595, 2 of 3 reads) | no | **new** | T05 re-rendered on the regridded panel; she runs toward camera and turns (pose) |

No clock is left for another round: render + checks + assemble/RTX + QC + eye is ~35 min against 23 min left under 6 h.
The next round, in order: T13 cut/timing so the grip is on screen at the eye's frame, T16 by a sunday_street board
redraw with the wordless-paint lead, shot 1 tighter (or the faces wall read against a mid-thigh medium close), T05
reseed, and the plan fixes above (shot 2 as a two-shot, shot 19's verb, shot 22's `exits`).
