# Why the plan takes hours now and took minutes before (2026-10-01 verdict)

Owner's question, on ep15's ~4.5 h plan fight: "how did you do this for the first 10
episodes and Sherlock?" Three experts (plan historian, deferral forensics, writer I/O
analyst) read the git history, every episode's learnings/timing/verdict files, and the
writer's actual inputs. Unanimous.

## The finding

**The rules didn't change. The writer did.**

- Every contract rule that refused ep15 (length floor, button beat, rule 5, numbering,
  dialogue dial) has existed since 2026-09-10 — before ANY episode shipped. G-LIGHT and
  G-SIZE since 09-16, G-AIM since 09-23.
- The fast era (SiS ep01-14, WotW ep01-11) had **no step 02, no ladder, no critic, no
  paid writer**. The operator session — a strong reasoning model with the GATE SOURCE
  CODE in context — authored each plan as a script, ran `plan_check` (free, seconds),
  and fixed every fault in one sitting. ep10's plan carries a docstring listing "WHAT
  TODAY'S GATES ASK OF THIS PLAN". Zero PLAN ladder rows exist for those 25 episodes;
  their plans are grandfathered.
- On 09-24, commit `004d219` handed the pen to gpt-5.6-luna at `reasoning_effort: none`,
  seeing only a brief that stated ZERO picture rules (until `06664a2`, written DURING
  ep15), inside a ladder that (until `33f11b4`/`414a3a6`, same night) discarded 1-fault
  drafts and judged stale ghosts. A blind writer re-discovered pre-existing rules one
  paid refusal at a time.

## The measured bill

| | fast era (25 eps) | ep12 | ep13 | ep14 | ep15 |
|---|---|---|---|---|---|
| PLAN ladder rungs | 0 | 5 | 58 | 60 | **82** |
| PLAN hours | 0 | 0.23 | 1.86 | 3.30 | **4.58** |
| deferral passes | – | 0 | 5 | 6 | **15** |

- The battery is **97%** of ep14-15 plan time (contract 37% + G-gates 59%); the
  critic/judge is 851 s total. The cost is REJECTED DRAFTS, not judging.
- The whack-a-mole, measured: battery counts swing 1 → 49 → 1 → 57 rung to rung — a
  rewrite that clears the G-gates breaks a contract rule and vice versa. Only 4 of 72
  contract-clean rungs had a single gate blocking.
- Every DEFER restarts a fresh 4-rung ladder (~1,100 s) on the next run; ep15 paid for
  15 ladders.
- The writer's call: ~125-195k chars of brief (camera catalog 25k on every call;
  places up to 41k), one call asked for a whole 20-shot plan, median 284 s, ~57-82
  rungs. ep15 was also the worst-supplied chapter: the screenplay has ZERO elements
  for ch15 (ep16 has 441).

## The fix (built 2026-10-01)

**The plan returns to being AUTHORED — the fast era's method, formalized:**

1. **One writer ladder per episode, ever.** `PLAN_LADDERS_MAX = 1`: the paid writer
   gets one 4-rung ladder as an optional first draft. A second deferral refuses with
   "author the plan in session against plan_check" instead of burning another ~18 min
   ladder — ep15's 15 ladders can never recur. (The deferral aside still carries the
   best draft to author FROM.)
2. **The authoring loop is the documented path** (SKILL): author/repair plan.json
   directly, run `scripts/episode/plan_check.py` (free, seconds) until "clean -- lines
   may render", using the gates' own template phrases (the ep15 session proved every
   gate cure is formulaic: light directions, head fractions, pace words, head swaps,
   coda arithmetic). The ladder-night fixes stay: rules in the brief (06664a2),
   converged drafts never discarded (33f11b4), the judge judges the disk (414a3a6).
3. **Plans may be authored book-level, before episodes run** — same standing design as
   title cards: the inputs (chapter, screenplay, cast rows, gates) all exist at bind
   time; an authored plan costs ~minutes per chapter in one sitting.

Prior verdicts this extends: 2026-09-30_five_hour_plan.md (P1 "mechanical-first plan
ladder" — superseded by authorship), 2026-09-30_rounds_debate.md.
