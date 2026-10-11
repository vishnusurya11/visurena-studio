#!/usr/bin/env python
"""Phase-0 CPU prework (S_skeptic_verdict.md §2 rows 84-88, §4 "before the pause").

1. Content-matched ruler calibration: the narrator's villa front and study in ep01-03
   (owner: good, refs-only Krea2) against the same places in ep26-27 (owner: low
   quality, Qwen panels). A ruler votes on the bench only at AUC >= 0.75.
2. The ep04 split of cause 2: ep04 ran Singularity int8 + the turbo LoRA at 1.0+0.7 on
   the refs-only recipe of ep01-03. Its takes that staged the SAME place picture
   (same `wide_establishing_<md5>` bytes) as an ep01-03 take are compared ruler by ruler.

    uv run --no-sync --group measures python scripts/bench/calibrate.py <out_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.bench import rulers  # noqa: E402

EP = ROOT / "library/20260827135508_the-war-of-the-worlds/episodes"
EARLY = {"ep01": ["T03", "T18", "T19", "T20", "T21", "T22"], "ep02": ["T00", "T01", "T20", "T21", "T22"],
         "ep03": ["T11"]}
LATE = {"ep26": ["T15", "T16", "T17"],
        "ep27": ["T00", "T01", "T02", "T03", "T10", "T11", "T12", "T13", "T16", "T22", "T23", "T24", "T25"]}
VOTE_AT = 0.75


def takes(sets: dict) -> list[Path]:
    return [EP / ep / "takes/r2v" / f"{t}.mp4" for ep, ts in sets.items() for t in ts]


def wides(ep: str) -> dict[str, list[str]]:
    """take -> the staged place pictures' content names."""
    out = {}
    for g in sorted((EP / ep / "takes/r2v").glob("T??.graph.json")):
        graph = json.loads(g.read_text("utf-8"))
        out[g.name[:3]] = [n["inputs"]["image"] for n in graph.values()
                           if n.get("class_type") == "LoadImage" and n["inputs"]["image"].startswith("wide_")]
    return out


def ep04_pairs() -> tuple[list[Path], list[Path], list[str]]:
    early = {w: f"{ep}/{t}" for ep in ("ep01", "ep02", "ep03") for t, ws in wides(ep).items() for w in ws}
    shared = sorted({w for ws in wides("ep04").values() for w in ws} & set(early))
    e04 = [EP / "ep04/takes/r2v" / f"{t}.mp4" for t, ws in wides("ep04").items() if set(ws) & set(shared)]
    e13 = [EP / ep / "takes/r2v" / f"{t}.mp4" for ep in ("ep01", "ep02", "ep03")
           for t, ws in wides(ep).items() if set(ws) & set(shared)]
    return e13, e04, shared


def table(good: list[dict], bad: list[dict]) -> dict:
    out = {}
    for k, d in rulers.DIRECTION.items():
        g = [r[k] * d for r in good if r.get(k) is not None]
        b = [r[k] * d for r in bad if r.get(k) is not None]
        a = rulers.auc(g, b) if g and b else None
        med = lambda xs: round(sorted(xs)[len(xs) // 2] * d, 4) if xs else None  # noqa: E731
        out[k] = {"auc": a, "votes": bool(a is not None and a >= VOTE_AT), "good_median": med(g),
                  "bad_median": med(b), "n": [len(g), len(b)]}
    return out


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    det = rulers.detector()
    m = lambda ps: {str(p): rulers.measure(p, det) for p in ps if p.exists()}  # noqa: E731
    early, late = m(takes(EARLY)), m(takes(LATE))
    e13, e04, shared = ep04_pairs()
    a13, a04 = m(e13), m(e04)
    doc = {"calibration": table(list(early.values()), list(late.values())),
           "ep04_split": {"shared_place_pictures": shared,
                          "ep01_03_vs_ep04": table(list(a13.values()), list(a04.values())),
                          "ep04_vs_late": table(list(a04.values()), list(late.values()))},
           "per_take": {"early": early, "late": late, "ep01_03_shared": a13, "ep04_shared": a04}}
    (out_dir / "calibration.json").write_text(json.dumps(doc, indent=1), "utf-8")
    print(json.dumps({k: v for k, v in doc.items() if k != "per_take"}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
