#!/usr/bin/env python
"""Bench a judge over the library's casebooks and record the result.

    uv run python scripts/calibration/bench.py <judge>|--all [<codex>]

Runs the named judge (from `studio.judges.registry`) over every harvested
casebook under library/*/casebook/ (or one book's), appends a `## Bench
<date>` section to docs/calibration/<judge>.md and writes the baseline the
ratchet test compares against to docs/calibration/bench/<judge>.json (codex
ids, sha8s and relative paths only).  No video is decoded: the judges read
the machine values each row carries.  No GPU, no model, no credit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import judge_bench as jb  # noqa: E402
from studio.judges import registry  # noqa: E402

LIBRARY = ROOT / "library"
DOCS = ROOT / "docs" / "calibration"


def casebooks(library: Path = LIBRARY, codex: str | None = None) -> list[Path]:
    """Every harvested casebook, or the one book's."""
    if not library.exists():
        return []
    return sorted(p for p in library.glob("*/casebook") if (p / "labels.jsonl").is_file()
                  and (codex is None or p.parent.name.startswith(codex)))


def outcomes_for(entry, folders: list[Path]) -> list[jb.Outcome]:
    rows = [r for folder in folders for r in jb.load_rows(folder, entry.kind)]
    return jb.run(rows, entry.judge, entry.classes)


def write(docs_dir: Path, name: str, outcomes: list[jb.Outcome], version: str,
          machine_version: str = "") -> tuple[Path, Path]:
    """Append the report to <name>.md (created with a heading when absent); replace bench/<name>.json."""
    doc, base = Path(docs_dir) / f"{name}.md", Path(docs_dir) / "bench" / f"{name}.json"
    doc.parent.mkdir(parents=True, exist_ok=True)
    base.parent.mkdir(parents=True, exist_ok=True)
    head = "" if doc.exists() else f"# {name} calibration\n\nBenched by scripts/calibration/bench.py against the casebooks.\n"
    with doc.open("a", encoding="utf-8") as fh:
        fh.write(head + "\n" + jb.report(outcomes, name, version, machine_version))
    base.write_text(json.dumps(jb.baseline(outcomes, name, version, machine_version), indent=2), encoding="utf-8")
    return doc, base


def machine_version() -> str:
    from scripts.calibration.harvest_labels import machine_version as mv
    return mv()


def bench_one(name: str, folders: list[Path], docs_dir: Path = DOCS) -> dict:
    entry = registry.get(name)
    outcomes = outcomes_for(entry, folders)
    doc, base = write(docs_dir, name, outcomes, entry.version, machine_version())
    r = jb.recall(outcomes, "owner")
    return {"judge": name, "rows": len(outcomes), "recall_owner": f"{r.k}/{r.n}",
            "recall_all": jb.recall(outcomes, "all").point, "false_refusals": jb.false_refusals(outcomes).point,
            "misses": len(jb.misses(outcomes)), "doc": str(doc.relative_to(ROOT)), "baseline": str(base.relative_to(ROOT))}


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    folders = casebooks(codex=argv[1] if len(argv) > 1 else None)
    if not folders:
        print("no harvested casebook under library/: run scripts/calibration/harvest_labels.py <codex> first")
        return 1
    names = registry.names() if argv[0] == "--all" else [argv[0]]
    for name in names:
        print(json.dumps(bench_one(name, folders)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
