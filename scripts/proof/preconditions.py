"""List every gap a chapter meets in the book before any run: voices, base sheets, place pictures, book fields.

    uv run --no-sync python scripts/proof/preconditions.py ch2 [--out <json>] [--book <book folder>]

DESIGN 2026-10-21_ep02_proof 4.3 (package P2, R5).  Read-only, $0, minutes: the Jekyll book's
named records only (studio/rehearsal/preconditions.py).  Each gap prints as a predicted park
or a just-in-time ref step with its cost from the book's own draw times; F14 plants exactly
these gaps.  Writes results/preconditions_ch<N>.json beside the design (git-ignored) and prints
its path first."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import settings  # noqa: E402
from studio.rehearsal import preconditions as pre  # noqa: E402

BOOK = settings.REAL_LIBRARY / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
RESULTS = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof" / "results"


def chapter_of(arg: str) -> int:
    """`ch2` or `2` -> 2."""
    return int(arg.lower().removeprefix("ch"))


def gap_line(g: dict) -> str:
    cost = (f"median {g['cost_s']:.0f} s, p90 {g['cost_p90_s']:.0f} s ({g['cost_basis']})" if g["cost_s"]
            else g["cost_basis"])
    head = {"park": "PREDICTED PARK", "jit": "JIT REF STEP", "unknown": "UNKNOWN", "owner": "OWNER"}[g["outcome"]]
    return f"  {head} at step {g['step']}: {g['kind']} {g['what']} | cost {cost}" + (f" | {g['note']}" if g["note"] else "")


def report_lines(out: dict, path: Path) -> list[str]:
    """The path first, then the cast read, every gap, and the totals."""
    lines = [str(path), f"chapter {out['chapter']}: speakers {', '.join(out['cast']['speakers'])}",
             f"  present {', '.join(out['cast']['present'])}"]
    lines += [gap_line(g) for g in out["gaps"]] or ["  no gap"]
    lines.append(f"{len(out['gaps'])} gaps: {out['parks']} predicted parks, {out['jit_steps']} JIT ref steps "
                 f"costing {out['jit_cost_s']:.0f} s at the median draw, {out['jit_cost_p90_s']:.0f} s at p90 "
                 f"(draw seconds only; the refs runner's gates are unmeasured); props {out['props']['status']}")
    return lines


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("chapter")
    p.add_argument("--out", type=Path)
    p.add_argument("--book", type=Path, default=BOOK)
    args = p.parse_args(argv)
    n = chapter_of(args.chapter)
    out_path = args.out or RESULTS / f"preconditions_ch{n}.json"
    out = pre.audit(args.book, n)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n".join(report_lines(out, out_path.resolve())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
