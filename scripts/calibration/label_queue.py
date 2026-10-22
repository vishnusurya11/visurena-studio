#!/usr/bin/env python
"""The owner's label queue: a seeded random draw within strata of SHIPPED artefacts.

    uv run python scripts/calibration/label_queue.py <labels.jsonl>... --out <queue.jsonl> [--seed N]

Strata (fleet H ruling A17, with the skeptic's F2 fixes):
- `R:<gate>`      shipped takes a HARD take-gate row refused (hard and not ok);
                  a soft deduction refuses nothing and makes no stratum;
- `R-panel:<why>` shipped panels a panel check refused (a panel_dq flag, or
                  `content` for a failed content read);
- `P` / `P-panel` shipped takes / panels nothing refused: the only view of misses.

Each stratum is a simple random sample from its own seeded stream; the draw is
then de-duplicated per artefact, so a take two gates refused is ONE item naming
both strata, and `p_select` is its true inclusion probability over every stratum
it belongs to: 1 - prod(1 - n_h / N_h).  The random strata hold at least
RANDOM_FLOOR of the queue.  The sizes and the floor are CONVENTIONS from the
ruling, not measurements.  CPU only; reads the harvested rows, writes the queue.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import casebook  # noqa: E402
from studio.casebook import Row  # noqa: E402

PER_GATE, P_SIZE, PANEL_SIZE = 10, 60, 10
RANDOM_FLOOR = 0.20
"""The share of the queue drawn from the random strata (P, P-panel): a convention, not a measurement."""
RANDOM = ("P", "P-panel")


def shipped(row: Row) -> bool:
    """A kept artefact that went out: the harvest's default row, never a losing attempt."""
    return row.verdict_by == "default" and "/attempts/" not in row.path and "_fail" not in row.path


def take_strata(row: Row) -> list[str]:
    gates = (row.machine.get("take_dq") or {}).get("gates") or []
    hard = sorted({g["name"] for g in gates if g.get("hard") and not g.get("ok", True)})
    return [f"R:{name}" for name in hard] or ["P"]


def panel_strata(row: Row) -> list[str]:
    flags = sorted(set((row.machine.get("panel_dq") or {}).get("flags") or []))
    failed = (row.machine.get("panel_content") or {}).get("passed") is False
    named = [f"R-panel:{f}" for f in flags] + (["R-panel:content"] if failed else [])
    return named or ["P-panel"]


def strata(rows: list[Row]) -> dict[str, list[tuple[str, str]]]:
    """Stratum -> its members (codex, path), sorted, from the shipped takes and panels."""
    out: dict[str, set] = {}
    for row in rows:
        if not shipped(row) or row.kind not in ("take", "panel"):
            continue
        for name in (take_strata(row) if row.kind == "take" else panel_strata(row)):
            out.setdefault(name, set()).add((row.codex, row.path))
    return {name: sorted(members) for name, members in sorted(out.items())}


def size_of(name: str, per_gate: int, p_size: int, panel_size: int) -> int:
    if name == "P":
        return p_size
    return panel_size if name.startswith(("R-panel", "P-panel")) else per_gate


def draw(members: dict[str, list], sizes: dict[str, int], seed: int) -> dict[str, list]:
    """Each stratum's simple random sample, from its own stream: one stratum never moves another."""
    return {name: random.Random(f"{seed}:{name}").sample(pop, min(sizes[name], len(pop)))
            for name, pop in members.items()}


def floor_p(members: dict[str, list], sizes: dict[str, int], seed: int) -> dict[str, int]:
    """Grow P until the random strata hold RANDOM_FLOOR of the de-duplicated queue (or P runs out)."""
    sizes = dict(sizes)
    while "P" in members and sizes["P"] < len(members["P"]):
        drawn = draw(members, sizes, seed)
        unique = {k for keys in drawn.values() for k in keys}
        rand = {k for name in RANDOM if name in drawn for k in drawn[name]}
        if not unique or len(rand) / len(unique) >= RANDOM_FLOOR:
            break
        sizes["P"] += 1
    return sizes


def inclusion(key: tuple, members: dict[str, list], sizes: dict[str, int]) -> float:
    """1 - prod(1 - n_h / N_h) over every stratum the artefact belongs to."""
    miss = math.prod(1 - min(sizes[h], len(pop)) / len(pop) for h, pop in members.items() if key in pop)
    return round(1 - miss, 6)


def build(rows: list[Row], seed: int = 0, per_gate: int = PER_GATE, p_size: int = P_SIZE,
          panel_size: int = PANEL_SIZE) -> list[dict]:
    """The queue: one item per drawn artefact, its strata, its true p_select, in a seeded order."""
    members = strata(rows)
    sizes = floor_p(members, {h: size_of(h, per_gate, p_size, panel_size) for h in members}, seed)
    drawn, by_key = draw(members, sizes, seed), {(r.codex, r.path): r for r in rows if shipped(r)}
    keys = sorted({k for picked in drawn.values() for k in picked})
    random.Random(f"{seed}:order").shuffle(keys)
    return [{"codex": k[0], "unit": by_key[k].unit, "kind": by_key[k].kind, "path": k[1], "sha8": by_key[k].sha8,
             "strata": [h for h, pop in members.items() if k in pop], "drawn_in": [h for h in drawn if k in drawn[h]],
             "p_select": inclusion(k, members, sizes), "seed": seed} for k in keys]


def summary(queue: list[dict], members: dict[str, list]) -> str:
    """Per stratum: drawn n of N; the share drawn at random; the conventions named as conventions."""
    lines = [f"{h}: drew {sum(h in q['drawn_in'] for q in queue)} of {len(pop)}" for h, pop in members.items()]
    rand = sum(any(s in RANDOM for s in q["strata"]) for q in queue)
    lines.append(f"{len(queue)} items, {rand} from the random strata ({rand / max(1, len(queue)):.0%}); the "
                 f"sizes ({PER_GATE} per gate, {P_SIZE} P, {PANEL_SIZE} per panel stratum) and the "
                 f"{RANDOM_FLOOR:.0%} random floor are a convention, not a measurement")
    return "\n".join(lines)


def option(argv: list[str], name: str, default: str | None = None) -> str | None:
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


def main(argv: list[str]) -> int:
    out, seed = option(argv, "--out"), int(option(argv, "--seed", "0"))
    sources = [a for a in argv if not a.startswith("--") and a not in (out, str(seed))]
    if not (sources and out):
        print(__doc__)
        return 2
    rows = [r for path in sources for r in casebook.read_rows(Path(path))]
    queue = build(rows, seed)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("".join(json.dumps(q) + "\n" for q in queue), encoding="utf-8")
    print(summary(queue, strata(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
