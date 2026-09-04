#!/usr/bin/env python
"""Render one video clip per beat, every one bound to its reference sheets.

Coverage, not shots: each clip is a long take the edit cuts several shots out
of.  A second angle inside one H3 generation measured free (631s for a two-shot
243-frame clip against 690s for a single-shot one), and a 243-frame unit is the
cheapest per usable second, so long takes are both better craft and cheaper.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.clip_cache import digest_of, is_current, record
from studio.comfy import run, stage_image
from studio.h3 import NATIVE_H, NATIVE_W, frames_for
from studio.h3_prompt import build as h3_document
from studio.shot_grammar import FRAMING, LADDER
from studio.trailer_refs import visual_description
from studio.trailer_shot import is_scene_safe

ROOT = Path(__file__).resolve().parents[2]
CLIP_SECONDS = 7.0
"""One shot per take now, so a take needs to hold ONE shot, not four.

At 10.1s a take was 243 frames of which 2.6s was reference leak and roughly 2.5s
was used -- the rest existed so several shots could be cut from one render, and
that is precisely what produced four moments of one image instead of four
images.  7.0s aligns to 175 frames, leaving 4.69s after the head trim against a
4.0s MAX_SHOT, and renders in appreciably less time."""
STEPS = 8
"""Eight, not four.  At four steps the final Euler step drops sigma from ~0.72
to zero -- one step doing three quarters of the denoising -- which is the
arithmetic behind the mushy, smeared look.  Two independent published sources
call four a draft mode."""


def is_complete(video: Path) -> bool:
    """True when a file is not just present but finished and readable.

    An existence check is not a completeness check.  mp4 writes its index last,
    so a render interrupted mid-copy leaves a file that looks done, gets
    skipped as done, and silently poisons the cut with an unreadable take.
    """
    if not video.exists() or video.stat().st_size < 10_000:
        return False
    result = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    return not result.stderr.strip()


WORKFLOW = "video_minimax_h3_r2v_turbo"
SEED_BASE = 51000


def bound_slots(beat: dict, refs: dict) -> list[str]:
    """The sheets H3 binds: the beat's characters, then its location, two at most."""
    chars = [f"char-{c}" for c in beat["cast"] if f"char-{c}" in refs]
    loc = f"loc-{beat['location_id']}"
    return (chars + ([loc] if loc in refs else []))[:2]


def take_values(beat: dict, plan: dict, refs: dict, style: str, seed: int,
                tightest: str | None = None) -> dict:
    """What the model is asked for one beat's long take.

    A clip is a long take the edit cuts SEVERAL sizes out of, so the take has
    to contain them: open on the widest size any of this beat's shots asks for
    and arrive at the tightest.  `tightest` overrides that arrival -- the
    identity ladder's alternate setup asks for a face the recogniser can read,
    and holds that size for the whole take.
    """
    char_ids = [r for r in bound_slots(beat, refs) if r.startswith("char-")]
    described = [visual_description(refs[c]["physical"]) for c in char_ids]
    for who, text in zip(char_ids, described):
        if not is_scene_safe(text):
            raise ValueError(f"{who}'s description carries reference-sheet language, "
                             f"which would animate a character sheet: {text[:120]}")
    loc_id = f"loc-{beat['location_id']}"
    wanted = sorted({s["size"] for s in plan["shots"] if s["beat_id"] == beat["beat_id"]}
                    or {"medium"}, key=LADDER.index)
    open_size, close = (tightest, tightest) if tightest else (wanted[-1], wanted[0])
    return {
        "prompt": h3_document(
            style=style, character=" ".join(described),
            place=refs[loc_id]["name"] if loc_id in refs else beat["location_id"],
            action=beat["image_prompt"], open_framing=FRAMING[open_size],
            close_framing=FRAMING[close], camera=beat["motion"], seconds=CLIP_SECONDS,
            arc=beat["arc"]),
        "width": NATIVE_W, "height": NATIVE_H, "frames": frames_for(CLIP_SECONDS),
        "steps": STEPS, "seed": seed, "ref_image_size": "max",
        "filename_prefix": f"TR-{beat['beat_id']}"}


def recipe_for(values: dict, bound: list[str], refs: dict, book: Path) -> dict:
    """Everything that decides what the model draws -- what identifies the clip.

    Skipping on the beat ID meant a plan rebuilt from scratch reused every old
    render under the new names.
    """
    return {"prompt": values["prompt"], "refs": bound, "seed": values["seed"],
            "frames": values["frames"], "steps": values["steps"],
            "width": values["width"], "height": values["height"], "workflow": WORKFLOW,
            "ref_digests": [digest_of(book / refs[r]["rel_path"]) for r in bound]}


def render_take(values: dict, bound: list[str], refs: dict, book: Path, dest: Path) -> Path:
    """One H3 render, staged references in, the finished mp4 at `dest`."""
    values = dict(values)
    for slot, ref_id in enumerate(bound, start=1):
        values[f"ref_image_{slot}"] = stage_image(book / refs[ref_id]["rel_path"])
    written = run(WORKFLOW, values, timeout=3600)
    video = next((p for p in written if p.suffix in (".mp4", ".webm")), None)
    if not video:
        raise RuntimeError(f"{dest.stem} produced no video: {written}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(video.read_bytes())
    record(dest, recipe_for(values, bound, refs, book))
    return dest


def main(book_glob: str, trailer_id: str = "main") -> None:
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    out = book / "trailer" / trailer_id
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    refs_doc = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    refs = {r["ref_id"]: r for r in refs_doc["refs"]}
    clips_dir = out / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    for index, beat in enumerate(plan["beats"]):
        dest = clips_dir / f"{beat['beat_id']}.mp4"
        bound = bound_slots(beat, refs)
        if not bound:
            print(f"  {beat['beat_id']} SKIPPED: nothing to bind to")
            continue
        try:
            values = take_values(beat, plan, refs, refs_doc["palette"], SEED_BASE + index * 7)
        except ValueError as exc:
            raise SystemExit(f"REFUSED: {exc}")
        values["filename_prefix"] = f"TR-{book.name[:8]}-{beat['beat_id']}"
        recipe = recipe_for(values, bound, refs, book)
        # Two questions, asked separately: is the file finished, and is it the
        # file this plan asks for.  Conflating them is what silently shipped
        # nine of nine Scarlet clips from the previous plan.
        if is_complete(dest) and is_current(dest, recipe):
            print(f"  {beat['beat_id']} is current, skipping")
            continue
        if dest.exists():
            reason = "stale" if is_complete(dest) else "unreadable"
            print(f"  {beat['beat_id']} is {reason}; re-rendering")
            dest.unlink()
        print(f"  [{index + 1}/{len(plan['beats'])}] {beat['beat_id']} <- {', '.join(bound)}")
        render_take(values, bound, refs, book, dest)
        print(f"      -> {dest.name}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
