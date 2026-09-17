"""Say a trailer line with the character's TIMBRE and the beat's EMOTION.

IndexTTS2 takes the two apart: `ref_audio` carries who is speaking,
`emotion_audio` carries how, and `emotion_alpha` says how far to push it.  So
a line is never read at one temperature -- Holmes stating a deduction is cold,
Hope naming the hour of his revenge is a threat, and both are the same voice.

Both references come from the character's own bank (`voice_bank`), so the
emotion is that character feeling something rather than a stranger's read
pasted onto their timbre.
"""
from __future__ import annotations

from pathlib import Path

from studio import comfy
from studio.voice import _stage_reference, clip_seconds, post_process
from studio.trailer_stage_spec import VoiceLine

WORKFLOW = "audio_indextts2_tts_single_speaker"
TIMEOUT = 900.0

ALPHA = 0.8
"""How far the emotion reference is pushed.  Below this the read comes back
neutral and the bank was wasted; at 1.0 the timbre starts to follow the
emotion clip instead of the speaker's."""

ROOM_S = 0.12
"""Silence appended after the last sample, so the last consonant has somewhere
to release.  MEASURED on episode 10: the median trailing room across thirty
lines was 0.05 s, fourteen had less, and l14 ("young.") and l05 ended with
0.00 s at -25 / -30 dB in their last 50 ms -- cut off on the edit.  120 ms is
under the 0.70 s BREATH the timeline already leaves between lines, so nothing
downstream moves; the timeline reads the seconds off the file either way."""


def pad_room(out: Path, seconds: float = ROOM_S) -> Path:
    """`seconds` of digital silence appended to `out`, in place."""
    import numpy as np
    import soundfile as sf

    audio, rate = sf.read(str(out), dtype="float32", always_2d=True)
    tail = np.zeros((int(round(seconds * rate)), audio.shape[1]), dtype=np.float32)
    sf.write(str(out), np.concatenate([audio, tail]), rate, subtype="PCM_16")
    return out


def values_for(text: str, timbre: Path, emotion: Path, seed: int,
               alpha: float = ALPHA) -> dict:
    """What the workflow is filled with for one spoken line."""
    return {"text": text, "seed": seed, "emotion_alpha": alpha,
            "ref_audio": _stage_reference(Path(timbre)),
            "emotion_audio": _stage_reference(Path(emotion)),
            "filename_prefix": "trailer_say"}


def say(text: str, timbre: Path, emotion: Path, seed: int, out: Path,
        index: int = 0, speaker: str | None = None, alpha: float = ALPHA,
        run=None) -> VoiceLine:
    """One line, in this character's voice, with this beat's feeling."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    produced = (run or comfy.run)(WORKFLOW, values_for(text, timbre, emotion, seed, alpha),
                                  timeout=TIMEOUT)
    post_process(produced[0], out)
    pad_room(out)
    return VoiceLine(index=index, text=text, speaker=speaker, rel_path=out.name,
                     seconds=clip_seconds(out), seed=seed)
