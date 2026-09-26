# Architecture

The studio read as a company. **Code is management** (runners and step scripts decide
order, hand out briefs, assemble, count and gate). **Agents are specialists** (one
brief in, one typed object out; no agent edits a file or reads another agent's
answer). The registry `stages.yaml` is the org chart the code runs; the Step is the
brick (`docs/ARCHITECTURE.md`).

| where | what |
|---|---|
| [index.html](index.html) | **The main architecture page.** Open it in a browser. Tab *Current*: the book → screenplay org chart (who reports to whom), the desk (the work-order tables, the views, the tick's verbs and the board — `uv run python command_center.py` → http://127.0.0.1:8700, its pages and its order buttons — built C1–C11), an animated walk-through of one book's run, the roster. Tab *Future*: the proposed big-studio shape — the debate's verdicts, the five-division org chart with built / partial / missing / slot states, unit-of-work grammar, the owner gates, an animated future run, the order of work. Tab *Command Center*: the department tables, the standard contract, the drive and the board with its actions — built 2026-09-26. Published copy: https://claude.ai/artifact/6HCxs36mcpFk2TJS389QXr |
| [decisions/](decisions/) | Architecture decisions, one dated file each, with the debate that produced them. A decision that the owner has ruled on also gets its line in `docs/DECISIONS.md`. |
| [plan/](plan/) | Plans and trackers for the work that follows a decision. One file per initiative; status at the top; checkboxes per step. |

## Departments today (2026-09-24)

| department | registry | leader (code) | agents | spends |
|---|---|---|---|---|
| Analysis — asserts what the book says | `stages.yaml: analysis`, 6 steps | `analysis.py` → `scripts/analysis/step_0N_*.py` | book cartographer, ingest validator, scene breakdown (1st AD), script supervisor, casting director, story analyst, dialogue editor, extraction auditor, entity resolver, gap filler, journey tracer, profile writer | text model only |
| Screenplay — invents, per (book, target) | `stages.yaml: screenplay`, 5 steps | `scripts/screenplay/step_0N_*.py` | story editor, screenwriter, shot designer, adaptation auditor | text model only |
| Audit bench | — | `scripts/*/audit_locations.py` | location auditor | text model only |
| Trailer | `stages.yaml: trailer`, 10 steps | `trailer.py` + `.claude/skills/trailer` | skill-driven | $0, local GPU |
| Refs & Cast — the reference bible | `stages.yaml: refs`, 4 steps | `refs.py` → `scripts/refs/step_0N_*.py` | look_back (local VLM); `judge:look` signs `refs/verdict.json` | $0, local GPU |
| Episode — one chapter, one master | `stages.yaml: episode`, 12 steps | `episode.py` → `scripts/episode/step_NN_*.py` | episode_writer + plan_reader (critic); panel reader, Whisper inside the wrapped scripts; judges `plan`, `panel_eye`, `take_eye`, `master_eye` sign PLAN / EYE ×2 / MASTER; no step parks on a person | $0, local GPU |
| Shorts | not in the registry yet | `.claude/skills/shorts-*` (8 Claude skills) | showrunner, story, screenwriter, art, cinematographer, sound, editor, publisher | Higgsfield credits, gated |
| Studio desk — the department tables and the tick (2026-09-26) | `work_orders` + a view per registered stage, `work_steps`, `orders`, `holds`, `v_queue`, `v_attention` | `studio.py tick · queue · verify · board` → `studio/tick.py`; `studio_cli.py` for the owner's hand; every run ticks its own book first (`Tracker`) | none — code only; judges and the owner sign files, nobody types a state | nothing |

## Decisions

| date | file | status |
|---|---|---|
| 2026-09-24 | [decisions/2026-09-24_future_departments.md](decisions/2026-09-24_future_departments.md) + [stages_future.yaml](decisions/2026-09-24_stages_future.yaml) | PROPOSAL — the big-studio shape: five divisions, one registry stage per format line, unit grammar, seven owner gates. Awaiting the owner. |
| 2026-09-25 | [decisions/2026-09-25_command_center.md](decisions/2026-09-25_command_center.md) + [research/](decisions/research/2026-09-25_command_center/) | DECIDED (owner, 2026-09-25) — the Command Center: one work-order row per (book, department, unit), a view per department, standard `in:`/`out:` in the registry and a `manifest.json` across the boundary, tick + pull drive, the local board. Tab *Command Center* on the page. BUILT 2026-09-26. |
| 2026-09-24 | [decisions/2026-09-24_judges_replace_the_eye.md](decisions/2026-09-24_judges_replace_the_eye.md) | DECIDED (owner) — no refs/episode step parks on a person: judges with priced ladders sign LOOK, PLAN, EYE ×2, MASTER as pass or flagged; the owner audits after the fact; casebook + bench + ratchet. |

## Plans

| date | file | status |
|---|---|---|
| 2026-09-25 | [plan/2026-09-25_command_center_build.md](plan/2026-09-25_command_center_build.md) | DONE 2026-09-26 — eleven commits in six waves: the tables, the contract, the drive, the board and its actions |
| 2026-09-24 | [plan/2026-09-24_registry_departments.md](plan/2026-09-24_registry_departments.md) | IN PROGRESS — commits 1-3 and 6 done by the episode build; 4, 5, 7-10 open |
| 2026-09-24 | [plan/2026-09-24_episode_department_build.md](plan/2026-09-24_episode_department_build.md) | DONE 2026-09-24 — refs + episode as registry departments with runners, twelve independent steps, the writer agent, eyes as files |
| 2026-09-24 | [plan/2026-09-24_judges_replace_the_eye_build.md](plan/2026-09-24_judges_replace_the_eye_build.md) | DONE 2026-09-24 — casebook, bench, ratchet; gates.yaml; picture, take, plan and master judges with priced ladders; every refs/episode park removed; the audit sheet |
| 2026-09-24 | [docs/audit/2026-09-24_skills_book_neutral_plan.md](../docs/audit/2026-09-24_skills_book_neutral_plan.md) | NOT STARTED — scrub every book name and episode id out of the skills; guard test |

## Rules this folder inherits

- Skills, agents and docs name no book, character, episode or take.
- One checkout, on master; everything book-specific lives under `library/<book>/`.
- A page here that changes what the studio *is* needs a decision file; a decision the
  owner rules on gets its `docs/DECISIONS.md` line.
