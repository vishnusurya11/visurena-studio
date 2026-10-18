"""Render a Prism plan on the local ComfyUI -- only on the owner's go, never over a busy GPU.

    uv run python -m prism.render plan          # writes <root>/plan.json, prints counts; renders nothing
    uv run python -m prism.render go --go       # renders every missing job, model by model

The run root defaults to docs/audit/prism (git-ignored: renders are evidence, not code).
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

from prism.catalog import load_guides, load_styles, load_subjects
from prism.plan import Job, jobs, pending, write_plan

ROOT = Path("docs/audit/prism")
SUBJECTS = Path("prism/subjects/dracula.json")


class NoGo(RuntimeError):
    """A render was asked for without the owner's go."""


class GpuBusy(RuntimeError):
    """ComfyUI has work queued (the series); Prism would thrash its models."""


def render_one(job: Job, root: Path, runner, cold: bool) -> dict:
    started = time.monotonic()
    made = runner(job.workflow, job.values)
    seconds = round(time.monotonic() - started, 1)
    target = Path(root) / job.out
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(made[0], target)
    return {"style": job.style, "subject": job.subject, "model": job.model, "out": job.out,
            "seconds": seconds, "cold": cold}


def record(row: dict, root: Path) -> None:
    with (Path(root) / "timings.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps(row) + "\n")


def render_all(planned: list[Job], root: Path, runner, *, go: bool, busy) -> list[dict]:
    if not go:
        raise NoGo("Prism renders only on the owner's go (--go)")
    if busy():
        raise GpuBusy("ComfyUI is busy; pause the series or wait for the queue to empty")
    Path(root).mkdir(parents=True, exist_ok=True)
    rows, loaded = [], set()
    for job in pending(planned, root):
        try:
            row = render_one(job, root, runner, cold=job.model not in loaded)
        except Exception as fault:  # one failed image never stops the run; a re-run fills the gap
            row = {"style": job.style, "subject": job.subject, "model": job.model, "out": job.out,
                   "error": f"{type(fault).__name__}: {fault}"[:300]}
        loaded.add(job.model)
        record(row, root)
        rows.append(row)
    return rows


def library_plan() -> list[Job]:
    return jobs(load_styles(Path("prism/styles")), load_subjects(SUBJECTS), load_guides(Path("prism/models")))


def main(argv: list[str]) -> int:
    planned = library_plan()
    ROOT.mkdir(parents=True, exist_ok=True)
    write_plan(planned, ROOT / "plan.json")
    todo = pending(planned, ROOT)
    print(f"{len(planned)} jobs planned, {len(todo)} to render: {dict(Counter(j.model for j in todo))}")
    if argv[:1] != ["go"]:
        return 0
    from studio import comfy
    render_all(planned, ROOT, comfy.run, go="--go" in argv, busy=comfy.busy)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
