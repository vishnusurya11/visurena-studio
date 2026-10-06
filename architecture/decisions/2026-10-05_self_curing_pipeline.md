# The pipeline cures its own plans, pictures and publish — no hands between launch and the Short

**Date:** 2026-10-05 · **Status:** approved (owner, 2026-10-05: "i need python scripts
instead to do that using the open api call .. the budget is $3 for episode .. update the
scripts to implement them by itself") · **Research:** ten specialist specs under
[research/2026-10-05_self_curing_pipeline/](research/2026-10-05_self_curing_pipeline/) ·
**Tracker:** [../plan/2026-10-05_self_curing_pipeline.md](../plan/2026-10-05_self_curing_pipeline.md)

## The problem, measured

ep17 and ep18 both shipped — but only because the session agent (Claude) hand-edited
plan.json, refs.json, prop cards and grid files between steps. Every class of hand fix is
listed in the research specs with its evidence. The writer deferred twice per episode on
faults with mechanical cures; the lint and the timeline refused AFTER signing on faults
visible at plan time; the panel judge passed "faces 3/2"; duplicates (a second captain, a
second curate, twice) were caught only by a human-grade eye on frame strips; every hand
edit lapsed the plan signature and paid the writer again (~$0.2–0.4/relaunch), and the
writer re-added the very clauses the hand had removed.

## The ruling

Judgement the hand supplied becomes an **API call inside the scripts** (through
`studio/llm`, any tier, every call behind `guard_spend` and the **$3/episode** ceiling).
Everything deterministic becomes **pure code**. Ten areas, each a gate + cure pair in the
existing battery/ladder pattern:

| # | Area | Gate | Cure |
|---|------|------|------|
| 1 | Setup light + phantom people | G-LIGHT (fixed dispatch), G-PHANTOM | sentence surgery; workhorse rewrite |
| 2 | Camera moves | G-MOVES, M2 | catalog-based head rewrite; LLM fallback |
| 3 | Source quotes | G-SOURCE | span-snap to chapter text (free) |
| 4 | Machines/creatures | G-STAGE | card-name substitution, auto prop sheets |
| 5 | Clone text | body-part + two-positions gates | clause surgery; LLM rewrite; re-run after every writer round |
| 6 | Speech holes | projected-silence gate | hold trims; LLM micro-lines |
| 7 | Take-prompt lint | lint folded into the battery | substitution tables at the right data layer; LLM fallback |
| 8 | Duplicate vision | faces N>M hard; G-TWIN (local VLM) | seed bump → 1×1 isolate → flag; retake once → keep-best |
| 9 | Orchestration | — | clean plans re-sign free; retakes re-judged; dead clock → terminal; comfy retry; beds contract |
| 10 | Publish | existing upload gates | metadata + sign-off generated from measured data; one API call |

**Proof of done:** ep19 runs through `scripts/episode/drive.py` to a published public
Short with zero hand edits, under $3.
