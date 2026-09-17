"""Listening to a voice on the GPU: who is speaking, and at what pitch.

Two measurements, both of which the repo was doing badly.

WHO IS SPEAKING.  `voice.similarity` uses Resemblyzer -- GE2E, 2019, roughly
5% EER on VoxCeleb1.  ECAPA-TDNN measures 0.73% on the same set, an order of
magnitude sharper, and the difference matters because the whole cast currently
scores a MEDIAN 0.70 against a 0.65 same-person line.  With a blunt instrument
you cannot tell "these voices are genuinely alike" from "this encoder cannot
separate them", and those two findings call for opposite fixes.

AT WHAT PITCH.  The register checks in this session used a hand-rolled
autocorrelation F0 -- fine for a sanity check, wrong often enough on creaky and
breathy voices to mislead.  torchcrepe is a trained pitch model and runs on the
same GPU.

WHY THIS MODULE LIVES APART FROM `voice.py`.  The repo venv carries
`torch 2.14.0+cpu` -- no CUDA at all -- while ComfyUI's embedded python has
`2.11.0+cu130`.  So anything wanting the GPU runs under ComfyUI's interpreter,
and `voice.py` keeps its CPU Resemblyzer path for the pipeline steps that
already trust its numbers.  Two encoders, two thresholds, neither pretending to
be the other.
"""
from __future__ import annotations

from pathlib import Path

ECAPA = ("D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable/ComfyUI"
         "/models/spkrec/ecapa")

SAME_SPEAKER = 0.55
"""ECAPA cosine at or above which two clips are one person.

NOT Resemblyzer's 0.65 -- a different encoder has a different scale, and
carrying the old number across would be the classic mistake.  0.55 is the
conventional operating point for ECAPA on VoxCeleb-like audio and is a
STARTING GUESS here: recalibrate against a pair known to be the same character
and a pair known not to be, then write the measured number in its place."""

_MODEL = {}
_HEARD: dict[tuple[str, int, int], object] = {}


def best_device() -> str:
    """The GPU when there is one, and honestly the CPU when there is not.

    The repo venv carries a CPU-only torch while ComfyUI's embedded python has
    CUDA, so the same module runs in both and the caller does not have to know
    which interpreter it is in.  ECAPA is small: 253 pairs took 3.3 s on the
    4090 and the CPU path is usable, just slower."""
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def _shim() -> None:
    """Two API removals that speechbrain 1.0.3 has not caught up with.

    `torchaudio.list_audio_backends` went in torchaudio 2.11, and
    `hf_hub_download(use_auth_token=)` went in huggingface_hub -- speechbrain
    passes it even when the source is a local directory, so pinning the
    weights on disk does not avoid it.  Both are dropped rather than worked
    around, because the alternative is holding this env back to older torch
    for a keyword nobody uses."""
    import huggingface_hub
    import torchaudio

    if not hasattr(torchaudio, "list_audio_backends"):
        torchaudio.list_audio_backends = lambda: ["soundfile"]

    if not getattr(huggingface_hub.hf_hub_download, "_shimmed", False):
        real = huggingface_hub.hf_hub_download

        def without_auth(*args, **kwargs):
            kwargs.pop("use_auth_token", None)
            return real(*args, **kwargs)

        without_auth._shimmed = True
        huggingface_hub.hf_hub_download = without_auth
        import speechbrain.utils.fetching as fetching

        fetching.huggingface_hub.hf_hub_download = without_auth


def encoder(device: str = "") -> object:
    """ECAPA-TDNN, loaded once, kept on the GPU."""
    _shim()
    device = device or best_device()
    if device not in _MODEL:
        from speechbrain.inference.speaker import EncoderClassifier

        # COPY, not the default symlink: Windows refuses to link without
        # Developer Mode, and the failure surfaces as WinError 1314 deep
        # inside speechbrain's fetcher rather than as a permissions message.
        try:
            from speechbrain.utils.fetching import LocalStrategy

            extra = {"local_strategy": LocalStrategy.COPY_SKIP_CACHE}
        except (ImportError, AttributeError):  # pragma: no cover - older speechbrain
            extra = {}
        _MODEL[device] = EncoderClassifier.from_hparams(
            source=ECAPA, savedir=ECAPA, run_opts={"device": device}, **extra)
    return _MODEL[device]


def embed_samples(samples, device: str = ""):
    """The 192-d ECAPA embedding of samples already in memory, uncached."""
    import numpy as np
    import torch

    device = device or best_device()
    batch = torch.tensor(np.asarray(samples, dtype="float32")).unsqueeze(0).to(device)
    with torch.no_grad():
        got = encoder(device).encode_batch(batch)
    return got.squeeze().detach().cpu().numpy()


def embedding(clip: Path, device: str = ""):
    """The 192-d ECAPA embedding of one file, computed once and kept.

    Cached on size and mtime, so a re-rendered clip is re-read: comparing a
    cast of N is N*(N-1)/2 pairs but only N voices."""
    import soundfile as sf

    device = device or best_device()
    path = Path(clip)
    stat = path.stat()
    key = (str(path), stat.st_size, int(stat.st_mtime))
    if key not in _HEARD:
        wave, _ = sf.read(str(path))
        _HEARD[key] = embed_samples(wave, device)
    return _HEARD[key]


def self_similarity(clip: Path, device: str = "") -> float:
    """One clip's first half against its second: does a voice agree with ITSELF?

    MEASURED on the cast of A Study in Scarlet (ep10 DQ, CPU ECAPA): Watson
    0.762, Drebber 0.770, Lucy 0.721, Young 0.706, Holmes 0.704, Hope 0.695,
    Stangerson 0.559, Ferrier 0.498.  A design clip that changes voice halfway
    has a whole-clip embedding that is an AVERAGE of two people, and no line
    rendered from it can score well against an average -- Ferrier's best line
    in the book is 0.815 and his median 0.726 against Watson's 0.855.  The
    fault is visible at cast time, from one file, before a line is said."""
    import numpy as np
    import soundfile as sf

    wave, _ = sf.read(str(clip), dtype="float32", always_2d=True)
    mono = wave.mean(axis=1)
    half = len(mono) // 2
    a, b = embed_samples(mono[:half], device), embed_samples(mono[half:], device)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def similarity(a: Path, b: Path, device: str = "") -> float:
    """Cosine between two voices, on the GPU."""
    import numpy as np

    device = device or best_device()
    ea, eb = embedding(a, device), embedding(b, device)
    return float(np.dot(ea, eb) / (np.linalg.norm(ea) * np.linalg.norm(eb) + 1e-9))


def apart(clips: dict[str, Path], device: str = "") -> dict[tuple[str, str], float]:
    """Every pair of a cast, scored -- N embeddings, not two per pair."""
    import itertools

    device = device or best_device()
    for clip in clips.values():
        embedding(clip, device)
    return {(one, other): similarity(clips[one], clips[other], device)
            for one, other in itertools.combinations(sorted(clips), 2)}


def nearest(clip: Path, cast: dict[str, Path], device: str = "") -> tuple[str, float]:
    """The voice already cast that this one sounds most like.

    What an audition is scored on: a candidate is only as good as its WORST
    resemblance, because one collision is one collision."""
    device = device or best_device()
    if not cast:
        return "", 0.0
    scored = [(who, similarity(clip, other, device)) for who, other in cast.items()]
    return max(scored, key=lambda row: row[1])


def pitch(clip: Path, device: str = "") -> float:
    """Median F0 in hertz, from torchcrepe rather than autocorrelation."""
    import numpy as np
    import torch
    import torchaudio
    import torchcrepe

    device = device or best_device()
    wave, rate = torchaudio.load(str(clip))
    wave = wave.mean(dim=0, keepdim=True)
    if rate != 16000:
        wave = torchaudio.functional.resample(wave, rate, 16000)
    found = torchcrepe.predict(wave.to(device), 16000, hop_length=160,
                               fmin=60.0, fmax=400.0, model="full",
                               device=device, batch_size=512)
    voiced = found[found > 0].detach().cpu().numpy()
    return float(np.median(voiced)) if voiced.size else 0.0


def report(scores: dict[tuple[str, str], float], line: float = SAME_SPEAKER) -> str:
    """The cast's spread, worst pair first."""
    import statistics as st

    values = sorted(scores.values())
    over = [pair for pair, score in scores.items() if score >= line]
    head = (f"{len(scores)} pairs | min {values[0]:.2f} median "
            f"{st.median(values):.2f} max {values[-1]:.2f} | "
            f"{len(over)} at or above {line}")
    worst = sorted(scores.items(), key=lambda row: -row[1])[:12]
    return "\n".join([head, *(f"  {a} vs {b}: {s:.2f}" for (a, b), s in worst)])
