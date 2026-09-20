"""The title card's fades.

MEASURED on WotW ep03 (2026-09-19), the owner watching: the card's SOUND faded
in and out, its PICTURE did not, so the last shot hard-cut into the card and the
card hard-cut to black -- "it ended abruptly".  The picture now dips up from
black and down to it, and the sound's fade matches the picture's.
"""
from __future__ import annotations

IN_S = 0.5
OUT_S = 0.8


def card_fades(seconds: float) -> dict:
    """Fade timings and the ffmpeg filter fragments for a card of `seconds`."""
    in_d = min(IN_S, seconds)
    out_start = round(max(seconds - OUT_S, 0.0), 3)
    out_d = min(OUT_S, seconds)
    return {"in_d": in_d, "out_start": out_start, "out_d": out_d,
            "video": f"fade=t=in:st=0:d={in_d},fade=t=out:st={out_start:.3f}:d={out_d}",
            "audio": f"afade=t=in:d={in_d},afade=t=out:st={out_start:.3f}:d={out_d}"}
