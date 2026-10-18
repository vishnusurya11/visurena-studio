---
name: prism
description: Grow and measure Prism, the studio's style library - research NEW visual styles (anime first, at most 3 live-action) with web agents, merge only styles the library does not hold, plan every style x 5 subjects x 3 local models (Krea2, FLUX 3 Klein, Qwen-Image 2.1), render ONLY on the owner's go, and build the dark comparison board. Use when adding styles, re-running style research, rendering the style eval, or picking a style/model for a new book.
---

# Prism: the style library

Code `prism/`, cards `prism/styles/<id>.json` (one per style), prompt-writer guides
`prism/models/<model>.json` (one per model, each with its `system_prompt`), fixed
subjects `prism/subjects/dracula.json` (1 character, 1 location, 3 scenes; shot sizes,
angles, lenses, light and figure counts all differ). Renders, plan, timings and the
board live under `docs/audit/prism/` (git-ignored). Contract: `prism/catalog.py`.

## One run (repeat any time; each run adds only what is new)

1. **Brief.** `uv run python -m prism.research brief > docs/audit/prism/research/<run>/brief.md`
   - It lists every held style; agents never redo one. `<run>` is the next run id it prints.
2. **Research.** Launch 2-4 background web agents (tokens only; say the count first).
   - Each gets the brief, a disjoint list of NEW styles, and the card shape.
   - Each writes one card per style into `docs/audit/prism/research/<run>/candidates/`.
   - Mix: anime first. Live-action stays at 3 or fewer unless the owner says otherwise.
   - Agents also list styles worth a later run in their report. Keep that backlog in `docs/audit/prism/research/backlog.md`.
3. **Merge.** `uv run python -m prism.research merge docs/audit/prism/research/<run>/candidates`
   - It validates against the contract and refuses a held id or name and broken cards.
   - Fix a refused card in the inbox and merge again.
4. **Plan.** `uv run python -m prism.render plan` writes `docs/audit/prism/plan.json` and prints the jobs to render.
5. **ASK THE OWNER.** Nothing renders without a go. Give the job count, the models, and an ETA from the warm medians.
6. **Render, on go only.** The series must be paused or the queue empty; render refuses a busy ComfyUI.
   - Run `uv run python -m prism.render go --go`.
   - It renders model-major (each model loads once), skips what exists, and logs `timings.jsonl` with the cold load marked.
7. **Engine times.** After the run, `uv run python -m prism.timing` puts ComfyUI's own execution time on every row.
   - The render's wall clock is quantised by the client's 5 s poll: every model read 10.1-10.2 s on r001.
8. **Board.** `uv run python -m prism.board` prints the board's full path.
   - The owner picks a best model per style there and clicks "Copy picks".
9. **Verdicts.** `uv run python -m prism.verdicts <picks.json>` sets each card's `verdict.best_model` and status.

## Rules learned

- Within one model, only the style words move across styles. The subject form and seed are shared, so the board compares looks.
- Each model has its own trained caption form: Krea2 is 90-200 words, style first, recapped last; FLUX 3 Klein is 180-320 words in generative voice; Qwen 2.1 is 330-480 words in observer voice. One shared subject text would put two of the three outside their form. So a writer agent per model follows that guide's `system_prompt` and writes:
  - the style-neutral subject forms (`forms.<model>` on the subject set)
  - each card's `models.<model>.style` and `recap`
  Files go in with `uv run python -m prism.writer <writer.json>`. A new style needs its three writer parts before it renders.
- A camera line names no lens millimetres: on Krea2 they pull an anime style photographic (contract-checked).
- Krea2's built-in LLM `refine_prompt` stays OFF for the eval: it rewrites our words, so it would test its words instead of ours.
- All three run at cfg 1. A negative prompt does nothing there; say an `avoid` item as a positive description.
