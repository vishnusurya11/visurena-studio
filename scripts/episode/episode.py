#!/usr/bin/env python
"""The blind path: one chapter, one command, the seven steps in order.

    uv run python scripts/episode/episode.py <codex_id> <episode>

Each step skips what already exists, so a rerun resumes.  The plan must
already be written (`episode-writer`); this runs everything after it and
stops at the first gate that refuses.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from studio.episode_home import episode_arg

STEPS = ("say_lines", "timeline", "frames", "storyboard:grids", "shots", "storyboard:review",
         "assemble", "qc")


def step(name: str):
    """`file` or `file:function`; the function defaults to `main`."""
    file, _, entry = name.partition(":")
    spec = importlib.util.spec_from_file_location(f"ep_{file}", HERE / f"{file}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"ep_{file}"] = module
    spec.loader.exec_module(module)
    return getattr(module, entry or "main")


def queue_is_clear() -> bool:
    """A job already on the ComfyUI queue would swap H3 out mid-round (250-470 s each)."""
    import json
    import urllib.request

    with urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=5) as response:
        queue = json.loads(response.read())
    return not queue["queue_running"] and not queue["queue_pending"]


def main(book_id: str, number: int, until: str = "") -> None:
    """Run the steps in order; `until` stops AFTER the named step."""
    for name in STEPS:
        if name == "shots" and not queue_is_clear():
            raise SystemExit("ComfyUI queue is not empty; the H3 round would pay a model swap")
        print(f"== {name}", flush=True)
        step(name)(book_id, number)
        if until and name == until:
            print(f"stopped after {until}", flush=True)
            return


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    until = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--until=")), "")
    main(args[0], episode_arg(sys.argv), until)
