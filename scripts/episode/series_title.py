#!/usr/bin/env python
"""The series title card, drawn locally: one picture for the book, re-lettered per episode.

    uv run python scripts/episode/series_title.py <codex_id> <episode>

1. title/series_base.png -- the art, ONCE per book, no text (Krea2 house style),
   from the words in title/motif.txt.
2. title/epNN.png -- Ideogram 4 letters the series, "EPISODE N" and the
   chapter's own name on black, screened over that same picture; Qwen3-VL reads
   it back and the card is kept only when every line reads exactly (up to
   TRIES seeds).
3. title/epNN.mp4 -- 4 s on H3 i2v; assemble appends it after the last frame.
Free: local GPU only.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import canvas, episode_home
from studio.comfy import run, run_text, stage_image
from studio.h3 import frames_for
from studio.refs_pack import styled
from studio.series_title import card_lines, missing_lines, plate_caption, screen_over

TRIES = 6
SECONDS = 4.0
OCR_ASK = ("Transcribe every word of lettering in this image exactly as it is spelled, "
           "line by line, top to bottom. Output only the transcription.")


def base_art(folder: Path) -> Path:
    out = folder / "series_base.png"
    if not out.exists():
        motif = (folder / "motif.txt").read_text(encoding="utf-8").strip()
        made = run("image_krea2_cinematic_2x", {"prompt": styled(motif), "width": 1024,
                   "height": 1024, "seed": 7100, "filename_prefix": "series_title/base"})[0]
        shutil.copyfile(made, out)
    return out


def letter(base: Path, lines: list[str], seed: int) -> Path:
    """Ideogram draws the words alone on black; they are screened over the art."""
    from PIL import Image
    plate = run("image_ideogram4_t2i", {"prompt": plate_caption(lines), "seed": seed,
                "aspect_ratio": "1:1 (Square)", "megapixels": 1,
                "filename_prefix": "series_title/plate"})[0]
    out = base.with_name(f"lettered_{seed}.png")
    screen_over(Image.open(base), Image.open(plate)).save(out)
    return out


def reads(card: Path) -> str:
    return run_text("image_qwen3vl_caption", {"prompt": OCR_ASK, "image_1": stage_image(card)})


def lettered_card(base: Path, lines: list[str], out: Path) -> Path:
    for attempt in range(TRIES):
        card = letter(base, lines, 5200 + attempt)
        wrong = missing_lines(lines, reads(card))
        print(f"  lettering try {attempt + 1}: {'OK' if not wrong else f'misread {wrong}'}", flush=True)
        if not wrong:
            shutil.copyfile(card, out)
            return out
    raise SystemExit(f"no lettering read back exactly in {TRIES} tries: {lines}")


def motion_prompt(lines: list[str]) -> str:
    quoted = ", ".join(f'"{line}"' for line in lines)
    return ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from "
            "[Shot 1]) is fully referenced.\n\n"
            "integrated_multimodal_description: [Shot 1] Cinematic title card. Begin exactly from "
            "<Picture 1>. The camera pushes in slowly and steadily for the whole shot. Thin smoke "
            "drifts across the sky from left to right and the red light pulses once. The lettering "
            f"{quoted} stays exactly as drawn, sharp and legible, for every frame.\n\n"
            "overall_soundscape: A low wind over open heath, one distant deep metallic hoot.\n\n"
            "non_diegetic_music: N/A")


def animate(card: Path, lines: list[str], out: Path, aspect: str, number: int) -> Path:
    w, h = canvas.size(aspect)
    made = run("video_minimax_h3_i2v_turbo", {
        "prompt": motion_prompt(lines), "width": w, "height": h,
        "frames": frames_for(SECONDS + 0.25), "steps": 8, "seed": 91000 + number,
        "start_image": stage_image(card), "filename_prefix": "series_title/anim"}, timeout=1800)
    shutil.copyfile(next(p for p in made if p.suffix in (".mp4", ".webm")), out)
    return out


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    folder = book / "title"
    play = json.loads((book / "screenplay/feature/screenplay.json").read_text(encoding="utf-8"))
    chapter = json.loads((book / f"source/chapters/ch_{number:02d}.json").read_text(encoding="utf-8"))
    lines = card_lines(play["title"], number, chapter["title"])
    card = folder / f"ep{number:02d}.png"
    if not card.exists():
        lettered_card(base_art(folder), lines, card)
    video = folder / f"ep{number:02d}.mp4"
    if not video.exists():
        animate(card, lines, video, episode_home.load_plan(book, number).aspect, number)
    print(f"title card -> {video}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
