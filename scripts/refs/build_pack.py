#!/usr/bin/env python
"""Draw a book's reference pack locally: characters, locations, props.

    uv run python scripts/refs/build_pack.py <book_id> [--kind characters] [--only narrator] [--view wide_establishing] [--limit N] [--dry]

Reads each entity's `profile.design` from analysis/<kind>/<id>.json and writes
library/<book>/refs/<kind>/<id>/<name>.png, skipping pictures already on disk.
One sheet per character: wardrobe states are said in the ref2v take prompt.
Every picture drawn is logged to refs/pack.jsonl with its prompt and seed.
Local GPU only -- spends nothing.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.comfy import run
from studio.refs_pack import jobs_for, only_views, pending, relpath, values_for

LIBRARY = Path(__file__).resolve().parents[2] / "library"
KINDS = ("characters", "props", "locations")


def book_dir(book_id: str) -> Path:
    hits = [p for p in LIBRARY.iterdir() if p.name.startswith(book_id)]
    if not hits:
        raise SystemExit(f"no book matching {book_id!r}")
    return hits[0]


def profiles(book: Path, kind: str) -> list[tuple[str, dict]]:
    folder = book / "analysis" / kind
    rows = [(p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in sorted(folder.glob("*.json"))]
    return [(eid, row.get("profile") or {}) for eid, row in rows if eid != "index"]


def all_jobs(book: Path, kinds, only):
    jobs = [j for k in kinds for eid, prof in profiles(book, k) for j in jobs_for(k, eid, prof)]
    return [j for j in jobs if not only or j.entity in only]


def draw(book: Path, job) -> Path:
    out = run(job.workflow, values_for(job))[0]
    target = book / relpath(job)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(out, target)
    return target


def log(book: Path, job, seconds: float) -> None:
    row = {"path": relpath(job), "workflow": job.workflow, "prompt": job.prompt,
           "seed": values_for(job)["seed"], "seconds": round(seconds, 1)}
    with (book / "refs" / "pack.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("book_id")
    ap.add_argument("--kind", choices=KINDS, action="append")
    ap.add_argument("--only", action="append")
    ap.add_argument("--view", action="append", help="draw only these location views")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    book = book_dir(a.book_id)
    jobs = only_views(all_jobs(book, a.kind or KINDS, a.only), set(a.view or []))
    todo = pending(jobs, lambda rel: (book / rel).exists())
    todo = todo[: a.limit] if a.limit else todo
    print(f"{len(todo)} pictures to draw", flush=True)
    for i, job in enumerate(todo, 1):
        if a.dry:
            print(relpath(job), flush=True)
            continue
        t = time.time()
        print(f"[{i}/{len(todo)}] {draw(book, job)}  {time.time() - t:.0f}s", flush=True)
        log(book, job, time.time() - t)


if __name__ == "__main__":
    main()
