# Architecture

The studio read as a company. **Code is management** (runners and step scripts decide
order, hand out briefs, assemble, count and gate). **Agents are specialists** (one
brief in, one typed object out; no agent edits a file or reads another agent's
answer). The registry `stages.yaml` is the org chart the code runs; the Step is the
brick (`docs/ARCHITECTURE.md`).

| where | what |
|---|---|
| [index.html](index.html) | **The main architecture page.** Open it in a browser. Tab *Current*: the book → screenplay org chart (who reports to whom), an animated walk-through of one book's run, the roster. Tab *Future*: the proposed big-studio shape — the debate's verdicts, the five-division org chart with built / partial / missing / slot states, unit-of-work grammar, the owner gates, an animated future run, the order of work. Published copy: https://claude.ai/artifact/6HCxs36mcpFk2TJS389QXr |
| [decisions/](decisions/) | Architecture decisions, one dated file each, with the debate that produced them. A decision that the owner has ruled on also gets its line in `docs/DECISIONS.md`. |
| [plan/](plan/) | Plans and trackers for the work that follows a decision. One file per initiative; status at the top; checkboxes per step. |

## Departments today (2026-09-24)

| department | registry | leader (code) | agents | spends |
|---|---|---|---|---|
| Analysis — asserts what the book says | `stages.yaml: analysis`, 6 steps | `analysis.py` → `scripts/analysis/step_0N_*.py` | book cartographer, ingest validator, scene breakdown (1st AD), script supervisor, casting director, story analyst, dialogue editor, extraction auditor, entity resolver, gap filler, journey tracer, profile writer | text model only |
| Screenplay — invents, per (book, target) | `stages.yaml: screenplay`, 5 steps | `scripts/screenplay/step_0N_*.py` | story editor, screenwriter, shot designer, adaptation auditor | text model only |
| Audit bench | — | `scripts/*/audit_locations.py` | location auditor | text model only |
| Trailer | `stages.yaml: trailer`, 10 steps | `trailer.py` + `.claude/skills/trailer` | skill-driven | $0, local GPU |
| Episode | not in the registry yet | `.claude/skills/episode` + `scripts/episode/*` | skill-driven | $0, local GPU |
| Shorts | not in the registry yet | `.claude/skills/shorts-*` (8 Claude skills) | showrunner, story, screenwriter, art, cinematographer, sound, editor, publisher | Higgsfield credits, gated |

## Decisions

| date | file | status |
|---|---|---|
| 2026-09-24 | [decisions/2026-09-24_future_departments.md](decisions/2026-09-24_future_departments.md) + [stages_future.yaml](decisions/2026-09-24_stages_future.yaml) | PROPOSAL — the big-studio shape: five divisions, one registry stage per format line, unit grammar, seven owner gates. Awaiting the owner. |

## Plans

| date | file | status |
|---|---|---|
| 2026-09-24 | [plan/2026-09-24_registry_departments.md](plan/2026-09-24_registry_departments.md) | NOT STARTED — the ten commits that turn the proposal into stages, if approved |
| 2026-09-24 | [docs/audit/2026-09-24_skills_book_neutral_plan.md](../docs/audit/2026-09-24_skills_book_neutral_plan.md) | NOT STARTED — scrub every book name and episode id out of the skills; guard test |

## Rules this folder inherits

- Skills, agents and docs name no book, character, episode or take.
- One checkout, on master; everything book-specific lives under `library/<book>/`.
- A page here that changes what the studio *is* needs a decision file; a decision the
  owner rules on gets its `docs/DECISIONS.md` line.
