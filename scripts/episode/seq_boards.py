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
setup; `draw()` returns early only when the sheet's `.prompt.txt` still matches
the prompt it would send, so a re-run costs nothing for UNCHANGED sheets and
redraws the ones whose prose you edited.  Owner's design, 2026-09-11: takes are
windows on this board.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image

from studio.episode_home import episode_arg
from studio import actor_gate, episode_board as board, episode_gutter, episode_home, episode_seq_board as sq, prop_refs, route_gate, sheet_gate
from studio import cast_refs, look_gate, plan_gates
from studio import house_style
from studio import episode_spec as ep_spec
from studio import frame_match
from studio.episode_spec import Episode, Setup
from studio.trailer_refs import contract_description


def storyboard():
    spec = importlib.util.spec_from_file_location("ep_storyboard", ROOT / "scripts/episode/storyboard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def physicals(book: Path) -> dict[str, dict]:
    """Every character as `{"physical": <invariant>, "wardrobe": {<state>: <garments>}}`.

    MEASURED on episode 9: this returned the physical ALONE, the Part Two rows
    keep their garments in `wardrobe[state]`, and the sheet's WARDROBE block --
    "these stay the same in every panel" -- named no garment for Lucy, Hope or
    Ferrier on any sheet.  `sq.look` reads either shape, so the London callers
    that hand a bare string are unchanged."""
    return {r["entity_id"]: {"physical": contract_description(r.get("physical", "")),
                             "wardrobe": dict(r.get("wardrobe") or {})}
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

    AND IT LOOKS AS FAR IN AS THE TAKE GUARD DOES, by asking it.  This used to
    stop at `GUTTER_EDGE` = 6 pixels while `episode_gutter.band` -- which crops
    the same leak out of a rendered take -- looks `MAX_FRAC` = 8 % of the side,
    61 pixels of a 768 cell.  A residue between the two passed here and was
    cropped there, and the crop changes the picture's geometry, so the assembled
    frames stop matching the take they were cut from and the EDIT gate fails the
    whole episode.

    MEASURED, episode 8: Q17_0 and Q18_0 carry a paper-white band at rows 8 to 19
    from the bottom, eight pixels past where this stopped looking.  Both shipped,
    the take guard cropped 22 and 21 pixels off T17 and T18, and qc reported
    "edit: FAIL | segments off 2/28" on an episode whose pictures were fine.

    `episode_gutter`'s window is the calibrated one -- measured on episode 1,
    where four takes ended with a paper-white band the owner saw as a white bar
    at 28 s and 37 s -- so it owns the number and this asks for it."""
    bad = []
    for c in cells:
        a = np.asarray(Image.open(c).convert("L"), dtype=float)
        if any(episode_gutter.band(a, edge) > 0 for edge in episode_gutter.EDGES):
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
    cells = [sb.conform(sheet, sq.cells_in(boards) / sq.named(s), boxes[i])
             for i, s in enumerate(group)]
    heights, regress = ladder_check(cells, group, route, setup)
    looked = look_of(cells, out.stem)
    row_bands, col_bands = board.bands(grey, 0), board.bands(grey, 1)
    # ALTERNATE pairs are a row in the report and nothing more: an alternate
    # feeds no take, so a twin there (ep10 Q26_0 / Q26_0A, 0.718) buys no retry.
    alike = sq.alt_duplicates(cells, group)
    for a, b in alike:
        print(f"  WATCH {out.stem}: ALTERNATE {b} reads as {a} (over ALIKE {sq.ALIKE})", flush=True)
    return {"sheet": sheet.name, "route": route, "cells": [c.name for c in cells],
            "gutters_ok": len(row_bands) == rows - 1 and len(col_bands) == cols - 1,
            "white_lines_in": white_lines(cells), "door_heights": heights, "regressions": regress,
            "duplicates": sq.duplicates(cells, group), "alternate_duplicates": alike,
            "strict": strict, "look": looked}


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


def grid_of(cells: int, a_cell: Path) -> tuple[int, int]:
    """The (cols, rows) a sheet of this many cells was laid out on.

    The aspect comes from the CELL ON DISK, not from a module default. A cell
    is cut to the plan's delivery shape, so a square cell means a square sheet
    table -- and reading it off the artefact is the only way a tool that did
    not load the plan can be right about it. (Measured the hard way minutes
    earlier: `storyboard.conform` reads module globals, and an ad-hoc re-cut
    that did not call `adopt` wrote four 768x1344 cells into a 1:1 episode.)"""
    w, h = Image.open(a_cell).size
    cols, rows, _canvas = sq.grid(cells, "1:1" if w == h else "9:16")
    return cols, rows


def remeasure(boards: Path) -> list[str]:
    """Re-take every sheet report's cell verdict from the cells on disk. FREE.

    A gate that is recalibrated has to be re-runnable on work already paid for.
    MEASURED, episode 9: `episode_gutter.FLAT` was moved off a London number onto
    one calibrated for the desert, every cell went clean, the master passed and
    edit integrity passed -- and `qc` still failed the episode, because it reads
    `seq_<setup>.dq.json` and that file records what was measured AT DRAW TIME.
    Redrawing to refresh a verdict costs $0.13 a sheet and throws away pictures
    that were never wrong.

    It is NOT forgiving: it reads the cells again and reports whatever it finds.
    A report whose cells are missing is left alone -- an empty measurement that
    reads as a pass is this repo's most-found fault."""
    changed = []
    for path in sorted((boards / "sheets").glob("seq_*.dq.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        cells_room, sheets_room, took = sq.cells_in(boards), boards / "sheets", False
        for entry in report.get("sheets", []):
            on_disk = [cells_room / n for n in entry.get("cells", [])]
            if not all(c.exists() for c in on_disk):
                continue
            entry["white_lines_in"] = white_lines(on_disk)
            # `gutters_ok` is derived from the SHEET, and the sheet is on disk too,
            # so it is retaken the same way rather than left at its draw-time value.
            drawn = sheets_room / entry["sheet"]
            if drawn.exists():
                grey = np.asarray(Image.open(drawn).convert("L"), dtype=float)
                cols, rows = grid_of(len(entry["cells"]), on_disk[0])
                entry["gutters_ok"] = (len(board.bands(grey, 0)) == rows - 1
                                       and len(board.bands(grey, 1)) == cols - 1)
            took = True
        if not took:
            continue
        finals = report["sheets"]
        report["white_lines_in"] = [n for e in finals for n in e["white_lines_in"]]
        report["passed"] = all(clean(e) and e["gutters_ok"] for e in finals)
        path.write_text(json.dumps(report, indent=1), encoding="utf-8")
        changed.append(report.get("setup") or path.stem)
    return changed


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


def drop_end_copies(boards: Path, entry: dict, group: list[dict] | None = None) -> list[dict]:
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
            other = a if end == b else b
            start = sq.cells_in(boards) / f"{other}.png"
            # the START seg's motion: `end_panel` blanks it on the END seg
            said = next((s.get("motion", "") for s in (group or [])
                         if not s.get("end")
                         and sq.cell_name(s["shot"], s["sub"], False)[:-4] == other), "")
            # THE MEASURED VERDICT, not one hardcoded word for two opposite
            # faults. All seven of episode 6's retired ENDs were re-stagings
            # (0.330 down to -0.007) and every one was logged as "a copy".
            sim = float("nan")
            if start.exists():
                sim = frame_match.similarity(frame_match.load(start),
                                             frame_match.load(old / cell.name))
            dropped.append({"dropped_end": end, "similarity": round(float(sim), 3),
                            "reason": sq.drop_reason(end, other, sim, said)})
    return dropped


def reroll_reason(entry: dict) -> str:
    """Why a strict retry of this attempt would be the same prompt drawn again.

    MEASURED on episode 10: the mountain sheet was refused by `white_lines()`
    alone (Q02_0's prompted moonlit rifle barrel), `strict_prefix` had no
    duplicate and no regression to name, and the retry drew the byte-identical
    prompt for $0.13 -- the two sheets differ by two blank lines."""
    faults = [f"white_lines_in {entry['white_lines_in']}" for _ in [0] if entry.get("white_lines_in")]
    if not entry.get("gutters_ok", True):
        faults.append("gutters_ok False")
    return (f"the sheet failed on {' and '.join(faults) or 'nothing the prefix names'}, which the STRICT "
            f"prefix cannot address (it names duplicates and ladder regressions only), so the retry "
            f"would be a re-roll of the same prompt; redraw the cell alone (redraw_panel.py) or accept it")


def strict_text(entry: dict, setup: Setup, text: str, name: str, k: int) -> str:
    """The strict retry's prompt, or "" when the retry has no offender to name
    and would be a re-roll: the refusal is written into the entry and printed."""
    prefix = sq.strict_prefix(entry["duplicates"], entry["regressions"], setup)
    if not prefix:
        entry["strict_refused"] = reroll_reason(entry)
        print(f"  {name} sheet {k}: strict retry refused -- {entry['strict_refused']}", flush=True)
        return ""
    return prefix + "\n\n" + text


def draw_sheet(sb, boards: Path, name: str, k: int, group: list[dict], route: list[int], grid: tuple,
               setup: Setup, physical: dict[str, str], refs: list[Path], report: dict,
               aspect: str = "9:16", props: list[dict] | None = None) -> dict:
    """One sheet: the draw, and one strict retry that names its own offender --
    and no retry at all when it has no offender to name (`strict_text`)."""
    entry = {"duplicates": [], "regressions": []}
    for strict in (False, True):
        text = sq.prompt(group, setup, physical, previous=False, first=(k == 0), geography=route,
                         aspect=aspect, props=props)
        if strict:
            if not (text := strict_text(entry, setup, text, name, k)):
                break
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
    report["dropped_ends"] += drop_end_copies(boards, entry, group)
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
                                if r.get('kind') == 'prop'], setup=setup)
    # AND IT SAYS WHAT IT DROPPED.  This filter was silent, so episode 7's
    # terrier -- the one prop whose bible note says its identity has to hold
    # across three shots -- was dropped from the references of three paid
    # sheets without a word.  The plan gate in `main` now refuses before the
    # money; this stays as the last word in case a row is written afterwards.
    for gone in [r for r in shown if not (book / r['rel_path']).exists()]:
        print(f"  WATCH {name}: {gone['entity_id']} is named in this setup and its "
              f"reference {gone['rel_path']} is not on disk -- drawn unbound", flush=True)
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



def book_words(book: Path) -> str:
    """Every chapter of the source, as one string, for the quote gate.

    THE WHOLE BOOK AND NOT THIS CHAPTER: a recap line quotes an EARLIER chapter,
    and episode 5's longest lift is Doyle's chapter III describing the corpse,
    carried forward into episode 5's second line.

    AND THE BOOK WITH ITS ATTRIBUTIONS SPLICED OUT.  Doyle writes the tag inside
    the speech -- `," remarked Lestrade, "` -- and there are 222 of them, each
    one splitting a quotation into two shorter runs.  Episode 7's closing line is
    such a speech with the tag deleted, every word Doyle's, and it scored 11
    against the raw source because no run there is longer than the half the tag
    left.  It is 17, the longest lift in the series, and it is the last thing the
    episode says."""
    out = []
    for path in sorted((Path(book) / "source" / "chapters").glob("ch_*.json")):
        doc = episode_home.read_json(path)
        out.append(" ".join(p["text"] for p in doc.get("paragraphs", [])))
    return ep_spec.quote_corpus(" ".join(out))

def unbound_cast(book: Path, episode: Episode) -> list[str]:
    """Every reason a cast member of this episode is not ready for a paid sheet.

    Episode 9's three leads had no `sheet` block, so their cards were built from
    the wardrobe sentence alone; Lucy's was drawn by a male-only template; and
    the cast gate never ran between the cards and the sheets. `cast_refs.bound`
    knows the reasons; this asks for each person in the state their setup puts
    them in, once."""
    out, seen = [], set()
    for setup in episode.setups.values():
        for who in setup.cast:
            if (who, setup.state) in seen:
                continue
            seen.add((who, setup.state))
            out += [f"{who} ({setup.state}): {why}" for why in cast_refs.bound(book, who, setup.state)]
    return out


def look_of(cells: list[Path], name: str) -> list[str]:
    """The look gate on one sheet's cells: printed per picture, and the
    episode-level verdict is left to `main` after every sheet is in."""
    said = look_gate.faults(cells)
    for line in said:
        print(f"  WATCH {name}: LOOK {line}", flush=True)
    return said


def main(book_id: str, number: int, only: str | None = None, sheet: int | None = None) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    # THE LAST FREE MOMENT.  A wrong actor drawn into a sheet is paid for twice --
    # once to draw it and once to draw it again -- and episode 3 shipped a whole
    # master with Holmes making Gregson's gesture because nothing read the plan
    # before the draw.  `actor_gate` was written and then called by nothing, which
    # is a comment, not a gate.
    # THE RUN DECLARES ITS PLACE before it makes anything. Episode 8 was drawn
    # and rendered saying "1881 London" over an 1847 Utah desert because the
    # palette reached the location plate alone.
    house_style.adopt(episode.where, episode.light)
    # THE LIGHT, THE PLAN AND THE CAST, before a cent (docs/analysis/ep08_ep09_why_worse.md).
    # Episode 9 passed every gate below and looked worse than 4-7: no black floor
    # because its palette was a colour list, a first-frame prose a quarter of ep04-08's,
    # nine identical closes, a rescue that never happens, and a cast that was never
    # bound. Each of these is free to read and refuses here, in this order.
    if unlit := house_style.faults(episode):
        raise SystemExit("G-LIGHT refuses the plan:\n  " + "\n  ".join(unlit))
    for note in plan_gates.advisories(episode, plan_gates.series_lines(book, number), rate=plan_gates.series_rate(book, number)):
        print(f"  ADVISORY {note}", flush=True)
    if thin := plan_gates.faults(episode):
        raise SystemExit("the plan fails the authoring gates:\n  " + "\n  ".join(thin))
    if loose := unbound_cast(book, episode):
        raise SystemExit("the cast is not bound (cast_refs.bound):\n  " + "\n  ".join(loose))
    for note in actor_gate.advisory_episode(episode):
        print(f"  ADVISORY {note}", flush=True)
    if faults := actor_gate.hard_episode(episode):
        raise SystemExit("the plan fails the actor gate:\n  " + "\n  ".join(faults))
    # AND THE MOTION, for the same reason and at the same price.  A head with no
    # camera move renders a photograph -- every one of the 10 stillest takes in
    # episodes 4-5 is one, and not one of the 19 takes whose head names a move
    # was ever penalised (p = 0.0041).  Drawing its sheet costs $0.20 before the
    # GPU learns that.
    still = episode.still_motions()
    for index, code, why in (f for f in still if f[1] not in ep_spec.HARD_MOTION):
        print(f"  ADVISORY shot {index} {code}: {why}", flush=True)
    if hard := [f for f in still if f[1] in ep_spec.HARD_MOTION]:
        raise SystemExit("the plan fails the motion gate:\n  "
                         + "\n  ".join(f"shot {i} {c}: {w}" for i, c, w in hard))
    # AND WHO IS CARRYING WHAT.  Episode 4's shot 2 put Watson's black stick and
    # Holmes's sticking plaster on ONE hand in a full-frame insert -- authored in
    # the plan, drawn into the paid cell Q02_0.png, then rendered.  Measured over
    # the 140 shots on disk: one crossed mark, and it is that one.
    refs = episode_home.read_json(book / "refs" / "refs.json")["refs"]
    crossed, vague = ep_spec.plan_marks(episode, refs)
    for note in vague:
        print(f"  ADVISORY marks not measured -- {note}", flush=True)
    if crossed:
        raise SystemExit("the plan fails the mark gate:\n  " + "\n  ".join(crossed))
    # AND THE NARRATION IS WRITTEN, NOT COPIED.  The 8-word ceiling has been in
    # the spec since episode 1 and gated nothing: lines over it run 1, 0, 0, 5,
    # 6, 4 across the six published plans, and episodes 2 and 3 -- the two that
    # quote nothing -- are the two a writing review rated highest.
    said = book_words(book)
    lifted, borrowed = ep_spec.quoted_lines(
        [l.model_dump() for l in episode.lines], said)
    for line in borrowed:
        print(f"  ADVISORY line {line['index']} speaks {line['lifted']} of Doyle's own "
              f"words; dialogue may, and the craft is in the TRIM", flush=True)
    if lifted:
        raise SystemExit(
            "the plan fails the quote gate -- narration is Watson's own prose:\n  "
            + "\n  ".join(f"line {l['index']} lifts {l['lifted']} consecutive words: "
                           f"{l['text']!r}" for l in lifted))
    # AND WATSON IS IN HIS OWN EPISODE.  Measured over the seven delivered plans,
    # narration lines in which the narrator is the acting subject: ep01 4, ep02 5,
    # ep03 2, ep04 1, ep05 1, ep06 3, ep07 0 -- and episode 7 is the one that
    # reads as a police report. Its whole first person is one `me` and one `our`,
    # in a single line where he is the object of somebody else's request, in the
    # chapter where a doctor hands an animal over to settle a question.
    said = [l.model_dump() for l in episode.lines]
    in_shot = {who for s in episode.setups.values() for who in s.cast}
    telling = next((l["speaker"] for l in said if l["kind"] == "narration"), "")
    if quiet := ep_spec.silent_narrator(said, cast=in_shot, narrator=telling):
        raise SystemExit("the plan fails the witness gate:\n  " + "\n  ".join(quiet))
    print(f"  first person {ep_spec.first_person_share(said) * 100:.1f}% of narration "
          f"(delivered 0.7-6.3; the two best-rated episodes are 5.7 and 4.4), "
          f"{len(ep_spec.narrator_acts(said))} line(s) where Watson acts", flush=True)
    # AND EVERY REFERENCE THE BIBLE DECLARES IS ACTUALLY ON DISK.  A row that
    # names a picture nobody drew is dropped by `draw_setup`'s existence filter,
    # which was silent: episode 7's terrier was unbound across three $0.13
    # sheets and three rendered shots, and its own bible note says its identity
    # had to hold.  Free to check, here, before the first sheet.
    if blank := prop_refs.undrawn(refs, book):
        raise SystemExit("the bible declares references that are not on disk:\n  "
                         + "\n  ".join(blank))
    for name in episode.setups:
        if only and name != only:
            continue
        draw_setup(book, episode, number, name, sheet)
    # THE LOOK OF THE WHOLE EPISODE, once every sheet is in. A single pale cell is
    # a picture of a pale place; an episode whose MEDIAN cell has no black floor,
    # or is one hue, is what the owner called "a print, not a projection". Reported
    # per sheet above as it was cut; refused here on the roll-up, before the GPU.
    cells = sorted(p for p in sq.cells_in(episode_home.boards_dir(book, number)).glob("Q*.png")
                   if not p.stem.endswith(("E", "A")))
    if flat := [f for f in look_gate.faults(cells) if f.startswith("episode:")]:
        raise SystemExit("the drawn episode fails the look gate (studio/look_gate.py):\n  "
                         + "\n  ".join(flat) + "\n  Rewrite `light` and the setups' light, then redraw.")


if __name__ == "__main__":
    if "--remeasure" in sys.argv:
        # FREE: retake every sheet verdict from the cells on disk, for when a
        # gate has been recalibrated since the draw. Never redraws.
        number = episode_arg(sys.argv)
        boards = episode_home.boards_dir(episode_home.book_dir(sys.argv[1]), number)
        took = remeasure(boards)
        print(f"re-measured {len(took)} sheet report(s): {', '.join(took) or 'none'}")
        raise SystemExit(0)
    ACCEPT_DIRTY = "--accept-dirty" in sys.argv
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--setup=")), None)
    one = next((int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--sheet=")), None)
    main(sys.argv[1], episode_arg(sys.argv), only, one)
