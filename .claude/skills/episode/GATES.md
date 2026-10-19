# Gates

Every gate the episode chain runs, what it actually measures, and whether it
stops the chain. **HARD** means a non-zero exit, or a refusal the next step
enforces. **Advisory** means it is printed and never counted.

The one rule under all of them, from the 2026-09-22 audit: **a gate that
measured nothing has passed nothing.** Every gate refuses an empty set, a
missing input, or an unread picture.

## Plan — `scripts/episode/plan_check.py <book> <n>` (exit 1 on any hard fault)

| gate | measures | kind |
|---|---|---|
| CONTRACT | `episode_spec` validation: lengths, voices (at most 4), dialogue 5-20%, negations, "slow", driven lips at close/medium close, beat before the button | HARD |
| G-LIGHT | every setup names a light source with a direction; no overhead sun outdoors | HARD |
| G-SIZE | a close or medium close names its head fraction | HARD |
| G-SCALE | a shot that is not a wide never carries its setup's wide geometry | HARD |
| G-FIRSTFRAME | median `at_rest` at least 40 words with at least 3 frame-edge words a shot; median setup `described` at least 90 words, `geometry` at least 60 | HARD |
| G-SYNC | a dialogue line is the first line on its shot | HARD |
| G-VARIETY / G-MOVE / G-STORY | size mix (an insert every 6 shots), travel per second of the shot, first dialogue within the first quarter | HARD |
| G-MOVES | every shot's camera head read to a catalog move (`docs/calibration/camera_catalog.md`: the verb; the `camera` line's low/high angle when the camera stays put; over-shoulder): at least 8 distinct moves, no move on more than a quarter of the shots, never the same move on two shots running. A dialogue exchange held locked / over the shoulder / at a held angle is ONE shot/reverse-shot unit: no repeat, and those shots leave the share's count (never its total) (2026-10-13). Fixture lock: the orbiting list (18 of 23 pans) fails, the varied list (12 moves) passes | HARD on a plan of the new form (a `source` span on any shot); advisory on an older plan, every one of which fails it |
| G-STILL | a move MiniMax-H3 ignores (`rack_focus`, `tilt_down`, `crane_down`: the catalog's substitutes `pull_reveal`, `crane_up`) or a low/high angle held with no move, on a shot not declared `still` -- except a dialogue shot, whose actor carries the verb (2026-10-13). ep13 first pass: those moves 4/4 failed, the angle holds read 82-100 % static; a replay flags 5 of ep13's 7 frozen or off-panel takes before a render | HARD on a plan of the new form, with G-MOVES |
| G-SOURCE | a shot that claims a count (`extras > 0`), a posture word (kneels, sits, lying, astride) or a staged prop id carries `source` spans, and every span is found in the chapter text (`analysis/chapters`) by fuzzy match at 0.85; no chapter text is a refusal, not a pass | HARD on a plan of the new form; advisory on a plan with no span anywhere |
| CELL GATES (`studio/cell_gates.py`) | G-ANCHOR: no sideways truck on a medium-or-closer person leaning on / sitting on / standing at the set. G-AIM: every noun a move starts on or aims at is in `at_rest`. G-HAT: one hat worn and held in one picture. G-PLACE: a frame landmark the setup's words and drawn picture (`refs/pack.jsonl`) lack. G-LAID: a close or medium close on one person lying down whose camera neither looks down on the face nor lies level with it (ep10 T18) | HARD. G-LAID fires on ep10 shot 18 alone across ep05-10. Calibrated over ep01-09: G-ANCHOR fires on 7 shots of ep05-09, 5 visible faults (ep09 T02 the owner's, T10, T20; ep07 T13; ep08 T14), silent on the walker ep08 T05 |
| TAKE BUILDER | `takes_r2v.refuse_long_shots` / `refuse_still_motions`, run on the plan | HARD |
| WRITE | a plan script writes `plan.json` only through `episode_home.write_plan`, which refuses a plan the contract refuses and leaves the old file (guard test) | HARD |
| MOTION, MARKS, ACTOR | motion wording; the last clause moves a limb or head; staging marks | HARD |
| CAST BOUND | a book cast from sheets: every cast member has a row and a sheet on disk | HARD |
| QUOTE | at most 8 consecutive book words in a line | HARD |
| G-LOOK (decision 2026-10-10) | a setup's `looks` pick is a look the book's table allows this chapter (`continuity_place.look_gate`); a book without `refs/looks.json`/`places.json` is legacy and not judged | HARD, CODE CURE: the pick is dropped (`plan_repair`), never the writer |
| G-PLACE (decision 2026-10-10) | a setup's place is a member's master or a drawn view: a lookalike new id (0.85), a member with nothing drawn whose room a sibling drew, a framing/hour/state view of a RECURRING place (`continuity_place.place_gate`) | HARD, CODE CURE: rewritten to the member / its master, the state kept in `place_state` |
| G-LOOK-WORDS | one-face shot prose naming a hair colour the look contradicts (`scripts/refs/continuity_replay.py`) | ADVISORY: refuses nothing (7 on 27 WotW plans) |
| ONE PER TAKE / TAKE LENGTH | every shot is its own take, inside the 8 s budget | HARD |
| LISTEN (step 04, `say_lines`) | every line heard word for word (Whisper) and its voice against the design clip (ECAPA; floors 0.70 >= 4 s, 0.65 >= 2 s, 0.60, none under 2 s, lower for a felt delivery); a resume says a failed line on NEW seeds, the reference alternating design / best line from the third try (2026-10-14) | HARD per try; after 8 tries the best try heard right within 0.08 of its floor is kept, flagged keep_best (Jekyll ep01 l15, 2026-10-14) |
| TIMELINE | `placed.json` is of this plan AND this voice (`episode_home.load_placed`) | HARD |
| SHEET TEXT | the Scarlet book's paid-sheet check; skipped for sheet books, and a crash is printed, never counted silently | HARD where it applies |
| G-STORY advisories, G-NAMES, G-RATE, G-MOTION, L8 pace, G-SUNSPLIT, G-LIGHT-SIDE, G-HAT with "bareheaded" | caption-like lines, first hearing of a name, speaking rate, motion wording, a face split under a sun, the light side of a face, a hat clash the picture already resolves | advisory |

**2026-10-13 additions (Jekyll ep01 review, `docs/audit/2026-10-13_jekyll_ep01_review/`):**

| gate | measures | kind |
|---|---|---|
| NARRATOR (step 02, before any writer) | the book has a narrator: `refs/narrator.json` (`studio/book_narrator.py`), else the one speaker every PUBLISHED episode narrates with (WotW `unnamed_first_person_narrator`, Scarlet `john_watson`). Unset = `SystemExit("NARRATOR: ...")`; the writer is never asked | STOP |
| G-SPEAKER | unset narrator: ONE plan-wide row naming no cast member (no cure); a narration speaker that is neither the narrator nor a cast member is named against the narrator, never the cast; narration spoken by a character while the narrator narrates nothing is refused (Jekyll ep01's `henry_jekyll`); a `tale` is a cast member's, never the narrator's; a character narrating BESIDE the narrator is advice (WotW ep22 curate, ep24 artilleryman) | HARD; the free cure maps `narrator`/`the narrator` to the book's narrator |
| G-PACE | at most 310 words (`MAX_PLAN_WORDS`; WotW ep01-03 298/266/307) and at least 15 s of beats + codas (`MIN_PAUSE_S`; WotW 18-20 s, Jekyll ep01 9.4 s). Cures: `cut_lines` takes the longest cuttable narration line (never first/last/answer, never on hook/turn/spike/answer/button, only from a two-line shot) until inside 310 words and the 174 s budget; `breathe` grows beats (turn, spike, answer first) to the floor, then cuts lines. A breath is never shaved for budget; step 05's measured-runtime trim (10e4c5a) stays the last resort | HARD before anything is drawn, advisory after (the G-SETUP rule) |
| G-ACTION | an empty shot (no face, no extras) whose every action clause is moved only by weather (wind, leaves, birds, smoke, light...) is filler; more than 2 and each is named. Every shipped WotW/Scarlet plan: 0-2; Jekyll ep01: 7 | HARD, no cure (creative) |
| G-PRESENT (2026-10-14, Jekyll ep01 HEL, `studio/scene_cast.py`) | a scene = consecutive shots on one setup; a person in the picture of shot N (faces, cut faces, or a proper-name token of his row in frame/at_rest/end -- common nouns like "person", "boy", "wife" never count) who is not in the opener's picture and not in `enters` is refused; an `enters`/`exits` whose motion shows no arrival/leaving is refused. Replay over every plan on disk: WotW ep01-27 108, Scarlet ep01-14 88, Jekyll ep01 3 (shots 5, 12, 19) -- 103 of the 199 open on a wide/full that holds nobody (the owner's fault), the rest on a single/insert; all 42 plans are rendered, so all are advice; zero refused | HARD before anything is drawn, advisory after; no cure (the writer re-frames the opener or marks the entrance) |
| G-PRESENT-WIDE | a later wide/full shot of the scene whose picture leaves out someone present (no `exits`). Replay: WotW 28, Scarlet 23, Jekyll 0. Not hard: no field says where a wide points (Scarlet ep08 shot 14 is the sky) and old plans list nobody in a wide's `faces` | ADVISORY |
| G-TALK | a dialogue shot's camera TRAVELS (push, pull, track, follow, crane, orbit, handheld; a pan or tilt is no travel); at most 1. WotW ep01-03: 0/1/0; Jekyll ep01: 7 | HARD before anything is drawn, advisory after |
| `tale` line kind | a character's own telling, in his voice, voice-over (mouth closed) over the told pictures; keeps the book's words (QUOTE advisory, not hard), outside the dialogue ceiling, meets the chapter's speech floor (G-DIAL), counts as character speech for G-STORY's first-speech and narration-run walls | contract |
| STUDIO_RATE | a book with no measured voice projects at 2.45 words/s (`episode_spec.STUDIO_RATE`), never the 3.0 guess; the book's own measure once one episode is voiced | projection |
| G-HOOK / G-SPIKE (the plan critic) | the critic lists the chapter's `threat` and `spike` with the shots that show and lines that tell each; G-HOOK: neither shot 0 nor line 0 carries the threat; G-SPIKE: the key event is told by lines only. Faulted when most of the k readings agree. A `nonscene` row may be folded away | critic fault -> the ladder |

**2026-10-17 additions: the anime-TV grammar (owner; `studio/grammar_battery.py`, the battery's
`GRAMMAR` row; decision `architecture/decisions/2026-10-17_anime_tv_grammar.md`).** HARD on a plan
declaring `grammar: anime_tv` (set by code from the band) until something is drawn from it; advice on
a legacy plan. Calibrated by replaying 41 plans (`scripts/episode/grammar_replay.py`; WotW ep01-27,
Scarlet ep01-14, Jekyll ep01): the mechanical walls fire on none of the owner-approved WotW ep01-03 /
Scarlet ep05, ep07; the grammar-definitional ones fire on almost every legacy plan, and those fires are
the old grammar the owner replaced. Jekyll ep01 `plan_v3.json`: 0 rows, VERDICT clean.

| gate | measures | replay (plans firing of 41; owner-approved) | kind |
|---|---|---|---|
| G-FACES | share of the cut at close / medium close with a face, >= 0.55 | 38; 5 | HARD (grammar) |
| G-WIDE | <= 2 wides; each <= 4.0 s, the opener 5.0 s, by the voice ruler | 38; 5 | HARD |
| G-MEDIUM / G-FULL | a medium <= 7.0 s / a full <= 5.0 s | 31; 4 / advisory | HARD / advisory |
| G-INSERT | an insert 1.0-3.0 s | 39; 5 | HARD |
| G-PUSH | <= 2 pushes; no AMOUNT on a camera head | 37; 3 | HARD, cured free (`strip_amounts`, `hold_extra_pushes`) |
| G-LOCKED | >= 0.50 of the cut locked off | 37; 4 | HARD |
| G-TWO | a reaction with 2+ faces is a locked medium | 7; 0 | HARD |
| G-PAYOFF | a payoff shot with dialogue is a locked close | 8; 1 | HARD |
| G-OTS | over-the-shoulder at close / extreme close | 4; 0 | HARD, cured free (`ots_medium_close`) |
| G-UNSUPPORTED | silhouette, black shapes against, Dutch, canted, tilted horizon; extreme close on a face or eyes | 3; 0 | HARD |
| G-SHOTS | cut shots <= 28 (`episode_capacity.MAX_SHOTS`; 30 fit at 5.91 h, capped at 28 / 5.65 h until the retake shares are re-priced) | 1 (WotW ep21, 32 shots, 9.2 h measured); 0 | HARD |
| G-COLD | line 0 <= 10 words; a sound on shot 0 at <= 0.25 s | 39; 5 | HARD |
| G-ACT | one act_out; start at 0.35-0.55 of the picture; beat + coda >= 1.2 s; a bed tone change at it or the next shot; before the turn | 40; 5 | HARD |
| G-CAPTION | a narration line > 0.80 of its words in frame + motion (CAPTION_WALL); a line where the narrator acts is the witness, exempt | 8; 0 (WotW ep03 l15 exempted) | HARD |
| G-REACT | after each exchange of 2+ speakers, a silent face (or one inner line) | 17; 3 | HARD |
| G-MA | >= 3 shots holding beat + coda >= 1.2 s | 12; 3 | HARD |
| G-INNER | an inner line over its speaker's own face; the "owner has not heard it" note | -- | HARD / advisory note |
| G-TEASE, G-MOTIF | the tease loops to the hook's place and names its image; a grammar plan names its motif | -- | advisory |
| G-DIAL ceiling (every plan) | dialogue <= the chapter's speech + 0.08, inside 0.20-0.35 (`dial_ceiling`) | never lower than the old 0.20 | HARD |

Also: G-MOVES on a grammar plan leaves locked and over-the-shoulder shots out of the share and the
twice-running rule; G-VARIETY's closes a person is 12 on a grammar plan; ONE PER TAKE reads
`episode_takes.budget_for` (a grammar plan never packs); G-SOURCE reads a `tease` shot's spans in the
NEXT chapter. `plan_check.py <book> <n> --plan=<file>` judges a scratch plan as undrawn.

**2026-09-26 additions, all HARD:** G-COVER (every shot a `source` span; the
furthest reaches 90 % of the chapter's paragraphs and the title event's last
paragraph -- ep12 reached 57 of 69), G-SHOUT (a `!` line is dialogue), G-SOUND
(every setup an `ambience`; a loud event in the prose carries `sounds`).

**2026-09-29 addition:** G-BED (HARD) -- every bed tone is one of the five
(`plain`, `light`, `uneasy`, `grave`, `thrilling`); a synonym the bed folds
(alarm -> thrilling, dread -> grave, ...) is an advisory. ep14's writer wrote
five words the bed did not know and the episode was refused at assembly.

**2026-09-28 addition:** G-SETUP (HARD before anything is rendered, advisory
after) -- a setup holds at most `MAX_SETUP_SECONDS` = 50 s of projected picture;
measured on the plans whose place held (33-50 s) against those that drifted
(ep13 hedge 89 s, ep14 attic 52 s). One place at one hour from one side: split
attic / dormer view / doorstep / street the way ep11 gave one location three
views. On the board, `panel_place` (EYE_PANELS) names a loose panel that is the
staged room's mirror -- ADVISORY, no rung, until calibrated.

## Timeline — `timeline.py` (HARD)

The measured runtime must sit in 120-174 s — the PICTURE's budget, derived in
`episode_spec` as the 180 s YouTube-Shorts wall less the ~6 s tail (title card
+ chip) that assemble appends after the picture; never restate either number.
A measured overrun is cured in step 05 before any refusal stands (A99): the
holds of every shot shaved to the budget less 0.5 s, floors kept, recorded,
re-timed, re-signed; a timeline over the budget is never `done`. Every line at its shot's start plus the handle (`misaligned`). The fingerprint
covers only timing inputs, so a reworded frame does not stale it.

## Grids and the panel cut — `grids.py`, `panels.py` (HARD)

- **G-GRID-SHAPE (2026-10-11, C1_verdict #3):** a grid holds 1 or 4 cells, never 2
  or 3 (`grid_layout.GOOD = (1, 4)`; n shots lay out as [4]*(n//4) + [1]*(n%4)).
  Strip grids seamed 15/201 panels against 0/198 square-ish (p = 4.7e-5): Qwen
  draws its own grid count on a 2:1 or 3:1 canvas. ep19-27 replay: +1..7 grid
  calls per episode (mean +4.4), the same megapixels.
- **grids:** the chapter stamp; the shot count equals cols x rows; at most 3
  slots. The cast is dressed from the same chapter row as the take
  (`cast_refs.row`); a guard refuses a chapter given as a number.
- **Every size stages the sheet (2026-10-14, Jekyll ep01 HEL).** A grid stages the
  one-figure sheet of everyone its panels hold (faces + names in the picture
  words), wides included -- `wide_only` drew ep01's shot 0 and shot 7 people
  from words, two strangers then a bearded Hyde, and the chained room carried
  them into shots 8-9. Slots left after the place/room reserve go to the closest
  readable faces (`scene_cast.pick`: largest size a face reads at, then panel
  count, kept in first-appearance order); the rest are said in wardrobe words.
  Takes apply the same pick at `MAX_FACES` (4).
- **panels:** a grid is stale when the prompt it would be given now, or any
  picture it would stage, differs from its manifest's `inputs`. Older
  manifests fall back to `drawn_from` (plan fields), then to the plan hash. A
  shot in two grids or none is refused. The seam shave takes an edge gutter up
  to 48 px or a thin pale run within 120 px, with darker picture on both
  sides; the panel is then cropped square, never stretched, and written only
  when its pixels changed.

## Take prompts — `takes_r2v.py <book> <n> --from-refs --prompts` ($0, no GPU)

The take lint (`episode_ref_official.check`) runs on every built prompt:

- the length per block: 240-360 words with references only, 150-360 when the
  storyboard panel is staged (the panel is the room: the place is named once,
  in the summary, and the soundscape is one line naming no place);
- the style line: 16 words at most, no stray capitals (place names count as names);
- banned props (for example gloves, where the book gives bare hands);
- a last frame reaching the prompt;
- mid-sentence fragments.

Run it before any audio or picture exists. **HARD.**

Staging: a take stages only its setup's declared cast plus the shot's own
faces (`takes_r2v.staging_candidates`). Candidates used to be every row in
`refs.json`, matched by the last word of a display name. Six published takes
staged the wrong person that way (ep05 T19, ep06 T08, ep07 T09/T19/T24/T26).

## Looks and place states — step 03 (decision 2026-10-10)

| gate | where | measures | kind |
|---|---|---|---|
| LOOK-STATE (`judge:look_state`, gates.yaml `LOOK_STATE`) | 03_04, every new look picture | the VLM LISTS headwear, hair colour, facial hair, top, dirt in a closed vocabulary; code compares the look's markers | HARD on headwear, hair colour, facial hair (none / moustache / beard / stubble / sideburns; sideburns and beard are one cheek family, 2026-10-14) -- wrong OR unread (an unparsed answer, or a stated head marker the reader did not name, refuses; 2026-10-11); headwear compares by FAMILY in LOOK-STATE and G-LOOK-PANEL alike (`look_table.family`): brimmed = {felt_hat, other_hat}, every other marker, bowler included, is its own family (C2_verdict #4); ADVISORY on top, dirt; ladder seed+1 with the faulted layer first, cap 2, terminal keep_best flagged |
| relative identity (inside LOOK-STATE) | face-changing looks | facenet cos(look, base) minus the nearest other cast sheet | ADVISORY until the bench fits it |
| undrawn look | grids, takes | `pack_refs.look_sheet` | HARD: refuses, never the base sheet |
| one look per person (step 06) | `takes_r2v.opened` | `continuity.look_faults`: the staged picture and the words name ONE look on the table, the row is stamped with the table's look, the look is drawn | HARD |
| G-LINEAGE (2026-10-11, C2_verdict #9) | refs 02 sheets (`step_02_sheets.lineage`, `studio/lineage.py`) | a new character sheet version against every earlier staged version of the same row: head crop (top 35 %), MTCNN p > 0.95, VGGFace2 cosine | ADVISORY: a pair < 0.60 outside an age-up (a declared `age_up`, or a `_young`/`_child` row that is not simply the name) writes `audit/lineage.jsonl` and a WARNING; never a refusal. 0.60 is calibrated on Scarlet's photoreal sheets (flags exactly Hope 8826eb07 and Brigham c9192677); WotW narrator looks vs base: n 14, min 0.70, median 0.81. Hard only after a cast-wide WotW distribution (H8) |
| head unauthored (2026-10-11, C1_verdict #9) | refs 01_03 `looks_table.build`, `look_timeline.head_refusal` | a NEW table's character none of whose looks names hair, face or headwear | HARD refusal before the write (blank markers make LOOK-STATE pass anything); existing looks.json never re-judged; WotW replay 0/47 |
| G-LOOK-WORDS (beard, 2026-10-11, C1_verdict #6) | plan battery (`plan_check` continuity), `continuity_place.look_word_faults` | a head tag (a parenthetical naming face/eyes/hair) of a one-face shot whose staged look's marker is `beard` that says no beard | HARD, but CURED IN CODE FIRST (`cure_beard_tags`, plan_repair `continuity_beards`): the look's own beard phrase is appended to the tag, so the writer never loops; ep25 replay: exactly the 4 bare tags cured, 8 untouched |
| SHEET-ROW (2026-10-15, Jekyll ep01 v2 girl; `studio/judges/sheet_row.py`, a row of LOOK at refs/04) | every base `sheet.png` of an entity on refs/looks.json | the VLM LISTS headwear kind, colour and material, the garments' colour (whole sheet) and the eyes (whole sheet + head crop); code compares the base look's layers: headwear colour; a DISTINCT material (knitted/lace/felt/straw/silk/fur/leather/metal; silk = felt) other than the row's; a garment colour the row gives no garment (boots and hats left out); eyes `hollow` on BOTH reads where the row asks none | HARD (the sheet ladder climbs) on colour, material, garment colour, eyes; ADVISORY on the hat's kind (LOOK-STATE owns it). Replay: the lace girl 3/3 refused, the redrawn girl passes, 7 other Jekyll sheets: Lanyon refused (true), the constable refused (eyes; his helmet row vs cap sheet flagged) |
| grandfathering (2026-10-15) | refs/04 first verdict | only sheets older than the newest shipped master read light; a sheet drawn after it is read in full (`fresh_paths`); a drawn look is never asked the house sheet-form nouns (`look.asked_words`) | rule |
| same-place band | 03_05, every derived state | DINOv3 cosine of the variant to its source, `places.SAME_PLACE_BAND` 0.80 | FLAG, uncalibrated |

## Cast rows — `cast_refs.chapter_refusal`

`refs.json` holds one chapter's clothes. The take builder, the grids and both
content checks refuse rows stamped for another chapter. **HARD.**

## Panels — two gates, and the takes refuse without both

| script | writes | measures | calibration |
|---|---|---|---|
| `panel_check.py` | `storyboard/panel_dq.json` | people against `faces`+`extras` (faces need detector confidence 0.8 or more); missing face at medium or tighter (a back view the plan asks for is exempt); sharpness against the house control for the setup's hour; ink (small bright marks by their rim); tiling | ep06 29/29, ep08 20/20; the only failures are real (ep07 13 stacked, ep09 12 empty). Ink: worst clean panel 0.00417, caption band 0.01009, wall 0.007 |
| `panel_check.py` stacked | (same file) | the strongest full row or column gutter line at 512 | HARD above 0.90: ep07 S12-S14 read 1.000, every other published panel at most 0.748 (ep09 S07, a chalk cross) |
| `panel_check.py` seam | (same file) | any full row or column of the STAGED h3 panel at >= 250 luma over >= 95 % of its length, anywhere (not the outer 8 % the take guard searches) | HARD (2026-10-11, R2_verdict §2.1): fires on 18/572 WotW panels in 9 episodes, all 18 read by eye as a cell split into two pictures, 0 false positives (`docs/audit/2026-10-10_continuity_retro/bench_evidence/r2/seam_panels_wotw.jpg`); 16 also read `stacked` and all 18 shipped on the panel ladder's keep_best. Cure: **the seam rung** (2026-10-11) -- the seed bump is measured NOT to cure it |
| `panel_check.py` G-FRAME (advisory, uncalibrated) | (same file): `face_h`, `planned_size`, `frame_advisory` | the tallest present face (YuNet, score >= 0.7) against the planned size, every faced non-back panel; flag an MCU < 0.22 or a close < 0.32 | ADVISORY until calibrated on the owner-judged episodes (C2_verdict #8): no cure, no wall, no ladder effect. The MCU floor sits ABOVE today's MCU median (0.208, 84 panels ep12-27; it flags 48/84) |
| `panel_content_check.py` | `storyboard/panel_content.json` | a vision model LISTS people, copies, lettering, hour, landform, the main figure's POSTURE and subjects; code judges (a shot naming one posture family for its one person -- lying, sitting, crouching/kneeling -- fails a picture that shows another; ep10 T18) the list against the plan, the place's `landform` and the book's `dq_rules.json` | ep09 19/23, all four failures real (see `docs/calibration/content_gate.md`) |

`takes_r2v` refuses when either verdict is missing, fails a shot, skipped a
shot, or is older than a redrawn panel. **HARD.**

**Seam/stacked rung (2026-10-11, C1_verdict #4, `panel_ladder.SEAMED`):** a `seam`
or `stacked` fault isolates its shot into its own 1x1 ONCE, on whichever rung reads
it, OUTSIDE the 2-grid cap (`Climb.redrawn` and `ladder.json climbed` untouched),
and writes no reprose. A shot already alone is not curable. A shot still seamed at
the terminal is written to `storyboard/refs_only.json` (owner ruling 2026-10-11):
its take stages no panel (sheets + place + words), ships unattended, the fault is
signed `refs_only: true` and lands in the audit sheet; the coherence measure and
the still terminal never read that panel.

G-LOOK-PANEL (2026-10-10): on a one-face panel the content reader's subjects
are read for hat, hair, facial hair and top against the STAGED look's markers
(`panel_content.look_advisories`) into `look_advisory` on the row. ADVISORY:
armed HARD only at recall >= 0.8 and false refusals <= 0.1 over every narrator
panel of a finished book. A beard on a look whose facial hair is `none` stays
the HARD contradiction it was, judged by markers now.

J5 (2026-10-11, calibrated on the owner's ep05/07 good and ep08/09 bad,
`tests/fixtures/content_gate/wotw_owner_fixtures.json`): **'hills' on a flat place
is ADVISORY** (`landform_advisory` into `look_advisory`; 11/11 refusals on ep05 were
a far horizon); mountains stay HARD, cliffs stay HARD unless the staged place is a
pit. The hour is not judged on a setup that asks for the last daylight
(`judged_at_night`). An over-the-shoulder shot holds one more figure. A plan whose
shots predate `extras` (field unset) declares a crowd by naming people/crowd/
figures/others in the shot's words (`crowd_declared`). Open: named walk-ons in a
legacy plan (ep05 s10/s18/s19), a dusk crowd's silhouettes read as copies (s16).

The content reader is read STRICTLY (2026-09-23): a reply cut off inside
`subjects` is salvaged (the judged fields come first) and one cut before
them still refuses; `"false"` is false; a subjects string is split into
words; fewer people than the shot NAMES fails (inserts and back views the
plan asks for excepted); banned words match by stem. Re-judging ep09's 23
stored readings raised no new failure.

## Takes

| script | writes | measures | kind |
|---|---|---|---|
| `take_dq.py` | `T<NN>.dq.json` | frozen start and share (frozen-whole: one rule for every look -- the drawn-look relaxations 9ea1304/85ef81c were dropped by the owner, 2026-10-14), cut landing, churn, zoom, face at end, look, pulse, lip-sync lag and WER; **held** (a person pinned while the set slides: lock = 1 - face travel / scenery travel, hard at 0.75 over 100 px, only when the plan keeps the subject in place); **jump** (lowest similarity between consecutive frame signatures, hard below 0.50: a switch of picture, whatever the brightness) | HARD rows as marked in the report. held: ep09 T02 1.01 over 1055 px and T10 1.05 fail; eligible passes top out at -0.42 (n=2 fires against 3 passes: thin). jump: T15's two faults 0.08 and 0.16, every accepted ep08/09 take 0.83 or more |
| `take_content_check.py` | `T<NN>.content.json` | the panel content rules on 3 frames past the head leak, each read alone | HARD |
| G-MOVE (2026-10-13, Jekyll ep01) | `T<NN>.dq.json` row `camera-move` (`take_zoom.move_row`, off the subject zoom read) | the planned move against the rendered one: a move that plans no scale change (pan, tilt, track, locked, rise) fails past 3.0x either way; a planned push past 3.5x; a pull-back has no wall | HARD. Calibrated on the owner-liked WotW ep01-03 (69 takes): 0 fire (max 2.68x on a pan, 3.29x on a push, pulls to 9.1x liked). Fires on Jekyll ep01 T14 (a tilt rendered as a 4.75x push into a caricature) and WotW ep20 T06 (a 4.26x push). Does NOT fire on Jekyll T13 (2.54x push): WotW pushed further and was liked, so scale cannot call it. Cure: move_type (`overrun` -> locked). The camera record's `scale_curve` now compounds quarter-second steps (it was clamped at 1.25x); its stillness boolean is `still_ok` (was `camera_ok`), still unread |
| G-PANEL-BOARD (2026-10-13, Jekyll ep01) | `take_dq.panel_board`: a --from-refs take that staged `storyboard/h3/shot_NN.png` is judged with that panel as its one cell at frame 0 | foreign (every other shot's panel and the plates), cut-landing (opens on its panel), drift, coherence off-board, last-vs-cell are MEASURED (they read `not measured (no cell)` on all 27 Jekyll takes) | foreign and last-vs-cell HARD (0 fires in 47 takes; lowest last 0.21 against 0.20); cut-landing and off-board SCORED ADVISORIES on a panel board -- as HARD rows they failed 8 and 11 of WotW ep19's 20 shipped takes (H3 opens on a first-frame panel at similarity -0.18 to 1.00) |
| G-DEAD (2026-10-13, Jekyll ep01) | `assemble.dead_plan` -> `work_r2v/dead_cuts.json` (`studio/dead_footage`) | no still held past 2.5 s, no take that FAILED the take gate, never a still or failed take beside another, in the master | HARD at step 10. Cure, $0 and clock-free: the dead shot leaves the cut and its live, non-dialogue neighbours cover its seconds, slowed at most 1.5x; a dialogue shot is never cut or slowed. What no cut cures REFUSES the master -> retake (move_type), never a flagged ship. `near_dead` (static share >= 0.45) is reported, never a dead run: owner-liked WotW ep01 opens on two 1.00-static space shots |
| G-TAIL (2026-10-11, C1_verdict #7) | `T<NN>.dq.json` row `tail`, `measures.tail` (`take_dq.tail_measure`, `invented_speech.tail_state`) | dialogue takes only: FAIL when the SHIPPED tail (line end + 0.25 s to the placed end) is louder than -45 dB AND (Whisper hears words after the line's last shared word, OR the mouth is open >= 6 frames with >= 2 rises). Exempt: a post-line clause asking for a mouth action (laugh, call, shout, pant, eat, drink, bite, mouth). A guide whose speech end is > 1.0 s off placed.json's line end was overwritten: UNMEASURABLE, never invented. Whisper runs only on a loud tail | HARD. Replay over 204 shipped dialogue takes: fails exactly wotw ep10/T21 ("Moving!") and ep26/T25 (mouth branch, armed on 0 false fails); the laugh ep25/T21 exempt; the 5 overwritten early-Scarlet guides unmeasurable. Cure: ONE reseed (the router's seed; a repeated fault goes to the terminal), then keep_best flagged; never a shorter shot (the voice is the ruler) |
| G-GAIT (2026-10-14, Jekyll HEL ep01 T03) | `T<NN>.dq.json` row `gait` (`studio/gait.py`: CPU person box, Farneback flow, ground from the bands beside the feet) | only when the plan asks a SUBJECT to walk or run ("travelling two strides at a walking pace" is the camera, never a walker): FAIL a shuffle -- cadence >= 3.0 steps/s (`SHUFFLE_CADENCE`) AND a step under 0.045 body heights (`SHUFFLE_STEP`). Unmeasured: under 2 s with the feet in frame, a walk toward/away from the camera (depth), or no step rhythm | HARD. Replay over 91 walker takes: 20 measurable, fires on Jekyll ep01 T03 only (3.94 steps/s, 0.027 heights a step: legs patter, the body glides); 0 fires on WotW ep01-27 and Scarlet ep01-14 (nearest non-fire WotW ep06 T23 4.04/0.048; liked WotW ep03 T07 3.1/0.052). One positive: a first calibration. Cure: the PLAN's gait verb -- "walks briskly in profile, left to right, a long stride", feet in the picture; a reseed of a mince minces again |
| G-WARP (2026-10-18, main session from measured evidence, for owner veto) | `T<NN>.dq.json` row `warp`, `measures.warp` (`studio/warp_gate.py`, CPU lane inside `take_dq --cpu-only`, ~20 s a take; the GPU never waits) | every take that stages a face: MTCNN every 2nd frame (min 24 px, prob >= 0.9) linked into tracks by IoU > 0.3 (a swap is a new track, never a fault); Farneback fwd/bwd at 384 px, residual only where they agree (< 1.5 px); E(t) = face residual - (2.51 x bg residual (body excluded) + 1.69 x face flow + 1.00); S = p90 E, Se = p90 over the eye mask. FAIL S > 2.5 or Se > 3.0 (HARD: the ladder's `seed` cure, at most 2 retakes, then F2); WARN 1.5 < S <= 2.5 -> F2; UNMEASURABLE (face tracked on < 45 % of searched frames) -> F2 | HARD on fail. Fitted on 27 clips, NO owner labels: every S/Se/share/span is logged in the dq record to refit on labelled takes. Replication on the Kawajiri POC: C 0.98/-0.89 pass (prototype 0.98/-0.90), W 2.30/3.04 fail (2.65/3.12), M 1.57/2.08 warn (1.30/1.64 pass: the swap between two men reads higher here; M goes to F2, ~100 s) |
| identity (G4.7, sheets in again 2026-10-14) | `T<NN>.dq.json` row `identity` (`take_verdict.identity_report`, facenet against the take's OWN staged sheets) | STRANGER (best cosine < 0.45 on a readable face) and DRIFT (< 0.75 within a segment) | ADVISORY (`take_verdict.TAKE_IDENTITY_HARD = False`): the row is measured, counted and noted ("advisory: STRANGER ..."), and the master eye flags each take with a finding (`master_eye.take_identity`, kind `take_identity`, low, never a climb). From 2026-09-25 (4c5f14c) to 2026-10-14 it read "not measured" on every take: the sheets were never handed in. Replay with sheets (`docs/audit/2026-10-14_jekyll_ep01_hel_v2/identity_replay.*`): it would refuse 23 of 118 shipped WotW ep19-27 face takes and 37 of 97 Scarlet ep08-14 (STRANGER on stylised, turned or small faces; walk-ons) and 2 of 10 Jekyll HEL v1 -- HARD stays off until it is recalibrated on drawn faces |
| G-LOOK-TAKE (2026-10-10) | `T<NN>.content.json` `look_log` | the hair family changing across the 3 frames, or off the staged look on 2 of them (`take_content.look_log`) | LOG ONLY: its only cure is a re-render (3/21) |
| `take_frame.row` (letterbox, in `T<NN>.dq.json`) | — | bars at the top AND bottom, each >= 4 % of the height, each either flat (row spread <= 2.0) or ending at an edge (the picture rises >= 12 levels past it) | HARD. ep14 T26: 54/256 rows of bars. ep21 T27/T30: a dark cellar read 3.6-5.3 spread, 1.5-3.3 step, and is NOT a letterbox (2026-10-08) |

**G-TAKE-INPUTS (2026-10-15, Jekyll ep01 iter4 T06; `studio/take_inputs.py`).** A kept take's graph
must have staged exactly the pictures its card stages NOW (content-addressed LoadImage names against
`staged_name` of the current sheets and panel). `take_dq.settle` ranks only attempts made from the
current inputs (a score never compares across a changed input: iter4 kept a 95 on the superseded lace
girl over four current 10-40s); under `--attempts` the WORDS count too (2026-10-16, iter7 T06,
`take_dq.reworded`): a roll whose recorded prompt is not the card's is not current, so a plan cure is
never undone by an older higher score; when none is current the take fails its HARD `inputs` row and the
ladder retakes it. A swap writes `{"unknown_provenance": true}` for a roll with no graph of its own,
never another roll's graph (the open "archived attempt carries another render's graph" bug). HARD
walls: before assemble builds any cut, QC row `inputs` (count line "inputs: all N takes current"),
and step 09 prints every kept take's staged names and stops on a stale or superseded one. After any
sheet, place or panel redraw, every take that stages it is stale: re-render it or the master waits.

**PROMPT LINT (2026-10-15, `studio/prompt_lint.py`, CLI `scripts/episode/prompt_lint.py <book> <n>`).**
Deterministic, $0, a HARD wall in `takes_r2v --prompts` (step 06) and before every render; grids run
`studio/grid_lint.py` before any grid is posted. Take rules: P1 case garble ("tHE FOCUS"), P2
"The camera is On", P3 a panel cure read as a noun phrase, P4 a staged Subject never cited / a staged
epithet left free, P5 a second description in parentheses, P6 Subject-definition debris (another cast
name, "described as", "with a long."), P7 a stub speaker clause, P8 "as the line ends ... as he
speaks", P9 "the lean continues" / garbled end noun, P10 the closed mouth on the listener, P11 a
dangling aim, P13 an unstaged person, P14 lettering bait with no unlettered sentence, P15 a lens length
in a drawn book, P17 an over-the-shoulder side against its edge / a vertical pan, P18 one action per
1.2 s. Plan rules: P11, P12 (every tag fragment is in the current row: `cast_alias.retag`), P13, P17.
File rules (after a render): the graph's prompt is prompts.json's, the graph not older than its take.
Grid rules: P14 "picture" for a door's panels, P15 a raw dossier row for an unslotted person, P16 a
girl/woman "the person in <imageN>", a physique word inside "wears:", a parenthetical after a slot.

**SCENE PALETTE (2026-10-15, advisory, `scripts/episode/scene_palette.py`).** One frame per take; a
take whose open-blue-sky share (top third) or saturation sits far from its scene's median is named
(iter4: pavement_day T12 sunny inside an overcast scene). Uncalibrated: refuses nothing.

Take currency: a take is kept only when it was rendered from the same prompt
AND the same staged picture bytes (content-addressed names in its
`graph.json`).

**FACE REFINE GATE (2026-10-17, owner approved; `studio/face_refine.decide`, measures `studio/face_gate.py`,
calibration `docs/calibration/face_refine.md`).** Per refined face crop of a wide/full or small-faced take, at window
scale and on the 768 crops: the refined crop must DIFFER from the crop it was rendered from (mean |refined - source|
>= 0.5 per pixel, `SAME_MAX`; first wall: a refine that returns its input passes every other one); identity (facenet
cosine to the person's sheet at the crop's face -- the detected one, else the box the window was cut round; the sheet's
face from facenet, the loose detector, else its head band, so a DRAWN face is read) may not drop by more than 0.05;
seam (feather-band level difference) <= 18; face-region flicker pasted <= 1.10 x the take's + 0.5; faces = the most any
one sampled crop shows (centre inside the window core, overlapping boxes merged): a clone is more than the source's
most (at least 1), a loss is 0 where the source had one. Kawajiri POC W (2026-10-18): change 12.3 (the old echo 0.0),
identity 0.33 -> 0.32 (Hyde's sheet; Utterson's and Enfield's read -0.02-0.23 on the same crops), faces 1/1 (the old
summed count read 6 vs 3: the sharper face was found in more frames), KEPT. A broken wall FALLS BACK to the unrefined take, never a refusal of the episode; every
decision and its measures in `takes/r2v/refine.json`. Calibrated on F2 (kept by eye: flicker ratio 0.81-0.95) against
F3 (refused by eye: 1.15-1.32), three takes: thin. A crop is pasted only onto the take bytes it was made from (sha8).
CLOCK: priced 110 s per face per 192 frames; runs only while `leaves_reserve(step, price + 550 s)`; else `REFINE CUT`
logged, `status: cut` recorded, the take ships unrefined.

## QC — `qc.py <book> <n> --engine=r2v`

QC fails on any of these:

- loudness or true peak out of range;
- a planned cut missing;
- a line not heard;
- a silent gap over 6.0 s (it names the silent shot the gap is made of);
- an unmeasured edit;
- **any take without a current dq AND content verdict;**
- **no title card** (`title_card` false).
- **a delivered master past the 180 s Shorts wall, or unmeasured**
  (`episode_spec.short_refusal` on `seconds`) -- 2026-09-30, ep14 shipped as a
  video at 182.58 s.
- **a planned sound the master does not let you hear** (`sound`, `episode_sound.presence`,
  6 dB over the second before it) -- 2026-09-26. Since 2026-10-17 QC listens where the
  placer LAID the cue (`audio/sfx/onsets.json`, `sfx_onset.measured_starts`), not where
  the plan put it: a cue moved onto its measured moment is heard there.

A take that failed and spent its retake budget does not fail the master. That
is the owner's call, and it was measured.

The master's SIZE is whatever step 10's upscale delivered (2026-10-18: `av3`,
hqdn3d per shot + realesr-animevideov3 4x -> 3072; `rtx4x` -> 3072; `rtx2x` and
the Lanczos fallback -> 1536). av3's denoise is temporal, so it starts fresh on every
cut assemble knows (the takes' joins from layout.json, the card, the chip): no frame
blends across a hard cut. QC's segment mean cap is 2.0 for av3 as for rtx (av3 measured
1.50-1.77 on correct segments, `edit_gate.segment_cap`). Nothing
downstream assumes one: QC and the judges scale what they read, the card and the
chip ride the same pass as the cut, `book_compilation` conforms every piece to
its 1536 square, the upload checks only that it is square. A fallback is not a
fault, but it is never silent: `UPSCALE FALLBACK:` on stderr and its reason in
the `upscale` row's note on timing.jsonl.


## Publish — `youtube_upload.py`

**THE PUBLISH LOCK (2026-09-26, `studio/publish_lock.py`).** Both doors -- the
upload and the public flip -- refuse on:

- **an open terminal**: any gate whose last row in `learnings.jsonl` ended
  `keep_best`, `flag` or `still`. ep12 went public with PLAN, EYE_PANELS,
  EYE_TAKES and MASTER all ended in terminals. Since the owner's ruling of
  2026-10-01 ("no human input at publish", `docs/DECISIONS.md`) a terminal on a
  gates.yaml `auto` gate is cleared by the judge that signed it
  (`publish_lock.judge_waivers`; the upload ledger records `auto_cleared` with the
  judge's name). A terminal on a gate the registry does not call `auto` is still
  the OWNER's to clear, in `review/waiver.json` (`{"GATE": "reason"}`); the
  assistant never writes that file.
- **a voice that is not one voice**: `review/speaker_check.json` `ok: false`.
- **no director's sign-off**: `review/director_signoff.md` naming THIS cut's
  sha8, with four written sections -- `## Watched` (the master full size WITH
  sound, timestamped notes), `## Take strips` (every strip read), `## Coverage`
  (the plan's last paragraph against the chapter's), `## Flags` (every open flag
  accepted or refused). A green QC is not a watch.

It refuses on failed takes, content failures and unjudged takes. One
`--override="<reason>"` waives the QC pass and the take roll-up and is
recorded in the ledger; nothing waives "already uploaded". The title comes
from the book's own `series`/`display_title`/`episodes` in
`source/book.json`, never from a default.

`youtube_privacy.py ... public` (the flip every episode takes, because the
insert is forced private) refuses when QC is not about the uploaded sha8, QC
failed, or any take failed or was never judged, as they stand at the flip.
The human sign-off is waived by the owner's standing instruction; these are
not. Dry-run on 2026-09-23: ep09 passes; ep05-ep08, public before the
content gate existed, would be refused for unjudged or lettered takes.

## Board states — what the Command Center shows (`studio/command_center/views.py`)

Each row is one (department, unit) in `work_orders`; the board shows a state, never
computes one a runner did not write, except the three marked derived.

| shown | means | who moves it |
|---|---|---|
| queued | ready: every `requires` row is done and the first step's inputs exist | a runner takes it |
| blocked | waits on X (`blocked_on`: a required stage/unit like `refs/04`, or `in: <glob>`) | the tick, when X lands |
| running | a run holds the lease | the run |
| stale *(derived for a lapsed lease)* | the run lost its lease, or the disk disagrees with the row (`blocked_on` says which) | an order or a new run |
| flagged *(derived)* | done, with judge flags (audit rows) that are neither acknowledged nor published | the owner's acknowledge, or the upload |
| done | finished; a published unit with flags shows done (2026-10-01 ruling), its gate chips kept as the audit trail | -- |
| deferred / failed / escalated / held | a step handed it back / crashed / asked the owner / a hold parks it | a retry, a fix, the owner, a lift |

`flags` on a row counts the unit's audit rows -- history, not open work: it never
goes down. Needs you and the inbox read `views.flags_open` (done + flags, not
acknowledged, not published), the department page and the sidebar dots read the same
function. Published = a done `publish` row, or the publish record on disk: youtube.json
AND an upload row with a video id (`backfill.publish_row`); youtube.json alone is a
draft. The tick settles an episode from that record (`tick.settle_published`): a
queued/blocked row, or one whose lease ran out, becomes `done` with the uploaded file
(found by the upload's sha8) as its deliverable.

## Known gaps — not measured yet

- **continuity (2026-10-10):** the relative-identity margin, the same-place
  band and G-LOOK-PANEL are uncalibrated; the GPU acceptance replay (looks
  staged in one ep25 and one ep27 grid; the villa and the study reverse as
  one-hop edits, `scripts/refs/look_replay.py`, `place_replay.py`) is not run.
  Phase 2: "the panel IS the sheet" (panel vs staged sheet), GeomCons on the
  master's fixed things, the production designer.
- **framing:** a medium close drawn as a full figure passes (face 0.112
  against published 0.101-0.3). It needs a closed-vocabulary FRAMING answer
  from the content reader, judged against the planned size.
- **a take against its own panel:** BUILT 2026-10-13 as G-PANEL-BOARD (the staged
  panel is the cell). Off-board and the opening stay advisory until an owner-judged
  pinned-panel episode calibrates them; WotW ep01-03 (the liked set) staged no panel.
- **copies in a crowd:** the reader's lookalike count missed nine identical
  sappers and two identical hussars; pairwise face embeddings are the fix
  (YuNet + SFace ONNX via the OpenCV already installed).
- **OCR:** no library installed; EasyOCR's weights are cached locally. ep08's
  "NEWSPAPER BOY" is already in the PANEL, so OCR belongs at the panel stage.
- **two pictures stacked in one frame:** the line score reads 1.00 on ep07
  S12-S14 and at most 0.748 on 124 clean panels; wall 0.90 is ready to build.
- **not to build:** a darkness wall (it would fail 39 of 127 accepted takes;
  the known dark fault is only the second darkest) and same-setup layout
  correlation (19 accepted pairs above 0.75; one camera position per place is
  owner decision D4).

## Judges — the taste gates are signed by code, never by a person (2026-09-24)

Decision `2026-09-24-automate-the-taste-gates` (owner). `gates.yaml` names who signs
each gate; every refs/episode row is `auto`. A judge signs `pass` or `flagged`, never
`fault`, never a waiver; a terminal rung writes a flagged verdict, a learning and an
audit row (`library/<book>/audit/rows.jsonl`); no step reads the audit sheet. Each
judge is benched against the casebook (`scripts/calibration/bench.py`) and a ratchet
test refuses a commit that loses a catch. `fitted_on` is carried on every measure.

| gate | judge | measures | ladder | terminal | errs toward |
|---|---|---|---|---|---|
| LOOK (refs/04) | `judge:look@1` | must nouns (look_back), recognised strings (OCR), extra limbs (keypoints), lookalike pair (trait card), stranger (face embedding); style outlier and near voice as flags | redraw on the next seed → defining state first | best sheet kept flagged; a lookalike pair bound flagged | refuse on nouns, lettering, identity; flag on style |
| PLAN (episode/02) | `judge:plan@1` | the battery (plan_check, cell gates, G-MOVES, G-STILL, G-SOURCE, G-SPEAKER, G-PACE, G-ACTION, G-PRESENT, G-TALK); the critic lists turn, answer, coverage, threat, spike, claims with spans ×3; code judges (G-HOOK, G-SPIKE, a `nonscene` row foldable) | improve ×2 → model_tier (the reasoning tier) → terminal; no fresh brief (C2_verdict #3, 2026-10-11) | critic fault: best draft signed flagged; battery still refusing: defer (plan.deferred.json, no signature) | the battery refuses; the critic flags |
| LAYOUT (episode/07) | `grid_layout@1` | a rule: grids ≤ 9, cols × rows = shots, a face alone in a 1x1 when a setup mixes sizes | — | — | deterministic |
| EYE panels (episode/08) | `judge:panel_eye@1` | stored dq + content rows; hats worn and held; a reference handed back; posture; framing; clones; lettering; invented landmark; repeats; one short size read | redraw grid seed → reprose the frame (timing untouched); cap 2 grids; framing/posture take no rung (no rung ever moved one on ep13: cure them in the prompt) | best panel kept flagged | refuse on calibrated rows; flag on thin rows |
| EYE takes (episode/09) | `judge:take_eye@1` | dq rows incl. pass-through, rotation, leak, cut vote, lag; content; identity vs sheet; clones | seed → move type → shorter → head cut → re-plan the cell (priced) | a still from the panel on a narration shot (≤2, never adjacent), else best take flagged, high on dialogue/turn/button | refuse where calibrated; "cannot tell" on wides |
| MASTER (episode/11) | `judge:master_eye@1` | qc hard rows; shadow, faces, board, repeats, story from measures; a 30-frame read; cross-take identity | one retake through the take ladder, then its recut (no free recut: step 11's master is already current) | the rubric flagged with evidence; never waived by a judge | refuse → retake on measured fields; flag on story |

The owner's eye: `library/<book>/audit/<unit>.html` (`scripts/audit/sheet.py`), every
flag with its numbers beside the wall and a seeded sample of passes per gate; a finding
is `scripts/audit/note.py <codex> <unit> <artefact> <class> "<words>"` → the casebook
overlay → the bench → the ratchet. What still needs a signature: PUBLISH, paid credits,
OVERRIDE, the synthetic declaration; `RENDER_HOLD` is the brake.


## The run itself (five-hour plan, 2026-09-30)

- **One episode, one clock.** The 5 h ceiling covers the EPISODE across resumes
  (`Budget.charge(spent_before(home))`); a spent ceiling takes terminals, and the
  driver never auto-resumes past it. ep14 got 31 fresh ceilings.
- **One episode, one commit.** The driver warns when HEAD moved since the episode
  started (ep14 ran on 23 commits). Fix bugs after the ship, not during it.
- **The GPU never waits on a check** (owner, 2026-10-14; decision
  `2026-10-14-gpu-never-waits-for-checks`). Step 09 and every ladder round run two lanes
  (`studio/take_overlap.py`): the GPU renders back to back; the CPU runs `take_dq
  --cpu-only` on each take the moment it lands (`shots.json` written after its bytes).
  The CPU lane never touches ComfyUI -- with an embedder installed the leak row is
  DEFERRED (`deferred: ["leak"]`, never cached, never current) to the GPU window. A cure
  the dq rows alone order (`move_type`, `seed`) queues behind the first renders as the
  ladder's ROUND 1 (`ladder.json` `early: true`, recorded at launch, joined by later jobs,
  cap 2 unchanged; an `EYE_TAKES early_cures` learning). The GPU checks (VL content, a
  deferred leak) run only when no render is queued AND the CPU lane is idle -- never
  between renders, one VL load; then the strip, the eye, round 2. The CPU rows are
  stamped `within: "takes"` so the clock sums the wall once.
- **GPU when idle, CPU when rendering** (owner 2026-10-18; `studio/compute_device.py`). Every
  heavy NON-render job asks `device_for(job, need_gb)`: "cuda" only when the ComfyUI queue is
  empty twice 2 s apart, no GPU claim of ours is live (`claim()`: the av3 master pass, the
  whisper worker) and `need_gb` is free on nvidia-smi after a POST /free sent only on an empty
  queue; else "cpu", today's path byte for byte. Any probe failure is "cpu". Every decision is
  a `DEVICE <job> -> <device>: <reason>` line and a row of `library/.device/decisions.jsonl`.
  `VISURENA_DEVICE=cpu` is the kill switch. Wired: whisper (`voice_qc.any_transcriber` ->
  `studio/routed_whisper`: a worker under ComfyUI's embedded python, a render arriving mid-batch
  closes it and the rest goes to the CPU) and the master encode (`studio/video_encoder`: NVENC
  p7 cq = crf + 5 on cuda, x264 on cpu). The VL reads already run on ComfyUI (GPU); facenet and
  EasyOCR are still CPU (see LESSONS 2026-10-18).
- **Renders before ComfyUI checks** (owner, 2026-09-30) still holds: the H3 stack evicts
  the judge, so a ComfyUI read between renders pays two cold loads. The CPU checks are
  not ComfyUI reads.
- **A book's title cards ALL exist before its first episode** (owner design):
  `scripts/episode/titles_batch.py <book>` bakes every missing card in one i2v
  session; drive.py runs it automatically before any launch, outside the
  episode's clock. A card without a plan takes the series aspect; a card that
  fails its lettering gate blocks that episode's launch.
- **The working set lives on the NVMe** (`extra_model_paths.yaml`, `nvme_fast` stanza,
  C:\comfy_models). Never delete the `.hdd_bak` originals without a verified load.

## Step caps (owner approved 2026-10-18; `stages.yaml` `caps:`, audit `docs/audit/2026-10-18_step_caps/STEP_CAPS.md`)

Every step has a round cap and a wall. At the cap the step **keeps its best attempt, logs
`CAP <phase>: r/N rounds, mm:ss, kept best (k advisories)`, and goes on**. It never defers,
never re-authors past the table, never parks on style. The 6 h episode clock is the outer
wall (the walls below sum to more than 6 h; no run hits them all).

| step | phase | rounds | per | wall min | gate |
|---|---|---|---|---|---|
| 01 | bind | 1 | pass | 2 | |
| 02 | plan | 3 | climb (2 climbs per episode) | 30 | PLAN |
| 03 | places | 3 | draw | 15 | |
| 04 | voice | 2 | episode | 30 | |
| 05 | timeline | 1 | pass | 2 | |
| 06 | prompts | 1 | pass | 2 | |
| 07 | grids | 1 | grid | 30 | |
| 08 | panel_checks | 1 | round | 30 | |
| 08 | regrid | 2 | episode | 20 | EYE_PANELS |
| 09 | takes | 1 | pass | 120 | |
| 09 | take_dq | 1 | round | 30 | |
| 09 | take_content | 1 | round | 20 | |
| 09 | take_eye | 1 | round | 10 | |
| 09 | strip | 1 | round | 2 | |
| 09 | retakes | 2 | episode | 45 | EYE_TAKES |
| 09 | face_refine | 1 | take | 15 | |
| 10 | assemble | 1 | pass | 15 | |
| 10 | upscale | 1 | pass | 15 | |
| 11 | qc | 1 | episode | 30 | |
| 11 | master_eye | 1 | episode | 30 | MASTER |
| 12 | deliver | 1 | pass | 2 | |
| 13 | publish | 1 | pass | 10 | |

- **The plan: two climbs per episode**, each three writer rounds inside 30 min. A refusal on
  tier-1 faults only (a line a downstream builder repeats) parks **once**: one tier-1
  re-author per episode, never a second defer. Tier 2 gets the rounds, then the best draft
  is signed flagged. Tier 3 (voice-measured grammar rows, the G-VARIETY insert count) is
  advice and never refuses.
- Caps are per **episode** where the table says so (voice, regrid, retakes, qc, master_eye),
  so a relaunch, a resume or a drive restart does not reset them.
- A step logs `STEP <id> start` (Seattle time) on entry, so a killed step is still visible.

## Speed arms — `scripts/bench/rulers.judge_arm` (bench only, C1_verdict 2026-10-11)

| rule | measures | kind |
|---|---|---|
| (a) same draw | PSNR(arm, ctl) - PSNR(ctl seed 2, ctl) >= 3 dB on every shot | CLASSIFIES only: under it the arm is a new draw, judged by rulers and eye; no PSNR floor refuses an arm (28 dB refused the shipped 8-step on 6/6) |
| (b) identity | per shot delta id >= -2 sigma_seed (pooled RMS of seed pairs, recomputed when a seed-2 control lands); dialogue mean >= -0.02 | HARD |
| (c) banding | mean <= ctl + .005, no shot worse by > .03 | HARD |
| (d) clones | <= the production take's count on the same shot | HARD |
| (e) invented speech | tail words where the control's own tail on that seed has none; prompt-asked mouth actions exempt | HARD for dialogue |

**Arm rule:** a speed arm passes the INVENTED-SPEECH check on S4, D1 and D2 x 2
seeds, or it is adopted for **narration takes only**. Dialogue stays on the 8-step
at 12/3 until an arm passes. **Amend (C2_verdict, 2026-10-11):** a speed arm on dialogue
must also pass on >= 2 shipped takes whose control tail sounds above -45 dB (ep10/T21,
ep15/T21): its tail words a subset of the control's at the same seed, tail dB within +-6,
lower-face tail ratio within the control's range, mouth.lag within +-1 frame. CK8 failed
it on 2026-10-11 (ep10/T21 "keep moving" vs "moving"; ep15/T21 mouth 1.14 vs .94-.97).

**Adopted (2026-10-11 bench):** CK int8 attention on the 8-step BASE for narration takes
(`takes_r2v.NARRATION_BASE`). Out: G1 (4-step on the authors' grid, lost the S3 frogs).

**Superseded (2026-10-18, main session on measured evidence; owner 2026-10-17 picked Wuli V4 and
approved Spark):** the take model is routed by PLANNED SIZE, not by lane (`takes_r2v.workflow_for`).
Close / medium_close / medium / insert -> `WULI_BASE` (Wuli 8-step HQ int8 + Spark); any wide or
full segment, or no sizes -> `SPARK_BASE` (the CK 8-step with Spark attention); `ROLLBACK_BASE` is
the CK 8-step. Proof (`docs/audit/2026-10-18_wuli_spark/`), Kawajiri POC C/M/W at the POC seeds,
Spark (POC) vs Wuli+Spark: content clean 3/3 both; clone pairs 0 both; G-TAIL on the speaking
close C pass both (tail -76.9 / -90.8 dB, no words); G-WARP S/Se C 0.98/-0.90 vs 0.49/0.30, M
1.30/1.64 vs 1.46/1.32, W 2.65/3.12 vs **4.13/7.22**; close identity (facenet on a drawn face,
advisory) 0.531 vs 0.561; every arm fails only frozen-whole, the POC's locked cards. The dialogue
arm rule above was NOT re-run on the WotW ep10/T21 / ep15/T21 controls: G-TAIL stays HARD on every
dialogue take and is the net.

**Regrid bar (bench, `scripts/refs/look_replay.tally`, C2_verdict #7):** the denominator is
face-visible cast panels -- a plan frame `from behind|seen from behind|back to (the )camera|walking
away` or a wide / extreme_wide / establishing size is exempt; over-the-shoulder is NOT. A
face-visible panel with no face read is a miss; an empty denominator is unmeasurable, never a pass.
Replays: C1 ep25 regrid 2/2 PASS, ep25 round 0 0/1 FAIL, ep27 study_table 3/3 PASS.

## The clock, SAFETY and the boundary (C3_verdict, 2026-10-11; decided on the owner's behalf, D1-D12)

- **Clock:** one ceiling per episode, 5 h internal (D5), from the first launch to public: the
  union of the episode's run spans (`studio/run_clock.py`: a run row, a 60 s heartbeat, a kill
  counted to its last beat). `retry` stamps `attempt_at` and never resets it (D2). Past it,
  rungs are terminal and signed flagged; the takes, grids, panels or lines MISSING on disk still
  render (firsts are never refused, only repeats); nothing parks on the clock (D3). A third
  spent-clock stop in a row parks `clock_loop` (a backstop).
- **The downstream reserve (6 h for EVERY episode, 2026-10-11, for veto):** below the ceiling a
  rescue rung also runs only while spent + its price + the shares of the firsts still owed after
  its step fit under 6 h (`Budget.leaves_reserve`; owed after 02 = 203 min, 08 = 137, 09 = 32);
  a refusal is the ceiling's terminal (`rungs_closed`), never a park; an unpriced rung passes.
  Past the ceiling a verdict on the SAME bytes stands under moved code: a take's dq report
  (`take_dq --ceiling-spent`) and a PASSING QC report; a QC fail is measured again.
- **SAFETY (closed list, `gate_policy.SAFETY`):** a master over the Short length or with no
  title card; a line not heard; an unjudged or stale take; loudness out of band after the
  leveller; a plan BUILDER line; money; publish auth; GPU lost. Only these stop a spent-clock
  episode (`SAFETY: <name>` parks by its name). Sound cues, gaps, cut misses and every taste gate
  ship flagged (QC: `ceiling_flagged` + an audit row).
- **Plan battery lines** are tagged BUILDER (a downstream script repeats the refusal --
  `studio/plan_tags.BUILDER`: CONTRACT, G-LIGHT, PLAN GATES, TAKE LENGTH, TAKE BUILDER,
  MOTION hard, G-TAKELINT, CAST BOUND, ACTOR) or JUDGED (everything else, ONE PER TAKE
  included). At a spent clock a JUDGED-only best draft signs keep_best flagged; a BUILDER line
  buys one climb (<= 3 unpriced rungs), then `SAFETY: plan_builder`. Plan rungs are priced
  (improve 240 s, model_tier 90 s).
- **QC order:** the cheap rows first; Whisper only on a master that can still pass (at a spent
  clock: whose failed rows are all flaggable). An unmeasured line (`lines: null`) is not heard.
- **Boundary stop:** `autopilot.py pause --at-boundary`; the run stops between steps, rungs,
  grids or takes and exits `paused_at_boundary` (read as PAUSED, never a stop).
- **G-FRAME (advisory):** MCU face < 0.15, close < 0.25 of the frame height (D9). Never a wall.
- **The reader** (`panel_content` / `take_content` / LOOK-STATE): one seeded, cached read. A
  cached refusal is never re-read; only a redraw escapes it.
- **MASTER-EYE content = the panel gate's J5** (2026-10-11): `master_eye.content_faults` judges each
  frame by `pc.judge_staged` (last-daylight hour, shoulder +1, legacy crowd in words), never its own copy.
