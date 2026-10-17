"""The inner voice: a character thinking, in his own voice, close to the ear.

Anime-TV grammar (owner 2026-10-17), research 04 P3, tested as G1 on 2026-10-16
(docs/audit/2026-10-16_model_tests/voice/results.json).  An `inner` line is
recorded by the speaker's OWN engine (IndexTTS2 clone) with the `hushed` delivery
-- the G1 VoiceDesign read was breathier but another man (ECAPA 0.23 / 0.67) --
and assemble lays it through the close-mic chain G1 tested.  The hushed -5 dB is
the mix's delivery offset (`episode_emotion.OFFSETS`), so the chain carries no
gain of its own.  ADVISORY until the owner has heard it: the battery prints a
G-INNER note on every plan that uses one.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

DELIVERY = "hushed"
"""How an inner line is said when the plan names no delivery."""
CHAIN = "highpass=f=110,lowpass=f=6500,aecho=0.8:0.88:35|70:0.22|0.12"
"""G1's 'inner treatment' less its -5 dB: the room and the band of a voice heard
from inside the head."""


def command(src: Path, dst: Path) -> list[str]:
    return ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", CHAIN, str(dst)]


def treat(wavs: dict[int, Path], lines: list[dict], work: Path, run=subprocess.run) -> dict[int, Path]:
    """`wavs` with every inner line's file replaced by its close-mic copy in `work`."""
    out = dict(wavs)
    for line in lines:
        if line.get("kind") != "inner" or line["index"] not in wavs:
            continue
        dst = Path(work) / f"inner_l{line['index']:02d}.wav"
        run(command(wavs[line["index"]], dst), check=True)
        out[line["index"]] = dst
    return out
