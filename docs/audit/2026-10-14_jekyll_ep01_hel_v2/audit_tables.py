"""Jekyll HEL ep01 v2: the per-take DQ coverage and per-shot cast tables, read off disk ($0, read-only).

    uv run python docs/audit/2026-10-14_jekyll_ep01_hel_v2/audit_tables.py [episode_dir] > tables.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EP = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    ROOT / "library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde" / "episodes" / "ep01")
SHORT = {"gabriel_john_utterson": "L", "richard_enfield": "E", "edward_hyde": "H", "child_of_hyde_incident": "G"}
WEARS = {"lawyer's dark suit": "L", "fashionable dark frock coat": "E", "narrow-shouldered frame": "H",
         "pinafore": "G"}
LABELS = {"Mr. Utterson": "L", "the lawyer": "L", "Mr. Enfield": "E", "Mr. Hyde": "H", "the little man": "H",
          "the girl": "G", "the child": "G"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def who(ids) -> str:
    return ",".join(SHORT.get(i, i) for i in ids) or "-"


def row_of(gates: list[dict], name: str) -> dict | None:
    return next((g for g in gates if g.get("name") == name), None)


def cell(g: dict | None) -> str:
    if g is None:
        return "absent"
    note = str(g.get("note") or "")
    if note.startswith("not measured") or note.startswith("n/a"):
        return f"n/m ({note[:40]})"
    mark = "PASS" if g.get("ok") else ("FAIL" if g.get("hard") else "adv")
    return f"{mark} {note[:48]}"


def dq_table() -> list[str]:
    room = EP / "takes" / "r2v"
    out = ["| take | verdict | attempts | hard rows ran / failed | frozen-whole | gait | identity | content | "
           "unmeasured rows |", "|---|---|---|---|---|---|---|---|---|"]
    for path in sorted(room.glob("T[0-9][0-9].dq.json")):
        d = load(path)
        gates = d.get("gates") or []
        hard = [g for g in gates if g.get("hard")]
        failed = [g["name"] for g in hard if not g.get("ok")]
        unmeasured = [g["name"] for g in gates if str(g.get("note", "")).startswith(("not measured", "n/a"))]
        c = load(room / f"{path.name[:3]}.content.json") or {}
        content = "PASS" if c.get("passed") else ("FAIL " + "; ".join(map(str, c.get("faults") or []))[:60] if c else "absent")
        out.append(f"| {path.name[:3]} | {'PASS' if d.get('passed') else 'FAIL'} {d.get('score')} | "
                   f"{len(d.get('attempts') or [])} | {len(hard)} / {', '.join(failed) or '0'} | "
                   f"{cell(row_of(gates, 'frozen-whole'))} | {cell(row_of(gates, 'gait'))} | "
                   f"{cell(row_of(gates, 'identity'))} | {content} | {', '.join(unmeasured) or '-'} |")
    return out


def grid_people(ep: Path) -> dict[int, str]:
    """Shot -> who the grid that drew it staged by sheet (its prompt's reference lines)."""
    out: dict[int, str] = {}
    for js in sorted((ep / "storyboard" / "grids").glob("*.json")):
        g = load(js)
        txt = js.with_suffix(".txt").read_text(encoding="utf-8") if js.with_suffix(".txt").exists() else (g.get("prompt") or "")
        staged = []
        for line in re.findall(r"The person in <image\d> wears:[^\n]*", txt):
            hit = next((v for k, v in WEARS.items() if k in line), None)
            if hit and hit not in staged:
                staged.append(hit)
        for s in g.get("shots") or []:
            out[int(s)] = f"{js.stem.replace('ep01_grid_', '')}: {','.join(staged) or 'none'}"
    return out


def take_people(ep: Path) -> dict[int, str]:
    recs = load(ep / "takes" / "r2v" / "shots.json") or []
    out = {}
    for r in recs:
        staged = [SHORT.get(p.split("/")[2], p.split("/")[2]) for p in r.get("refs") or [] if "/characters/" in p]
        out[r["index"]] = ",".join(staged) or "none"
    return out


def cast_table() -> list[str]:
    plan = load(EP / "plan.json")
    panels = {p["shot"]: p for p in (load(EP / "storyboard" / "panel_content.json") or [])}
    grids, takes = grid_people(EP), take_people(EP)
    out = ["| shot | setup | size | present (setup cast) | faces | extras | enters | grid sheets | take sheets | "
           "panel people | take people |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in plan["shots"]:
        i = s["index"]
        tc = load(EP / "takes" / "r2v" / f"T{i:02d}.content.json") or {}
        p = panels.get(i, {})
        out.append(f"| {i} | {s['setup']} | {s['size']} | {who(plan['setups'][s['setup']]['cast'])} | "
                   f"{who(s['faces'])} | {s.get('extras', 0)} | {who(s.get('enters') or [])} | {grids.get(i, '-')} | "
                   f"{takes.get(i, '-')} | {p.get('people', '-')} | {tc.get('people', '-')} |")
    return out


if __name__ == "__main__":
    print("\n".join(dq_table()))
    print()
    print("\n".join(cast_table()))
