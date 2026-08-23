# Visurena Studio — Architecture

Status: decided 2026-08-21/22. Changes here require a matching entry in [DECISIONS.md](DECISIONS.md).

## The brick

Every domain has a base case + a recursive rule. For this studio it is the **Step**:

> a unit with a deterministic identity (`production_id + step_name + input_hash`), that
> consumes prior artifacts, produces one artifact on disk, costs a known amount, and
> passes a gate.

Everything regenerates from it:

| Concept | Is really |
|---|---|
| Department | an ordered list of Steps |
| Production (short / audiobook / song / novel) | a DAG of Steps |
| Agent | a Step whose executor is an LLM tool-loop |
| Skill | the prompt + procedure a Step uses |
| A2A | a Step invoked over the wire |
| Scheduler | a policy that emits Steps at times |

Consequence: **the agent framework is a node-level choice, not the foundation.**
Two prior pipelines (E3, house_of_novels) failed because the pipeline *was* the
framework, so a framework quirk meant a dead pipeline.

## Four layers, decided independently

| Layer | Choice |
|---|---|
| 1. Step runner — DAG, ledger, gates | **written in-house** (`packages/stepwise`), SQLite |
| 2. Model gateway + structured output | **Strands Agents SDK** |
| 3. Agent loops | Strands — only two real ones |
| 4. Interactive driver | Claude Code `.claude/skills/shorts-*` |

Anthropic SDK direct is permitted only for prompt-cached long-context parser calls.
LangChain, LangGraph and Pydantic AI are not used in this repo.

## The load-bearing rule

> **Strands owns models and agents. `stepwise` owns the DAG, the ledger, and the gates.**

No agent framework's persistence knows about money. Strands sessions, LangGraph
checkpointers and the rest snapshot *conversation/graph state*; the real state here is
**artifacts on disk + credits burned**.

Concrete failure: a Graph is mid-way through `shot_03`. Higgsfield has taken 195 credits
and written `clips/raw/shot_03.mp4`. The machine crashes before the node is marked
complete. On resume the node looks unfinished and re-runs — **195 credits gone twice.**

Node-completion is not artifact-existence. The idempotency key must be:

```
input_hash -> does the artifact already exist -> skip
```

That is ~30 lines and it is ours.

## Gate = policy, not pause

```
Gate(step, artifact, cost) -> APPROVE | REJECT | ESCALATE
```

- **Interactive mode:** every gate is `ESCALATE` — ask the owner.
- **Automated mode:** `APPROVE if cost <= ceiling and qc_score >= threshold else ESCALATE`.
- **Escalation never blocks.** The production parks in `awaiting_approval`, emits a
  notification, and the runner moves on to other productions.

Default policy for any credit-spending step is `ESCALATE`. Ceilings are raised
per-department, deliberately, only after that department has proven itself.

**Automation is not a mode you switch on — it is gates you retire one at a time.**

## Two runtimes, one contract

| Runtime | What it does |
|---|---|
| Interactive — Claude Code skills | a production gets **authored**, owner approves spend |
| Headless — Python | a production gets **manufactured**, unattended |

The seam is **JSON contracts on disk** inside a self-contained production folder
(`scene.json`, shot list, `audio.json`). Both runtimes read and write the same files.
The procedure lives in Python; the skill is a thin interactive driver over it. One
implementation, two drivers — never two implementations.

## "Windows now, server later" — obey from line one

1. `ArtifactStore` protocol — `LocalStore` now, `S3Store` later. Departments never call `open()`.
2. `StepStore` protocol — SQLite now, Postgres later.
3. Pull-based queue with DB leases, even at one worker. An in-memory queue forces a rewrite.
4. **Never store an absolute path.** `production_id` + relative path only. Absolute
   `D:\Projects\...` strings in a table are unfixable a year later.

## Phases

| | |
|---|---|
| **P0** | Restore `studio_parser` from commit `d060598`, wrap as Steps. Zero credits. |
| **P1** | Build `stepwise` (ledger, gates, resume). Drive the Dracula short with all gates ESCALATE. |
| **P2** | Refactor the 8 `shorts-*` skills into thin drivers over `studio.departments`. |
| **P3** | Flip gate policies to auto, one department at a time, cheapest first. |
| **P4** | Server move: swap `StepStore` and `ArtifactStore`. |

## Publishable artifact

`packages/stepwise` is generalizable beyond this repo. LangGraph, Strands, Temporal and
Prefect all assume steps are cheap and freely retryable; none treat **credits spent** and
**artifact-on-disk** as first-class resume keys. Build it as a standalone package and
import it, rather than burying it in `studio_orchestrator/`.
