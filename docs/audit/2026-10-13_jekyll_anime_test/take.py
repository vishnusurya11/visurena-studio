"""One ~4 s H3 image-to-video take from the strongest anime still (slow push-in), as style A's take.py.

uv run python docs/audit/2026-10-13_jekyll_anime_test/take.py RECIPE SUBJECT "ACTION"
Writes <RECIPE>_<SUBJECT>_h3.mp4 beside this file and appends its seconds to times.jsonl.
768 x 768, 90 frames (3.75 s at 24 fps), 8 steps, the style A take's seed.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
import zlib
from pathlib import Path

from studio import comfy

HERE = Path(__file__).resolve().parent
HEAD = ("The scene from the input image, brought to life as hand-drawn 2D anime: flat cel shading, crisp ink "
        "outlines and hard black ink shadows hold on every frame; lighting, palette and environment stay exactly "
        "as in the source image throughout.\nSHOT 1: A slow, steady push-in toward the figure. ")
FOOT = ("No cut.\nAudio: {audio}\nAbsolutely no text anywhere in frame: no titles, captions, subtitles, "
        "watermarks, logos, signage, labels or lettering of any kind.")


def prompt(action: str, audio: str) -> str:
    """The take prompt: style hold, the push-in, the action, the audio, the no-text wall."""
    return HEAD + action + " " + FOOT.format(audio=audio)


def main() -> None:
    recipe, subject, action = sys.argv[1:4]
    audio = sys.argv[4] if len(sys.argv) > 4 else "night wind, distant footsteps on wet cobbles, a hissing gas lamp."
    still = HERE / recipe / f"{subject}.png"
    text = prompt(action, audio)
    values = {"prompt": text, "start_image": comfy.stage_image(still), "width": 768, "height": 768,
              "frames": 90, "seed": zlib.crc32(b"jekyll_samples/take"),
              "filename_prefix": f"jekyll_anime/{recipe}_{subject}_h3"}
    start = time.time()
    out = comfy.run("video_minimax_h3_i2v_turbo", values)
    seconds = round(time.time() - start, 1)
    dest = HERE / f"{recipe}_{subject}_h3.mp4"
    shutil.copy2(out[0], dest)
    row = {"recipe": recipe, "subject": subject, "take": dest.name, "seconds": seconds, "frames": 90, "prompt": text}
    with open(HERE / "times.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(dest, seconds, flush=True)


if __name__ == "__main__":
    main()
