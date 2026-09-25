#!/usr/bin/env python
"""Sign the LOOK: the owner has looked at every sheet in refs/ and approves the pack.

    uv run python scripts/refs/sign_look.py <codex_id> "<note>"

Writes refs/verdict.json bound to the sha8 of refs/pack.jsonl as it stands now.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, refs_verdict  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) < 3 or not argv[2].strip():
        raise SystemExit(f'usage: {argv[0]} <codex_id> "<note>"  (a note in your own words is the signature)')
    path = refs_verdict.sign(episode_home.book_dir(argv[1]), argv[2].strip())
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
