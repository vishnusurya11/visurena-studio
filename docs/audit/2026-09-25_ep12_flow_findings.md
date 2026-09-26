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
