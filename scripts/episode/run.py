"""Run one episode stage under the clock.

    uv run python scripts/episode/run.py <codex_id> <n> <stage> [-- <args for the stage>]
    uv run python scripts/episode/run.py <codex_id> <n> --report

The stage is one of `STAGES`; its script is launched as a subprocess with the
book and episode, the wall time is stamped into `episodes/epNN/timing.jsonl`
whether it passed or failed, and the exit code is the stage's own. `--report`
prints the total, per stage, retries counted, slow stages named.

OWNER 2026-09-16: "check time to get total time for a episode". This is the
one road every stage takes so that the number exists.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_clock, episode_home

STAGES = {
    "lines": "scripts/episode/say_lines.py",
    "respot": "scripts/episode/respot.py",
    "timeline": "scripts/episode/timeline.py",
    "frames": "scripts/episode/frames.py",
    "sheets": "scripts/episode/seq_boards.py",
    "takes": "scripts/episode/takes_r2v.py",
    "take_dq": "scripts/episode/take_dq.py",
    "assemble": "scripts/episode/assemble.py",
    "qc": "scripts/episode/qc.py",
    "title": "scripts/episode/title.py",
    "eye_review": "scripts/episode/eye_review.py",
    "publish": "scripts/publish/youtube_upload.py",
}


def command(stage: str, book_id: str, number: int, extra: list[str]) -> list[str]:
    return [sys.executable, STAGES[stage], book_id, str(number), *extra]


def run(book_id: str, number: int, stage: str, extra: list[str]) -> int:
    """Launch the stage and stamp it; the stage's own exit code comes back."""
    if stage not in STAGES:
        raise SystemExit(f"unknown stage {stage!r}; one of {', '.join(STAGES)}")
    book = episode_home.book_dir(book_id)
    with episode_clock.timed(book, number, stage, note=" ".join(extra)):
        done = subprocess.run(command(stage, book_id, number, extra))
        if done.returncode:
            raise SystemExit(done.returncode)
    return 0


def main(argv: list[str]) -> int:
    book_id, number = argv[1], int(argv[2])
    if "--report" in argv:
        print(episode_clock.report(episode_home.book_dir(book_id), number))
        return 0
    stage = argv[3]
    extra = argv[argv.index("--") + 1:] if "--" in argv else argv[4:]
    return run(book_id, number, stage, extra)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
