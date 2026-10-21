"""Build recordings.json for one source episode: every take, crop, grid, place, line, VL read and SDK stream it recorded.

    uv run --no-sync python scripts/proof/index_recordings.py <book folder> <episode> [--out <json>] [--root <library>]
    uv run --no-sync python scripts/proof/index_recordings.py 20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde 1

DESIGN 2026-10-21_ep02_proof 2.1 (package P2).  Read-only, $0: named files only, never a walk
(studio/rehearsal/recordings.py).  The same builder runs on a named WotW or Scarlet delivered
episode.  Writes results/recordings/<book>_ep<NN>.json beside the design (git-ignored) and
prints its path first."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import settings  # noqa: E402
from studio.rehearsal import recordings  # noqa: E402

RESULTS = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof" / "results" / "recordings"


def report_lines(out: dict, path: Path) -> list[str]:
    """The path first, then the source and each kind's count."""
    counts = ", ".join(f"{k} {v}" for k, v in sorted(out["counts"].items()))
    return [str(path), f"{out['source']}: {counts}",
            f"vl_text: {out['vl_hits']} of {out['counts'].get('vl_text', 0)} (picture x ask) reads found in the cache"]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("book")
    p.add_argument("episode", type=int)
    p.add_argument("--root", type=Path, default=settings.REAL_LIBRARY)
    p.add_argument("--out", type=Path)
    args = p.parse_args(argv)
    out_path = args.out or RESULTS / f"{args.book.split('_', 1)[0]}_ep{args.episode:02d}.json"
    out = recordings.build(args.root / args.book, args.episode, args.root, text_key=recordings.default_text_key())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n".join(report_lines(out, out_path.resolve())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
