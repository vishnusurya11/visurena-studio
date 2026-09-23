# Pipeline audit, 2026-09-22

Episode 9 production was stopped so that this could happen. Five read-only
agents audited the pipeline from five sides: the DQ gates, the prompts, the
skills, structural fault classes in the code, and the published pictures
looked at frame by frame. Their findings are merged and ranked here.
Duplicates are collapsed.

The most serious claims were checked by hand before they went on this list:
the truncated character text, the broken style line in all 20 ep08 takes, the
CFG 1.0 grid sampler, the crowd regex, the retitle default, the unread
panel_dq.json, and the published frames of ep07 and ep08.

**The one pattern under most of it: the gates exist, but they quietly stand
down.** The people and clone checks are off on about 80% of shots. The cast
gate fails every plan, so everyone reads past it. The take gate has measured
identity zero times in 76 published takes. The content checks cannot block
anything. The next biggest pattern is **words written before, or apart from,
the picture they describe.**

---

## Tier 0 — decisions only the owner can make

| # | Decision | Why it is yours |
|---|---|---|
| D1 | **Episodes 7 and 8 are public with visible faults.** ep08 33–40 s: the newspaper's headline reads "NEWSPAPER BOY", a cast label printed into the picture. ep08 40–48 s: four identical copies of the shopman. ep07 88–92 s: two pictures stacked in one frame, split by a white line, with the narrator clean-shaven in that shot. ep07 124–129 s: a dark jacket turns into a white shirt mid-shot. ep08 62–106 s: the bridge and carriage shots are almost black on a phone. | YouTube cannot swap the file under an existing video. A fix means a new upload that loses the URL and views, or leaving it as it is. |
| D2 | **The cast sheets and the places are in two different styles.** The sheets are smooth 3D renders and the location wides are brush-stroke paintings, and the takes come out as a mix of both. Re-drawing every sheet in the location recipe would fix it. | It changes how every character looks, partway through the series. |
| D3 | **1x1 grids.** Your rule is a 2x2 minimum ("1x1 is useless"), written only in a docstring. ep09 used four 1x1 grids, two 2x1 and one 3x1, because its setups hold 2, 3, 5 and 8 shots. | Keep the rule and refuse these grids, or allow the exception. |
| D4 | **One camera position per place.** "One wide per location" has turned into one vantage per location. ep08's four junction shots are the same view down the platform (layout correlation 0.77–0.86), and the pit shots correlate 0.82–0.88. A second designed view per place, such as the reverse that already exists for three places, would fix it. | It touches your 2026-09-18 one-picture rule, the one made after two views of one observatory became two rooms. |

## Tier 1 — gates that exist but stand down

Fix these first. They are pure code with no GPU, and they protect everything downstream.

1. **The crowd regex has no word boundaries, so the people and clone checks are off on about 80% of shots.** The boundaries were removed deliberately after a heredoc turned `\b` into a backspace byte. Now "compartment" matches `men`, "a hand's breadth" matches `hand`, and the cast rows copied into plans match `man`. This is how the four identical shopmen passed at 100/100. The same fault is in `panel_content`'s OTHERS/WORN/PRINTED lists: "surface" matches `face`, "chair" matches `hair`, "papered wall" matches `paper`. *Fix:* take crowd from `setup.crowd` plus a new `Shot.extras` count, not from the prose, and use real word boundaries written by a patch script.
2. **The missing-face rule only fires at close sizes.** ep09 panel 12, an "empty garden" planned with two people, passed. *Fix:* fire whenever `planned > 0` and no cast face is found (medium and wider through the VLM count).
3. **CAST BOUND fails every WotW plan** (7, 18, 6 and 24 hard faults on ep06–09), because it was written for the other book's bust-and-card casting. So `plan_check` exits 1 every time and nobody reads the exit code. *Fix:* a binding rule for one sheet per character, then make the driver refuse on exit 1.
4. **The content gates live in a session temp folder.** They return no exit code, count an unread panel as clean, and never write their verdict anywhere the upload refusal reads. *Fix:* move them to `scripts/episode/`, exit 1 on any fault, unread picture or zero rows, and write HARD rows into `panel_dq.json` and `T*.dq.json`.
5. **`takes_r2v` never reads `panel_dq.json`,** so a failed panel goes straight to the GPU.
6. **Gates that pass on nothing:** `panel_check` (0/0), `take_dq` with no records, `qc`'s takes rollup never compares against `shots.json`, `failed_takes` with no dq files, and `voice_qc` (0/0). *Fix:* every runner asserts that the number of items judged equals the plan's count.
7. **Every CLI defaults the episode to 1.** takes_r2v, assemble, episode, say_lines, timeline, respot, qc and more do this. `takes_r2v wotw --retake=3` silently re-renders **ep01's** T03 on the GPU. *Fix:* one `episode_arg()` that refuses when the number is missing.

## Tier 2 — wrong answers waiting for the next episode

8. **Book-wide location rows were rewritten for ep09.** I did this with `_ep09_anchor.py`. A retake of any earlier episode on the Common now stages ep09's daylight pit. *Fix:* the plan's setup names its own view, and the rows keep every view.
9. **`refs.json` is stamped `chapter: 9` and nothing checks the chapter,** so an ep08 retake would get ep09's wardrobe.
10. **Take currency compares only the prompt text.** ep05 has 16 refs and ep07 has 6 panels that changed after their takes rendered. Those takes still count as "current" and would be skipped. *Fix:* compare the staged image digests, the seed and the frame count.
11. **`placed.json` freshness is checked only in `plan_check`.** Eight other readers load it unchecked. The fingerprint leaves out the measured line lengths, and ep01–07 have no fingerprint at all.
12. **Grid names are not scoped to the episode.** ep10's "pit" and "lawn" grids would overwrite ep09's in ComfyUI's output folder, and the exporter would then cut the wrong episode's panels. The manifest is also written before the render and carries no plan hash.
13. **Wrong series text on publish.** `youtube_retitle` defaults to `--total=14` (the other book's count), so it would title WotW videos "Ep NN/14". `title.py` falls back to "Sherlock Holmes".
14. **`plan.json` was patched directly for ep01, ep03 and ep04.** Re-running those plan `.py` files silently reverts fixes that already shipped.
15. **Absolute paths are stored in 197+ `T*.dq.json` files,** in `voice_qc.json` and in `story.md`. CLAUDE.md forbids this.

## Tier 3 — prompts

16. **Character text in grids is cut at 600 characters.** The narrator's ends "Straw boater w --", so the hat that identifies him never arrives. *Fix:* bind by name plus 3–5 distinguishing items from the row, since the sheet in the slot already carries the face.
17. **The style line is broken in every ep08 take.** It reads "…1894, is gaslight, black shadows" because `SKIP_WORDS` lacks "is", "that" and "was". It also says "Horsell, Surrey" at Woking junction, in the carriage and in the village street, because `where` is episode-wide. *Fix:* the missing skip words, and `where` taken per setup.
18. **The grid sampler runs at CFG 1.0, so the negative prompt is never computed.** Every "no beard, no duplicates, no lettering" placed there has done nothing. *Fix:* enable CFG 2.5–4 with real negatives, or delete the negative so nobody believes it works.
19. **Grid prompts are 626–1472 words and the subject starts 31–62% of the way in.** A one-panel prompt still says "storyboard/grid/panel" 13 times. *Fix:* order the prompt as layout line → subject-first panel blocks → one line per cast member → one place line → one style line. Budgets: 1x1 ≤ 150 words, 2x2 ≤ 350.
20. **Wide geometry is pasted verbatim into 35 of the 78 non-wide shots in ep06–09.** This emptied ep09's close-up. *Fix:* a HARD plan lint.
21. **"This panel is the place alone" is emitted for panels whose prose names a person** (12/23 empty-cast shots in ep06, 8/17 in ep08). *Fix:* a lint, plus "an unnamed soldier (no reference)" in place of the sentence.
22. **42–47 amount phrases per episode** go to a model measured to obey 0 of 16. *Fix:* strip them and keep only "with small/large amplitude".
23. **Storyboard words and run-ons reach the video prompt.** "The panel cutting him at the chest" appears in 20+ lines, and there are run-ons like "…across his chest working the platform".
24. **Take prompts run about 726 words, with the place stated three times,** plus a 65-word boilerplate soundscape whose "murmur of people" invites extras. *Fix:* the place once, a soundscape of 15 words or fewer, the appearance of 8 words or fewer, and the saved words spent on action.
25. **Sheet prompts** lead with 36 words ending "Cinematic film still of". 28 of 86 say "photographic realism", which contradicts the style, and face features such as the moustache come mid-list. *Fix:* format → who → face features → clothes → backdrop.
26. **Location prompts put the defining state late.** The lawn's fire arrived about 55 words in and was not drawn. *Fix:* state → hour and light → 3 landmarks, under 60 words, with a lint that the first 20 words name the light and the state.
27. **A 13-year-old boy is called "this man"** in take prompts.

## Tier 4 — new checks for what nobody measures

28. **Same-setup layout correlation.** Flag two shots of different planned size that correlate above 0.75, and run it on the panels before any take. (Measured medians: ep07 0.23, ep08 0.35, ep09 0.44.)
29. **Face embeddings.** Use them for identity against the sheet (measured on none of the 76 takes), for clones in one frame, and for a sheet's face turning up on an extra. Calibration: ep07's clean-shaven narrator and ep08's shopman clones should fail; ep08's newspaper boy should pass.
30. **OCR on takes.** Any word of 4+ letters fails, and a cast or setup name is a certain failure (ep08's "NEWSPAPER BOY").
31. **A detector for two pictures stacked in one frame.** ep07 S14 scores 1.00; every other shot scores 0.31 or less.
32. **A darkness wall.** The black share is already computed and never enforced (T14 0.96). Fail above 0.75, or below mean 25, unless the plan marks the shot a silhouette.
33. **Read every reference picture back against its prompt.** Check facial hair in both directions, the must-appear event nouns (fire, smoke, pit), and the landmark.
34. **Plan contract checks:** a shot's faces are a subset of its setup's cast; the shot's hour agrees with the setup's hour; plan colour words agree with the sheet (the plan says hussars "in dark blue" and the sheet is green).
35. **Smaller checks:** set continuity within a setup (hue); a shot that changes into another object; near-still shots; posterisation; QC checks for runtime, 1:1 frame and title card; cuts found on brightness-normalised frames.
36. **Thresholds fitted to night:**
    - The tiled wall of 0.90 sits beside clean night panels at 0.867.
    - The sharpness control is always horsell_common.
    - A "dark" in the prose ("dark brows") sends a day shot to the night control.
    - The hour check only runs one way.
    - `parse` fills a missing key with a default instead of raising, so it fails open.

## Tier 5 — skills and structure

37. **The episode skill describes the wrong pipeline.** Its header says "no storyboard", and its one command block is the other book's (a paid storyboard step, a Sherlock title card). Five of the ten steps that really run are absent from it. *Fix:* a `SKILL.md` of 350 lines or fewer holding the real chain, plus `GATES.md`, `LESSONS.md`, `GRIDS.md` and a `SCARLET_ARCHIVE.md`.
38. **Promote the session drivers into `scripts/` with tests.** These are grids, panels, panel_dq, panel_content, take_content, fit_beats and places. Today the storyboard stage cannot be re-run after this session ends.
39. **The skill and memory contradict themselves.** They disagree on the push-in rule, the publish rule, the voice similarity floor (0.70 vs 0.65), and composed frames vs panels.
40. **The two skill copies have drifted, and `master` is 52+ commits behind `wotw-refs-poc`.**
41. **Guard tests** so each fault class cannot come back:
    - every CLI refuses a missing episode
    - no drive letter in any library artefact
    - no bare `next(genexpr)`
    - derived files are read only through checked loaders
    - every writer's path is some reader's path
    - every place's anchor file exists
    - plan models use `extra="forbid"`
    - the plan `.py` regenerates `plan.json` byte-identically
    - gates refuse empty input
    - the escape scan also covers `.sh`, `.md` and the skills

---

## Order of work

1. **Tier 1, and #8 and #7 from Tier 2.** These are gates that stand down and writes that hit the wrong episode. No GPU, no spend. Each fault gets a failing test first.
2. **The rest of Tier 2, then the Tier 3 prompt fixes.** Measure each against the ep06–08 prompts on disk before and after.
3. **Tier 4 checks,** each calibrated on the published episodes, where the known faults above are the positives.
4. **Tier 5 skill rewrite last,** so that it describes the fixed pipeline rather than the one being fixed. Drivers are promoted along the way.
5. **Episode 9 resumes** on the fixed pipeline. Its plan, refs and audio stand; its grids and panels are redrawn.

## Publishable

The prompt findings generalise beyond this repo. They are measured, with
counts, and they suit a short write-up or benchmark note, "What
reference-conditioned image and video models ignore":

- negations
- amounts (0 of 16 obeyed)
- details buried mid-sentence
- subject position in long prompts
- a disabled negative branch at CFG 1
