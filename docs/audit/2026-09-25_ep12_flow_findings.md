# Episode 12 through the episode department: findings

2026-09-24/25. WotW chapter XII ("Weybridge and Shepperton") was driven
through `episode.py` and its twelve steps to test the new department end to
end. This file lists what the run found. Each item is FIXED (with the commit)
or OPEN (with what fixing it needs). Numbers are the order they were found.

## Fixed (test first, on master)

| # | What broke | Fix | Commit |
|---|---|---|---|
| 5 | `step_02_plan` run alone resolved to the screenplay stage (both stages have a `step_02_plan`) | the folder names the stage | 64a8fc3 |
| 6 | a writer draft the Episode contract refused raised inside the agent's parse and killed step 02 before the improve loop | a ValidationError is a refusal round | 4c0f5ec |
| 7 | the writer saw only the last round's refusals and traded one fault for another | every refusal so far goes back | 787ba1e |
| 8 | the writer skill never stated the 16-word where+light wall or the banned pace words | said outright in `agents/skills/episode_writer.md` | ceec663 |
| 13 | steps 09 and 10 were "done" when their files existed: a re-planned shot was never re-rendered, the master never re-cut | step 09 asks `take_currency` per card; step 10 asks the master to be newer than takes, `placed.json`, `heads.json`, the card | f9c9465 |
| 18 | step 08 died when a panel checker found faults (exit 1) instead of feeding the panel judge | `checked()`: exit 1 with a rewritten verdict feeds the judge | 598562c |
| 19 | a plan edited after its signature was "grandfathered" (a timeline beside it) and never re-judged | only a plan with no `plan.verdict.json` is grandfathered | 8ca900c |
| 1 | step 01 asked for `--cast` by hand though the analysis lists each chapter's people | the chapter's individuals from the analysis, protagonist first | 08243ce |
| 20 | the panel eye asked Qwen3_VQA for 64 tokens; the node's floor is 128 | 128 | cc0d187 |
| 21 | GroundingDINO (LayerStyle) crashed twice on newer transformers (`get_head_mask`, the attention-mask dtype) | two-line patch in the node, `.bak_2026-09-24` beside it (outside the repo) | -- |
| 25 | the leak embedder sent `image`; the workflow's input is `image_1` | `image_1` | 0b3a29e |
| 26 | `image_embed.json` is a TODO placeholder, treated as installed; every take crashed | a TODO node class is not an install | 6c2898e |
| 27 | take_verdict handed the identity gate SegmentReports where sample indices belong | `sample_starts()` | 4fe9bbf |
| 28a | the identity gate crashed on faces with no sheet to compare | 'not measured' | e8359be |
| 29, 30 | a take checker that found faults (exit 1) killed step 09 and the take ladder's retake rung | one shared `take_ladder.measured()`, fresh-verdict rule | 3cb7053, dd44b32, 313743f |
| 31 | the head-cut rung never fired: its leak measure needs the missing DINOv3 | `take_leak.step_leak`: the one switch in the first second, calibrated on 290 takes (heads 0.85-1.17, others <= 0.62, wall 0.75) | 1c99d43 |
| 32 | an interrupted render left a new graph beside the old video, and currency read the take as current | a graph >60 s newer than its video is an unfinished render | 82c291c |
| 34 | `stills.json` outlived a retake: T19 was stilled at 07:09, retaken at 08:03 and passed, and every cut kept holding the panel, so QC failed the edit | a still row stamps `decided`; `assemble.stills_of` drops a row whose take is newer; `stills.json` is a step-10 input | 7157cc7 |

## Open -- needs a decision or more than a code fix

| # | What | Why it is open | What would fix it |
|---|---|---|---|
| 4 | the writer's "local tier" is a paid OpenAI model (`gpt-5.6-luna`, reasoning off) | owner cost decision in `models.yaml` | more reasoning, or edit-the-last-draft rounds; the writer never converged in 3 runs on ep12 |
| 9 | each writer round redrafts the whole plan from scratch | design | hand the previous draft back with the refusals and ask for an edit |
| 2 | the analysis registered no hussar lieutenant and no orchid man for ch12, and registered `god` as a minor character (ch11, ch13 bind him) | analysis-stage data | re-run the casting pass for those chapters; mark invoked names as non-physical |
| 2b | analysis character rows carry no gender; a newly bound character gets `None None` until named by hand | analysis-stage data | a gender field in the profile writer |
| 28b | the identity gate is armed but gets no sheets in the runner | calibration | `sheets_of()` is wired and held back: on 34 face takes (ep10-12) the armed gate with sheets failed 3 CORRECT takes (ep11 T11, ep12 T02 STRANGER 0.29-0.42; ep10 T17 DRIFT 0.72) and caught nothing; recalibrate STRANGER/DRIFT on stylised, soot-dark, turned faces, then hand the sheets in (one line in `take_verdict.measure`) |
| 12 | the take-prompt length lint runs at step 06, after the lines are voiced; ten ep12 prompts were short | order | a cheap prompt-length estimate in step 02's battery |
| 16 | the panel lettering (ink) check reads small dark flying fragments as text (ep12 shot 19, two seeds) | calibration | let the content gate's own `text` answer confirm an ink flag before it fails a panel |
| 23, 24 | the render ceiling is per RUN, not per episode (a resumed run gets a fresh budget); step 08's new judge overran its 20-min share by ~50 min | design | persist the unit's spend across runs; re-price the panel judge's share |
| 11, 17 | two sessions share one checkout: one `uv run` re-synced the venv under the other's tests and half-removed Pillow; one ComfyUI queue timed a 600 s wait out | tooling | a lock around `uv sync`, `--no-sync` in the runner, a GPU lease the runner holds |
| 22 | the judges and measures were built on fakes and never run live before this episode (items 20-31 above) | process | run each new measure once on a real input before arming it |
| -- | ep06 T01, published, opens on 12 frames of the pit wide before its mirror close (a head leak the new step measure finds) | a published episode | a `heads.json` entry for ep06 and a re-cut, if the owner wants it republished |
| 33 | `heads.json` is not bound to the render it trims: a retake keeps the old head | design | stamp each head with the take's graph hash; drop it when the take changes (the same rule as 34) |
| 35 | QC's edit gate compares every segment against its take, so a genuine still (the ladder's terminal rung) can never pass QC | design | the gate reads `stills.json` and matches a still segment against its panel's push, not the take |
| 36 | the MASTER ladder's `recut` rung re-assembles the same takes with the same heads: ep12 master_iter5, iter6 and iter7 are byte-identical, so two rungs spent ~40 min re-making the bed and re-running QC and moved nothing | design | skip a recut when no cut input changed since the master (step 10's `inputs()`), go straight to `retake_shot` |
| 37 | the master eye's first verdict is neither printed nor written before the ladder climbs; the log shows re-cuts with no reason until the rubric is signed at the end | observability | print each verdict's faults (kind, where) as the gate judges it |
| 38 | the `retake_shot` rung never fired on ep12 (the faces fault named shot 6) and nothing in the log says why -- most likely the run's RENDER ceiling had less than the rung's 9-min price left | observability + 23/24 | print a skipped rung and its reason; persist the unit's spend (23/24) |
| 39 | ep13: a VoiceDesign emotion clip is another voice (no seed); the narrator's shouts fell to 0.25-0.54 similarity | fixed: the delivery rides as IndexTTS2's emotion vector on the speaker's own clip (49ebac0) | -- |
| 40 | the similarity gate judged one-second lines: slices of the narrator's OWN voice scored 0.07-0.58; the pace wall (fitted on 6-word lines) refused 3-word lines | fixed: under 2 s similarity is recorded not gated (e94901d); under 5 words pace is not measured | -- |
| 41 | the posture check read a bound tag ('curls lying on a low forehead') as the shot asking for a man lying down | fixed: bracketed tags are not a posture (27a0d27) | -- |
| 42 | step 07 said 'skipped: output exists' over grids drawn from an older plan; panels.py then refused | fixed: the board asks panels.py's staleness question (commit after 27a0d27) | -- |
| 43 | step 04 and step 06 refusals reach the runner log as 'exit 1' only; the script's own reason is not captured | tooling | capture the child's last lines into the refusal |
| 44 | 2026-09-26 ~05:33 local: ComfyUI died on 'CUDA error: unknown error'; nvidia-smi: 'GPU is lost. Reboot the system to recover' | hardware/driver | reboot; ep13 resumes at step 07 (board) |
| 45 | no gate compares one character ACROSS panels: ep13's board had the narrator bald in 5 panels (his sheet wears a hat; the tag named no hair) and the curate two colours (row flaxen, sheet brown); caught by eye | gate | MEASURED: a face embedding does NOT separate it -- the bald-narrator panels score 0.72-0.80 against his sheet, ep12's good narrator panels 0.65-0.93; both curate looks 0.67-0.93 (facenet reads the face, not the hair). The fix is a HAIR answer in panel_content's closed vocabulary (bald / hair colour of the main figure) judged in code against the cast row |
| 46 | a detached runner launched from cmd.exe has no ffmpeg on PATH (the bash PATH has C:/Users/vishn/bin) | tooling | put ffmpeg on the system PATH, or have the runner resolve it from a config |
| 47 | the plan critic is nondeterministic: the same plan drew different 'invented' faults run to run | fixed in part: a fault must name a head noun absent from the shot's own source spans (`backed()`) | a fixed seed / temperature 0 on the critic's model |
| 48 | `panel_content` re-reads all 25 panels on every EYE_PANELS rung (~15 min a rung), so step 08 ran 28 min against a 20-min share and deferred every run | fixed: shares re-priced inside the same 5 h ceiling (58bbe5c) | read only the panels the rung redrew |
| 49 | the EYE_PANELS `reprose` rung writes its cure into plan.json; re-running a hand-authored plan.py (ep13, to fix six closes) overwrote those cures, so the reprosed grids read stale and were redrawn from the plain prompt | process | a hand plan.py carries the ladder's cures forward (or refuses to overwrite a plan.json newer than itself) |
| 50 | the EYE_PANELS ladder ended keep_best (terminal) on 9 framing faults; 7 were real: every close's binding line listed trousers, braces and socks, and six shots said 'sitting ...' | fixed: a person whose every picture is a close is bound by items above the chest (9cb4609); the six picture clauses name head and shoulders | -- |
| 51 | the ep12 plan no longer regenerates byte-identical (`test_a_plan_script_regenerates_its_plan[ep12]`) since the curate/tripod row edits of 2026-09-26 | data drift | regenerate ep12's plan.json or pin the test to the rows it was built from |
| 52 | step 08 said 'skipped: output exists' after step 07 redrew 13 grids: the old panels still carried their verdicts | fixed: a grid newer than the last cut is a refusal (d0c4fea) | -- |
| 53 | the EYE_PANELS judge reads a hands insert whose chest is in the frame as 'medium' (ep13 shot 12, three draws) | calibration | an insert asks whether the hands are the picture's subject, not whether a torso shows |
| 54 | step 09 checks all 25 takes on the CPU (~1 min each) before it re-renders any; the GPU idled ~20 min on ep13 | design | pipeline: queue a failed take's retake to ComfyUI as soon as its check fails, while the next take is checked |
