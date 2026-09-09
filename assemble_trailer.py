"""Assemble the trailer the page describes: picture, cue, voices, mix.

Run after `render_trailer.py`: `uv run python assemble_trailer.py <codex_id>`.
Every stage skips what is already on disk, so a killed run resumes.

The order is the professional one and the reverse of what this repo used to
do: the PAGE was written first, the cue is asked FOR it (`script_cue`), the
picture is cut TO it (`script_cut`), and the bed STOPS where it speaks
(`script_mix`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.trailer.build_music import render_cue
from studio import script_cue, script_cut, script_mix, voice
from studio.trailer_script import TrailerScript

LIBRARY = Path("library")
CUE_SEED = 8001


def book_dir(codex_id: str) -> Path:
    found = sorted(LIBRARY.glob(f"{codex_id}*"))
    if not found:
        raise SystemExit(f"no book in library for {codex_id}")
    return found[0]


def load_page(out: Path) -> TrailerScript:
    return TrailerScript.model_validate_json(
        (out / "trailer_script.json").read_text(encoding="utf-8"))


def cue_for(book: Path, page: TrailerScript, out: Path) -> Path:
    """The cue this page asked for, rendered once."""
    ask = script_cue.ask_for(page)
    text = script_cue.brief(page)
    (out / "music/script_cue_brief.txt").parent.mkdir(parents=True, exist_ok=True)
    (out / "music/script_cue_brief.txt").write_text(text, encoding="utf-8")
    return render_cue(book, text, CUE_SEED, out / "music",
                      duration=int(ask.seconds) + 2, prefix="script-cue")


def speak(book: Path, page: TrailerScript, out: Path) -> list[tuple[float, Path]]:
    """Every written line, said in its speaker's designed voice."""
    said = []
    for beat in page.beats:
        if not beat.line:
            continue
        card = book / "analysis/characters" / f"{beat.speaker}.json"
        if not card.exists():
            print(f"  {beat.id}: no cast card for {beat.speaker}; the line is cut", flush=True)
            continue
        who = json.loads(card.read_text(encoding="utf-8"))
        reference = voice.design_reference(who, out / "voice/refs")
        dest = out / "voice/script" / f"{beat.id}.wav"
        if not dest.exists():
            print(f"  {beat.id}: {beat.speaker} says “{beat.line[:48]}…”", flush=True)
            voice.clone_line(reference, beat.line, voice.seed_for(beat.speaker, 0), dest,
                             speaker=beat.speaker)
        said.append((page.at(beat), dest))
    return said


def build(book: Path) -> Path:
    out = book / "trailer/main"
    page = load_page(out)
    print(f"page: {len(page.beats)} beats, {page.seconds}s, {page.aspect}", flush=True)

    picture = out / "work/script_picture.mp4"
    if not picture.exists():
        script_cut.cut(page, out / "clips/script", out / "work/script", picture)
    print(f"picture: {picture.name}", flush=True)

    bed = cue_for(book, page, out)
    print(f"cue: {bed.name}", flush=True)

    lines = speak(book, page, out)
    print(f"voice: {len(lines)} of {len(page.spoken())} lines", flush=True)

    master = out / f"TRAILER60-{book.name.split('_', 1)[-1]}.mp4"
    script_mix.mix(picture, bed, lines, script_cue.spoken_windows(page),
                   out / "work/script", master, page.seconds)
    return master


if __name__ == "__main__":
    made = build(book_dir(sys.argv[1] if len(sys.argv) > 1 else "20260822113400"))
    print(f"=== TRAILER60 done | {made} ===", flush=True)
