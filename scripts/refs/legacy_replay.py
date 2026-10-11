#!/usr/bin/env python
"""The legacy-path replay (C1_verdict #10): a shipped take of a book on the OLD
pipeline (A Study in Scarlet: `char-*_indoor` sheets, `boards/cells`, no
refs/looks.json) replayed from its own ran `T*.graph.json`. Bench only, $0.

    uv run python scripts/refs/legacy_replay.py lag <book_id> <episode> T04 [T05 ...]

The graph stages exactly the content-addressed names it shipped with; a job may
swap named pictures (the bench's re-cut cell) and the seed.  A graph that staged
an UNHASHED name is refused: ep01-03 staged `char-*_bench.png` / `voice_NN.wav`
names later episodes overwrote in ComfyUI/input, so their inputs are unknown.
Lip lag is read with `measure/mouth.lag` (the mouth against the voice), never the
dq `lag` row, which reads the mux and sat at 0.000 on all 80 Scarlet dialogue takes.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

HASHED = re.compile(r"_[0-9a-f]{8}\.\w+$")
LOADERS = {"LoadImage": "image", "LoadAudio": "audio"}


def staged(graph: dict) -> dict[str, str]:
    """{node id: the file name it loads} for every image and audio loader."""
    return {k: n["inputs"][LOADERS[n["class_type"]]] for k, n in graph.items() if n.get("class_type") in LOADERS}


def refuse_unhashed(graph: dict) -> None:
    if bad := sorted({v for v in staged(graph).values() if not HASHED.search(v)}):
        raise SystemExit(f"REFUSED: unhashed staged names, inputs unknown (overwritten in ComfyUI/input): {bad}")


def replay_graph(shipped: dict, swaps: dict[str, str] | None = None, seed: int | None = None) -> dict:
    """The shipped graph, its named pictures swapped and its seed set; nothing else moves."""
    refuse_unhashed(shipped)
    out = json.loads(json.dumps(shipped))
    for k, name in staged(out).items():
        if name in (swaps or {}):
            out[k]["inputs"][LOADERS[out[k]["class_type"]]] = swaps[name]
    if seed is not None:
        next(n for n in out.values() if n.get("class_type") == "RandomNoise")["inputs"]["noise_seed"] = seed
    return out


def lip_lag(video: Path, guide: Path) -> dict:
    """`measure/mouth.lag`: the mouth's aperture against the guide's voice envelope."""
    from studio import av_sync, take_lock
    from studio.measure import mouth
    frames = take_lock.frames(video, None)
    voice = mouth.voice_envelope(av_sync.load_mono(guide, 24000), 24000)
    return mouth.lag(mouth.apertures(frames, mouth.facemesh()), voice)


def main(argv: list[str]) -> int:
    if argv[0] == "lag":
        from studio import episode_home
        from studio.comfy import COMFY_ROOT
        room = episode_home.takes_dir(episode_home.book_dir(argv[1]), int(argv[2]), "r2v")
        for take in argv[3:]:
            graph = json.loads((room / f"{take}.graph.json").read_text(encoding="utf-8"))
            refuse_unhashed(graph)
            guide = next(v for v in staged(graph).values() if v.endswith(".wav"))
            print(take, json.dumps(lip_lag(room / f"{take}.mp4", COMFY_ROOT / "input" / guide)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
