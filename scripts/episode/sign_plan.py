#!/usr/bin/env python
"""Sign a unit's plan: the owner's APPROVE, bound to the plan's sha8.

    uv run python scripts/episode/sign_plan.py <codex_id> <n> "<note>"

Writes `episodes/epNN/plan.verdict.json`.  The next run of the episode stage
resumes past the PLAN gate; a plan rewritten after this is unsigned again.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, plan_verdict  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) < 4 or not argv[3].strip():
        raise SystemExit(f'usage: {argv[0]} <codex_id> <n> "<note>"  (the note is required)')
    book = episode_home.book_dir(argv[1])
    plan = episode_home.plan_path(book, int(argv[2]))
    if not plan.exists():
        raise SystemExit(f"nothing to sign: {plan} does not exist")
    out = plan_verdict.sign(plan, argv[3].strip())
    print(f"signed {plan_verdict.plan_sha8(plan)} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
