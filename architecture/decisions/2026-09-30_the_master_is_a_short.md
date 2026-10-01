# 2026-09-30 — The delivered master is a Short (owner: "these are hard requirements")

**Trigger.** ep14 went public and YouTube filed it as a regular VIDEO, not a Short.
The owner: "This should have been short not video .. fix it" and "these are hard
requirements … it has to be short .. the format has to be 1*1". Measured: the master
ran 182.58 s; YouTube classifies a square upload as a Short only up to 3:00.

**Finding (two audit agents, 2026-09-30).** Every runtime wall in the pipeline capped
the PICTURE at 180 s (contract band, timeline refusal, G-RATE's hardcoded 180) while
assemble appends a ~4.46 s animated title card + 0.25 s chip AFTER the picture.
ep01-13 delivered 139.6-175.8 s — ep14 was the first plan to cut past 175 s of
picture, so the gap never showed. qc measured `seconds: 182.58` and judged it by
nothing; the upload and the public flip check no duration or aspect at all, and
`--override` waives `qc.passed` at upload (ep14's upload carried one). The 1:1 rule
was enforced only at the plan battery (G-ASPECT); nothing ever opened the final mp4.

**Decision.** Both hard requirements are held at every stage, derived from ONE place:
- `episode_spec.SHORT_WALL_S = 180.0`, `TAIL_ALLOWANCE_S = 6.0` (card + chip +
  margin), `MAX_SECONDS = SHORT_WALL_S - TAIL_ALLOWANCE_S` (174) — never restated.
  The contract validator, the writer's brief (`plan_brief.band`), G-RATE and the
  timeline refusal all pick the derivation up automatically.
- `episode_spec.short_refusal(master_seconds)` is the one sentence about a delivered
  master; assemble refuses before the name goes on the file, and qc's verdict fails
  on `seconds` over the wall or unmeasured.
- Both publish doors (upload and the public flip) judge THE FILE ITSELF:
  `youtube_publish.file_refusals(file_facts(master))` — length ≤ 180 s AND
  width == height — unwaivable past every override and stale report.
- SKILL/GATES/LESSONS and the handbook now state the requirement (the handbook still
  said 9:16).

**ep14 repair.** Beats/codas trimmed 25% through `write_plan` (the contract defended
the button's 1.0 s breath), timeline re-placed 177.88 → 172.7 s, re-assembled as
`master_iter8.mp4`: 177.42 s, 1536x1536, sha8 994ee36f. Re-QC'd and re-uploaded as a
Short; the 182.58 s upload (NJnkwmNbe_Y) set private first, with the reason in the
ledger.
