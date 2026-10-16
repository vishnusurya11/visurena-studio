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
