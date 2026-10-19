"""The work grid (timeline debate 2026-10-18, D3; owner go): one row per planned shot, a cell per
stage -- board (the shot's grid), panel, take -- each with the round it is on and the word that
put it there.  A loop is a round on a cell, never an arrow.

`read` is the one reader (the episode folder today; the run stream's round events later);
everything after it is pure.  Directory listings are cached by the folder's mtime so a 2 s poll
lists nothing that did not change (D: is a spinning disk)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from studio.command_center.viewer_model import grid_name

FAIL = re.compile(r"T(\d+)_fail\d+\.mp4$")


@lru_cache(maxsize=512)
def _names(folder: str, mtime_ns: int) -> tuple[str, ...]:
    return tuple(sorted(p.name for p in Path(folder).iterdir()))


def names(folder: Path) -> tuple[str, ...]:
    """A folder's entries, listed again only when it changes; () when it is not there."""
    try:
        return _names(str(folder), folder.stat().st_mtime_ns)
    except OSError:
        return ()


def _json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def superseded(sb: Path) -> list[str]:
    """Stems of every earlier grid draw: storyboard/superseded/ and its reason folders."""
    top = sb / "superseded"
    stems = [Path(n).stem for n in names(top) if n.endswith(".png")]
    for sub in names(top):
        if (top / sub).is_dir():
            stems += [Path(n).stem for n in names(top / sub) if n.endswith(".png")]
    return stems


def take_inputs(tk: Path) -> dict:
    """Which takes exist, passed, failed before, and the faults a cure round named per shot."""
    have = set(names(tk))
    takes = {int(n[1:3]) for n in have if re.fullmatch(r"T\d\d\.mp4", n)}
    passed = {n: _json(tk / f"T{n:02d}.dq.json", {}).get("passed") for n in takes if f"T{n:02d}.dq.json" in have}
    fails: dict[int, int] = {}
    for n in names(tk / "attempts"):
        if m := FAIL.match(n):
            fails[int(m.group(1))] = fails.get(int(m.group(1)), 0) + 1
    faults: dict[int, list[str]] = {}
    for r in (_json(tk / "ladder.json", {}) or {}).get("rounds") or []:
        for shot, words in (r.get("faults") or {}).items():
            faults.setdefault(int(shot), []).extend(words)
    return {"takes": takes, "passed": passed, "fails": fails, "faults": faults}


def read(home: Path, unit: str) -> dict:
    """Everything the grid draws, from the episode folder."""
    sb = Path(home) / "storyboard"
    have = set(names(sb))
    flags = {r["shot"]: r.get("flags") or [] for r in _json(sb / "panel_dq.json", []) or []
             if isinstance(r, dict) and isinstance(r.get("shot"), int)}
    return {"unit": unit, "layout": _json(sb / "layout.json", []) or [],
            "climbed": set((_json(sb / "ladder.json", {}) or {}).get("climbed") or []),
            "grids": {Path(n).stem for n in names(sb / "grids") if n.endswith(".png")},
            "superseded": superseded(sb), "panels": {int(n[5:7]) for n in have if re.fullmatch(r"shot_\d\d\.png", n)},
            "flags": flags, **take_inputs(Path(home) / "takes" / "r2v")}


def cell(state: str, rnd: int = 1, note: str = "") -> dict:
    return {"state": state, "round": rnd, "note": note}


def board_cell(name: str, shots: list[int], inp: dict) -> dict:
    """The grid: drawn (its file, or a cut panel of its shots: a later layout renames grids) or
    waiting; its round (1 + earlier draws); `climbed` when its ladder ran."""
    redraws = sum(1 for s in inp["superseded"] if re.fullmatch(rf"{re.escape(name)}(_v\d+)?", s))
    drawn = name in inp["grids"] or any(n in inp["panels"] for n in shots)
    return cell("done" if drawn else "waiting", 1 + redraws, "climbed" if name in inp["climbed"] else "")


def panel_cell(n: int, inp: dict) -> dict:
    """The panel: cut or waiting; `flag` with its dq words."""
    if n not in inp["panels"]:
        return cell("waiting", 0)
    words = inp["flags"].get(n) or []
    return cell("flag" if words else "done", 1, ", ".join(words))


def take_cell(n: int, inp: dict) -> dict:
    """The take: rendered (done, fail, or checking before its dq), its attempt, the cure's fault."""
    if n not in inp["takes"]:
        return cell("waiting", 0)
    ok = inp["passed"].get(n)
    state = "check" if ok is None else ("done" if ok else "fail")
    return cell(state, 1 + inp["fails"].get(n, 0), ", ".join(dict.fromkeys(inp["faults"].get(n, []))))


def grid(inp: dict) -> list[dict]:
    """One row per planned shot, in shot order: {shot, board, panel, take}."""
    out = []
    for row in inp["layout"]:
        board = board_cell(grid_name(inp["unit"], row), row.get("shots") or [], inp)
        for n in row.get("shots") or []:
            out.append({"shot": n, "board": board, "panel": panel_cell(n, inp), "take": take_cell(n, inp)})
    return sorted(out, key=lambda r: r["shot"])


def clean(r: dict) -> bool:
    return all(r[k]["state"] == "done" and r[k]["round"] == 1 and not r[k]["note"] for k in ("board", "panel", "take"))


def fold(rows: list[dict]) -> list[dict]:
    """Runs of clean shots fold into `{clean: "00–05", n}`; every other row stays."""
    out, run = [], []
    for r in rows + [None]:
        if r is not None and clean(r):
            run.append(r["shot"])
            continue
        if run:
            span = f"{run[0]:02d}" if len(run) == 1 else f"{run[0]:02d}–{run[-1]:02d}"
            out.append({"clean": span, "n": len(run)})
            run = []
        if r is not None:
            out.append(r)
    return out
