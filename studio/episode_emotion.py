"""How an episode line is SAID: its delivery, its emotion clip, its lift, its level.

ROOT CAUSE 2026-09-26 (D11).  `say_lines` handed IndexTTS2 the cast's quiet
reading clip as the emotion reference as well as the timbre, so every line in
twelve episodes was read at one temperature -- the largest pitch lift on any
'!' line in the series is +2.3 semitones -- and the mix then levelled a whisper
and a scream to one loudness.

IndexTTS2 already takes the two apart (`studio/voice_say.py`): the timbre from
the cast's design clip, the delivery from a SECOND clip in the same voice.  So
each speaker gets one clip per register, designed once from their own design
instruction plus a director's note (`voice_bank.DELIVERY`), kept under
`cast/<speaker>/voice/emotion/<register>.wav`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from studio import voice_bank

OFFSETS = {"shouting": 3.0, "exultant": 2.0, "urgent": 1.0, "hushed": -5.0, "grieving": -2.0,
           "threatening": -2.0}
"""dB on top of the line target in the mix: a shout sits above the narration,
a whisper under it.  Everything else lands at the target."""
LIFTED = frozenset({"shouting", "exultant"})
"""The registers whose pitch must rise over the speaker's calm read."""
LIFT_ST = 2.0
"""Semitones a shout must rise over the calm median.  The series' flat shouts
measure -1.5 to +1.1; the one line that was heard as raised (ep02 Ogilvy) +2.3."""


def delivery_of(line) -> str:
    """The written delivery, else a shout for a line that ends in '!', else calm."""
    if getattr(line, "delivery", ""):
        return line.delivery
    return "shouting" if line.text.rstrip(" \"'’”").endswith("!") else voice_bank.TIMBRE


def instruct_for(sheet: dict, register: str) -> str:
    """The speaker's own design instruction with the register's delivery note."""
    note = voice_bank.DELIVERY.get(register, voice_bank.DELIVERY[voice_bank.TIMBRE])
    return f"{sheet.get('instruction', '').strip()} Speak this {note}"


def voice_dir(book: Path, speaker: str) -> Path:
    return Path(book) / "cast" / speaker / "voice"


def emotion_clip(book: Path, speaker: str, register: str, render: Callable | None = None) -> Path:
    """The clip that carries HOW: the design clip when calm, else the register's
    clip, designed once in this speaker's voice and kept."""
    folder = voice_dir(book, speaker)
    if register == voice_bank.TIMBRE:
        return folder / "design.wav"
    out = folder / "emotion" / f"{register}.wav"
    if not out.exists():
        sheet = json.loads((folder / "voice.json").read_text(encoding="utf-8"))
        (render or render_design)(instruct_for(sheet, register), out)
    return out


def render_design(instruct: str, dest: Path) -> Path:
    """One Qwen3-TTS VoiceDesign read of the bank passage, conformed to `dest`."""
    from studio import voice
    dest.parent.mkdir(parents=True, exist_ok=True)
    made = voice.comfy.run(voice.DESIGN_WORKFLOW,
                           {"text": voice_bank.bank_text({}, voice_bank.TIMBRE), "instruct": instruct,
                            "filename_prefix": f"emotion_{dest.stem}"}, timeout=voice.DESIGN_TIMEOUT)
    return voice._render(made[0], dest)


def f0_median(wav: Path) -> float:
    """The median voiced pitch of a clip, Hz (pYIN); 0 when nothing is voiced."""
    import librosa
    import numpy as np
    audio, rate = librosa.load(str(wav), sr=16000, mono=True)
    f0, voiced, _ = librosa.pyin(audio, fmin=60.0, fmax=500.0, sr=rate)
    got = f0[voiced & ~np.isnan(f0)] if f0 is not None else []
    return float(np.median(got)) if len(got) else 0.0


def lift_st(wav: Path, calm_hz: float) -> float:
    """How far a clip's median pitch sits above the calm median, in semitones."""
    import math
    got = f0_median(wav)
    return 12.0 * math.log2(got / calm_hz) if got > 0 and calm_hz > 0 else 0.0


def prosody_ok(register: str, wav: Path, calm_hz: float) -> bool:
    """A lifted register must rise LIFT_ST over the calm read; others are not asked."""
    return register not in LIFTED or lift_st(wav, calm_hz) >= LIFT_ST


def offset_of(register: str) -> float:
    return OFFSETS.get(register, 0.0)
