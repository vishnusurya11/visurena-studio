#!/usr/bin/env python
"""Render candidate cues for a book and keep the one that MEASURES best.

Two takes, then the loudness range decides -- not taste, and not the filename.
The 2026-08-25 trailer inherited a 4.0 LU wall-of-sound bed purely because
`SH-cue-action_*` sorted before the good cue in a glob.  Choosing on a measured
number is the fix for that whole class of bug.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dataclasses import asdict

from studio.beatmap import (envelope, late_density, onsets, stopdowns,
                            structural_impacts, title_moment, trailer_fitness)
from studio.comfy import run
from studio.music_tone import (caption, caption_stamp, cue_is_current,
                               load_tone, lyrics_plan, sections_for,
                               stamp_cue)
from studio.trailer_music import PINNED_DURATION

ROOT = Path(__file__).resolve().parents[2]


def loudness_range(audio: Path) -> float:
    """LRA in LU -- how much room the cue leaves between quiet and loud."""
    result = subprocess.run(
        ["ffmpeg", "-nostats", "-i", str(audio), "-filter_complex",
         "ebur128=framelog=verbose", "-f", "null", "-"],
        capture_output=True, text=True, errors="replace")
    for line in reversed(result.stderr.splitlines()):
        if "LRA:" in line and "LU" in line:
            return float(line.split("LRA:")[1].split("LU")[0].strip())
    return 0.0


def duration_of(audio: Path) -> float:
    """Length in seconds, read from ffmpeg -- ffprobe is not installed here."""
    result = subprocess.run(["ffmpeg", "-i", str(audio), "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    for line in reversed(result.stderr.splitlines()):
        if "time=" in line:
            stamp = line.split("time=")[1].split()[0]
            hours, minutes, seconds = stamp.split(":")
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return 0.0


def render_cue(book: Path, text: str, seed: int, dest_dir: Path,
               seconds: float = 100.0) -> Path:
    """One seed of one caption, rendered once: the stamp keys the cache on the
    RECIPE, so a rewritten caption re-renders and the same caption does not."""
    stamp = caption_stamp(text)
    current = [c for c in dest_dir.glob(f"cue-{seed}.*") if cue_is_current(c, stamp)
               and c.suffix in (".flac", ".wav", ".mp3")]
    if current:
        return current[0]
    print(f"  rendering cue seed={seed} ...")
    written = run("audio_minimax_music_3", {
        "caption": text, "lyrics": lyrics_plan(sections_for(round(seconds / 11.1)), seconds),
        "duration": PINNED_DURATION, "seed": seed, "steps": 30,
        "cfg_scale": 1.7, "top_k": 50, "format": "flac",
        "filename_prefix": f"CUE-{book.name[:8]}-{seed}"}, timeout=1800)
    dest = dest_dir / f"cue-{seed}{written[0].suffix or '.flac'}"
    dest.write_bytes(written[0].read_bytes())
    stamp_cue(dest, stamp)
    return dest


def candidate(dest: Path, seed: int) -> dict:
    """The measured row for one rendered cue: what `cues.json` ranks on."""
    times, db = envelope(dest)
    moment = title_moment(times, db)
    grid = onsets(times, db)
    return {"seed": seed, "rel_path": f"trailer/music/{dest.name}",
            "seconds": round(float(times[-1]), 2),
            "lra": loudness_range(dest),
            "fitness": round(trailer_fitness(times, db, grid), 1),
            "grid": [round(t, 2) for t in grid],
            "late_onsets": late_density(grid, float(times[-1])),
            "impacts": [round(t, 2) for t in structural_impacts(times, db)],
            "stopdowns": [round(t, 2) for t in stopdowns(times, db)],
            "title_stopdown": round(moment[0], 2) if moment else None,
            "title_impact": round(moment[1], 2) if moment else None}


def main(book_glob: str, seeds: list[int], seconds: float = 100.0) -> None:
    """Render candidate cues FOR THIS BOOK and keep the one that measures best.

    `palette` used to be the second argument and it was the book's VISUAL grade
    string -- colour words, pasted into a music prompt because the two ideas
    share a word.  It was the only book-specific token in the caption.  The
    tone is authored per book now, beside the reference sheets, for the same
    reason those are: it is a decision about the work, not about the render.
    """
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    dest_dir = book / "trailer/music"
    dest_dir.mkdir(parents=True, exist_ok=True)
    tone = load_tone(book)
    print(f"  tone: {tone.genre}")
    print(f"  lead: {tone.lead_instrument}")
    candidates: list[dict] = []
    for seed in seeds:
        entry = candidate(render_cue(book, caption(tone), seed, dest_dir, seconds), seed)
        print(f"  seed {seed}: {entry['seconds']}s  LRA {entry['lra']} LU  "
              f"fitness {entry['fitness']}  grid {len(entry['grid'])}  "
              f"title {entry['title_impact']}")
        candidates.append(entry)
    best = max(candidates, key=lambda c: c["fitness"])
    (dest_dir / "cues.json").write_text(
        json.dumps({"chosen": best["seed"], "chosen_path": best["rel_path"],
                    "caption": caption(tone), "tone": asdict(tone),
                    "candidates": candidates}, indent=1), encoding="utf-8")
    print(f"chosen: seed {best['seed']} (fitness {best['fitness']}, title at {best['title_impact']}s)")


if __name__ == "__main__":
    main(sys.argv[1], [int(s) for s in sys.argv[2].split(",")])
