"""Measure every rendered seed's metre and write it beside the cue.

    uv run python scripts/trailer/metre_report.py <codex_id>

Eight seeds of one caption ranged 0.31-0.97 bars-in-mode, so the grid a
cut can use is a property of the SEED, and each one gets its own
metre-<seed>.json.  Cues live in trailer/main/music/ for a run and in
trailer/music/ for the shipped Scarlet trailers; both are reported.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from studio.beatmap import Tracker, metre
from studio.paths import book_dir
from studio.trailer_stage_spec import Metre

SEED = re.compile(r"cue-(\d+)")


def music_dirs(book: Path) -> list[Path]:
    """Every music folder holding rendered cues, run folder first."""
    candidates = [book / "trailer" / "main" / "music", book / "trailer" / "music"]
    return [d for d in candidates if any(d.glob("cue-*.*"))]


def cues_in(music: Path) -> list[tuple[int, Path]]:
    """(seed, path) for every rendered cue, ignoring sidecars."""
    found = []
    for path in sorted(music.glob("cue-*.*")):
        match = SEED.fullmatch(path.stem)
        if match and path.suffix in (".flac", ".wav", ".mp3"):
            found.append((int(match.group(1)), path))
    return found


def report(music: Path, book: Path, track: Tracker | None = None) -> list[Metre]:
    """Write metre-<seed>.json for every cue in `music` and return them."""
    measured = []
    for seed, path in cues_in(music):
        found = metre(path, seed=seed, rel_path=path.relative_to(book).as_posix(), track=track)
        (music / f"metre-{seed}.json").write_text(found.model_dump_json(indent=2), encoding="utf-8")
        measured.append(found)
    return measured


def line_for(found: Metre) -> str:
    return (f"seed {found.seed}: {found.bpm:6.1f} bpm  bars_in_mode {found.bars_in_mode:.2f}"
            f"  grid {found.grid:<6}  slots {len(found.slots)}  fitness {found.fitness:.1f}")


def main(codex_id: str, track: Tracker | None = None) -> list[Metre]:
    book = book_dir(codex_id)
    measured: list[Metre] = []
    for music in music_dirs(book):
        print(music.relative_to(book).as_posix())
        for found in report(music, book, track):
            print("  " + line_for(found))
            measured.append(found)
    return measured


if __name__ == "__main__":
    main(sys.argv[1])
