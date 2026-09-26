"""Generated sound effects for an episode: the cue, its level, where it lands.

An episode master had no effects at all: `mix_with_lines` was handed an empty
cue list.  This module makes the list.  A `Cue` names a sound in plain words
against one shot; `render` asks Stable Audio 3 (`audio_stableaudio3_sfx`, local,
$0) for it and levels the result; `placed` turns the rendered cues into the
`(master seconds, file)` pairs `trailer_assemble.mix` lays at unity gain; and
`event_db` lets QC ask whether a sound the plan names is audible in the master.

LEVEL.  `mix` sums every cue at unity (`amix ... normalize=0`), resampled to
48 kHz, then applies ONE gain to the whole programme to land -14 LUFS.  So a
cue's level in the file IS its level in the mix, relative to the lines
(levelled to -16 LUFS integrated) and the bed (~-25.6 LUFS, ducked under
lines).  Hence two targets, below, each measured the way its shape reads.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from pydantic import BaseModel, Field, field_validator

from studio import comfy
from studio.trailer_assemble import _ffmpeg, integrated, limiter, momentary

WORKFLOW = "audio_stableaudio3_sfx"
TIMEOUT = 600.0
STEPS, CFG = 8, 1.0
"""The manifest's sampler: 8 steps / cfg 1.0 (1 step collapses)."""

RATE = 48000
"""What `mix` resamples every input to; written at it so nothing resamples twice."""

CUE_LUFS = -20.0
"""Loudest MOMENTARY (400 ms) loudness of an event cue, before `gain_db`.

Momentary peak, not integrated: a gunshot is 200 ms of event and two seconds
of tail, and gated integrated loudness of that shape wanders by the length of
the tail.  -20 M sits about 4 LU under the lines (-16 I, whose own momentary
peaks run near -12) and ~6 LU over the bed: heard, never over a voice.  A cue
that should dominate (a gun at close range) asks for it with `gain_db`."""

CUE_TP = -3.0
"""True-peak ceiling on a levelled cue, the same as a line's (LINE_TP)."""

AMBIENCE_LUFS = -34.0
"""Integrated loudness of an ambience bed: ~8 LU under the music bed
(BED_TARGET_LUFS -25.6) and 6 over the -40 room tone.  Steady material, so
integrated is the honest measure."""

AMBIENCE_RENDER = 10.0
"""Seconds generated for an ambience bed; the loop is one LOOP_FADE shorter."""

LOOP_FADE = 1.0
"""Seconds of the render's head crossfaded into its tail to hide the seam."""

SPAN_FADE = 0.3
"""Fade at each end of a laid ambience span, so a setup enters and leaves soft."""

TAIL_FADE = 0.1
"""Fade on a cue's last samples: the generation is trimmed, not ended."""

PAD_FLOOR = -70.0
"""dBFS under which a file's last 200 ms is SA3's padding, not sound.
MEASURED 2026-09-26 on 12 live generations: every one stopped early (a 4 s
gun at 2.2-2.6 s, an 8 s crowd at 6.6 s) and padded with a -88 dB floor."""

PAD_MARGIN = 12.0
"""dB over that floor a 10 ms window must reach to count as the sound."""

SILENT_LUFS = -70.0
PRODUCTION = "realistic field recording, natural perspective, no music, no dialogue"
AMBIENT = "continuous background ambience, even level, no single loud event"


class Cue(BaseModel):
    """One sound, on one shot: what it is, when, how long, how loud."""

    shot: int
    sound: str = Field(min_length=3)
    at: float = Field(default=0.0, ge=0.0)
    seconds: float = Field(default=2.0, ge=1.0, le=10.0)
    gain_db: float = Field(default=0.0, ge=-20.0, le=12.0)

    @field_validator("sound")
    @classmethod
    def _worded(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a cue needs a sound")
        return value.strip()


def prompt_for(cue: Cue, where: str = "") -> str:
    """The SA3 prompt: the trained prefix, the sound, the place, the production
    words.  `where` carries period and place from the book, never the code."""
    parts = [f"TrackType: SFX, {cue.sound}"] + ([where] if where else []) + [PRODUCTION]
    return ", ".join(parts)


def values_for(prompt: str, seconds: float, seed: int, prefix: str) -> dict:
    """The workflow's inputs.  The trim defaults to 2 s in the template, so it
    is set to the generated length or every cue comes back two seconds long."""
    return {"prompt": prompt, "seconds": seconds, "trim_start": 0.0,
            "trim_duration": seconds, "seed": seed, "steps": STEPS, "cfg": CFG,
            "filename_prefix": prefix}


def file_name(cue: Cue) -> str:
    """shotNN_<hash of the sound>.wav: stable, and two sounds on a shot differ."""
    digest = hashlib.sha1(cue.sound.encode("utf-8")).hexdigest()[:8]
    return f"shot{cue.shot:02d}_{digest}.wav"


# ---------------------------------------------------------------- the cache

def ask_for(prompt: str, seed: int, seconds: float, target: float) -> dict:
    """What made a file: the sidecar's content and the cache key.  No path."""
    return {"prompt": prompt, "seed": seed, "seconds": seconds, "target": target}


def cached(out: Path, ask: dict) -> bool:
    """Whether `out` exists and its sidecar records this exact ask."""
    side = out.with_suffix(".json")
    if not (out.exists() and side.exists()):
        return False
    return json.loads(side.read_text(encoding="utf-8")) == ask


def remember(out: Path, ask: dict) -> None:
    out.with_suffix(".json").write_text(json.dumps(ask, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- the level

def peak_momentary(path: Path) -> float:
    """The loudest 400 ms of a file, LUFS; -inf for silence."""
    readings = [m for _, m in momentary(path)]
    return max(readings, default=float("-inf"))


def content_end(path: Path) -> float | None:
    """Seconds at which the sound stops and SA3's padding starts; None when
    the file ends on sound (an ambience, a cue that filled its length)."""
    audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
    levels = window_db(audio.mean(axis=1), rate, 0.01)
    floor = float(np.median(levels[-20:]))
    if floor > PAD_FLOOR:
        return None
    alive = np.nonzero(levels > floor + PAD_MARGIN)[0]
    return round((int(alive[-1]) + 1) * 0.01, 3) if len(alive) else None


def level(src: Path, out: Path, gain_db: float, end: float | None = None) -> Path:
    """One gain through the true-peak limiter, cut at `end`, tail faded, 48 kHz WAV."""
    seconds = end or sf.info(str(src)).duration
    fade = f"afade=t=out:st={max(seconds - TAIL_FADE, 0.0):.3f}:d={TAIL_FADE}"
    out.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-t", f"{seconds:.3f}", "-af",
             f"aresample={RATE},volume={gain_db:.2f}dB,{limiter(CUE_TP)},{fade}",
             "-ar", str(RATE), "-c:a", "pcm_s16le", str(out)], f"levelling {out.name}")
    return out


def gain_to(measured: float, target: float, what: Path) -> float:
    """The dB from measured to target; a silent generation is refused."""
    if measured < SILENT_LUFS:
        raise RuntimeError(f"{what.name} came back silent ({measured} LUFS)")
    return target - measured


def generate(prompt: str, seconds: float, seed: int, run, prefix: str) -> Path:
    """One workflow run; the first file it wrote."""
    produced = (run or comfy.run)(WORKFLOW, values_for(prompt, seconds, seed, prefix),
                                  timeout=TIMEOUT)
    return Path(produced[0])


def render(cue: Cue, out: Path, seed: int, run=None, where: str = "") -> Path:
    """Generate one cue and level its loudest moment to CUE_LUFS + gain_db."""
    out, target = Path(out), CUE_LUFS + cue.gain_db
    ask = ask_for(prompt_for(cue, where), seed, cue.seconds, target)
    if cached(out, ask):
        return out
    raw = generate(ask["prompt"], cue.seconds, seed, run, f"sfx_{out.stem}")
    level(raw, out, gain_to(peak_momentary(raw), target, out), content_end(raw))
    remember(out, ask)
    return out


def render_all(cues: list[Cue], folder: Path, seed: int, run=None,
               where: str = "") -> list[tuple[Cue, Path]]:
    """Every cue into `folder`, the n-th on seed + n."""
    return [(cue, render(cue, Path(folder) / file_name(cue), seed + n, run, where))
            for n, cue in enumerate(cues)]


# ---------------------------------------------------------------- placing

def placed(rendered: list[tuple[Cue, Path]], shots: list[dict]) -> list[tuple[float, Path]]:
    """The `(master seconds, file)` pairs `mix` takes, from placed.json rows."""
    rows = {int(s["index"]): s for s in shots}
    return [(start_of(cue, rows), path) for cue, path in rendered]


def start_of(cue: Cue, rows: dict[int, dict]) -> float:
    """Shot start + offset, pulled back so the cue ends inside its shot."""
    if cue.shot not in rows:
        raise KeyError(f"cue on shot {cue.shot}, which the cut does not have")
    row = rows[cue.shot]
    start, end = float(row["t_start"]), float(row["t_start"]) + float(row["seconds"])
    if cue.seconds > end - start + 1e-6:
        raise ValueError(f"shot {cue.shot} is {end - start:.2f}s; its cue "
                         f"'{cue.sound}' is {cue.seconds:.2f}s")
    return round(min(start + cue.at, end - cue.seconds), 3)


# ---------------------------------------------------------------- ambience

def spans(shots: list[dict], gap: float = 0.05) -> list[tuple[float, float]]:
    """(start, seconds) of each run of back-to-back shots."""
    out: list[list[float]] = []
    for row in sorted(shots, key=lambda s: float(s["t_start"])):
        start, seconds = float(row["t_start"]), float(row["seconds"])
        if out and start - (out[-1][0] + out[-1][1]) <= gap:
            out[-1][1] = round(start + seconds - out[-1][0], 6)
        else:
            out.append([start, seconds])
    return [(s, d) for s, d in out]


def loopable(src: Path, out: Path, fade: float = LOOP_FADE) -> Path:
    """Drop the head and crossfade it (equal power) into the tail: the file's
    end now runs into its own start with no seam."""
    audio, rate = sf.read(str(src), dtype="float32", always_2d=True)
    n = int(fade * rate)
    body = audio[n:].copy()
    ramp = np.linspace(0.0, np.pi / 2, n, dtype=np.float32)[:, None]
    body[-n:] = body[-n:] * np.cos(ramp) + audio[:n] * np.sin(ramp)
    sf.write(str(out), body, rate, subtype="FLOAT")
    return out


def render_bed(sound: str, out: Path, seed: int, run=None, where: str = "") -> Path:
    """One loopable ambience clip at AMBIENCE_LUFS integrated, cached."""
    cue = Cue(shot=0, sound=f"{sound}, {AMBIENT}", seconds=AMBIENCE_RENDER)
    ask = ask_for(prompt_for(cue, where), seed, AMBIENCE_RENDER, AMBIENCE_LUFS)
    if cached(out, ask):
        return out
    raw = generate(ask["prompt"], AMBIENCE_RENDER, seed, run, f"amb_{out.stem}")
    loop = loopable(raw, out.with_suffix(".seam.wav"))
    level(loop, out, gain_to(integrated(loop), AMBIENCE_LUFS, out))
    loop.unlink()
    remember(out, ask)
    return out


def loop_to(clip: Path, seconds: float, out: Path) -> Path:
    """The loop repeated to exactly `seconds`, faded in and out."""
    fades = (f"afade=t=in:d={SPAN_FADE},"
             f"afade=t=out:st={max(seconds - SPAN_FADE, 0.0):.3f}:d={SPAN_FADE}")
    _ffmpeg(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", str(clip),
             "-t", f"{seconds:.3f}", "-af", fades, "-ar", str(RATE),
             "-c:a", "pcm_s16le", str(out)], f"looping {out.name}")
    return out


def ambience(sound: str, shots: list[dict], folder: Path, seed: int, run=None,
             where: str = "") -> list[tuple[float, Path]]:
    """A setup's ambience under its shots: one render, one cue per span."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    stem = "amb_" + hashlib.sha1(sound.encode("utf-8")).hexdigest()[:8]
    bed = render_bed(sound, folder / f"{stem}.loop.wav", seed, run, where)
    return [(start, loop_to(bed, seconds, folder / f"{stem}_{start:07.2f}.wav"))
            for start, seconds in spans(shots)]


# ---------------------------------------------------------------- QC

WINDOW = 0.05


def decode(path: Path, start: float, seconds: float) -> np.ndarray:
    """Mono float32 samples at RATE of one stretch of a file (any container)."""
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{seconds:.3f}",
         "-i", str(path), "-vn", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
        capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"could not decode {Path(path).name}: {result.stderr[-300:]!r}")
    return np.frombuffer(result.stdout, dtype=np.float32)


def window_db(samples: np.ndarray, rate: int, window: float = WINDOW) -> np.ndarray:
    """RMS level in dBFS of each whole `window`-second slice."""
    size = int(window * rate)
    count = len(samples) // size
    frames = samples[:count * size].reshape(count, size).astype(np.float64)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    return 20.0 * np.log10(np.maximum(rms, 1e-10))


def event_db(master: Path, start: float, seconds: float, around: float = 1.0) -> float:
    """dB by which the cue window's loudest 50 ms stands over the median of the
    `around` seconds before it.  A named sound the master lacks reads ~0."""
    lead = min(around, start)
    if lead < WINDOW:
        raise ValueError(f"no audio before {start:.2f}s to compare the cue against")
    levels = window_db(decode(master, start - lead, lead + seconds), RATE)
    split = int(round(lead / WINDOW))
    return round(float(levels[split:].max() - np.median(levels[:split])), 2)
