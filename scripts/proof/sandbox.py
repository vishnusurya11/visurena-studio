"""Build, checkpoint and restore a rehearsal sandbox; take and check the real-library stat guard.

    uv run --no-sync python scripts/proof/sandbox.py build <run_id> [--episode 2] [--no-fakes]
    uv run --no-sync python scripts/proof/sandbox.py checkpoint <sandbox> <name>
    uv run --no-sync python scripts/proof/sandbox.py restore <sandbox> <name>
    uv run --no-sync python scripts/proof/sandbox.py guard-snapshot <out.json>
    uv run --no-sync python scripts/proof/sandbox.py guard-check <before.json>

Run with VISURENA_LIBRARY UNSET: the builder is the one reader of the real book and DB (read
only, named records, never a walk).  A rehearsal process then sets
VISURENA_LIBRARY=<sandbox>/library and every studio path follows (DESIGN 1.1)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import settings  # noqa: E402
from studio.rehearsal import guard, sandbox  # noqa: E402

REAL_BOOK = settings.REAL_LIBRARY / f"{sandbox.REAL_CODEX}_{sandbox.SLUG}"
REAL_DB = settings.REPO / settings.db_path(env={})


def build(args: argparse.Namespace) -> int:
    box = sandbox.build(args.run_id, source_book=REAL_BOOK, real_db=REAL_DB, episode=args.episode,
                        manifest={"fakes": not args.no_fakes})
    print(box)
    print(f"rehearse with: {settings.ENV}={box / settings.LIBRARY_DIR}")
    return 0


def guard_snapshot(args: argparse.Namespace) -> int:
    snap = guard.snapshot(guard.named_paths())
    Path(args.out).write_text(json.dumps(snap, indent=1), encoding="utf-8")
    print(f"{len(snap)} guarded paths -> {Path(args.out).resolve()}")
    return 0


def guard_check(args: argparse.Namespace) -> int:
    before = {k: tuple(v) if v else None for k, v in json.loads(Path(args.before).read_text(encoding="utf-8")).items()}
    lines = guard.touched(before, guard.snapshot(guard.named_paths()))
    print("\n".join(lines) if lines else f"real library untouched: {len(before)} guarded paths unchanged")
    return 1 if lines else 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("run_id")
    b.add_argument("--episode", type=int, default=2)
    b.add_argument("--no-fakes", action="store_true")
    for name in ("checkpoint", "restore"):
        c = sub.add_parser(name)
        c.add_argument("sandbox")
        c.add_argument("name")
    sub.add_parser("guard-snapshot").add_argument("out")
    sub.add_parser("guard-check").add_argument("before")
    return p


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv)
    if args.cmd in ("checkpoint", "restore"):
        result = getattr(sandbox, args.cmd)(Path(args.sandbox), args.name)
        print(result or f"restored {args.name} into {args.sandbox}")
        return 0
    return {"build": build, "guard-snapshot": guard_snapshot, "guard-check": guard_check}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
