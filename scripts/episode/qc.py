#!/usr/bin/env python
"""Measure the delivered episode, never the intention.

    uv run python scripts/episode/qc.py <codex_id> <episode>

Four things, all read off `master.mp4`: it runs the planned length plus the
chip; it sits at the platform loudness; every cut the plan asked for is in the
picture; and every line can be HEARD on the master -- Whisper reads each
line's window of the final mix back, because a line levelled correctly on its
own can still be lost in the sum (08-assemble names this failure).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, voice_qc
from studio.episode_spec import Episode
from studio.trailer_assemble import clip_seconds, integrated, true_peak

LUFS_BAND = (-15.5, -12.5)
TP_CEILING = -1.0
CUT_TOLERANCE = 0.12
SCENE_THRESHOLD = 0.1
MAX_ERROR_RATE = voice_qc.MAX_ERROR_RATE
PTS = re.compile(r"pts_time:\s*([0-9.]+)")


def planned_cuts(placed: dict) -> list[float]:
    return [shot["t_start"] for shot in placed["shots"][1:]]


def seen_cuts(video: Path, threshold: float = SCENE_THRESHOLD) -> list[float]:
    result = subprocess.run(
        ["ffmpeg", "-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo",
         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    return [round(float(m), 3) for m in PTS.findall(result.stderr)]


def missing_cuts(planned: list[float], seen: list[float], tol: float = CUT_TOLERANCE) -> list[float]:
    """Planned cuts with no detected cut within the tolerance."""
    return [cut for cut in planned if not any(abs(cut - s) <= tol for s in seen)]


def window(master: Path, at: float, seconds: float, out: Path) -> Path:
    """One line's stretch of the master's audio, mono 24 kHz, for the ear."""
    start, span = max(0.0, at - 0.2), seconds + 0.5
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{span:.3f}",
                    "-i", str(master), "-vn", "-ac", "1", "-ar", "24000", str(out)], check=True)
    return out


def heard_on_master(master: Path, lines: list[dict], work: Path, listen) -> list[dict]:
    out = []
    for line in lines:
        clip = window(master, line["at"], line["seconds"], work / f"qc_l{line['index']:02d}.wav")
        heard = listen(clip)
        rate = voice_qc.error_rate(heard, line["text"])
        out.append({"index": line["index"], "heard": heard, "error_rate": round(rate, 3),
                    "passed": rate <= MAX_ERROR_RATE})
    return out


def longest_gap(lines: list[dict], until: float) -> float:
    """The longest hole in speech, from the placed lines' measured windows."""
    ordered = sorted(lines, key=lambda line: line["at"])
    gaps, end = [], ordered[0]["at"] if ordered else 0.0
    for line in ordered:
        gaps.append(line["at"] - end)
        end = max(end, line["at"] + line["seconds"])
    gaps.append(until - end)
    return round(max(gaps), 2) if gaps else until


def verdict(report: dict) -> bool:
    return (report["lufs_ok"] and report["tp_ok"] and not report["missing_cuts"]
            and all(row["passed"] for row in report["lines"]))


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    master = episode_home.master_path(book, number)
    work = episode_home.home(book, number) / "work"
    placed = episode_home.read_json(episode_home.home(book, number) / "placed.json")
    lines = placed["lines"]
    lufs, tp = integrated(master), true_peak(master)
    seen = seen_cuts(master)
    report = {
        "master": episode_home.relative(book, master),
        "seconds": clip_seconds(master), "planned_seconds": placed["duration_s"],
        "title_card": (book / "title" / "title.mp4").exists(),
        "lufs": lufs, "lufs_ok": LUFS_BAND[0] <= lufs <= LUFS_BAND[1],
        "true_peak": tp, "tp_ok": tp <= TP_CEILING,
        "planned_cuts": planned_cuts(placed), "seen_cuts": seen,
        "missing_cuts": missing_cuts(planned_cuts(placed), seen),
        "lines": heard_on_master(master, lines, work, voice_qc.any_transcriber()),
        "longest_gap_s": longest_gap(lines, max(l["at"] for l in lines)),
        "speech_s": round(sum(line["seconds"] for line in lines), 1),
    }
    report["passed"] = verdict(report)
    episode_home.write_json(episode_home.home(book, number) / "qc.json", report)
    said = sum(row["passed"] for row in report["lines"])
    print(f"{report['seconds']:.2f}s | {lufs:.1f} LUFS {tp:.1f} dBTP | "
          f"cuts missing {len(report['missing_cuts'])}/{len(report['planned_cuts'])} | "
          f"lines heard {said}/{len(report['lines'])} | speech {report['speech_s']}s, "
          f"longest gap {report['longest_gap_s']}s | {'PASS' if report['passed'] else 'FAIL'}")
    print(f"-> {episode_home.home(book, number) / 'qc.json'}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
