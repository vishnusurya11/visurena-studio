# Jekyll ep01 iter5 pass -- the three audits repeated on the new master

Final master: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/cut/master_iter6.mp4`
(sha8 d2e9ffb4, 147.33 s, 3072 RTX 4x). `master_iter5.mp4` (fd550cb6) is the first full cut of this pass;
the master eye's own rung retook T00 and the pipeline recut it as iter6 (same everything else). Both kept.
Previews: `cut/master_iter5_preview720.mp4` (22.5 MB), `cut/master_iter6_preview720.mp4` (22.5 MB, 720x720).

## 1. Staged references per take, by hash (01_staged_refs.md repeated)

`verify_tools.py refs` -> `staged_refs_iter5.json`: **inputs: 23 of 23 takes current** (every kept take's
graph stages exactly the sheet_front and panel bytes its card stages now; no `superseded/` hash, no
foreign graph). QC's own row agrees: `inputs: all 23 takes current` (qc_r2v.json, sha8 d2e9ffb4).
Staged sheet ids: Utterson `sheet_front_02e2c64b`, Enfield `ba2d1ee1`, Hyde `fb7a1347`, the girl `45becc16`
(the new girl sheet; the lace sheet b54219a4 is gone from every graph). T06 stages Hyde, girl, Enfield +
its current panel. Every speaker first, panel last, no empty slot.
Grids: every manifest now records `load_images` and `words_only`; chained grids stage the room, not the
plate, so shots 6/7 stage two of three people and shot 22 both men.

## 2. The prompt lint (02_prompts.md repeated)

- `scripts/episode/prompt_lint.py <book> 1`: **PROMPT LINT: clean** (23 take prompts, the plan, the files:
  every graph's prompt is prompts.json's and no graph is older than its take). It counted 275 faults on
  the iter4 prompts.
- `grids.py <book> 1 --prompts`: **17 grids, 0 with lint faults**.
- `plan_check.py`: **VERDICT: clean** (G-TAKELINT clean on the panel band).
- Classes checked by eye on the built prompts: no "tHE", no "The camera is On", no cure lead, every staged
  Subject cited, the epithets bound ("<Subject 1> on the door steps"), no second description, no
  "lank," speaker, no "as the line ends ... as he speaks", no "the lean continues", no "with the now in
  frame", no lens, the unlettered sentence in every summary, "toward the lawyer" aimed at the frame edge.

## 3. Visual QA by eye (03_visual_qa.md repeated) -- `scene_*.jpg` here

| scene | what the frames show | standing |
|---|---|---|
| door_day (T00-T02, T22) | ONE door: the grey gable block, the red-black blistered door above two steps, the kerb lamp; Utterson grey-haired in the long black overcoat with white buttons; Enfield mid-grey coat, cream waistcoat, black gloves, cane; the tramp in the recess on T22 | T02 lost the over-the-shoulder shoulder (a known 1x1 limit); its face reads Utterson now |
| night_cross_street (T03-T07) | the girl once in T06 (fallen) with Hyde striding over her; she reads as a child (half his height) in T05-T07; Hyde adult in build, a head shorter than Enfield in T07 | T06 eye: "4 figures for 3" on the high wide's last frames (tiny figures) -- flagged |
| night_door (T08-T10) | the SAME door at night (the one-edit night state); Hyde in black; T10 Enfield's black glove takes a blank cheque | T09 is the man going in at the door (the words now follow the drawn picture) |
| pavement_day (T11, T12, T18-T21) | the same door, grey overcast in every take (no sunny T12); Enfield gloved and caned; Utterson's white buttons | -- |
| sunday_street (T13-T17) | grey sky, oxblood and bone shutters; Utterson grey | T15 content reads lettering on a shop sign (flagged); T13 clones advisory (facenet 0.751) |

SCENE PALETTE: 1 advisory (T16 saturation, a hands insert); the pavement T12 sunny-sky fault is gone.
SHEET-ROW on the rewritten rows (`sheet_row_iter5.jsonl`): Utterson, Enfield, Hyde, girl, Lanyon, the new
constable all pass (hat-kind advisories only).

## 4. Gates on the final master

- QC (master_iter6, d2e9ffb4): **PASS** -- 147.33 s, -14.1 LUFS, -1.8 dBTP, cuts 0/22 missing, lines heard
  21/21, longest gap 5.43 s, takes 23/23 pass, inputs all 23 current.
- Master eye: **flagged** after one retake (T00): board, story, content at shots 15/19/22, identity
  advisories (STRANGER on small or turned faces T02, T07, T16). No owner waiver written.
- Take eye: keep_best flagged at the round cap (T06 figure count, T13 clones, T15 lettering).
- Panel eye: keep_best flagged (shot 2 missing the shoulder, shot 4/5 framing wider than asked).

## 5. Faults still standing, with their reason

1. **T02 over-the-shoulder draws no shoulder** -- Qwen 1x1 grids drop the shoulder on every seed (LESSONS
   2026-10-15); a plan rewrite to a two-shot is the cure, not done (owner's dialogue shot).
2. **T15 lettering on a shop sign** -- the grid and take both carry the unlettered sentence; H3 still
   letters a sign. OCR at the panel stage is the open GATES gap.
3. **T13 clones advisory, identity STRANGER advisories** -- the take identity row is advisory by the
   2026-10-14 ruling; listed for the owner's eye.
4. **Enfield's dark eye bands** -- on his sheet; the sheet is truth.
5. **Constable sheet try 3** keeps a bell at the throat where the row says a lantern (not in ep01).

## 6. Mistakes in this pass

- `step_07_board --seed-bump=1` redraws EVERY grid, not the missing ones: a full regrid + panels + 23 takes
  (~70 min) where three grids were meant. The skill says it; I misread it.
- The first panel and take eyes refused their rungs on the reserve because the fresh clock still summed
  the iter1-4 timing rows (8220 s); fixed by keeping only this pass's rows in timing.jsonl.
- T09 took five renders: an "insert of the lock" pinned on a panel that every seed drew as the whole man.

---

# iter7 pass (2026-10-16, 00:28-02:12 Seattle) -- the master eye's last flags on master_iter6

Final master: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/cut/master_iter7.mp4`
(QC sha8 45f9fcd5, 147.33 s, 3072 RTX 4x). Preview `cut/master_iter7_preview720.mp4` (22.4 MB, 720x720).
master_iter1-6 kept. Frame every 8 s: `iter7/master_iter7_every_8s.jpg` (looked at: one Enfield in the
spike, the two-shot at the door, no sign board on the Sunday walk). Tools: `iter7/every_8s.py`,
`iter7/verify_tools.py` (refs -> `iter7/staged_refs_iter7.json`).

## What was done, through the pipeline only
- `plan.py` (iter7 block in SHOT_FIXES) -> `plan.json`; `plan_check` VERDICT clean; `takes_r2v --prompts`
  PROMPT LINT clean (23 + the plan); `grids.py --prompts` 17 grids, 0 faults; the two grids whose prompt
  changed, and only those (prompt diff against each drawn `.txt`): `door_day_1x1_s02` and
  `sunday_street_2x2_a` (old ones in `storyboard/superseded/*_iter6.*`).
- `panels.py`, step 08 (both panel gates + `judge:panel_eye`, keep_best flagged on the iter6 faults at shots
  4 and 9, unchanged pictures); the shot 2 "missing" fault is gone.
- `takes_r2v --retake` round 1: T02, T06, T13, T14, T15, T16 (T13/T14/T16 because their panels came from the
  redrawn Sunday grid -- G-TAKE-INPUTS); round 2 (`--last`): T06, T14; round 3 (`--last`): T06.
- `take_dq --attempts`, `take_content_check` (23/23 clean), step 10 (cut + RTX), step 11 (QC + master eye).

## The flags
| flag | finding | result |
|---|---|---|
| T02 OTS shoulder | plan rewrite: a locked medium-close two-shot, both faces at the thirds | CLEARED: panel draws both men; take 51.8 PASS; identity STRANGER advisory gone |
| T15 lettering | the panel itself drew a lettered board over a shop; the track revealed more fronts. Cell now "a long flat soot-black brick wall of tall closed oxblood shutters", the camera pulls back ahead of him | CLEARED: content clean on the take and the master; 60 PASS |
| T06 4 figures for 3 | the 4th was a SECOND Mr. Enfield (two top hats side by side at the LEFT on the crane's last frames) -- a duplicate, not a passer-by; extras was already 0. Cure: his run aimed "toward the fallen girl" (G-AIM) | CLEARED on the third seed (80 PASS, one Enfield to the last frame, content clean). Seeds 1-2 froze the crane (67 %, 84 %) with sliding feet |
| T13 clones | the regrid + reseed: grip and turn on screen | CLEARED (clones row gone; 90 PASS) |
| T16 identity | an insert of the hands: no face to identify | CLEARED on the master eye (advisory gone); a face row on a hands insert measures nothing |
| shot 22 last frame | the crouched figure is THE BOOK'S TRAMP: staged in the plan (`extras: 1`, frame and at_rest "a ragged tramp ... in the recess", "strikes a match"), drawn in the panel, lights the match on the panels | STANDS as intended; the "1 figure for 2 named" at 140.2 s is the two men walking out at the right as the plan's motion says |

## The master eye on 45f9fcd5: flagged, 8 faults -> 6
- **board** 10 of 19 takes off their cell (share 0.526, wall 0.5): T00, T01, T03, T04, T07-T11, T19 -- none
  retaken in this pass; no cut change moves a last frame onto its cell. Stands.
- **story** the VLM lists "talking, standing" on the turn shot (13); the grip on the arm is on screen at
  ~80 s (sheet). No cut change can make the listing read it. Stands.
- **content shot_19 / shot_22** "1 figure for 2 named": T19's planned push-in toward Enfield takes the
  lawyer's shoulder out of frame; T22's men walk off as planned. Both by the plan's own motion. Stand.
- **identity** Utterson drift from his own median (new: the two-shot T02 and the Sunday takes add angles) and
  the T07 STRANGER advisory (Hyde turned away in a wide). Advisory by the 2026-10-14 ruling.

## Gates on iter7
- QC: **PASS** -- 147.33 s, -14.1 LUFS, -1.9 dBTP, cuts 0/22 missing, lines heard 21/21, longest gap 5.43 s,
  takes 23/23 pass, **inputs: all 23 takes current** (also `staged_refs_iter7.json`: 23 of 23).
- Prompt lint clean, grid lint clean, plan_check clean, take content 23/23 clean.
- publish/standing.json absent; nothing uploaded.

## Found and fixed in this pass
- `take_dq --attempts` ranked an attempt rendered from OLDER WORDS: the iter6 T06 render (90, the duplicate
  Enfield) was swapped back over the round-1 render of the cured plan, because G-TAKE-INPUTS read only the
  staged pictures. `take_dq.reworded` now marks an attempt whose recorded prompt differs from the card's as not
  current (tests in `tests/test_take_inputs.py`).
- The Sunday grid is the setup's anchor; `anchors/sunday_street.png` was NOT re-cut by `panels.py`, so shot 17
  (grid `sunday_street_1x1_b`) stays on the iter6 room. Not redrawn (only the named grids); by eye the street
  reads the same (oxblood shutters, grey sky).
