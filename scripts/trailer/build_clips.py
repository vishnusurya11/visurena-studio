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
from studio.trailer_refs import visual_description
from studio.trailer_shot import is_scene_safe, shot_prompt

ROOT = Path(__file__).resolve().parents[2]
CLIP_SECONDS = 10.0
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


def main(book_glob: str, trailer_id: str = "main") -> None:
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    out = book / "trailer" / trailer_id
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    refs_doc = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    refs = {r["ref_id"]: r for r in refs_doc["refs"]}
    style = refs_doc["palette"]
    clips_dir = out / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    for index, beat in enumerate(plan["beats"]):
        dest = clips_dir / f"{beat['beat_id']}.mp4"
        char_ids = [f"char-{c}" for c in beat["cast"] if f"char-{c}" in refs]
        loc_id = f"loc-{beat['location_id']}"
        slots = char_ids + ([loc_id] if loc_id in refs else [])
        if not slots:
            print(f"  {beat['beat_id']} SKIPPED: nothing to bind to")
            continue
        described = [visual_description(refs[c]["physical"]) for c in char_ids]
        for who, text in zip(char_ids, described):
            if not is_scene_safe(text):
                raise SystemExit(
                    f"REFUSED: {who}'s description carries reference-sheet "
                    f"language, which would animate a character sheet: {text[:120]}")
        values = {
            "prompt": shot_prompt(
                style, described,
                refs[loc_id]["name"] if loc_id in refs else beat["location_id"],
                beat["image_prompt"], beat["arc"], CLIP_SECONDS, index),
            "width": NATIVE_W, "height": NATIVE_H,
            "frames": frames_for(CLIP_SECONDS), "steps": STEPS,
            "seed": 51000 + index * 7,
            "ref_image_size": "max",
            "filename_prefix": f"TR-{book.name[:8]}-{beat['beat_id']}"}
        bound = slots[:2]
        # The recipe is everything that decides what the model draws, and it
        # is what identifies the clip.  Skipping on the beat ID meant a plan
        # rebuilt from scratch reused every old render under the new names.
        recipe = {
            "prompt": values["prompt"], "refs": bound, "seed": values["seed"],
            "frames": values["frames"], "steps": values["steps"],
            "width": values["width"], "height": values["height"],
            "workflow": "video_minimax_h3_r2v_turbo",
            "ref_digests": [digest_of(book / refs[r]["rel_path"]) for r in bound]}
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
        for slot, ref_id in enumerate(bound, start=1):
            values[f"ref_image_{slot}"] = stage_image(book / refs[ref_id]["rel_path"])
        print(f"  [{index + 1}/{len(plan['beats'])}] {beat['beat_id']} "
              f"<- {', '.join(bound)}")
        written = run("video_minimax_h3_r2v_turbo", values, timeout=3600)
        video = next((p for p in written if p.suffix in (".mp4", ".webm")), None)
        if not video:
            raise RuntimeError(f"{beat['beat_id']} produced no video: {written}")
        dest.write_bytes(video.read_bytes())
        record(dest, recipe)
        print(f"      -> {dest.name}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
