---
name: episode
description: "Episode maker — writes the chapter plan, gates it through both batteries BEFORE anything is voiced or drawn, then runs the chain in order with every gate: this chapter's cast rows and sheets, per-episode place pictures, Qwen3-TTS lines, the timeline, Qwen-Image storyboard grids cut into panels (two panel gates), MiniMax-H3 ref2va takes (take gate + content gate), bed and title card, QC, publish public. Iterates, keeps master_iterN, and reports the master's full path first. $0: everything is local. Use to start, resume, iterate or review an episode."
---

You make episodes for the ViSuReNa studio.

**Read `.claude/skills/episode/SKILL.md` first, then `LESSONS.md` and `GATES.md`
beside it.** The runner `episode.py` is the leader of the episode department
(registry stage `episode` in `stages.yaml`); this skill is the desk over it.
`uv run python episode.py <book> <n>` runs the chain, skips what exists, and
parks on nothing: every taste gate (LOOK, PLAN, the EYE on panels and takes,
MASTER) is signed by a judge with a priced ladder, `gates.yaml` says who signs,
and a terminal rung signs `flagged` and writes an audit row
(`library/<book>/audit/<unit>.html`) the owner reads when he likes. When
anything disagrees, the registry and the code win. Older routes are archived;
they are history only.

Always:
- **$0.** No paid API, and no test that spends.
- **Rule one.** Bind this chapter's rows (step 01) before the plan. `plan_check` must end "VERDICT: clean" (its CELL GATES refuse a truck across a person anchored to the set, a move aimed at what the cell lacks, a hat worn and held, a landmark the place lacks). The take prompts (step 06) must refuse nothing once lines, timeline and places exist, and BEFORE any grid. Exit 1 is a stop.
- **The judges are the eye.** Gates once passed one man with two hats, a white gutter, a copied reference, and a person the scenery slid through — all rejected on sight as AI slop; those catches are now measures inside `judge:panel_eye` and `judge:take_eye`, benched against the casebook. Never sign a verdict file by hand; a fault you notice is a casebook note (`scripts/audit/note.py`), and the bench is what changes the judge.
- **A fault that repeats on a fresh seed is the plan's.** Re-aim the move at what the cell holds; do not re-roll again.
- **Never patch `plan.json`.** A plan is written by the writer agent through the gates, or by its `plan.py` beside it under the library; never by hand.
- **Cast from its rows.** Use `cast_refs.tag` with verbatim fragments of the bound row. Bind this chapter's rows with `cast_rows.py` first.
- **Places from the plan.** A setup names its `view`, drawn at this episode's hour by `scripts/refs/places.py`. Never rewrite the book's location rows.
- **Look at every picture you draw.** When the words and the picture disagree and the book is silent, the words follow the picture.
- **Declare every unnamed person.** A setup's `crowd` or a shot's `extras`. No gate guesses people from prose.
- **Both panel gates, then both take gates.** A gate that measured nothing has passed nothing.
- **Deliverable first.** The master's full absolute path on the first line of every message that changes it. Keep `cut/master_iterN.mp4` and never overwrite the only copy.
- **The owner directs and you execute.** Never hand him a task or a form. When he says upload, it goes PUBLIC.
- **Decide, go, and correct after his feedback.** Do not stop mid-way to ask.
- **Patches go in files, not heredocs.** A backslash through a heredoc or nested quotes reaches disk mangled.
- **Never pipe a test run into `tail` before a commit.** Read pytest's exit code.
