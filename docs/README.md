# Visurena Studio — Documentation

| Doc | What it holds |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | The brick, the four layers, the load-bearing rule, gate policy, phases |
| [DECISIONS.md](DECISIONS.md) | Decision log — what was chosen, what was rejected, and why |
| [db/SCHEMA.md](db/SCHEMA.md) | The `codex` table, the id scheme, deferred stage tracking |
| [db/EVENT_MODEL.md](db/EVENT_MODEL.md) | **Owner-directed** — the 3-piece model: codex + events table + file logs + step registry |
| [db/LIBRARY_STRUCTURE.md](db/LIBRARY_STRUCTURE.md) | **PROPOSAL** — flat library + scope folders + phased atlas/entity tables |
| [analysis/DESIGN.md](analysis/DESIGN.md) | **PROPOSAL** — the analysis stage: 3 layers + views, timeline format, pipeline A0-A9 |
| [analysis/research/](analysis/research/) | Seven research reports (NLP tooling, LLM patterns, schemas, formats, critics, tools, narratology) |
| [stepwise/DESIGN.md](stepwise/DESIGN.md) | **PROPOSAL** — Layer 1: tables, state machine, re-run + staleness-cutoff semantics |
| [command_center/DESIGN.md](command_center/DESIGN.md) | **PROPOSAL** — the DAG tracking UI: stack, screens, drill-down |
| [parser/](parser/README.md) | `studio_parser` — P0 target |
| [orchestrator/](orchestrator/README.md) | `studio_orchestrator` — predates current architecture |
| [shorts/](shorts/README.md) | The Higgsfield shorts pipeline and its 8 department skills |

Project rules — uv, test-first, spec-driven, and the no-test-may-spend-money clause —
live in [../CLAUDE.md](../CLAUDE.md), not here.

## Reading order

New to the project: `ARCHITECTURE.md` → `DECISIONS.md` → whichever component you are
touching.

## Rule

**Any architectural change needs an entry in `DECISIONS.md`.** A decision without a
recorded reason gets re-litigated in three months, usually badly.
