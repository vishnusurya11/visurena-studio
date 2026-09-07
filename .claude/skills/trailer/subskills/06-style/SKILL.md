---
name: trailer-style
description: Visual register - the house look, what actually decides it, and the only two doors out.
---

# Style

One slot is authored per book and it is 80 characters wide. `palette_for(register, setting)`
LOOKS UP story.json's register in a nine-row table (`trailer_refs.py:336-345`) at step 02, then
SPLICES `story.setting`, free LLM text `default "", max_length=80` (`step_01_story.py:39`),
between the grade and the light phrase (`:355-359`), unchecked (`step_02_refs.py:202`): 2 of
Scarlet's 19 words. Nine registers, eight distinct lines, all ending `; practical period light sources.`

TOTALITY IS NOT NEUTRALITY. The table is total over the enum (`set(Register.__args__) ==
set(PALETTES)`, `test_trailer_refs.py:45`), so no book ships without a grade line - but THREE ROADS
END ON ONE ROW: an unknown register falls to `procedural` (`:357`, `test:51`), step 01's ladder
terminates on `procedural` (`step_01_story.py:29`) and `fallback` hard-codes it (`:126`), and
`procedural` is byte-identical to `detective` (`:342-343`). The failure grade IS the Sherlock grade,
written into story.json as a choice; only learnings.jsonl tells them apart (`action:"procedural",
terminal:true`, `ladder.py:79`), and no step reads it. That path is also what makes a step return
`""`: `gate` keeps `violation["thesis"] = judged.thesis` (`:143`) and drops the rest, and `fallback`
(`:124-127`) has no `setting` parameter - so a book refused on SYLLABLE COUNT ships a grade with no
period though the model had answered the period. A FALLBACK MUST SALVAGE THE FIELDS THAT PASSED, NOT
ONLY THE ONE THAT FAILED; `thesis_from` (`:104-121`) already does it one field over, cutting a
refused refrain to a clause the contract takes instead of shipping null (run 10). MEASURED: all 6
step-01 rows this run are `thesis has 8 syllables; max is 7`, two at attempt 2 of 3, and `climb`
goes terminal on budget after attempt 1 too (`ladder.py:82-86`).

THE PALETTE SETS HUE; NOTHING LETS IT SET LIGHT. Its light clause is one clause; every prompt
carrying it also carries a FIXED block asking for even fill: `SHEET_FRAME`'s `even soft frontal light
with both eyes lit, shadowless` (`:25-31`) before it in `character_prompt`, `PLATE_FRAME`'s `Deep
focus, even natural light.` (`:40-44`) after it in `location_prompt`, `h3_prompt.py:131-133` keeping
detail in the shadowed side of every clip, `assemble.py:122-123` sending the batch to one exposure.
Five rows of nine (gothic, tragedy, procedural, detective, adventure) ask for deep shadow or hard
light and are contradicted inside their own prompt string; comedy's `bright even daylight` is the
only line no constant contradicts - the house look IS a comedy grade wearing the register's three
colour names. It travels three channels, each keeping less of it than the last.

- **Image - words.** `character_prompt` and `location_prompt` are the only users of
  `trailer_refs.STYLE` - anamorphic widescreen, film grain, a physical 35 mm still - plus palette,
  frame block, unlettered surfaces. ORDER IS THE LEVER AND NO TEST HOLDS IT: the book's own words
  lead in `character_prompt` (`:66`) because STYLE leading gave seven identical Victorian gentlemen,
  and trail FOURTH of five in `location_prompt` (`:72`), the trailing position that same docstring
  measured as "barely registered" - so a reorder reverts a measured fix in silence, on the one
  artifact H3 reads light from. Verbatim is OURS: unrewritten only because `load_workflow` reads
  `inject`, never the manifest's `optional: {refine_prompt: true}` (`comfy.py:23-31`).
- **Video - 19 words against 313.** `take_values(..., style=refs_doc["palette"])` is `body[0]`
  of the H3 document (`step_07_clips.py:481`), the same 19 words for all 22 Scarlet shots; the
  rest is 313 words of fixed literal prose, of which 77 are pure look direction (one motivated
  source, dust and haze, aged materials - `h3_prompt.py:131-137`), not one derived from the
  register: swapping a book to `comedy` cannot brighten its clips. The PLATE is the light
  anchor - H3 is told the location is `attribute_transfer` of "the palette, materials, period
  and quality of light" while the sheet carries all but its light (`:69-75`) - and it is the
  LOWEST-priority slot: `bound_slots` takes characters first and truncates to two
  (`build_clips.py:75`), so 22 of 22 Scarlet beats bind a plate only because `build_plan.py:46`
  writes `cast=[principal] if principal else []` - 20 beats with one cast member, 2 with none,
  never two. The first beat given two principals - a dialogue is two people - loses the plate and
  with it the only sentence in the document that names quality of light; h3_prompt's two-subject
  branch (`:64-71`, no attribute_transfer) has never reached a model.
- **Cut - neither, and the match misses.** A verbatim grade string in every prompt still gave
  clips spanning 42.9-96.6 frame-average luma, so `assemble.py:122-123` matches every segment to
  ONE target: the median clip's mean (floored at 32/255) and the median deviation. Both are read
  from the WHOLE take (`:112`) while the cut never shows a take's first 2.6s (`segment_start`,
  `head=HEAD_TRIM`): 18-72% of the frames they average - 57.2 of 162.2 rendered seconds - are H3
  opening on the reference image, a share set by SHOT LENGTH (B00/B06 72%, B20 18%), not by look.
  MEASURE THE LOOK ON THE FRAMES THE CUT SHOWS - the repo holds that rule for the OTHER
  statistic, `frames_of` sampling past HEAD_TRIM so the identity gate cannot pass on a picture of
  its own answer (BUILD 39); `luma_stats` never got it, and which way that pushes each clip is
  unmeasured. One pair for 22 shots, applied LAST: whatever the palette wins upstream is removed
  here. The lever is the TARGET, not the floor - grade to the act's median, or do not grade at
  all. And it misses even that target: `grade_to` solves `mean*contrast + brightness*255 =
  hero_mean`, but ffmpeg's eq pivots at mid-grey - `contrast*(v-0.5)+0.5+brightness`. MEASURED on
  a gray plane, input 60 at contrast 0.75 brightness 0.10 comes back 102, where that model
  predicts 70. A graded clip lands at `hero_mean + 127.5*(1-contrast)`: a flat clip (contrast
  clamped to 1.35) up to 45 luma DARKER than the hero, a contrasty one (0.75) up to 32 BRIGHTER -
  the grade spreads the batch it was written to close. The only convergence test
  (`test_clips_converge_on_the_hero`) passes deviation == hero_deviation, the one case where that
  error term is zero.

## What is established

- **No style LoRA is running.** `enable_lora` and `refine_prompt` are both `PrimitiveBoolean
  false` in `image_krea2_turbo_t2i.json` and `build_refs.generate` passes neither: every sheet
  and plate is base `krea2_turbo_fp8_scaled`. The one wired LoRA, `krea2_darkbrush` at 0.8,
  appends the trigger "muted minimalist sketch style" - non-photoreal, not the house look.
- **The palette is live on video, write-once on the image.** `palette_for` runs on every step 02
  (`step_02_refs.py:202`) and refs.json's `palette` and every record's `prompt` are rewritten
  from it - but `generate` returns an existing png before rendering (`build_refs.py:70-71`) and
  `location_records` never deletes one, so no plate is ever re-rendered: a corrected register
  repaints H3's 19 words, leaves every plate on the grade it was born with, and records a prompt
  that made no picture here. Sheets differ only where `render_sheet` unlinks on `fresh` (`:81`).
- **Nothing gates the look.** qc.json has 32 metrics, none a picture metric; the run's learnings
  rows span twelve gate kinds (identity through read) and none is style; BUILD.md has no style
  row; and the palette's only two tests read the returned STRING (`test_trailer_refs.py:42,48`),
  never a pixel. A look regression ships silently. One thing gates the look-TEXT and it stops at the
  authored slot: `MODEL_TEXT` (`:352`) puts all nine grade lines under `affirm.scan`, but every
  fixture composes them with `palette_for("detective")` and NO setting (`test_affirm.py:126-129`):
  no line carrying an authored `setting` is linted, and `setting` is the only part a book writes.
  `Tone.__post_init__` RAISES on any field a model wrote (`music_tone.py:165,202-207`) one channel
  over; `StorySpec.setting` has a `max_length` and no validator.
- No look reaches the plan: `step_06_plan.py` and `trailer_plan.py` never mention palette or
  style, `trailer_shot.shot_prompt` is tests-only, and `studio/shot_grammar.py` is the live one.

## The open question

A non-photoreal register can enter only through the reference image or `enable_lora`, both
UNTESTED; Krea 2 is Qwen-Image lineage (CLIP `qwen3vl_4b_fp8_scaled`), so FLUX Redux,
PuLID-FLUX, IP-Adapter and Kontext do not load against it. The free experiment is the PLATE,
not the video words: delete `Deep focus, even natural light.` from `PLATE_FRAME`, DELETE that
plate's png, and re-render at 8 turbo steps - rerunning step 02 alone renders nothing (above).
Only if the clip off it is still flat is `h3_prompt.py:131-137` the cause. No pixel measures this
yet: the sheets' 82.4-96.7 mean luma against the plates' 38.3-132.1 is a backdrop difference.
That render answers a second question free: move `described` to the front of `location_prompt`.
