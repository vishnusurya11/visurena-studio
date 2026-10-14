# Jekyll ep01 (HEL) -- cast continuity: who is in each shot, and who "magically appears"

Owner fault, 2026-10-14: *"the first shot doesn't have the actual characters in the
scene, so in the second shot the character magically appears. Double-check the
references. Every shot needs to have all characters involved in the references."*

Episode: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01`
(plan.json, storyboard/grids/*.json|txt, storyboard/h3/shot_NN.png, takes/r2v/TNN.graph.json),
master `cut/master_iter1.mp4`.

## Evidence (all in this folder)

| file | what it shows |
|---|---|
| `takes_00.jpg`, `takes_06.jpg`, `takes_12.jpg`, `takes_18.jpg` | per shot: the storyboard panel, then the take's first, middle and last frame (built from `takes/r2v/TNN.mp4`) |
| `sheets_vs_shot00.jpg` | the four cast sheets (lawyer, Enfield, Hyde, the girl) beside the two men of panel 0, enlarged |
| `panels_v1.jpg`, `frames_every_7s.jpg` | every panel; the master every 7.5 s |
| `replay_present.py` | the G-PRESENT replay over every WotW, Scarlet and Jekyll plan on disk |

Which sheets each step staged was read off the files: grid prompts (`<imageN> is a
reference sheet of one person`) and the take graphs' `LoadImage` names, mapped to
`refs/characters/<who>/sheet_front.png` by the content hash `comfy.staged_name` gives them.

## Scenes (a scene = consecutive shots on one setup)

| scene | shots | setup `cast` | present by the book |
|---|---|---|---|
| A door, Sunday | 0-2 | lawyer, Enfield | lawyer, Enfield (walking together) |
| B crossroads, 3 a.m. | 3-6 | Hyde, girl | Hyde, girl, **and Enfield** -- the narrating witness, who "took to my heels, collared my gentleman" at the corner, where the family gathered |
| C door, 4 a.m. | 7-10 | Hyde, Enfield, girl | Hyde, Enfield, the girl's family, the doctor |
| D court pavement | 11-12 | lawyer, Enfield | lawyer, Enfield |
| E bright street | 13-17 | lawyer, Enfield | lawyer, Enfield |
| F court pavement | 18-21 | lawyer, Enfield | lawyer, Enfield |
| G door (button) | 22 | lawyer, Enfield | (the plan's invention: the lawyer alone, a tramp) |

## Per shot

L = the lawyer (`gabriel_john_utterson`), E = Enfield, H = Hyde, G = the girl.
"words" = drawn from the row's wardrobe words, not from the sheet.

| shot | size | plan `faces` | grid sheets | take sheets | panel shows | take first -> last frame | fault |
|---|---|---|---|---|---|---|---|
| 0 | wide | L, E | **none** (`wide_only`) | L, E + panel | two specks at left: a **blond man in black** and a **man in a brown greatcoat** -- neither sheet (`sheets_vs_shot00.jpg`) | the same two strangers; a third man by the middle, a woman by the end | **the owner's fault**: the scene's people are not its people |
| 1 | medium_close | E | E + room (panel 0) | E | Enfield **from his sheet** (grey frock coat, tan waistcoat), standing before the door where panel 0 had nobody | Enfield; ends pointing his cane | **E appears**: first sight of the real Enfield |
| 2 | medium_close (OTS) | L, E | L, E + room | L, E | the lawyer from his sheet; Enfield's shoulder at the left edge | the shoulder is gone by mid-take; **a top-hatted man and a woman appear** at right by the end (extras 0) | L's real face first seen here; unplanned walk-ons |
| 3 | wide | H | H, G (2x2 grid 3-6) | H | Hyde, small at the far corner | Hyde; the street empty by the end | -- |
| 4 | medium | H | (same grid) | H | Hyde (sheet) | Hyde | -- |
| 5 | medium | G | (same grid) | G | the girl (sheet's red top, words' grey pinafore) | the girl | **G-PRESENT**: G first seen after the wide of shot 3, no entrance marked |
| 6 | full | H, G | (same grid) | H, G | Hyde and the girl at the corner | the collision; the girl down, Hyde walks on | Enfield (the book's witness) never in the scene |
| 7 | wide | E, H (+5 extras) | **none** (`wide_only`) | E, H + panel | Enfield in a **brown coat** (words) dragging a **bearded man in a red scarf** (Hyde from his row's words: "mutton-chop side-whiskers"; his sheet is clean-shaven, pale, wide hat) | the ring of family and a top-hatted man close in | **E appears** at the door (the book has him collar Hyde at the corner); Hyde is not his sheet |
| 8 | medium_close | H | H + room (panel 7) | H + panel (speaking: sheet leads) | the **bearded** man again (the room picture won over the sheet) | **the sheet's Hyde** (pale, wide hat) from frame 0 | **Hyde changes face** between shot 7 and shot 8 |
| 9 | insert | H | H + room | H + panel | **two Hydes**: the sheet's pale man in the wide hat AND the bearded man, at the lock | both, then a hand with the key | **a second Hyde appears** |
| 10 | medium (OTS) | H, E | H, E + room | H, E + panel | Hyde alone at the door; no shoulder, no ring | **the ring (three women) and the doctor walk in**, Enfield's top hat fills the left by the end | the ring present in shot 7 is absent from the plan of 8-10 (extras 0) and pops back mid-take |
| 11 | medium | E | E, L (2x2 grid 11,12,18,19) | E | Enfield by the door and the arch; no lawyer | Enfield | opener without the lawyer |
| 12 | medium | L, E | (same grid) | L, E | **the lawyer stands in the dark arch** beside Enfield | both | **G-PRESENT: L appears** |
| 13 | medium | L, E | L, E (2x2 13-16) | L, E | both walking | both; Sunday walkers behind (planned) | -- |
| 14 | medium_close | E | (same grid) | E | Enfield | **three or four walkers appear** behind him (extras 0) | unplanned walk-ons |
| 15 | medium | L, E | (same grid) | L, E | both | both | -- |
| 16 | insert | L | (same grid) | L | the lawyer's hands | same | -- |
| 17 | medium_close | L | L + room | L | the lawyer | **walkers appear** behind him (extras 0) | unplanned walk-ons |
| 18 | insert | E | (grid 11,12,18,19) | E | the keyhole and Enfield's cane ferrule | keyhole; the cane comes in | opener of scene F is an insert |
| 19 | medium_close (OTS) | E, L | (same grid) | E, L | Enfield over the lawyer's shoulder | same | **G-PRESENT: L appears** after the insert opener |
| 20 | insert | L, E | L, E + room | L, E | the handshake | same | -- |
| 21 | medium_close | L | L + room | L | the lawyer | same | -- |
| 22 | wide | L (+3 extras) | **none** (`wide_only`) | L + panel | the lawyer from **words** (blond, as in panel 0), a tramp | the tramp strikes a match; the lawyer a speck | the lawyer is not his sheet; Enfield gone (the plan's invention) |

## The magic appearances, in cut order

1. **0 -> 1, Enfield** (the owner's fault). Panel 0 holds two word-drawn strangers; the real Enfield first appears in shot 1, the real lawyer in shot 2. The plan was right (shot 0's faces are both men); the grid dropped both sheets.
2. **2, walk-ons**: a man and a woman appear behind the lawyer by the end of T02 (extras 0); Enfield's shoulder leaves.
3. **3 -> 5, the girl**: first seen after the crossing's wide, entrance unmarked (G-PRESENT). Mild: she runs in, but the plan never says so.
4. **6 -> 7, Enfield**: he walks into the story at the door dragging Hyde. The book's Enfield sees the trampling and collars Hyde at the corner; the plan's crossroads scene has no Enfield.
5. **7 -> 8 -> 9, Hyde**: a bearded man (words) becomes the sheet's pale man in T08, and panel 9 holds both -- a second Hyde appears.
6. **10, the family and the doctor**: present in shot 7, absent from the plan of 8-10, they walk back in mid-take.
7. **11 -> 12, the lawyer**: absent from the scene's opener, he is found standing in the court's arch (G-PRESENT).
8. **14, 17, walk-ons**: H3 adds Sunday walkers behind a close (extras 0).
9. **18 -> 19, the lawyer**: the scene opens on an insert; he appears in the reverse (G-PRESENT).
10. **22, the lawyer from words** again (the wide), and Enfield gone.

## Root cause

**R1 -- a wide drew its people from words (the owner's fault, shots 0, 7, 22).**
`grids.wide_only` (76fb28f, 2026-10-02 09:39) staged no sheet for a person who is only
ever wide/full in a grid: ep16 shot 19 had drawn the whole four-pose turnaround as four
women. At 12:49 the same day (7ad14e6) grids began staging the sheet's ONE-FIGURE crop,
which removed that cause at every size -- and `wide_only` stayed. Every establishing
wide since has drawn its people as strangers in the right clothes words; the take pins
the panel as its first frame on a silent take, so the sheets staged in T00 cannot
override two figures a tenth of the frame high.

**R2 -- the room chain carries the stranger forward (shots 8, 9).** A setup's later
grids stage its first panel as "this exact room, already drawn" (`grid_room`). Panel 7's
word-drawn bearded Hyde was in that room picture, so grid s08 drew him despite Hyde's
sheet, and grid b (shot 9) drew both. T08, a speaking take, leads with the sheet, so the
cut changes Hyde's face between 7 and 8.

**R3 -- the row and the sheet disagree (Hyde).** `refs.json` says "thick, bushy black
mutton-chop side-whiskers"; `refs/characters/edward_hyde/sheet.png` is clean-shaven.
Words-drawn Hyde and sheet Hyde are two men. (Not fixed here: a row/sheet decision.)

**R4 -- the plan opens scenes without their people (shots 5, 12, 19).** `faces` meant
"whose face must read", so an opener could be a single, an insert or an empty-set wide
and the next shot reveal the rest. Nothing measured scene presence. The replay shows it
is the house style: 199 such appearances in the 42 plans on disk, 103 of them after an
establishing wide that holds nobody.

**R5 -- presence is not carried through a scene (shots 6 -> 7, 8-10).** The crossroads
scene's `cast` omits Enfield although the book puts him there; the ring declared as
5 extras in shot 7 is 0 in shots 8-10, and H3 brings them back mid-take.

**R6 -- the ceiling picked by order.** Grids fill `MAX_SLOTS - reserve` (1 or 2) slots
in first-appearance order and takes truncate at `MAX_FACES`; neither asks who is most
visible. In ep01 no grid lost a held person to the ceiling (the wides lost theirs to
R1), but the order rule would drop a close-up face for a speck named first.

Not caused by references: the walk-ons H3 adds behind closes (T02, T14, T17) with
extras 0 -- the take invents them; noted for the content gate.

## Fix (commit on master)

- `scripts/episode/grids.py`: `wide_only` removed; every person a panel holds (faces +
  proper names in the picture words) is staged by his one-figure crop at every size;
  over the slot ceiling `scene_cast.pick` keeps the closest readable faces (largest size
  a face reads at, then panel count, in first-appearance order) and the rest are said
  in wardrobe words, as before. Each block's "who" names the same people.
- `scripts/episode/takes_r2v.py`: `people_staged` uses the same pick at `MAX_FACES`.
- `studio/scene_cast.py` (new): scenes, who a picture holds, the ceiling pick.
- `studio/episode_spec.py`: `Shot.enters`, `Shot.exits`.
- `studio/plan_gates.py` + `plan_check.present_gate`: **G-PRESENT** (hard before
  anything is drawn, advice after) and **G-PRESENT-WIDE** (advisory).

## Replay ($0, CPU) -- `uv run python docs/audit/2026-10-14_jekyll_ep01_hel/replay_present.py`

| book | plans | G-PRESENT (appears) | G-PRESENT-WIDE (advice) | refused |
|---|---|---|---|---|
| WotW | ep01-27 | 108 | 28 | 0 (all rendered: advice) |
| Scarlet | ep01-14 | 88 | 23 | 0 (all rendered: advice) |
| Jekyll | ep01 | 3 (shots 5, 12, 19) | 0 | 0 (rendered: advice) |

Openers of the 199 appearances: wide/full 103 (the owner's empty-set opener), medium 41,
medium close 24, insert 25, close 6. The detector's own false positives were looked for
by counting which row tokens fire from prose: common-noun tokens ("first", "person",
"boy", "wife") were reading as people and are now ignored (`scene_cast.COMMON`); a
sample of hits read by hand (WotW ep01 4->5, ep04 3->4/6, ep16 12->13; Scarlet ep02
0->1, ep03 7->8, ep09 3->4, ep13 5->6/7) were all real: the person is not in the
opener's picture. Known miss: an anonymous body part ("one bare sunburnt hand", Scarlet
ep02 shot 0) does not hold its owner -- the plan never said whose hand. G-PRESENT-WIDE stays advice because
a wide can point away from the people (Scarlet ep08 shot 14 is the sky over the rock).
No shipped plan is refused: the gate is hard only on a plan nothing has been drawn from.

## To fix THIS episode (not re-rendered here)

Re-plan (then `plan_check` must pass G-PRESENT):
- **shot 5**: `enters: ["child_of_hyde_incident"]`, motion "the girl runs in down the cross street ...".
- **shot 11**: the scene's opener holds both men (a medium two-shot by the door) -- or shot 12 becomes the opener.
- **shot 18**: scene F opens on the two men (fold the keyhole insert after a two-shot, or put the lawyer in it).
- **shots 3-7 (book)**: Enfield is the crossroads witness -- add him to `night_cross_street`'s cast with an
  entrance ("runs in from the cross street and collars the little man") so he is not first seen at the door.
- **shots 8-10**: the family ring and the doctor present in shot 7 are declared (`extras`) wherever the
  picture faces them, or shot 10 is framed tight on the steps.
- **Hyde's row vs sheet** (R3): one decision -- whiskers in the sheet or out of the row -- before any regrid.

Re-grid (new staging; a changed anchor stales its chained siblings):
- `door_day`: 1x1_a (shot 0, the anchor) -> 1x1_s01 (1), 1x1_s02 (2), 1x1_b (22).
- `night_door`: 1x1_a (shot 7, the anchor) -> 1x1_s08 (8), 1x1_b (9), 1x1_c (10).
- `pavement_day`: 2x2_a (11, 12, 18, 19) -> 1x1_b (20), 1x1_c (21).
- `night_cross_street` 2x2 (3-6) only if the Enfield entrance changes its frames.

Re-take: T00, T01, T02, T05, T07, T08, T09, T10, T11, T12, T18, T19, T20, T21, T22
(and T03-T06 if the crossroads is re-planned with Enfield). T14 and T17's walk-ons are
the take's own invention and need a reseed only.
