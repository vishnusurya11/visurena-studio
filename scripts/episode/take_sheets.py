#!/usr/bin/env python
"""One 2x3 storyboard sheet PER TAKE (PAID: one gpt-image call, ~$0.13), its
six cells cut between the gutters found on it, and a DQ scan before use.

    uv run python scripts/episode/take_sheets.py <codex_id> <episode> [--only=3]

Writes `frames/sheet_NN.png` (+ .prompt.txt), cells `frames/C{NN}_{k}.png`
(k = 0..5), and `frames/sheet_NN.dq.json`.  References, in this order: the
take's own approved panel(s) (the exact framing), the plate, the setup's
cast.  No previous sheet, no setup board: they carry other framings.
Acceptance per shot-run: the cells' camera scale within 5 % of the run's
first cell (a named push: monotonic, under 15 % travel); one redraw with a
STRICT opening, then the sheet stays a reference only.  Owner's design,
2026-09-10 evening, after the camera-pumping analysis.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image

from studio import cell_scale, episode_board as board, episode_home, episode_take_board as tb, episode_takes as tk
from studio.episode_spec import Episode
from studio.trailer_refs import contract_description


def storyboard():
    spec = importlib.util.spec_from_file_location("ep_storyboard", ROOT / "scripts/episode/storyboard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def physicals(book: Path) -> dict[str, str]:
    return {r["entity_id"]: contract_description(r.get("physical", ""))
            for r in episode_home.read_json(book / "refs" / "refs.json")["refs"] if r.get("kind") == "character"}


def takes_of(book: Path, episode: Episode, number: int) -> list[dict]:
    placed = episode_home.read_json(episode_home.home(book, number) / "placed.json")
    shots = [dict(s, setup=episode.shot(s["index"]).setup) for s in placed["shots"]]
    at = {l["index"]: (l["at"], l["seconds"]) for l in placed["lines"]}
    out = []
    for take in tk.takes(shots):
        take["placed"], take["at"] = shots, at
        out.append(take)
    return out


def runs(beats: list[dict]) -> list[list[int]]:
    """Cell indices grouped by the shot they depict (a take may hold several shots)."""
    out: list[list[int]] = []
    for b in beats:
        if out and beats[out[-1][-1]]["shot"] == b["shot"]:
            out[-1].append(b["cell"])
        else:
            out.append([b["cell"]])
    return out


def acceptance(cells: list[Image.Image], beats: list[dict], episode: Episode) -> dict:
    """Per shot-run camera consistency, from measured cell scale."""
    scales = cell_scale.scales_of(cells)
    verdicts = []
    for run in runs(beats):
        shot = episode.shot(beats[run[0]]["shot"])
        rel = [round(scales[k] / scales[run[0]], 3) for k in run]
        ok = cell_scale.consistent(rel, tb.names_push(shot.motion))
        verdicts.append({"shot": shot.index, "cells": run, "scale": rel, "push": tb.names_push(shot.motion), "ok": ok})
    return {"scales": scales, "runs": verdicts, "camera_ok": all(v["ok"] for v in verdicts)}


def lines_ok(cells: list[Path]) -> list[str]:
    bad = []
    for c in cells:
        a = np.asarray(Image.open(c).convert("L"), dtype=float)
        if any(a[i].mean() > 190 and a[i].std() < 30 for i in range(a.shape[0])) or \
           any(a[:, j].mean() > 190 and a[:, j].std() < 30 for j in range(a.shape[1])):
            bad.append(c.name)
    return bad


def draw_and_cut(sb, text: str, refs: list[Path], sheet: Path, frames_dir: Path, index: int) -> list[Path]:
    sb.draw(text, refs, sheet, tb.CANVAS)
    grey = np.asarray(Image.open(sheet).convert("L"), dtype=float)
    boxes = board.cell_boxes(grey, tb.COLS, tb.ROWS)
    return [sb.conform(sheet, frames_dir / f"C{index:02d}_{k}.png", boxes[k]) for k in range(tb.CELLS)]


def one(book: Path, episode: Episode, number: int, take: dict) -> Path:
    sb = storyboard()
    frames_dir = episode_home.frames_dir(book, number)
    shots = [episode.shot(i) for i in take["shots"]]
    first, setup = shots[0], episode.setups[shots[0].setup]
    lines = [l for l in episode.lines if l.shot in take["shots"]]
    beats = tb.beats(shots, take["placed"], lines, take["at"], take["seconds"])
    own = [frames_dir / f"S{s.index:02d}.png" for s in shots]
    refs = own + [frames_dir / f"plate_{first.setup}.png"]
    refs += [book / "refs" / "characters" / f"char-{who}.png" for who in setup.cast]
    push = tb.names_push(first.motion)
    report = {"beats": beats, "tries": []}
    for strict in (False, True):
        text = tb.prompt(beats, setup.described, setup.cast, physicals(book), setup.landmark, push, len(own), strict)
        sheet = frames_dir / (f"sheet_{first.index:02d}.png" if not strict else f"sheet_{first.index:02d}_strict.png")
        cells = draw_and_cut(sb, text, refs, sheet, frames_dir, first.index)
        acc = acceptance([Image.open(c) for c in cells], beats, episode)
        acc["white_lines_in"] = lines_ok(cells)
        acc["sheet"] = sheet.name
        report["tries"].append(acc)
        if acc["camera_ok"] and not acc["white_lines_in"]:
            break
    final = report["tries"][-1]
    report["passed"] = final["camera_ok"] and not final["white_lines_in"]
    report["sheet"] = final["sheet"]
    report["reference_only"] = not final["camera_ok"]
    episode_home.write_json(frames_dir / f"sheet_{first.index:02d}.dq.json", report)
    print(f"  take {first.index:02d} {final['sheet']}  camera {'OK' if final['camera_ok'] else 'FAIL -> reference only'} "
          f"scales {[f'{s:.2f}' for s in final['scales']]} white {final['white_lines_in']} tries {len(report['tries'])}", flush=True)
    return frames_dir / final["sheet"]


def main(book_id: str, number: int, only: int | None = None) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    for take in takes_of(book, episode, number):
        if only is not None and take["shots"][0] != only:
            continue
        one(book, episode, number, take)


if __name__ == "__main__":
    only = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--only=")), None)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1, only)
