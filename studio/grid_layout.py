"""The layout rule: which shots share a storyboard grid, and the grid's shape.

    storyboard/layout.json    [{setup, cols, rows, tag?, shots}, ...]

Step 07 used to park the unit on this file ("choose cols x rows per setup")
and the 2026-09-22 audit left the 2x2 minimum an open owner question (Tier 0,
D3: ep09 drew 1x1, 2x1 and 3x1 because its setups hold 2, 3, 5 and 8 shots).
This rule SUPERSEDES D3 as of 2026-09-24 (decision
2026-09-24-automate-the-taste-gates: no episode step parks on a person):

- a grid holds at most nine cells and `cols x rows == shots`, because a blank
  cell is a cell the drawer fills with its own invention (`grid_shape`);
- a count with no square-ish shape splits into the fewest, most balanced
  pieces: 5 -> 3 + 2, 7 -> 4 + 3, 10 -> 6 + 4, 19 -> 6 + 4 + 9;
- a setup that mixes a FACE (close sizes) with a WIDE puts each face in a 1x1
  of its own -- the skill's rule, measured: a mixed 2x2 drew a medium close
  as a full figure, and a 1x1 holds its head count where a 2x2 does not;
- a 1x1 is allowed; a strip of four or more is not (it is split).

Shots keep plan order inside a grid; a setup's grids are named by a tag so two
grids of one setup never share a file.
"""
from __future__ import annotations

import json
from pathlib import Path

MOST = 9
"""Cells a grid may hold."""
GOOD = (1, 2, 3, 4, 6, 8, 9)
"""Counts that lay out as one grid without a hole or a long strip."""
FACES = ("extreme_close", "close", "medium_close")
WIDES = ("wide", "full")
FILE = Path("storyboard") / "layout.json"


def shape(n: int) -> tuple[int, int]:
    """(cols, rows) for n cells, as square as n allows, wider than tall."""
    if n not in GOOD:
        raise ValueError(f"{n} cells is not one grid; split it first (pieces)")
    cols = min((c for c in range(1, n + 1) if n % c == 0 and c * c >= n), key=lambda c: c * c - n)
    return cols, n // cols


def pieces(n: int) -> list[int]:
    """The grid sizes n shots split into: the fewest, most balanced GOOD parts."""
    if n in GOOD:
        return [n]
    for small in range(n // 2, 0, -1):
        if small in GOOD and (n - small) in GOOD:
            return [n - small, small]
    return pieces(n - n // 2) + pieces(n // 2)


def mixed(shots: list[dict]) -> bool:
    """Does the setup hold a face AND a wide?"""
    sizes = {s.get("size", "") for s in shots}
    return bool(sizes & set(FACES)) and bool(sizes & set(WIDES))


def row(setup: str, cols: int, rows: int, shots: list[int], tag: str = "") -> dict:
    out = {"setup": setup, "cols": cols, "rows": rows, "shots": list(shots)}
    return {**out, "tag": tag} if tag else out


def rows_for(setup: str, shots: list[dict]) -> list[dict]:
    """One setup's grids: the run of non-faces in pieces, then every face alone
    when the setup mixes sizes."""
    faces = [s for s in shots if s.get("size") in FACES] if mixed(shots) else []
    rest = [int(s["index"]) for s in shots if s not in faces]
    parts, out, at = pieces(len(rest)) if rest else [], [], 0
    for k, n in enumerate(parts):
        tag = chr(ord("a") + k) if len(parts) > 1 else ""
        out.append(row(setup, *shape(n), rest[at:at + n], tag))
        at += n
    return out + [row(setup, 1, 1, [int(s["index"])], f"s{int(s['index']):02d}") for s in faces]


def layout(setups: dict, shots: list[dict]) -> list[dict]:
    """Every grid to draw, setups in plan order, shots in plan order."""
    order = list(setups or {}) + [s["setup"] for s in shots if s["setup"] not in (setups or {})]
    out = []
    for setup in dict.fromkeys(order):
        own = [s for s in shots if s["setup"] == setup]
        if own:
            out += rows_for(setup, own)
    return out


def name_of(number: int, grid: dict) -> str:
    """The grid's file stem, the way grids.py names it (episode-scoped)."""
    tag = grid.get("tag") or ""
    return f"ep{number:02d}_grid_{grid['setup']}_{grid['cols']}x{grid['rows']}{('_' + tag) if tag else ''}"


def argv(grid: dict) -> list[str]:
    """`<setup> <cols> <rows> [tag] --shots=..`, the way grids.py reads them."""
    out = [str(grid["setup"]), str(int(grid["cols"])), str(int(grid["rows"]))]
    out += [str(grid["tag"])] if grid.get("tag") else []
    return out + ([f"--shots={','.join(str(i) for i in grid['shots'])}"] if grid.get("shots") else [])


def write(home: Path, rows: list[dict]) -> Path:
    target = Path(home) / FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return target


def read(home: Path) -> list[dict]:
    target = Path(home) / FILE
    return list(json.loads(target.read_text(encoding="utf-8"))) if target.exists() else []
