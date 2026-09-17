"""Run one episode stage under the clock.

    uv run python scripts/episode/run.py <codex_id> <n> <stage> [--after] [-- <args for the stage>]
    uv run python scripts/episode/run.py <codex_id> <n> --report

The stage is one of `STAGES`; its script is launched as a subprocess with the
book and episode, the wall time is stamped into `episodes/epNN/timing.jsonl`
whether it passed or failed, and the exit code is the stage's own. `--report`
prints the total, per stage, retries counted, slow stages named.

OWNER 2026-09-16: "check time to get total time for a episode". This is the
one road every stage takes so that the number exists.

ONE GPU, ONE STAGE AT A TIME (ep10 synthesis F2). A stage in `GPU_STAGES` is
refused while ComfyUI's queue has work -- running or pending -- and the
refusal is stamped (`ok=False, note="refused: queue busy"`) so the ledger
shows the collision that did NOT happen. `--after` waits for the queue to
drain instead, polling every `WAIT_POLL` seconds up to `WAIT_CAP`. Episode 10,
20:20: a take_dq was started by hand while retakes were queued; the take
rendered at 598 s (warm 266) and the DQ ran five times its time and was re-run.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import comfy, episode_clock, episode_home

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

GPU_STAGES = {"lines", "frames", "takes", "title", "take_dq", "qc", "assemble"}
"""Every stage that puts a job on ComfyUI: TTS + Whisper + the ear (lines),
plates (frames), ref2va (takes), the H3 i2v animate (title), Whisper for the
lip gate (take_dq) and the master's lines (qc), ACE-Step tones (assemble)."""

WAIT_POLL = 20.0
WAIT_CAP = 7200.0
"""`--after`: how often the queue is asked, and how long before waiting is
itself refused -- two hours covers a full run of thirty takes."""

REFUSED = 3


def command(stage: str, book_id: str, number: int, extra: list[str]) -> list[str]:
    return [sys.executable, STAGES[stage], book_id, str(number), *extra]


def wait_free(busy, poll: float = WAIT_POLL, cap: float = WAIT_CAP) -> bool:
    """Poll until the queue is empty; False when the cap runs out first."""
    waited = 0.0
    while busy():
        if waited >= cap:
            return False
        time.sleep(poll)
        waited += poll
    return True


def refuse(book: Path, number: int, stage: str) -> int:
    """Stamp the refusal as a zero-second row and say so; the exit code names it."""
    now = time.time()
    episode_clock.stamp(book, number, stage, now, now, ok=False, note="refused: queue busy")
    print(f"refused: ComfyUI's queue is busy and {stage} would join it; "
          f"wait, or pass --after to wait here", file=sys.stderr)
    return REFUSED


def run(book_id: str, number: int, stage: str, extra: list[str], busy=None, after: bool = False) -> int:
    """Launch the stage and stamp it; the stage's own exit code comes back.
    A GPU stage meets the queue guard first."""
    if stage not in STAGES:
        raise SystemExit(f"unknown stage {stage!r}; one of {', '.join(STAGES)}")
    book = episode_home.book_dir(book_id)
    busy = busy or comfy.busy
    if stage in GPU_STAGES and busy() and not (after and wait_free(busy)):
        return refuse(book, number, stage)
    with episode_clock.timed(book, number, stage, note=" ".join(extra)):
        done = subprocess.run(command(stage, book_id, number, extra))
        if done.returncode:
            raise SystemExit(done.returncode)
    return 0


def main(argv: list[str], busy=None) -> int:
    book_id, number = argv[1], int(argv[2])
    if "--report" in argv:
        print(episode_clock.report(episode_home.book_dir(book_id), number))
        return 0
    stage = argv[3]
    extra = argv[argv.index("--") + 1:] if "--" in argv else argv[4:]
    return run(book_id, number, stage, [a for a in extra if a != "--after"], busy, "--after" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
