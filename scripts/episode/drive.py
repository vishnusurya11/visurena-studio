#!/usr/bin/env python
"""Drive one episode to its end, unattended: the ONE way to launch a run.

    uv run python scripts/episode/drive.py <codex_id> <episode>

Refuses a dirty tree (the code is frozen for the episode), records the SHA it
ran in `episodes/epNN/drive.jsonl`, runs `episode.py`, resumes a DEFERRED run,
and tells the owner on Telegram when the run completes, stops, or goes silent
for SILENCE_S (studio/episode_drive).  Ten-agent plan fixes #1 and #2.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_drive, episode_home  # noqa: E402

NOTIFY = Path("D:/Projects/KingdomOfViSuReNa/alpha/comfy_studio/poc/2026-08-25_2k-video-pipeline/scripts/notify_bench.py")
FFMPEG_DIR = "C:/Users/vishn/bin"
POLL_S = 30


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def notify(text: str) -> None:
    """Telegram, through the sibling project's tested script; a failed send is printed, never fatal."""
    print(f"[drive] {text}", flush=True)
    try:
        subprocess.run(["uv", "run", "--no-sync", "python", str(NOTIFY), "text", "--message", text[:3500]],
                       cwd=NOTIFY.parents[1], timeout=120, check=False)
    except (OSError, subprocess.SubprocessError) as why:
        print(f"[drive] notify failed: {why}", flush=True)


def ledger(home: Path, row: dict) -> None:
    with (home / "drive.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **row}) + "\n")


def run_once(codex: str, number: int, log: Path, label: str) -> str:
    """episode.py to its exit, the log watched for silence; returns the log text."""
    env = {**os.environ, "PATH": FFMPEG_DIR + os.pathsep + os.environ.get("PATH", ""), "PYTHONUNBUFFERED": "1"}
    with log.open("w", encoding="utf-8") as out:
        proc = subprocess.Popen(["uv", "run", "--no-sync", "python", "episode.py", codex, str(number)],
                                cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT)
        size, grew, told = 0, time.time(), False
        while proc.poll() is None:
            time.sleep(POLL_S)
            now_size = log.stat().st_size
            if now_size != size:
                size, grew = now_size, time.time()
            elif episode_drive.silent(grew, time.time(), told):
                notify(f"{label}: no log output for {episode_drive.SILENCE_S // 60} min\n"
                       f"{episode_drive.tail(log.read_text(encoding='utf-8', errors='replace'))}")
                told = True
    return log.read_text(encoding="utf-8", errors="replace")


def main(codex: str, number: int) -> int:
    label = f"{codex} ep{number:02d}"
    if episode_drive.dirty(git("status", "--porcelain")):
        notify(f"{label}: REFUSED to start: the working tree is dirty; commit the code first (fix #2)")
        return 2
    home = episode_home.home(episode_home.book_dir(codex), number)
    home.mkdir(parents=True, exist_ok=True)
    sha, runs = git("rev-parse", "HEAD").strip(), iter(range(1, 1000))
    ledger(home, {"event": "start", "sha": sha})

    def run() -> str:
        n = next(runs)
        text = run_once(codex, number, home / f"drive_run{n:02d}.log", label)
        ledger(home, {"event": "run", "n": n, "sha": sha, "outcome": episode_drive.outcome(text)})
        return text
    code = episode_drive.drive(run, lambda text: notify(f"{label}: {text}"))
    ledger(home, {"event": "end", "code": code, "sha": sha})
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], int(sys.argv[2])))
