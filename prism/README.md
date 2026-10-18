# Prism

Prism is a growing library of visual styles for local text-to-image models, with measurements. Every style is checked on the same five pictures across three models.

- **`styles/<id>.json`**: one card per style. A card holds:
  - what the look is: lineage, and concrete traits for line, shading, palette, lighting, faces, backgrounds, texture and camera
  - the model-neutral `style_words`
  - drifts to `avoid`
  - sources
  - optional per-model words
  - a verdict (best model, status)
- **`models/<model>.json`**: one prompt-writer guide per model:
  - the workflow and its fixed values
  - the prompt template (`{style}`, `{subject}`, `{camera}` order)
  - the word ceiling, and whether negatives work
  - evidence-backed findings
  - a `system_prompt` for an LLM that writes prompts in a held style for that model
- **`subjects/dracula.json`**: the fixed eval subjects: 1 character, 1 location and 3 scenes. Each varies shot size, angle, lens, light and figure count.

| Step | Command |
|---|---|
| Brief the researchers | `uv run python -m prism.research brief` |
| Merge new cards | `uv run python -m prism.research merge <inbox>` |
| Plan (renders nothing) | `uv run python -m prism.render plan` |
| Render (owner's go) | `uv run python -m prism.render go --go` |
| File a model's writer parts | `uv run python -m prism.writer <writer.json>` |
| Engine times (after a run) | `uv run python -m prism.timing` |
| Board (+ one-file copy with thumbnails) | `uv run python -m prism.board --portable` |
| File picks | `uv run python -m prism.verdicts <picks.json>` |

The run loop is described in `.claude/skills/prism/SKILL.md`. Renders and the board live in `docs/audit/prism/`, which is git-ignored.
