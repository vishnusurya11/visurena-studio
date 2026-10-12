"""One ~4 s H3 image-to-video take from the A fireside still (slow push-in).

uv run python docs/audit/2026-10-12_jekyll_style_samples/take.py
Writes A_3_fireside_h3.mp4 beside this file and appends its seconds to times.jsonl.
"""
from __future__ import annotations

import json
import shutil
import time
import zlib
from pathlib import Path

from studio import comfy

HERE = Path(__file__).resolve().parent
PROMPT = ("The scene from the input image, brought to life. Lighting, palette and environment stay exactly as in "
          "the source image throughout.\nSHOT 1: A slow, steady push-in toward the fireplace between the two men. "
          "The fire flickers; the grey-haired man on the right smiles and lifts his wine glass slightly; the lean "
          "man on the left sits still and listens. No cut.\nAudio: a crackling coal fire, a clock ticking, quiet "
          "room tone.\nAbsolutely no text anywhere in frame: no titles, captions, subtitles, watermarks, logos, "
          "signage, labels or lettering of any kind.")


def main() -> None:
    still = HERE / "A" / "3_fireside.png"
    values = {"prompt": PROMPT, "start_image": comfy.stage_image(still), "width": 768, "height": 768,
              "frames": 90, "seed": zlib.crc32(b"jekyll_samples/take"),
              "filename_prefix": "jekyll_samples/A_3_fireside_h3"}
    start = time.time()
    out = comfy.run("video_minimax_h3_i2v_turbo", values)
    seconds = round(time.time() - start, 1)
    dest = HERE / "A_3_fireside_h3.mp4"
    shutil.copy2(out[0], dest)
    row = {"style": "A", "scene": "3_fireside", "take": dest.name, "seconds": seconds, "frames": 90, "prompt": PROMPT}
    with open(HERE / "times.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(dest, seconds, flush=True)


if __name__ == "__main__":
    main()
