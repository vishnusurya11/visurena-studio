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

from studio import actor_gate, episode_board as board, episode_home, episode_seq_board as sq, prop_refs, route_gate, sheet_gate
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


ACCEPT_DIRTY = False
"""Draw a sheet whose TEXT the free gate refuses.  Set by `--accept-dirty`.

The escape is deliberate and it prints what it waived.  `sheet_gate` is the last
free moment before an irreversible spend, and on episode 3 it finds real faults
-- the hall carries three near-identical medium-closes of Holmes (Q22_0 against
Q12_0 at 0.886) -- so refusing is right.  But a gate with no sanctioned way past
it is a gate somebody eventually comments out, and a waiver nobody can read
afterwards is indistinguishable from a bug."""

GUTTER_EDGE = 6
"""How far into a cell a leaked gutter can reach, in pixels.  A residue is
contiguous with the frame edge it came from; `strip_white_edges` already takes
the first few, so what survives sits within a handful of pixels of the border."""

GUTTER_FLAT = 12.0
"""How uniform sheet paper is.  MEASURED on episode 3's cells: a real gutter
residue reads std 2-5, while the lit architecture this gate used to reject reads
26.9 (Q11_0.before col 83) and 30.0 (Q23_0 col 74) -- ten times the variance, and
74 to 83 pixels inside the picture."""


def white_lines(cells: list[Path]) -> list[str]:
    """The cells carrying a leaked white gutter, by name.

    THE TEST IS BRIGHT **AND** FLAT **AND** AT AN EDGE.  It used to be bright and
    loosely flat at ANY position, which rejected a lit doorway jamb as sheet
    paper -- and a rejection is not cheap: it made the hall sheet unclean, bought
    a $0.13 strict redraw, overwrote all nine of its cells, introduced a
    duplicate pair the first attempt did not have and got `Q11_0E` deleted.  Shot
    11 rendered with no END pin for a fault that was never there.

    `episode_board.bands` already uses bright-and-flat to FIND the gutters; this
    is the same brick, applied to what leaked through."""
    bad = []
    for c in cells:
        a = np.asarray(Image.open(c).convert("L"), dtype=float)
        rows, cols = a.shape
        edges = lambda n, size: n < GUTTER_EDGE or n >= size - GUTTER_EDGE
        if any(edges(i, rows) and a[i].mean() > 190 and a[i].std() < GUTTER_FLAT for i in range(rows)) or \
           any(edges(j, cols) and a[:, j].mean() > 190 and a[:, j].std() < GUTTER_FLAT for j in range(cols)):
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
            grid: tuple, boards: Path, strict: bool, setup: Setup | None = None) -> dict:
    """One paid draw, cut into its cells and gated.  PAID: one gpt-image call."""
    cols, rows, canvas = grid
    sheet = sb.draw(text, refs, out, canvas)
    grey = np.asarray(Image.open(sheet).convert("L"), dtype=float)
    boxes = board.cell_boxes(grey, cols, rows)
    cells = [sb.conform(sheet, sq.cells_in(boards) / sq.cell_name(s["shot"], s["sub"], s.get("end", False)), boxes[i])
             for i, s in enumerate(group)]
    heights, regress = ladder_check(cells, group, route, setup)
    row_bands, col_bands = board.bands(grey, 0), board.bands(grey, 1)
    return {"sheet": sheet.name, "route": route, "cells": [c.name for c in cells],
            "gutters_ok": len(row_bands) == rows - 1 and len(col_bands) == cols - 1,
            "white_lines_in": white_lines(cells), "door_heights": heights, "regressions": regress,
            "duplicates": sq.duplicates(cells, group), "strict": strict}


def clean(entry: dict) -> bool:
    """Is this attempt good enough to keep without a strict retry?

    `gutters_ok` belongs here.  It was computed on every attempt and only ever
    reached `report["passed"]`, which nothing reads -- `takes_r2v` takes its
    cells off disk.  MEASURED: `seq_corner_wall_0.png` returned FOUR column bands
    instead of two, so `cell_boxes` fell back to cutting the sheet in thirds;
    those cells are 663 px against a true 675-693 and every one then needed a
    bottom trim -- gutter leaking into the panel.  A sheet with misaligned cells
    is not a clean sheet, whatever its pictures say."""
    return bool(entry.get("gutters_ok", True)) and not (
        entry["regressions"] or entry["white_lines_in"] or entry["duplicates"])


def refuse_on_text(group: list[dict], setup, prompt: str, grid: tuple, name: str) -> None:
    """The FREE gate, at the last moment before the paid draw.

    `sheet_gate` is 430 lines and nine checks, four of them HARD, and it has
    never run on an episode: it is imported by `sheet_dq.py`, a separate manual
    command, and by nothing on the path that spends the money.  Episode 3 -- the
    one that shipped -- has no `sheet_dq.json` at all.  `sheet_dq.py`'s own
    docstring stated the wiring as an aspiration; this is it, built.

    HARD findings refuse for $0.  The rest print, because the advisory half is
    most of why the gate was worth writing and a gate that blocks on advice is a
    gate somebody turns off."""
    found = sheet_gate.sheet_findings(group, setup, prompt, grid)
    for fault in found:
        if not fault.hard:
            print(f"  WATCH {name}: {fault.check} panel {fault.panel} -- {fault.text}", flush=True)
    if not (hard := [f for f in found if f.hard]):
        return
    said = "\n  ".join(f"{f.check} panel {f.panel} -- {f.text} ({f.note})" for f in hard)
    if ACCEPT_DIRTY:
        # A SANCTIONED, LOGGED escape, because a gate with no way past it is a
        # gate somebody deletes.  It says what it waived, in the run's own output.
        print(f"  ACCEPT-DIRTY {name}: drawing anyway past {len(hard)} hard finding(s):\n  {said}",
              flush=True)
        return
    raise SystemExit(f"{name}: the sheet prompt fails the free gate, so nothing was drawn "
                     f"and nothing was spent:\n  {said}\n"
                     f"Fix the plan's panel prose, or pass --accept-dirty to draw regardless.")


def drop_end_copies(boards: Path, entry: dict) -> list[dict]:
    """An END cell that is still its own start panel after the strict retry is
    RETIRED to `boards/superseded/`: a copy is no destination for a take, and a
    copy left where cells live is one a later reader can still pick up.

    It used to build the path as `boards / f"{end}.png"` and cells moved to
    `boards/cells/` in the layout change.  Because it asks `.exists()` first it
    then skipped every cell in silence -- episode 4 had seven copied END cells,
    every one of their sheets was refused by `clean`, the strict retry ran, this
    was reached, and the report said `dropped_ends: []`, which read as good news.

    It moves rather than unlinks.  `sq.reaches` already refuses a copy as a
    destination, so deleting a picture that cost money to draw bought nothing."""
    dropped = []
    for a, b in entry["duplicates"]:
        end = next((n for n in (b, a) if n.endswith("E")), "")
        cell = sq.cells_in(boards) / f"{end}.png"
        if end and cell.exists():
            old = boards / "superseded"
            old.mkdir(parents=True, exist_ok=True)
            cell.replace(old / cell.name)
            dropped.append({"dropped_end": end, "reason": f"still a copy of {a if end == b else b} after strict"})
    return dropped


def draw_sheet(sb, boards: Path, name: str, k: int, group: list[dict], route: list[int], grid: tuple,
               setup: Setup, physical: dict[str, str], refs: list[Path], report: dict,
               aspect: str = "9:16", props: list[dict] | None = None) -> dict:
    """One sheet: the draw, and one strict retry that names its own offender."""
    entry = {"duplicates": [], "regressions": []}
    for strict in (False, True):
        text = sq.prompt(group, setup, physical, previous=False, first=(k == 0), geography=route,
                         aspect=aspect, props=props)
        if strict:
            text = sq.strict_prefix(entry["duplicates"], entry["regressions"], setup) + "\n\n" + text
        else:
            # the free gate, before the first dollar of this sheet
            refuse_on_text(group, setup, text, grid, name)
        out = sq.sheets_in(boards) / (f"seq_{name}_{k}_strict.png" if strict else f"seq_{name}_{k}.png")
        entry = attempt(sb, text, refs, out, group, route, grid, boards, strict, setup)
        report["sheets"].append(entry)
        print(f"  {name} sheet {k}{' STRICT' if strict else ''}: {[sq.label(s) for s in group]} -> "
              f"{entry['sheet']} gutters {entry['gutters_ok']} white {entry['white_lines_in']} "
              f"door {entry['door_heights']} regress {entry['regressions']} dupes {entry['duplicates']}",
              flush=True)
        if clean(entry):
            return entry
    report["dropped_ends"] += drop_end_copies(boards, entry)
    return entry


def draw_setup(book: Path, episode: Episode, number: int, name: str, only_sheet: int | None = None) -> dict:
    sb = storyboard()
    aspect = episode.aspect
    sb.adopt(aspect)          # the cells are cropped to the PLAN's canvas, never to a module default
    boards = episode_home.boards_dir(book, number)
    # the rooms are made before anything is written into them: PIL will not
    # create a parent, and a sheet that drew and then could not be cut has spent
    # the money for nothing
    for room in (sq.cells_in(boards), sq.sheets_in(boards), sq.plates_in(boards), sq.panels_in(boards)):
        room.mkdir(parents=True, exist_ok=True)
    setup = episode.setups[name]
    physical = physicals(book)
    segs = sq.segments(episode.shots, name)
    refs = [sq.plates_in(boards) / f"plate_{name}.png"]
    # the same cab in every setup that shows one; the cab setup's own plate IS that plate
    refs += [sq.plates_in(boards) / f"plate_{p}.png" for p in setup.props if p != name]
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
        entry = draw_sheet(sb, boards, name, k, group, route, grid, setup, physical, refs,
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
    # THE SHEETS ROOM, because `qc.sheets_rollup` globs it there.  This wrote to
    # `boards/` and `migrate_layout.py` moved the existing reports into
    # `boards/sheets/` without moving the writer, so every episode drawn after
    # the migration filed its reports where QC does not look -- and an empty
    # rollup renders as a clean one.
    episode_home.write_json(sq.sheets_in(boards) / f"{stem}.dq.json", report)
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
    ACCEPT_DIRTY = "--accept-dirty" in sys.argv
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--setup=")), None)
    one = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--sheet=")), None)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1, only, one)
