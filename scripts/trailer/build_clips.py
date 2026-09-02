#!/usr/bin/env python
"""Render one video clip per beat, every one bound to its reference sheets.

Coverage, not shots: each clip is a long take the edit cuts several shots out
of.  A second angle inside one H3 generation measured free (631s for a two-shot
243-frame clip against 690s for a single-shot one), and a 243-frame unit is the
cheapest per usable second, so long takes are both better craft and cheaper.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.comfy import run, stage_image
from studio.h3 import NATIVE_H, NATIVE_W, frames_for
from studio.trailer_shot import shot_prompt

ROOT = Path(__file__).resolve().parents[2]
CLIP_SECONDS = 10.0
STEPS = 8
"""Eight, not four.  At four steps the final Euler step drops sigma from ~0.72
to zero -- one step doing three quarters of the denoising -- which is the
arithmetic behind the mushy, smeared look.  Two independent published sources
call four a draft mode."""


def main(book_glob: str, trailer_id: str = "main") -> None:
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    out = book / "trailer" / trailer_id
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    refs = {r["ref_id"]: r for r in plan["refs"]}
    style = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))["palette"]
    clips_dir = out / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    for index, beat in enumerate(plan["beats"]):
        dest = clips_dir / f"{beat['beat_id']}.mp4"
        if dest.exists():
            print(f"  {beat['beat_id']} exists, skipping")
            continue
        char_ids = [f"char-{c}" for c in beat["cast"] if f"char-{c}" in refs]
        loc_id = f"loc-{beat['location_id']}"
        slots = char_ids + ([loc_id] if loc_id in refs else [])
        if not slots:
            print(f"  {beat['beat_id']} SKIPPED: nothing to bind to")
            continue
        values = {
            "prompt": shot_prompt(
                style, [refs[c]["prompt"].split("sharp focus.")[-1].split("No text")[0].strip()
                        for c in char_ids],
                refs[loc_id]["name"] if loc_id in refs else beat["location_id"],
                beat["image_prompt"], beat["arc"], CLIP_SECONDS),
            "width": NATIVE_W, "height": NATIVE_H,
            "frames": frames_for(CLIP_SECONDS), "steps": STEPS,
            "seed": 51000 + index * 7,
            "ref_image_size": "max",
            "filename_prefix": f"TR-{book.name[:8]}-{beat['beat_id']}"}
        for slot, ref_id in enumerate(slots[:2], start=1):
            values[f"ref_image_{slot}"] = stage_image(book / refs[ref_id]["rel_path"])
        print(f"  [{index + 1}/{len(plan['beats'])}] {beat['beat_id']} "
              f"<- {', '.join(slots[:2])}")
        written = run("video_minimax_h3_r2v_turbo", values, timeout=3600)
        video = next((p for p in written if p.suffix in (".mp4", ".webm")), None)
        if not video:
            raise RuntimeError(f"{beat['beat_id']} produced no video: {written}")
        dest.write_bytes(video.read_bytes())
        print(f"      -> {dest.name}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
