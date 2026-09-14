#!/usr/bin/env python
"""ONE storyboard per setup, drawn as a sequence of sheets (PAID: one gpt-image
call per sheet, $0.13 at 3x2 and $0.20 at 3x3), every shot and sub-shot in
story order with its route position, each END panel straight after the panel
it closes; cells cut between the gutters found on the sheet and DQ'd.

    uv run python scripts/episode/seq_boards.py <codex_id> <episode> [--setup=corridor] [--sheet=1]

Writes `frames/seq_<setup>_<k>.png` (+ .prompt.txt), cells `frames/Q{shot}_{sub}.png`
(and `Q{shot}_{sub}E.png` for an END panel), and `frames/seq_<setup>.dq.json`.
References: the location plate, the setup's prop plates (the same vehicle in
every setup that shows it), the setup's cast.  The PREVIOUS sheet is no longer
attached: it copied its framings into the new cells (reviewer 3, item 7).

`--sheet=<k>` redraws one sheet of a setup for $0.13 instead of the whole
setup; `draw()` returns early when the output file exists, so a re-run costs
nothing for sheets already on disk.  Owner's design, 2026-09-11: takes are
windows on this board.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image

from studio import actor_gate, episode_board as board, episode_home, episode_seq_board as sq, prop_refs, route_gate
from studio.episode_spec import Episode, Setup
from studio.trailer_refs import contract_description


def storyboard():
    spec = importlib.util.spec_from_file_location("ep_storyboard", ROOT / "scripts/episode/storyboard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def physicals(book: Path) -> dict[str, str]:
    return {r["entity_id"]: contract_description(r.get("physical", ""))
            for r in episode_home.read_json(book / "refs" / "refs.json")["refs"] if r.get("kind") == "character"}


def white_lines(cells: list[Path]) -> list[str]:
    bad = []
    for c in cells:
        a = np.asarray(Image.open(c).convert("L"), dtype=float)
        if any(a[i].mean() > 190 and a[i].std() < 30 for i in range(a.shape[0])) or \
           any(a[:, j].mean() > 190 and a[:, j].std() < 30 for j in range(a.shape[1])):
            bad.append(c.name)
    return bad


def ladder_check(cells: list[Path], group: list[dict], route: list[int],
                 setup: Setup | None = None) -> tuple[list, list[int]]:
    """The landmark's height in the ROUTE panels only, and the places where it
    went backwards.  With story order the route panels are scattered through the
    sheet, so the old `cells[:geography]` read close-ups as geography.  A shrink
    between two cells at the same place on the route is framing, not geography.

    A landmark at the route's START (the bench's flame, the gateway's arch) is
    walked AWAY from, so on that sheet the honest strip shrinks: read it back to
    front and the same gate measures the same law."""
    heights = [route_gate.door_height(cells[i - 1]) for i in route]
    paths = [group[i - 1].get("path") or 0.0 for i in route]
    read = list(range(len(route)))
    if setup is not None and setup.landmark_at == sq.START:
        read.reverse()
    tall, along = [heights[i] for i in read], [paths[i] for i in read]
    bad = [i for i in route_gate.regressions(tall)
           if any(abs(along[i] - along[j]) >= 0.1 for j in range(i) if tall[j] is not None)]
    return heights, sorted(read[i] for i in bad)


def attempt(sb, text: str, refs: list[Path], out: Path, group: list[dict], route: list[int],
            grid: tuple, frames_dir: Path, strict: bool, setup: Setup | None = None) -> dict:
    """One paid draw, cut into its cells and gated.  PAID: one gpt-image call."""
    cols, rows, canvas = grid
    sheet = sb.draw(text, refs, out, canvas)
    grey = np.asarray(Image.open(sheet).convert("L"), dtype=float)
    boxes = board.cell_boxes(grey, cols, rows)
    cells = [sb.conform(sheet, frames_dir / sq.cell_name(s["shot"], s["sub"], s.get("end", False)), boxes[i])
             for i, s in enumerate(group)]
    heights, regress = ladder_check(cells, group, route, setup)
    row_bands, col_bands = board.bands(grey, 0), board.bands(grey, 1)
    return {"sheet": sheet.name, "route": route, "cells": [c.name for c in cells],
            "gutters_ok": len(row_bands) == rows - 1 and len(col_bands) == cols - 1,
            "white_lines_in": white_lines(cells), "door_heights": heights, "regressions": regress,
            "duplicates": sq.duplicates(cells, group), "strict": strict}


def clean(entry: dict) -> bool:
    return not (entry["regressions"] or entry["white_lines_in"] or entry["duplicates"])


def drop_end_copies(frames_dir: Path, entry: dict) -> list[dict]:
    """An END cell that is still its own start panel after the strict retry is
    DELETED.  A copy kept on disk becomes a take's pin and freezes the render on
    the frame it repeats; the segment renders with no end pin instead."""
    dropped = []
    for a, b in entry["duplicates"]:
        end = next((n for n in (b, a) if n.endswith("E")), "")
        if end and (frames_dir / f"{end}.png").exists():
            (frames_dir / f"{end}.png").unlink()
            dropped.append({"dropped_end": end, "reason": f"still a copy of {a if end == b else b} after strict"})
    return dropped


def draw_sheet(sb, frames_dir: Path, name: str, k: int, group: list[dict], route: list[int], grid: tuple,
               setup: Setup, physical: dict[str, str], refs: list[Path], report: dict,
               aspect: str = "9:16", props: list[dict] | None = None) -> dict:
    """One sheet: the draw, and one strict retry that names its own offender."""
    entry = {"duplicates": [], "regressions": []}
    for strict in (False, True):
        text = sq.prompt(group, setup, physical, previous=False, first=(k == 0), geography=route,
                         aspect=aspect, props=props)
        if strict:
            text = sq.strict_prefix(entry["duplicates"], entry["regressions"], setup) + "\n\n" + text
        out = frames_dir / (f"seq_{name}_{k}_strict.png" if strict else f"seq_{name}_{k}.png")
        entry = attempt(sb, text, refs, out, group, route, grid, frames_dir, strict, setup)
        report["sheets"].append(entry)
        print(f"  {name} sheet {k}{' STRICT' if strict else ''}: {[sq.label(s) for s in group]} -> "
              f"{entry['sheet']} gutters {entry['gutters_ok']} white {entry['white_lines_in']} "
              f"door {entry['door_heights']} regress {entry['regressions']} dupes {entry['duplicates']}",
              flush=True)
        if clean(entry):
            return entry
    report["dropped_ends"] += drop_end_copies(frames_dir, entry)
    return entry


def draw_setup(book: Path, episode: Episode, number: int, name: str, only_sheet: int | None = None) -> dict:
    sb = storyboard()
    aspect = episode.aspect
    sb.adopt(aspect)          # the cells are cropped to the PLAN's canvas, never to a module default
    frames_dir = episode_home.frames_dir(book, number)
    setup = episode.setups[name]
    physical = physicals(book)
    segs = sq.segments(episode.shots, name)
    refs = [frames_dir / f"plate_{name}.png"]
    # the same cab in every setup that shows one; the cab setup's own plate IS that plate
    refs += [frames_dir / f"plate_{p}.png" for p in setup.props if p != name]
    # The WARDROBE CARD, not the identity bust: the bust is the picture with the
    # hat on. All six episode 2 sheets were drawn against Holmes in a deerstalker
    # and Watson in his bowler while every panel's prose said 'bare-headed'.
    refs += [sq.cast_sheet(book, who, name, setup.state) for who in setup.cast]
    shown = prop_refs.props_in(" ".join(str(v) for c in segs for v in c.values()),
                               [r for r in episode_home.read_json(book / 'refs' / 'refs.json')['refs']
                                if r.get('kind') == 'prop'])
    shown = [r for r in shown if (book / r['rel_path']).exists()]
    refs += [book / r['rel_path'] for r in shown]
    groups = sq.sheets(segs, setup, aspect)
    report = {"setup": name, "cells": len(segs), "route_cells": sum(len(r) for _, r, _ in groups),
              "sheets": [], "white_lines_in": [], "dropped_ends": []}
    finals = []
    for k, (group, route, grid) in enumerate(groups):
        if only_sheet is not None and k != only_sheet:
            continue
        entry = draw_sheet(sb, frames_dir, name, k, group, route, grid, setup, physical, refs,
                           report, aspect, shown)
        finals.append(entry)
        report["white_lines_in"] += entry["white_lines_in"]
        report.setdefault("regressions", []).extend([(entry["sheet"], i) for i in entry["regressions"]])
    # every sheet's LAST attempt, not report["sheets"][-1]: that can be one sheet's
    # strict retry while an earlier sheet still holds a pair of copies.
    report["passed"] = all(clean(e) and e["gutters_ok"] for e in finals)
    # a one-sheet redraw reports on that sheet alone and leaves the setup's own
    # dq.json where it is, rather than overwriting it with a partial verdict
    stem = f"seq_{name}" if only_sheet is None else f"seq_{name}_{only_sheet}"
    episode_home.write_json(frames_dir / f"{stem}.dq.json", report)
    return report


def main(book_id: str, number: int, only: str | None = None, sheet: int | None = None) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    # THE LAST FREE MOMENT.  A wrong actor drawn into a sheet is paid for twice --
    # once to draw it and once to draw it again -- and episode 3 shipped a whole
    # master with Holmes making Gregson's gesture because nothing read the plan
    # before the draw.  `actor_gate` was written and then called by nothing, which
    # is a comment, not a gate.
    for note in actor_gate.advisory_episode(episode):
        print(f"  ADVISORY {note}", flush=True)
    if faults := actor_gate.hard_episode(episode):
        raise SystemExit("the plan fails the actor gate:\n  " + "\n  ".join(faults))
    for name in episode.setups:
        if only and name != only:
            continue
        draw_setup(book, episode, number, name, sheet)


if __name__ == "__main__":
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--setup=")), None)
    one = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--sheet=")), None)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1, only, one)
