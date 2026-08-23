# studio_orchestrator

**Status: deleted from the working tree, recoverable from commit `d060598`.**
Design doc approved 2026-03-27, predates the architecture in
[../ARCHITECTURE.md](../ARCHITECTURE.md) and needs reconciling with it.

Turns parsed stories into scheduled YouTube uploads, run like a TV channel.

## Architecture as previously designed

Scheduler (weekly grid, slot manager, planner, show runner) plus a production pipeline of
independent departments (script, image, audio, video, upload) over a job queue and step
tracker.

## Conflicts to resolve

- The old design named LangGraph for Phase 2 agents. **Superseded** — Strands for agents,
  in-house `stepwise` for the DAG. See [../DECISIONS.md](../DECISIONS.md).
- Its `step_tracker.py` / `job_queue.py` / `pipeline.py` are the first draft of what
  `stepwise` becomes. Read them before designing `stepwise`; do not extend them in place.

## Prior art it reuses

Qwen3-TTS, ComfyUI, and YouTube upload from the E3 repo.
