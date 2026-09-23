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
| CELL GATES (`studio/cell_gates.py`) | G-ANCHOR: no sideways truck on a medium-or-closer person leaning on / sitting on / standing at the set. G-AIM: every noun a move starts on or aims at is in `at_rest`. G-HAT: one hat worn and held in one picture. G-PLACE: a frame landmark the setup's words and drawn picture (`refs/pack.jsonl`) lack | HARD. Calibrated over ep01-09: G-ANCHOR fires on 7 shots of ep05-09, 5 visible faults (ep09 T02 the owner's, T10, T20; ep07 T13; ep08 T14), silent on the walker ep08 T05 |
| TAKE BUILDER | `takes_r2v.refuse_long_shots` / `refuse_still_motions`, run on the plan | HARD |
| WRITE | a plan script writes `plan.json` only through `episode_home.write_plan`, which refuses a plan the contract refuses and leaves the old file (guard test) | HARD |
| MOTION, MARKS, ACTOR | motion wording; the last clause moves a limb or head; staging marks | HARD |
| CAST BOUND | a book cast from sheets: every cast member has a row and a sheet on disk | HARD |
| QUOTE | at most 8 consecutive book words in a line | HARD |
| ONE PER TAKE / TAKE LENGTH | every shot is its own take, inside the 8 s budget | HARD |
| TIMELINE | `placed.json` is of this plan AND this voice (`episode_home.load_placed`) | HARD |
| SHEET TEXT | the Scarlet book's paid-sheet check; skipped for sheet books, and a crash is printed, never counted silently | HARD where it applies |
| G-STORY advisories, G-NAMES, G-RATE, G-MOTION, L8 pace, G-SUNSPLIT, G-LIGHT-SIDE, G-HAT with "bareheaded" | caption-like lines, first hearing of a name, speaking rate, motion wording, a face split under a sun, the light side of a face, a hat clash the picture already resolves | advisory |

## Timeline — `timeline.py` (HARD)

The measured runtime must sit in 120-180 s, and every line at its shot's start
plus the handle (`misaligned`). The fingerprint covers only timing inputs, so a
reworded frame does not stale it.

## Grids and the panel cut — `grids.py`, `panels.py` (HARD)

- **grids:** the chapter stamp; the shot count equals cols x rows; at most 3
  slots. The cast is dressed from the same chapter row as the take
  (`cast_refs.row`); a guard refuses a chapter given as a number.
- **panels:** a grid is stale when the prompt it would be given now, or any
  picture it would stage, differs from its manifest's `inputs`. Older
  manifests fall back to `drawn_from` (plan fields), then to the plan hash. A
  shot in two grids or none is refused. The seam shave takes an edge gutter up
  to 48 px or a thin pale run within 120 px, with darker picture on both
  sides; the panel is then cropped square, never stretched, and written only
  when its pixels changed.

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
| `take_dq.py` | `T<NN>.dq.json` | frozen start and share, cut landing, churn, zoom, face at end, look, pulse, lip-sync lag and WER; **held** (a person pinned while the set slides: lock = 1 - face travel / scenery travel, hard at 0.75 over 100 px, only when the plan keeps the subject in place); **jump** (lowest similarity between consecutive frame signatures, hard below 0.50: a switch of picture, whatever the brightness) | HARD rows as marked in the report. held: ep09 T02 1.01 over 1055 px and T10 1.05 fail; eligible passes top out at -0.42 (n=2 fires against 3 passes: thin). jump: T15's two faults 0.08 and 0.16, every accepted ep08/09 take 0.83 or more |
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
- **any take without a current dq AND content verdict;**
- **no title card** (`title_card` false).

A take that failed and spent its retake budget does not fail the master. That
is the owner's call, and it was measured.

## Publish — `youtube_upload.py`

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

## Known gaps — not measured yet

- **framing:** a medium close drawn as a full figure passes (face 0.112
  against published 0.101-0.3). It needs a closed-vocabulary FRAMING answer
  from the content reader, judged against the planned size.
- **a take against its own panel:** every panel-comparison row reads "not
  measured (no cell)" on refs-only takes. Wired to the panel, off-board > 0.80
  and last < 0.30 would catch T14's transformed lawn (take-gate audit).
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
