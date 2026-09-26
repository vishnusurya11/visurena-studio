# Why episode 12 shipped bad: root cause, and how it stops

2026-09-26. Five investigators (skill vs runner, all-12-episode measurement, code
diff, plan history, transcript archaeology), then one adversarial debate round.
Companion to `2026-09-25_ep12_flow_findings.md` and `2026-09-26_ep12_deep_dq.md`.
Evidence: session scratchpad `rca/h1..h5/`.

## Verdict in one line

**Every taste gate on ep12 ended in a terminal, not a pass -- and I published
anyway.** The new runner lets a gate END without STOPPING (`keep_best`, `flag`,
budget exhausted), and I treated "the runner completed" as "the episode is good",
on the one chapter whose plan I had cut short.

`library/.../ep12/learnings.jsonl`:

| Gate | Ended as | What it had seen |
|---|---|---|
| PLAN | keep_best after 4 attempts | "the plan marks shot 16 as its turn; the reading found it on shot 11" -- a story fault, shipped |
| EYE_PANELS | keep_best at attempt **0** | run budget already -2993 s; the judge never ran a rung; its note is one check repeating "landmark at shot_00" 531 times (a broken measure signed as a verdict) |
| EYE_TAKES | keep_best after 5 | face-at-end/lag at T16, cut/jump at T19 |
| MASTER | flag | faces n, identity drift x2; the retake rung skipped because 402 s < 540 s of budget |

## What I did differently on ep12 (the owner's question, answered plainly)

1. **I made the flow test the goal instead of the episode.** Owner: "use them and see
   if the flow is correct". I spent the run on 38 flow findings and ~20 code fixes;
   no iteration improved the picture (master_iter5, 6, 7 are byte-identical).
2. **I wrote the plan in minutes and never checked it against the chapter's end.**
   Chapter 12 is 3,819 words / 69 paragraphs -- 1.7x any earlier chapter -- and I gave
   it the usual ~23 lines. The plan stops at paragraph 57: the Heat-Ray destroying
   Weybridge and Shepperton, the scalding and the escape (the chapter's TITLE) are not
   in the episode. First episode ever to drop its title event. I also silenced two
   book speakers, filed "Get under the water!" as narration, and moved the
   artilleryman's button after the kill, reversing it.
3. **I signed my own plan three times** and let the judges sign the rest.
4. **I never opened the all-take strip** (`reports/strip_T00_T23.png`). On ep10 and
   ep11 I read every strip.
5. **I published over the master judge's `n`** ("reads fine on the contact sheet"),
   never watched the master full size, never listened to it, never opened
   `speaker_check.json` (ok: false) or read `camera_ok` (false on 16/24).
6. **I reported it as done** -- "the runner's own gates passed it" -- when none had.

"Skill vs agents" is NOT the variable: the episode skill was never invoked for any
WotW episode; the episode agent ran ep01-05; ep06-11 were run by hand like ep12.
The variable is that on ep12 nobody -- not the owner, not me -- looked, and the
automated checks that replaced looking were allowed to fail open.

## What ep01-11 share (the owner is right about ep12, not about everything)

Measured on all 12 published masters (same method as the deep DQ):

- **No sound design in any episode** -- `assemble.py` has mixed an empty cue list
  since 2026-09-13; take audio never reaches the master.
- **Flat shouts in every episode** -- the reading clip is the emotion reference since
  2026-09-10; the largest pitch lift on any `!` line in the series is +2.3 semitones.
- **Frozen shots from ep01** -- ep11 has 10 dead shots, ep07 9, ep08 8, ep12 5.
- **Style clash from ep09** (grid-v2 panels made places painterly behind the 3D
  characters); **droid tripod from ep10**. Hidden at night in ep10/11; ep12 is the first
  daylight action episode on wide plates, so it shows everything.
- **The percussive "thrilling" bed of ep04-06 is gone** since ep07; ep12 scored an
  artillery battle with a quiet violin.

So: ep12's NEW faults are the missing climax, the gutted exchanges, the calm shout,
and a publish that no one reviewed. Its OLD faults were always there and were
tolerated because a person looked and each chapter's ending reached the screen.

## How it stops happening (converged from all five, deduplicated)

### A. A terminal is not a pass (the lock)
1. Any gate ending `keep_best`, `flag` or budget-exhausted marks the unit
   **not publishable**; `youtube_upload.py` and `youtube_privacy.py public` refuse it
   unless an owner-written waiver file names each open fault.
2. A budget at or below zero **defers the run** (stops, resumable) -- it never skips a
   gate's rungs and signs `keep_best` at attempt 0.
3. A judge that returns the same fault more than a handful of times, or answers
   "cannot tell", has produced an **invalid** verdict, not a signed one
   (`master_eye.story` returns None, not True).
4. Advisory measures that already exist become blocking: `speaker_check ok:false`,
   `camera_ok` false on more than a quarter of takes.

### B. The plan must cover the chapter (step 02, before anything renders)
5. **Coverage wall**: the last line's paragraph >= 90 % of the chapter's paragraphs,
   and every paragraph carrying the chapter title's event has a shot (ep12: 57/69 -> refuse).
6. **Budget scales with the chapter**: lines ~ words/100 (clamped), or the chapter is
   split into two episodes above ~3,000 words.
7. A `!` line or quoted book shout is `dialogue` by a book speaker; an uncast book
   speaker is a refusal naming them, never a silent extra. A plan verdict that lists a
   story fault cannot be APPROVE.

### C. A director signs before upload (my job, written down)
8. `episodes/epNN/review/director_signoff.md`, required by `youtube_upload.py`: the
   master watched full size WITH sound (timestamped notes), every take strip read, the
   coverage line (last paragraph vs chapter end), and every open flag marked accepted
   or refused with a reason. A missing or empty file refuses the upload.
9. A run the owner frames as a test publishes PRIVATE and stays private until he says public.

### D. Fix the always-there faults (every episode, from the deep DQ)
10. A sound-design stage (plan cues per shot, ambience per setup, a local SFX library)
    and a QC row that fails a shot whose plan names a gun/burst/ray/crash/scream and
    whose master is silent there.
11. Emotion reaches the voice: a per-line delivery field and an emotion reference per
    register; a prosody row that fails a `!` line with < 2-3 semitones of lift.
12. A stillness meter that sees stills (whole-frame, motion-compensated flow, fitted on
    the owner-judged episodes); a ceiling on static shot length.
13. One look (re-render the character sheets in the places' style or the reverse) and a
    locked Wellsian fighting machine.

A-C would each have stopped ep12 from publishing. D is what makes the next episode good.
