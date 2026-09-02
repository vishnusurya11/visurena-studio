#!/usr/bin/env python
"""Build every trailer end to end, one book at a time.

Serial on purpose.  The GPU serialises anyway, so running two books at once
buys nothing and costs the guarantee that the first one finishes: if anything
goes wrong at 4am there is still one complete trailer rather than two
half-rendered ones.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STEPS = ("build_plan", "build_clips", "assemble")


def run_step(step: str, book: str) -> bool:
    """Run one stage, streaming its output.  False means it failed."""
    started = time.time()
    print(f"\n=== {step} {book} ===", flush=True)
    result = subprocess.run(
        [sys.executable, "-u", str(ROOT / "scripts/trailer" / f"{step}.py"), book],
        cwd=ROOT)
    print(f"=== {step} {book}: "
          f"{'ok' if result.returncode == 0 else 'FAILED'} "
          f"in {time.time() - started:.0f}s", flush=True)
    return result.returncode == 0


def main(books: list[str]) -> int:
    finished: list[str] = []
    for book in books:
        if all(run_step(step, book) for step in STEPS):
            subprocess.run([sys.executable, "-u",
                            str(ROOT / "scripts/trailer/qc.py"), book], cwd=ROOT)
            finished.append(book)
        else:
            print(f"!!! {book} did not complete; continuing to the next book",
                  flush=True)
    print(f"\nfinished {len(finished)}/{len(books)}: {finished}", flush=True)
    return 0 if len(finished) == len(books) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
