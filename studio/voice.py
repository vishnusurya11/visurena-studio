"""Step 05's engine: a DESIGNED voice per character, every line cloned from it.

The rule (09-voice, V8): no real person's voice is ever cloned.  A character
gets a reference clip designed from an instruct derived from the cast card,
spoken in a sentence of the character's own; every trailer line is then a
clone of that reference, so ten lines sound like one speaker.  Two things are
never trusted from text: the seconds of a line (MEASURED from the file with
ffmpeg, because a plan built on a word-count estimate ends up 40% wrong) and
the speaker identity (a resemblyzer cosine against the reference).

Renders go through `comfy.run` on the two workflows named below; tests
replace it.  `SIMILARITY_FLOOR` was set by measurement, not chosen: see the
note beside it.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from studio import comfy
from studio.cast_card import age_band, infer_gender
from studio.trailer_assemble import clip_seconds
from studio.trailer_stage_spec import VoiceLine

SIMILARITY_FLOOR = 0.65
"""Measured 2026-09-04 by `test_threshold_separates_two_designed_voices` on the
live Qwen3-TTS render (Holmes + Lucy, five lines each, resemblyzer GE2E):
same-voice 0.696-0.884, cross-voice 0.393-0.521.  Anything in (0.52, 0.70)
separates every pair; 0.75 would have failed a 0.63 s two-word line whose
embedding is under-supported, not badly cloned.  0.65 keeps 0.13 of margin
above the worst cross-voice score.  One speaker pair, ten clips: revalidate
when a third designed voice exists."""
DESIGN_WORKFLOW = "audio_qwen3tts_design"
CLONE_WORKFLOW = "audio_qwen3tts_clone"
MAX_LINE_TOKENS = 512
"""A trailer line is <= 12 words; a runaway generation past this is a hallucination."""
LINE_LUFS = -20.0
"""Every line lands here so the ducker keys on the same thing (08-assemble)."""
RATE = 24000
DESIGN_TIMEOUT = 600.0
LINE_TIMEOUT = 300.0
MIN_INSTRUCT_WORDS, MAX_INSTRUCT_WORDS = 15, 40
MIN_REF_WORDS, MAX_REF_WORDS = 6, 25
"""Long enough to carry a timbre, short enough that a 1.7B design stays on one voice."""
AGE_WORD = {"young": "young", "middle": "middle-aged", "old": "elderly"}
DELIVERY = "Period diction of the source, an even unhurried pace, a calm neutral read."
"""Era goes into diction; an accent word drifts the model to American (09-voice)."""
NEUTRAL_SENTENCE = ("I have not seen the house since the autumn, "
                    "and the road was longer than I remembered.")
POST_CHAIN = "highpass=f=90,equalizer=f=3000:width_type=o:width=1:g=2"
"""Clear the room the bed's low band owns, then presence so the line reads at -20."""

_ENCODER = None


def _first_sentence(text: str) -> str:
    """The card's first sentence, ending with a full stop."""
    head = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0].strip()
    if head and head[-1] not in ".!?":
        head += "."
    return head


def voice_instruct(speaker: dict) -> str:
    """15-40 words from the card: sex, age, role, how they speak, and the delivery.

    A template, not a model call: the model would name an accent, and an accent
    word is the one thing that moves the voice the wrong way.
    """
    profile = speaker.get("profile", {})
    physical = profile.get("physical", "")
    gender = infer_gender(speaker.get("name", ""), speaker.get("aliases", []), physical)
    age = AGE_WORD[age_band(physical)]
    article = "An" if age[0] in "aeiou" else "A"
    parts = [f"{article} {age} {gender}, the {speaker.get('role', 'character')}.",
             _first_sentence(profile.get("voice", "")),
             _first_sentence(profile.get("mental", "")), DELIVERY]
    parts = [p for p in parts if p]
    while len(" ".join(parts).split()) > MAX_INSTRUCT_WORDS and len(parts) > 2:
        parts.pop(-2)
    return " ".join(parts)


def reference_text(speaker: dict) -> str:
    """A sentence of the character's own for the reference: 6-25 words, never a
    trailer line, so the clone's ref_text is not the line it is asked to say."""
    for quote in speaker.get("quotes", []):
        text = quote.get("quote", "").strip("“”\"'‘’ \n")
        if MIN_REF_WORDS <= len(text.split()) <= MAX_REF_WORDS:
            return text
    return NEUTRAL_SENTENCE


def seed_for(speaker_id: str, attempt: int) -> int:
    """One seed per character, advanced per reroll: the same seed twice is a bug."""
    base = int.from_bytes(hashlib.sha1(speaker_id.encode()).digest()[:4], "big")
    return base % (2**31 - 1024) + attempt


STAGES = ("trailer", "episodes")
"""The book-level folders a rendered line may live under."""


def book_relative(path: Path) -> str:
    """The path as an artifact stores it: relative to the book dir, posix."""
    path = Path(path)
    for parent in path.parents:
        if parent.name in STAGES:
            return path.relative_to(parent.parent).as_posix()
    raise ValueError(f"{path} is not under a book's {'/'.join(STAGES)} dir")


def _render(src: Path, dst: Path, filters: str = "") -> Path:
    """Conform to the voice format (24 kHz mono pcm) through an optional filter chain."""
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src)]
    if filters:
        cmd += ["-af", filters]
    cmd += ["-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", str(dst)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"ffmpeg failed rendering {dst.name}: {proc.stderr.strip()[-400:]}")
    return dst


def integrated_lufs(path: Path) -> float:
    """EBU R128 integrated loudness of a file, from ffmpeg's summary."""
    proc = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path),
                           "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                          capture_output=True, text=True)
    hit = re.search(r"Integrated loudness:\s*I:\s*(-?[\d.]+) LUFS", proc.stderr)
    if not hit:
        raise RuntimeError(f"no loudness summary for {path}: {proc.stderr[-400:]}")
    return float(hit.group(1))


def post_process(src: Path, dst: Path) -> Path:
    """The line chain, then one gain to LINE_LUFS.

    Two passes because the gain is a function of the filtered signal: the
    HPF takes energy out, so measuring before it would land the line low.
    """
    flat = dst.with_name(dst.stem + ".flat.wav")
    _render(src, flat, POST_CHAIN)
    gain = LINE_LUFS - integrated_lufs(flat)
    _render(flat, dst, f"volume={gain:.2f}dB,alimiter=limit=0.708:level=disabled")  # -3 dBFS ceiling
    flat.unlink()
    return dst


def design_reference(speaker: dict, out_dir: Path) -> Path:
    """One reference clip per character, cached by id; the instruct and the
    sentence sit beside it so a clone can read the ref_text back."""
    out = Path(out_dir) / f"{speaker['id']}.wav"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    text, instruct = reference_text(speaker), voice_instruct(speaker)
    produced = comfy.run(DESIGN_WORKFLOW, {
        "text": text, "instruct": instruct,
        "filename_prefix": f"trailer_voice_ref_{speaker['id']}"}, timeout=DESIGN_TIMEOUT)
    _render(produced[0], out)
    out.with_suffix(".txt").write_text(text, encoding="utf-8")
    out.with_suffix(".instruct.txt").write_text(instruct, encoding="utf-8")
    return out


def _stage_reference(reference: Path) -> str:
    """Stage under a content-hashed name: two books' `narrator.wav` would
    otherwise collide in ComfyUI's single input dir."""
    digest = hashlib.sha1(reference.read_bytes()).hexdigest()[:10]
    staged = Path(tempfile.gettempdir()) / f"trailer_ref_{digest}.wav"
    shutil.copy2(reference, staged)
    return comfy.stage_image(staged)


def clone_line(reference: Path, text: str, seed: int, out: Path,
               index: int = 0, speaker: str | None = None) -> VoiceLine:
    """Say `text` in the reference's voice; the seconds come from the file."""
    reference, out = Path(reference), Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ref_txt = reference.with_suffix(".txt")
    ref_text = ref_txt.read_text(encoding="utf-8").strip() if ref_txt.exists() else ""
    produced = comfy.run(CLONE_WORKFLOW, {
        "ref_audio": _stage_reference(reference), "ref_text": ref_text,
        "target_text": text, "seed": seed, "max_new_tokens": MAX_LINE_TOKENS,
        "filename_prefix": f"trailer_voice_line_{out.stem}"}, timeout=LINE_TIMEOUT)
    post_process(produced[0], out)
    return VoiceLine(index=index, text=text, speaker=speaker, rel_path=book_relative(out),
                     seconds=clip_seconds(out), seed=seed)


def _encoder():
    """The GE2E speaker encoder, loaded once (its weights ship in the package)."""
    global _ENCODER
    if _ENCODER is None:
        from resemblyzer import VoiceEncoder
        _ENCODER = VoiceEncoder("cpu", verbose=False)
    return _ENCODER


_EMBEDDED: dict[tuple[str, int, int], "object"] = {}


def embedding(clip: Path):
    """The GE2E speaker embedding of one file, computed once and kept.

    Comparing a cast of N is N*(N-1)/2 pairs but only N voices, and embedding
    inside `similarity` made it 2 per pair: 23 characters cost 506 embeddings
    where 23 would do.  The dot product is microseconds; the embedding is the
    whole cost.  Keyed on size and mtime so a re-rendered clip is re-read.
    """
    from resemblyzer import preprocess_wav

    path = Path(clip)
    stat = path.stat()
    key = (str(path), stat.st_size, int(stat.st_mtime))
    if key not in _EMBEDDED:
        _EMBEDDED[key] = _encoder().embed_utterance(preprocess_wav(path))
    return _EMBEDDED[key]


def similarity(a: Path, b: Path) -> float:
    """Cosine between resemblyzer (GE2E, 256-d) speaker embeddings of two files.

    Chosen over MFCC cosine because MFCC measures the room and the words as
    much as the speaker; GE2E was trained to ignore both.  CPU on purpose --
    the encoder is small, and it must never take VRAM off a render.
    """
    import numpy as np

    ea, eb = embedding(a), embedding(b)
    return float(np.dot(ea, eb) / (np.linalg.norm(ea) * np.linalg.norm(eb) + 1e-9))


def apart(clips: dict[str, Path]) -> dict[tuple[str, str], float]:
    """Every pair of a cast, scored -- N embeddings, not 2 per pair."""
    import itertools

    for clip in clips.values():
        embedding(clip)
    return {(one, other): similarity(clips[one], clips[other])
            for one, other in itertools.combinations(sorted(clips), 2)}
