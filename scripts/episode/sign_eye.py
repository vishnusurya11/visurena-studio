#!/usr/bin/env python
"""Sign an eye verdict on the panels or the takes of one unit.

    uv run python scripts/episode/sign_eye.py <codex_id> <n> panels|takes pass|fault "<what was seen>"

Writes storyboard/eye_<sha8>.json or takes/r2v/eye_<sha8>.json, bound to the
bytes of the pictures on disk at signing (studio/eye_verdict).  A redrawn
panel or a retaken take moves the fingerprint and the signature lapses.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, eye_verdict  # noqa: E402

WHICH = {"panels": ("storyboard", "shot_*.png"), "takes": ("takes/r2v", "T??.mp4")}
USAGE = "sign_eye.py <codex_id> <n> panels|takes pass|fault \"<what was seen>\""


def targets(home: Path, which: str) -> tuple[Path, list[Path]]:
    """(the folder the verdict lives in, the pictures it signs)."""
    folder, pattern = WHICH[which]
    room = Path(home) / folder
    return room, sorted(room.glob(pattern))


def main(argv: list[str]) -> int:
    if len(argv) < 6 or argv[3] not in WHICH or argv[4] not in eye_verdict.VERDICTS:
        raise SystemExit(f"usage: {USAGE}")
    home = episode_home.home(episode_home.book_dir(argv[1]), int(argv[2]))
    room, pictures = targets(home, argv[3])
    if not pictures:
        raise SystemExit(f"nothing to sign under {room}")
    out = eye_verdict.sign(room, pictures, argv[4], argv[5])
    print(f"{argv[4]} on {len(pictures)} file(s) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
