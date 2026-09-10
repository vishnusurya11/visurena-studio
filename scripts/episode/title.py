#!/usr/bin/env python
"""The episode's title card: one still from gpt-image, animated 4 s by H3.

    uv run python scripts/episode/title.py <codex_id> <episode>

The series name is the main title ("SHERLOCK HOLMES"), the book the subtitle,
"EPISODE N" the tag (owner, 2026-09-10), so the card is made once PER
EPISODE under `library/<book>/title/epNN.png|mp4` and appended after the
last frame.  PAID (one gpt-image call per episode); the still and the take
are cached and never redrawn.
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home
from studio.comfy import run, stage_image
from studio.h3 import frames_for
from studio.llm import _load_dotenv

W, H = 768, 1344
SECONDS = 4.0
MODEL = "gpt-image-2.5-sunburst"
WORKFLOW = "video_minimax_h3_i2v_turbo"
SEED = 91000
SERIES = "Sherlock Holmes"


def still_prompt(series: str, title: str, number: int, palette: str) -> str:
    return (f'A cinematic title card, vertical 9:16, photoreal 35 mm film still. Typography: the '
            f'words "{series.upper()}" set very large in an elegant Victorian serif, letterpress-'
            f'crisp, pale ivory, centred in the upper third; directly beneath, smaller, the words '
            f'"{title.upper()}"; at the very bottom, small and widely letter-spaced, "EPISODE '
            f'{number}". The picture: a black hansom cab racing straight toward the camera down a '
            f'fog-choked gaslit Victorian London street at night in heavy rain, the horse mid-'
            f'stride, wheels throwing spray, gas lamps blooming in the fog on both sides, wet '
            f'cobbles mirroring the lamps, the driver a dark shape high on the box. {palette} Fine '
            f'grain, deep shadow, cold blue-grey fog against warm lamplight. No faces readable, no '
            f'other text, no logo, no border.')


def take_prompt(series: str, title: str, number: int) -> str:
    return ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from "
            "[Shot 1]) is fully referenced.

"
            "integrated_multimodal_description: [Shot 1] Photoreal cinematic title card, night, "
            "rain, fog. Begin exactly from <Picture 1>. Through the whole shot the lettering "
            f'"{series.upper()}", "{title.upper()}" and "EPISODE {number}" stays exactly as drawn, '
            "perfectly still, sharp and legible. From 0 to 4 seconds the camera pushes in slowly; "
            "the hansom cab gallops toward the camera, the horse's legs driving, the wheels "
            "turning and throwing spray, rain falling in sheets through the lamplight, thick fog "
            "rolling across the street from left to right, every gas lamp flickering. In the "
            "final half second the cab fills the lower frame and the movement settles. No new "
            "text, no captions, no cut.

"
            "overall_soundscape: Galloping hooves and iron wheels on wet cobbles, heavy rain, "
            "wind, a distant church bell.

"
            "non_diegetic_music: N/A")


def draw(prompt: str, out: Path) -> Path:
    if out.exists():
        return out
    _load_dotenv()
    from openai import OpenAI
    from PIL import Image

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    result = client.images.generate(model=MODEL, prompt=prompt, size="1024x1536", quality="high", n=1)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_name(out.stem + "_raw.png")
    raw.write_bytes(base64.b64decode(result.data[0].b64_json))
    image = Image.open(raw).convert("RGB")
    scale = max(W / image.width, H / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - W) // 2, (resized.height - H) // 2
    resized.crop((left, top, left + W, top + H)).save(out)
    return out


def animate(still: Path, prompt: str, out: Path, seed: int) -> Path:
    if out.exists():
        return out
    made = run(WORKFLOW, {"prompt": prompt, "width": W, "height": H,
                          "frames": frames_for(SECONDS + 0.25), "steps": 8, "seed": seed,
                          "start_image": stage_image(still), "filename_prefix": "ep_title"},
               timeout=1800)
    video = next(p for p in made if p.suffix in (".mp4", ".webm"))
    out.write_bytes(video.read_bytes())
    return out


def card_path(book: Path, number: int) -> Path:
    return book / "title" / f"ep{number:02d}.mp4"


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    refs = episode_home.read_json(book / "refs" / "refs.json")
    play = episode_home.read_json(book / "screenplay" / "feature" / "screenplay.json")
    series, title = play.get("series", SERIES), play["title"]
    folder = book / "title"
    still = draw(still_prompt(series, title, number, refs["palette"]), folder / f"ep{number:02d}.png")
    prompt = take_prompt(series, title, number)
    (folder / f"ep{number:02d}.prompt.txt").write_text(
        still_prompt(series, title, number, refs["palette"]) + "

" + prompt, encoding="utf-8")
    take = animate(still, prompt, card_path(book, number), SEED + number)
    print(f"title card -> {take}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
