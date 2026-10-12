"""Jekyll look test: the same four subjects in three styles, same seed per subject.

uv run python docs/audit/2026-10-11_jekyll_look_test/render.py subjects.json [subject ...]
Writes <style>/<subject>.png beside this file and appends each render's seconds to times.jsonl.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
import zlib
from pathlib import Path

from studio import comfy
from studio.refs_pack import STYLE_LEAD

HERE = Path(__file__).resolve().parent
BOOK_WORDS = ("Cinematic live-action photograph, anamorphic widescreen, natural film grain, photoreal, "
              "no stylisation, no illustration. Muted desaturated palette of fog-white, soot-black, "
              "bottle-green and sick gaslight amber; late-Victorian London; heavy chiaroscuro, deep shadow, "
              "damp air. ")  # the book's own refs words (refs.json location rows, photoreal_lead)
LEADS = {
    "A": BOOK_WORDS + "A Victorian gothic film still: fog, gaslight, deep shadow. ",
    "B": STYLE_LEAD,
    "C": ("A dark gothic ink illustration, etched pen-and-ink cross-hatching with heavy black brushwork, "
          "a Victorian penny-dreadful engraving, of "),
}
TAIL = " No text, no lettering, no signage, no watermark."


def values(style: str, prompt: str, seed: int, name: str) -> tuple[str, dict]:
    """The workflow and its inject values for one cell."""
    prefix = f"jekyll_look/{style}_{name}"
    if style == "B":
        return ("image_krea2_cinematic_2x_neutraltile_visurena",
                {"prompt": prompt, "seed": seed, "width": 1024, "height": 1024, "filename_prefix": prefix})
    return ("image_krea2_turbo_t2i",
            {"prompt": prompt, "seed": seed, "aspect_ratio": "1:1 (Square)", "megapixels": 2,
             "refine_prompt": False, "enable_lora": style == "C", "filename_prefix": prefix})


def render(style: str, name: str, body: str) -> None:
    seed = zlib.crc32(f"jekyll_look/{name}".encode())
    prompt = LEADS[style] + body + TAIL
    workflow, vals = values(style, prompt, seed, name)
    start = time.time()
    out = comfy.run(workflow, vals)
    seconds = round(time.time() - start, 1)
    dest = HERE / style / f"{name}.png"
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(out[0], dest)
    row = {"style": style, "subject": name, "seed": seed, "seconds": seconds, "workflow": workflow, "prompt": prompt}
    with open(HERE / "times.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(style, name, seconds, flush=True)


def main() -> None:
    subjects = json.loads((HERE / sys.argv[1]).read_text(encoding="utf-8"))
    names = sys.argv[2:] or list(subjects)
    for style in ("A", "B", "C"):
        for name in names:
            render(style, name, subjects[name])


if __name__ == "__main__":
    main()
