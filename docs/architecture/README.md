# Architecture — the studio as a company

The studio's agents are read as an organisation: **code is management** (runners
and step scripts decide order, hand out briefs, assemble, count and gate), **agents
are specialists** (one brief in, one typed object out; no agent edits a file or reads
another agent's answer). The registry `stages.yaml` is the org chart the code runs.

| file | what it is |
|---|---|
| [story_department.html](story_department.html) | Two tabs. **Current:** book → screenplay, the org chart of the 17 agents in `agents/` (who reports to whom), an animated walk-through of one book's run, the roster. **Future:** the proposed big-studio shape — the debate's verdicts, the five-division org chart with built/partial/missing/slot states, unit-of-work grammar, the seven owner gates, an animated future run, the order of work. Open it in a browser. Published copy: https://claude.ai/artifact/6HCxs36mcpFk2TJS389QXr |
| [future_departments.md](future_departments.md) | PROPOSAL (2026-09-24, awaiting the owner): the debate record, the final structure per division, owner gates, the mapping of every existing script and skill to its slot, migration order, publishable packages. |
| [stages_future.yaml](stages_future.yaml) | DRAFT of the new registry stages (`refs`, `episode`, `shorts`, `publish`, `analytics`, `promo`, five empty slots) in `stages.yaml`'s conventions. Not applied. |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) | The brick (the Step), the four layers, the load-bearing rule, gate policy, "one folder". |
| [../DECISIONS.md](../DECISIONS.md) | Dated owner decisions behind the architecture. |

## Departments today (2026-09-24)

| department | registry | leader (code) | agents | spends |
|---|---|---|---|---|
| Analysis — asserts what the book says | `stages.yaml: analysis`, 6 steps | `analysis.py` → `scripts/analysis/step_0N_*.py` | book cartographer, ingest validator, scene breakdown (1st AD), script supervisor, casting director, story analyst, dialogue editor, extraction auditor, entity resolver, gap filler, journey tracer, profile writer | text model only |
| Screenplay — invents, per (book, target) | `stages.yaml: screenplay`, 5 steps | `scripts/screenplay/step_0N_*.py` | story editor, screenwriter, shot designer, adaptation auditor | text model only |
| Audit bench | — | `scripts/*/audit_locations.py` | location auditor | text model only |
| Trailer | `stages.yaml: trailer`, 10 steps | `trailer.py` + `.claude/skills/trailer` | skill-driven | $0, local GPU |
| Episode | not in the registry yet | `.claude/skills/episode` + `scripts/episode/*` | skill-driven | $0, local GPU |
| Shorts | not in the registry yet | `.claude/skills/shorts-*` (8 Claude skills) | showrunner, story, screenwriter, art, cinematographer, sound, editor, publisher | Higgsfield credits, gated |

Planned next: departments for episode video generation and for publishing / post /
promotion, designed to the same shape as analysis and screenplay. Their design goes
in this folder as `future_departments.md` plus a second tab in the HTML.

## Rules this folder inherits

- Skills, agents and docs here name no book, character, episode or take
  (`docs/audit/2026-09-24_skills_book_neutral_plan.md`).
- One checkout, on master; everything book-specific lives under `library/<book>/`.
