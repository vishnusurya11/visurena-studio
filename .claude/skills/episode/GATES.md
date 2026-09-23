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
| G-VARIETY / G-MOVE / G-STORY | size mix, travel amounts per size, first dialogue within the first quarter | HARD |
| MOTION, MARKS, ACTOR | motion wording; the last clause moves a limb or head; staging marks | HARD |
| CAST BOUND | a book cast from sheets: every cast member has a row and a sheet on disk | HARD |
| QUOTE | at most 8 consecutive book words in a line | HARD |
| ONE PER TAKE / TAKE LENGTH | every shot is its own take, inside the 8 s budget | HARD |
| TIMELINE | `placed.json` is of this plan AND this voice (`episode_home.load_placed`) | HARD |
| SHEET TEXT | the Scarlet book's paid-sheet check; skipped for sheet books, and a crash is printed, never counted silently | HARD where it applies |
| G-STORY advisories, G-NAMES, G-SUNSPLIT, G-LIGHT-SIDE | caption-like lines, first hearing of a name, a face split under a sun, the light side of a face | advisory |

## Take prompts — `takes_r2v.py <book> <n> --from-refs --prompts` ($0, no GPU)

The take lint (`episode_ref_official.check`) runs on every built prompt:

- the length per block (240-360 words);
- the style line: 16 words at most, no stray capitals (place names count as names);
- banned props (for example gloves, where the book gives bare hands);
- a last frame reaching the prompt;
- mid-sentence fragments.

Run it before any audio or picture exists. **HARD.**

Staging: a take stages only its setup's declared cast plus the shot's own
faces (`takes_r2v.staging_candidates`). Candidates used to be every row in
`refs.json`, matched by the last word of a display name. Six published takes
staged the wrong person that way (ep05 T19, ep06 T08, ep07 T09/T19/T24/T26).

## Cast rows — `cast_refs.chapter_refusal`

`refs.json` holds one chapter's clothes. The take builder, the grids and both
content checks refuse rows stamped for another chapter. **HARD.**

## Panels — two gates, and the takes refuse without both

| script | writes | measures | calibration |
|---|---|---|---|
| `panel_check.py` | `storyboard/panel_dq.json` | people against `faces`+`extras` (faces need detector confidence 0.8 or more); missing face at medium or tighter (a back view the plan asks for is exempt); sharpness against the house control for the setup's hour; ink (small bright marks by their rim); tiling | ep06 29/29, ep08 20/20; the only failures are real (ep07 13 stacked, ep09 12 empty). Ink: worst clean panel 0.00417, caption band 0.01009, wall 0.007 |
| `panel_content_check.py` | `storyboard/panel_content.json` | a vision model LISTS people, copies, lettering, hour, landform and subjects; code judges the list against the plan, the place's `landform` and the book's `dq_rules.json` | ep09 19/23, all four failures real (see `docs/calibration/content_gate.md`) |

`takes_r2v` refuses when either verdict is missing, fails a shot, skipped a
shot, or is older than a redrawn panel. **HARD.**

## Takes

| script | writes | measures | kind |
|---|---|---|---|
| `take_dq.py` | `T<NN>.dq.json` | frozen start and share, cut landing, churn, zoom, face at end, look, pulse, lip-sync lag and WER | HARD rows as marked in the report |
| `take_content_check.py` | `T<NN>.content.json` | the panel content rules on 3 frames past the head leak, each read alone | HARD |

Take currency: a take is kept only when it was rendered from the same prompt
AND the same staged picture bytes (content-addressed names in its
`graph.json`).

## QC — `qc.py <book> <n> --engine=r2v`

QC fails on any of these:

- loudness or true peak out of range;
- a planned cut missing;
- a line not heard;
- a silent gap over 6.0 s (it names the silent shot the gap is made of);
- an unmeasured edit;
- **any take without a current dq AND content verdict.**

A take that failed and spent its retake budget does not fail the master. That
is the owner's call, and it was measured.

## Publish — `youtube_upload.py`

It refuses on failed takes, content failures and unjudged takes, unless
`--override` names each fault. The title comes from the book's own
`series`/`display_title`/`episodes` in `source/book.json`, never from a
default.

## Known gaps — not measured yet

The audit's Tier 4 checks that are still to be built:

- face-embedding identity against the sheet, and clone detection that does not
  depend on the reader noticing;
- OCR (the "NEWSPAPER BOY" headline passed, because an insert on a paper is
  allowed lettering);
- a detector for two pictures stacked in one frame (ep07 S14 scores 1.00,
  every other shot 0.31 or less);
- a darkness wall (the black share is computed and never enforced);
- layout correlation between shots of one setup (one camera position per
  place);
- reading every reference picture back against its prompt.
