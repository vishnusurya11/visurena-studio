"""Jekyll style samples: six book scenes in styles A and C, same seed per scene.

uv run python docs/audit/2026-10-12_jekyll_style_samples/render.py [scene ...] [--seed-salt S] [--styles AC]
Writes <style>/<scene>.png beside this file and appends each render's seconds to times.jsonl.
Recipes are the 2026-10-11 look test's (docs/audit/2026-10-11_jekyll_look_test/render.py), with
style C's lead reworded so the corners are plain ink wash (the look test's signature scrawl).
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
import zlib
from pathlib import Path

from studio import comfy

HERE = Path(__file__).resolve().parent
BOOK_WORDS = ("Cinematic live-action photograph, anamorphic widescreen, natural film grain, photoreal, "
              "no stylisation, no illustration. Muted desaturated palette of fog-white, soot-black, "
              "bottle-green and sick gaslight amber; late-Victorian London; heavy chiaroscuro, deep shadow, "
              "damp air. ")
LEADS = {
    "A": BOOK_WORDS + "A Victorian gothic film still: fog, gaslight, deep shadow. ",
    "C": ("A dark gothic ink illustration, etched pen-and-ink cross-hatching with heavy black brushwork, "
          "a Victorian penny-dreadful engraving on dark toned paper, the whole sheet full-bleed, its edges "
          "and four corners plain black ink wash fading into shadow, of "),
}
TAIL = " No text, no lettering, no signage, no watermark."


def values(style: str, prompt: str, seed: int, name: str) -> dict:
    """The image_krea2_turbo_t2i inject values for one cell (LoRA on for C only)."""
    return {"prompt": prompt, "seed": seed, "aspect_ratio": "1:1 (Square)", "megapixels": 2,
            "refine_prompt": False, "enable_lora": style == "C",
            "filename_prefix": f"jekyll_samples/{style}_{name}"}


def render(style: str, name: str, body: str, salt: str) -> None:
    seed = zlib.crc32(f"jekyll_samples/{name}{salt}".encode())
    prompt = LEADS[style] + body + TAIL
    start = time.time()
    out = comfy.run("image_krea2_turbo_t2i", values(style, prompt, seed, name))
    seconds = round(time.time() - start, 1)
    suffix = f"_s{salt}" if salt else ""
    dest = HERE / style / f"{name}{suffix}.png"
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(out[0], dest)
    row = {"style": style, "scene": name, "seed": seed, "seconds": seconds, "file": dest.name, "prompt": prompt}
    with open(HERE / "times.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(style, name, seed, seconds, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--seed-salt", default="")
    ap.add_argument("--styles", default="AC")
    args = ap.parse_args()
    scenes = json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))
    for style in args.styles:
        for name in args.scenes or list(scenes):
            render(style, name, scenes[name], args.seed_salt)


if __name__ == "__main__":
    main()
