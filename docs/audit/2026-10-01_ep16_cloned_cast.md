# ep16: the cloned cast — three-agent root cause (2026-10-01)

Owner's report: "all renders are shit with duplicates and wrong and multiple same
character". Paused mid-run; three read-only agents dissected the graphs, the
staged refs/prompts, and the frames. Verdicts converge.

## The brick

The four NEW cast rows (narrators_brother, miss_elphinstone, mrs_elphinstone,
lord_garrick — the first principals ever added mid-book) were written by
`scripts/refs/cast_rows.py` with bare ids: the only character rows in refs.json
with **neither `display` nor `gender`**. Every fault class derives from that
omission, amplified by chapter 16 being the exodus (crowds in every shot).

## The cascade (all verified in artifacts)

1. **Women defined as men.** `adopt_names` keys WOMEN on `gender=="female"`;
   with the key absent, `noun()` says "man". Every multi-face prompt defines
   the Elphinstones as "this man alone"; speaking women get "His mouth shapes
   every syllable" (T10, T13).
2. **Surname collision.** `called()` binds the bare shared surname
   "Elphinstone": 8 takes staged a sheet the plan never declared; T22 tags
   Mrs as the picture of Miss; in 5 takes the same person exists once as a
   pinned subject and once as a named stranger — duplicates by construction.
3. **Staged-but-uncited brother.** Bare-surname branch of `called()` lacks
   `(?i)`, so "\bBrother\b" never matches "the brother"; in T07/08/12/16/21/25
   his sheet is a defined subject tagged zero times — a free face H3 must
   place somewhere (the "unused slot is a doll" class).
4. **Crowds with no pins — the amplifier.** All 26 shots carry a `crowd`
   clause ("many fugitives"), extras 0-1, no distinct extra looks (the
   standing walk-ons-get-their-own-look rule never reached grid prompts).
   The GRID drawer filled crowds with cast copies (3 brothers, duplicate
   purple Misses; Mrs's white look dropped — grid stage), and H3 minted more
   clone crowds even behind clean panels (render stage). ep15: zero crowd
   clauses — the class never fired before.
5. **Leaked cure text.** panel_ladder's clones-cure sentence ("Each person in
   the picture is a different man…") and a placeholder ("The named subject…")
   sit verbatim in plan S08/S12 frame fields and open those prompts.
6. **Machinery innocent.** Graphs node-identical to ep15 (Singularity UNET,
   turbo LoRA 1.0/0.7, no example.png, staged bytes = repo bytes, single
   NVMe model resolution). Benign find: the v1 plan compiler writes `take`
   as 1/2 so seeds are consecutive, not 7919-strided.
7. **Red gates ridden over.** Panels 08/15/19 FAILED, takes T10/19/21 FAILED
   — then the budget deferral dead-state ("cannot pay; nothing signed") and
   the resume's "skipped: output exists" shipped past known-red verdicts.
   One genuine judge miss: shot_21's panel (brother twice, "0 lookalikes").

## The fix list (owner's go pending)

(a) display+gender on the four rows; a face row without gender REFUSES at
bind, never defaults to "man". (b) shared-surname binding: longest distinct
phrase, case-insensitive. (c) strip leaked sentences; purge the eye-tag
identity dialect (100 "(grey eyes)" tags vs ep15's 0) back to full row
constants; MARKS refuses fragment constants. (d) one crowd truth: a crowd
clause requires distinctly-described extras; stager and content gate read the
same faces. (e) a FAILED panel/take invalidates its step's done() so resumes
recut instead of skipping. (f) the headroom budget fix (already written)
replaces the unresolvable deferral. Then recut bad grids/panels, re-render
the ruined takes.

Clean takes kept: T00, T03, T13, T24. Frames evidence in the session
scratchpad (ep16/T*_a|b.png); the clones at their origin:
`episodes/ep16/storyboard/grids/ep16_grid_grass_lane_rescue_2x1.png`.
