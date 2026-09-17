# Episode fixtures for the quality gates

Copied from `library/` (gitignored) on 2026-09-16 so the gates can be proven on the
episodes the owner judged: **ep05 and ep07 looked right; ep08 and ep09 looked worse.**
`docs/analysis/ep08_ep09_why_worse.md` has the ten-reviewer measurement behind every
threshold. A gate that does not fail ep09 and pass ep07 on these files is not the gate.

- `epNN_plan.json`          the plan as built
- `epNN_take_prompts.json`  every take's prompt, refs, faces, anchors, seconds
- `epNN_sheet_prompts.json` every sheet's first-attempt prompt

`ep10_plan.json` was copied 2026-09-16 (docs/analysis/ep10_dq_synthesis.md, section B): the
plan whose lead's words went to the narrator, whose turn shot holds the antagonist, and whose
tail runs 11.25 s without a line. The story gates built from it fire here and stay quiet on ep05/ep07.
