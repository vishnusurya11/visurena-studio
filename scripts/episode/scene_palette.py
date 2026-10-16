#!/usr/bin/env python
"""Within-scene weather/palette continuity over an episode's takes (advisory, CPU, $0).

    uv run python scripts/episode/scene_palette.py <book> <n>
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, scene_palette  # noqa: E402
from studio.episode_home import episode_arg  # noqa: E402


def scene_map(plan: dict) -> dict[int, str]:
    """{shot index: its setup}: one setup is one scene's place and hour."""
    return {int(s.get("index", n)): s.get("setup", "") for n, s in enumerate(plan.get("shots") or [])}


def mid_frame(take: Path):
    """The take's middle frame as RGB, read by ffmpeg at 128 px."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", "0.8", "-i", str(take), "-frames:v", "1",
                          "-vf", "scale=128:128", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(128, 128, 3)


def main(book_id: str, number: int) -> int:
    book = episode_home.book_dir(book_id)
    plan = episode_home.read_json(episode_home.plan_path(book, number))
    takes = episode_home.takes_dir(book, number, "r2v")
    by = {i: scene_palette.stats(mid_frame(p)) for i in scene_map(plan) if (p := takes / f"T{i:02d}.mp4").exists()}
    found = scene_palette.outliers(by, scene_map(plan))
    for t, why in found:
        print(f"  advisory T{t:02d}: {why}")
    print(f"SCENE PALETTE: {len(found)} advisory over {len(by)} takes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], episode_arg(sys.argv)))
