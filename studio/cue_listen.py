"""The listen gate: does the cue SOUND like what was asked for?

Runs 9-12 graded sixteen cues on form, tempo and grid and shipped four of
them; every one was a parlour chamber piece, because that is what the caption
asked for, and nothing in the pipeline could hear it.  Structure is measured
from onsets and loudness; the KIND of music is not in those numbers.

A text-audio model (CLAP: one embedding space for captions and sound) can
hear it.  The brick: the brief is a promise, the probes are the sounds a cue
has come back as before, and the cue passes when the brief is the nearest
sentence to what it sounds like.  Rank, never a threshold -- a cosine of 0.3
means nothing on its own, but "closer to 'a small chamber ensemble in a
parlour' than to 'orchestral trailer music'" is a finding a Learning can
quote and the next caption can answer.

The embedder is injected.  `ClapEmbedder` imports transformers inside its
constructor, so this module loads on a box without the checkpoint and the
tests never touch a model.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import numpy as np
from pydantic import BaseModel

from studio.music_tone import TRAILER_GENRE, Tone

PROBES = {
    "parlour": "a small acoustic chamber ensemble playing period music in a parlour room",
    "song": "a pop song with a drum kit, bass guitar and a singer",
    "drone": "a quiet ambient drone with slow synthesizer pads",
}
"""What a cue has come back as when the caption lost.  Each sentence names its
probe so a Learning row reads as English."""

CLAP_MODEL = "laion/clap-htsat-unfused"
CLAP_RATE = 48_000
WINDOW_SECONDS = 10
"""CLAP hears ten seconds.  Its processor takes a RANDOM ten seconds of a
longer clip, so one call on a 112 s cue scored a different slice each time
(measured 2026-09-06: the same file moved 0.51 -> 0.34 on one probe between
two runs).  The cue is embedded window by window and the windows averaged."""
BRIEF_WORDS = 40
"""CLAP's text tower truncates at 77 tokens; a brief stays well under it."""


class Verdict(BaseModel):
    """What the cue sounded nearest to, and every score behind that call."""

    heard: str
    scores: dict[str, float]
    why: str

    @property
    def passes(self) -> bool:
        return self.heard == "brief"


class Embedder(Protocol):
    def text(self, sentences: list[str]) -> np.ndarray: ...
    def audio(self, path: Path) -> np.ndarray: ...


def brief_for(tone: Tone) -> str:
    """The promise in CLAP's own register: genre, colour, mood, one sentence."""
    return f"{TRAILER_GENRE}, {tone.genre}, {', '.join(tone.mood)}"


def cosines(audio: np.ndarray, texts: np.ndarray) -> np.ndarray:
    """Cosine of the audio against each text row."""
    a = audio / (np.linalg.norm(audio) + 1e-9)
    t = texts / (np.linalg.norm(texts, axis=1, keepdims=True) + 1e-9)
    return t @ a


def listen(cue: Path, tone: Tone, embedder: Embedder) -> Verdict:
    """Rank the brief against the probes by what the cue sounds like."""
    names = ["brief", *PROBES]
    sentences = [brief_for(tone), *PROBES.values()]
    scored = cosines(embedder.audio(cue), embedder.text(sentences))
    scores = {name: round(float(s), 4) for name, s in zip(names, scored)}
    heard = max(scores, key=scores.get)
    return Verdict(heard=heard, scores=scores, why=why_of(heard, scores))


def why_of(heard: str, scores: dict[str, float]) -> str:
    """One line a Learning can carry: what it sounded like, against the brief."""
    if heard == "brief":
        return f"heard the brief ({scores['brief']}) above every probe"
    return (f"heard {heard} ({scores[heard]}) above the brief ({scores['brief']}): "
            f"the cue sounds like {PROBES[heard]}")


def verdict_path(cue: Path) -> Path:
    return cue.with_suffix(".listen.json")


def write_verdict(cue: Path, verdict: Verdict) -> Path:
    """The verdict beside the cue, like its caption and its cut map."""
    path = verdict_path(cue)
    path.write_text(verdict.model_dump_json(indent=2), encoding="utf-8")
    return path


def windows(samples: np.ndarray, rate: int = CLAP_RATE,
            seconds: int = WINDOW_SECONDS) -> list[np.ndarray]:
    """Consecutive full windows of the cue; a short tail is dropped."""
    step = rate * seconds
    return [samples[i:i + step] for i in range(0, len(samples) - step + 1, step)] or [samples]


def features_of(out) -> np.ndarray:
    """The projected embedding, whichever way transformers hands it back:
    a bare tensor before v5, an output object carrying it as
    `pooler_output` from v5 (measured on 5.16.1)."""
    tensor = getattr(out, "pooler_output", out)
    return tensor.detach().float().cpu().numpy()


class ClapEmbedder:
    """LAION CLAP through transformers; the checkpoint loads on first use."""

    def __init__(self, model_id: str = CLAP_MODEL, device: str | None = None):
        import torch
        from transformers import ClapModel, ClapProcessor
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = ClapModel.from_pretrained(model_id).to(self.device).eval()
        self.processor = ClapProcessor.from_pretrained(model_id)

    def text(self, sentences: list[str]) -> np.ndarray:
        import torch
        inputs = self.processor(text=sentences, return_tensors="pt", padding=True)
        with torch.no_grad():
            out = self.model.get_text_features(**{k: v.to(self.device) for k, v in inputs.items()})
        return features_of(out)

    def audio(self, path: Path) -> np.ndarray:
        import librosa
        import torch
        samples, _ = librosa.load(path, sr=CLAP_RATE, mono=True)
        inputs = self.processor(audio=windows(samples), sampling_rate=CLAP_RATE, return_tensors="pt")
        with torch.no_grad():
            out = self.model.get_audio_features(**{k: v.to(self.device) for k, v in inputs.items()})
        return features_of(out).mean(axis=0)
