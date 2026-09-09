"""Render the trailer's page: one H3 take per beat, from `shot_prompts.json`.

The old path built its shot list out of the MUSIC's spans.  This one renders
the page (`trailer_script.json`) that was written before anything existed, so
every take answers a beat that has a reason to be there.

Each take renders LONGER than the beat plays: `HEAD_TRIM` of reference leak at
the front and a seek handle at the back are rendered and never cut in, so the
seconds the page asks for come out of the middle of a clean take.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.trailer.build_clips import STEPS, render_take
from studio.h3 import FPS, legal_frames
from studio.trailer_assemble import HANDLE, HEAD_TRIM

VERTICAL_W, VERTICAL_H = 768, 1344
"""The 9:16 frame the page is composed for -- H3's native 1344x768, turned."""


def frames_for(seconds: float) -> int:
    """Frames to render for a beat that plays `seconds`, plus the tax."""
    return legal_frames(int((seconds + HEAD_TRIM + HANDLE) * FPS))


def seed_for(beat_id: str, take: int = 0) -> int:
    """Deterministic per beat, so a re-run reuses rather than re-rolls."""
    return 7000 + take * 100 + int("".join(c for c in beat_id if c.isdigit()) or 0)


def bound_slots(shot: dict) -> list[str]:
    """The reference sheets this take stages, in the order the labels bind:
    <Subject 1> is the person the identity comes from, <Subject 2> the second
    person or the place."""
    people = [r for r in (shot.get("character"), shot.get("second")) if r]
    return (people + [shot["place"]])[:2]


def values_for(shot: dict, width: int = VERTICAL_W, height: int = VERTICAL_H) -> dict:
    """What the workflow is filled with for one beat."""
    return {"prompt": shot["prompt"], "width": width, "height": height,
            "frames": frames_for(shot["seconds"]), "steps": STEPS,
            "seed": seed_for(shot["beat_id"]), "ref_image_size": "max",
            "filename_prefix": f"SC-{shot['beat_id']}"}


def render_one(shot: dict, refs: dict, book: Path, dest_dir: Path,
               width: int = VERTICAL_W, height: int = VERTICAL_H) -> Path:
    """One beat rendered to `dest_dir/<beat_id>.mp4`."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{shot['beat_id']}.mp4"
    return render_take(values_for(shot, width, height), bound_slots(shot),
                       refs, book, dest)


def load(book: Path) -> tuple[list[dict], dict]:
    """The prompts written for the page, and the sheets they bind."""
    out = book / "trailer/main"
    shots = json.loads((out / "shot_prompts.json").read_text(encoding="utf-8"))["shots"]
    refs = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    return shots, {r["ref_id"]: r for r in refs["refs"]}
