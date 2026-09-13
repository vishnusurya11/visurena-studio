#!/usr/bin/env python
"""A/B/C on one take: what the continuity reference should be.

    uv run python scripts/episode/ab_refs.py <codex_id> <episode> <shot> <arm> [<arm> ...]

Arms (same seed, same prompt, same anchors, same audio):
  sheet  - the 3x3 storyboard sheet + the plate (today's default)
  panel  - the take's own first panel + the plate
  strip  - the panels before/of/after the take side by side + the plate
Writes `work_r2v/ab_<arm>_T<shot>.mp4` and a strip of 8 frames per arm with
the closest sheet cell named under each frame (`work_r2v/ab_refs_T<shot>.png`).
Owner's ask, 2026-09-10: "debug further if this assumption is wrong".
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw

from studio import episode_home, episode_strip_ref, frame_match as fm
from studio.comfy import outputs_of, stage_image, submit, wait_record
from studio.trailer_assemble import clip_seconds


def engine():
    spec = importlib.util.spec_from_file_location("takes_r2v", ROOT / "scripts/episode/takes_r2v.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def refs_for(arm: str, card: dict, frames_dir: Path, work: Path, episode) -> list[str]:
    plate = f"plate_{card['setup']}.png"
    if arm == "sheet":
        return [n for n in card["refs"] if n.startswith("board_")] + [plate]
    if arm == "panel":
        return [f"S{card['index']:02d}.png", plate]
    if arm == "strip":
        out = work / f"strip_T{card['index']:02d}.png"
        episode_strip_ref.strip_for(frames_dir, card["shots"], episode.shots[0].index, episode.shots[-1].index, out)
        return [out.name, plate]
    raise SystemExit(f"unknown arm {arm}")


def render_arm(tr, arm: str, card: dict, book: Path, number: int, work: Path, episode) -> Path:
    frames_dir = episode_home.frames_dir(book, number)
    out = work / f"ab_{arm}_T{card['index']:02d}.mp4"
    if out.exists():
        return out
    faces = [n for n in card["refs"] if n.startswith("char-")]
    c = {**card, "refs": faces + refs_for(arm, card, frames_dir, work, episode),
         "prompt": card["prompt"].replace("the storyboard sheet of this scene",
                                          "the storyboard of this take" if arm == "strip" else
                                          "the first frame of this take")}
    for name in c["refs"]:
        src = frames_dir / name if (frames_dir / name).exists() else work / name
        stage_image(src if src.exists() else book / "refs" / "characters" / name)
    graph = tr.graph_for(c, book, number, work)
    for node in graph.values():  # the strip lives in work/, not frames/
        if node["class_type"] == "LoadImage" and node["inputs"]["image"].startswith("strip_"):
            node["inputs"]["image"] = stage_image(work / node["inputs"]["image"])
    graph[next(k for k, n in graph.items() if n["class_type"] == "SaveVideo")]["inputs"]["filename_prefix"] = f"ab_{arm}_{card['index']:02d}"
    began = time.time()
    made = outputs_of(wait_record(submit(graph), timeout=7200))
    out.write_bytes(next(p for p in made if p.suffix in (".mp4", ".webm")).read_bytes())
    print(f"{arm}: {out} in {time.time() - began:.0f} s", flush=True)
    return out


def judge(arms: dict[str, Path], card: dict, frames_dir: Path, work: Path, cells: dict) -> Path:
    tile, n = (240, 420), 8
    page = Image.new("RGB", (n * (tile[0] + 4), len(arms) * (tile[1] + 40)), "black")
    d = ImageDraw.Draw(page)
    for r, (arm, video) in enumerate(arms.items()):
        secs = clip_seconds(video)
        for k in range(n):
            at = min(secs * k / (n - 1), secs - 0.05)
            png = work / f"ab_{arm}_{card['index']:02d}_{k}.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(video), "-frames:v", "1", str(png)], check=True)
            frame = fm.load(png)
            best, score = fm.closest(frame, cells)
            page.paste(frame.resize(tile), (k * (tile[0] + 4), r * (tile[1] + 40) + 20))
            d.text((k * (tile[0] + 4) + 4, r * (tile[1] + 40) + 4), f"{arm} {at:.1f}s -> {best} {score:.2f}", fill="white")
    out = work / f"ab_refs_T{card['index']:02d}.png"
    page.save(out)
    return out


def main(book_id: str, number: int, shot: int, arms: list[str]) -> None:
    tr = engine()
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    work = episode_home.home(book, number) / "work_r2v"
    work.mkdir(exist_ok=True)
    card = next(c for c in tr.cards(book, episode, number) if c["index"] == shot)
    frames_dir = episode_home.frames_dir(book, number)
    setup_shots = [s.index for s in episode.shots if s.setup == episode.shot(shot).setup]
    cells = {f"S{i:02d}": fm.load(frames_dir / f"S{i:02d}.png") for i in setup_shots}
    done = {arm: render_arm(tr, arm, card, book, number, work, episode) for arm in arms}
    print("judge ->", judge(done, card, frames_dir, work, cells), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:])
