"""Jekyll anime-gothic test: the 2026-10-12 style A subjects redrawn as dark Victorian gothic anime.

uv run python docs/audit/2026-10-13_jekyll_anime_test/render.py RECIPE [subject ...] [--salt S]
Writes <RECIPE>/<subject>.png beside this file and appends each render's seconds to times.jsonl.
Seeds are style A's: crc32("jekyll_look/<subject>") for the cast and door, crc32("jekyll_samples/<scene>")
for the two scenes (subjects.json names each one's seed key). Bodies follow analysis/heads.json.
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
LEAD = ("A dark Victorian gothic anime film still: a mature seinen anime feature, 1990s hand-drawn cel animation, "
        "crisp ink linework, flat cel shading with hard black ink shadows, adult realistic proportions, long faces, "
        "painted gouache background art. Muted desaturated palette of fog-white, soot-black, bottle-green and sick "
        "gaslight amber; late-Victorian London; heavy chiaroscuro, thick fog, gaslight, deep shadow. ")
TAIL = (" Realistic adult anatomy, never chibi, never cute, no big sparkling eyes. "
        "No text, no lettering, no signature, no signage, no watermark.")
NEGATIVE = ("chibi, moe, cute, kawaii, big head, huge eyes, bright colours, pastel, photo, 3d render, text, "
            "lettering, signature, watermark, duplicate figure")
QWEN = "qwen" + chr(92)  # ComfyUI's LoRA subfolder separator on Windows
RECIPES = {  # name -> (workflow, extra inject values)
    "Q21": ("image_qwen_image_2_1_t2i", {"width": 1328, "height": 1328, "negative_prompt": NEGATIVE}),
    "DG": ("image_qwen_image_2_1_t2i_stylelora_visurena", {}),
    "NU": ("image_qwen_image_2_1_t2i_stylelora_visurena", {"style_lora": QWEN + "naoki_urasawa_qwen_v1.safetensors"}),
    "MA": ("image_qwen_image_2_1_t2i_stylelora_visurena", {"style_lora": QWEN + "MysticAnime.safetensors"}),
    "K2": ("image_krea2_turbo_t2i", {"aspect_ratio": "1:1 (Square)", "megapixels": 2, "refine_prompt": False,
                                     "enable_lora": False}),
}


def render(recipe: str, name: str, subject: dict, salt: str) -> None:
    seed = zlib.crc32(f"{subject['seed_key']}{salt}".encode())
    prompt = LEAD + subject["body"] + TAIL
    workflow, extra = RECIPES[recipe]
    values = {"prompt": prompt, "seed": seed, "filename_prefix": f"jekyll_anime/{recipe}_{name}", **extra}
    start = time.time()
    out = comfy.run(workflow, values)
    seconds = round(time.time() - start, 1)
    dest = HERE / recipe / f"{name}{'_s' + salt if salt else ''}.png"
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(out[0], dest)
    row = {"recipe": recipe, "workflow": workflow, "subject": name, "seed": seed, "seconds": seconds,
           "file": f"{recipe}/{dest.name}", "extra": {k: v for k, v in extra.items() if k != "negative_prompt"},
           "prompt": prompt}
    with open(HERE / "times.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(recipe, name, seed, seconds, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("recipe", choices=sorted(RECIPES))
    ap.add_argument("subjects", nargs="*")
    ap.add_argument("--salt", default="")
    args = ap.parse_args()
    subjects = json.loads((HERE / "subjects.json").read_text(encoding="utf-8"))
    for name in args.subjects or list(subjects):
        render(args.recipe, name, subjects[name], args.salt)


if __name__ == "__main__":
    main()
