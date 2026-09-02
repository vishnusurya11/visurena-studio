"""Where the music actually does something -- measured, not intended.

A generated cue does not land its hit where the prompt asked.  The 2026-08-25
trailer proves the cost: its cue's money impact sits at 80.5s, the title card
was cut at 75.21s, and the braam therefore lands two seconds INTO the button
shot.  Nothing in that chain was wrong except that the picture was conformed to
the section plan instead of to the audio.

So the cut grid is derived by decoding the audio and reading its envelope
directly.  Intent is a hypothesis; the waveform is the evidence.

Decoding rather than scraping ffmpeg's log is deliberate: the first version of
this module parsed ebur128's per-frame output, that build prints only a
summary, and the parse returned an empty list -- which the callers happily
reported as "0 impacts".  A measurement that cannot fail is not a measurement,
so `envelope` raises when it decodes nothing.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

WINDOW = 0.05
"""Envelope resolution in seconds.  At 24fps one frame is 0.0417s, so this is
about as fine as a cut can be placed anyway."""

RATE = 22050
IMPACT_DB = 6.0
"""A rise this big between adjacent windows reads as a hit, not a swell."""
STOPDOWN_DB = 9.0
"""A fall this big reads as the floor dropping out -- Pryn's stopdown."""


def decode(audio: Path) -> np.ndarray:
    """Mono float samples at RATE, straight from ffmpeg's PCM output."""
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(audio), "-f", "s16le",
         "-acodec", "pcm_s16le", "-ac", "1", "-ar", str(RATE), "-"],
        capture_output=True)
    if not result.stdout:
        raise RuntimeError(f"decoded no audio from {audio}: {result.stderr[-300:]!r}")
    return np.frombuffer(result.stdout, dtype="<i2").astype(np.float32) / 32768.0


def envelope(audio: Path) -> tuple[np.ndarray, np.ndarray]:
    """(times, dBFS) of windowed RMS across the file."""
    samples = decode(audio)
    width = int(RATE * WINDOW)
    count = len(samples) // width
    if count < 2:
        raise RuntimeError(f"{audio} is too short to have an envelope")
    blocks = samples[:count * width].reshape(count, width)
    rms = np.sqrt((blocks ** 2).mean(axis=1))
    return np.arange(count) * WINDOW, 20 * np.log10(np.maximum(rms, 1e-6))


def onsets(times: np.ndarray, db: np.ndarray, min_gap: float = 0.35,
           threshold: float = IMPACT_DB) -> list[float]:
    """Candidate cut points: moments the music pushes, thinned by `min_gap`.

    Thinning matters musically, not just computationally.  Every drum stroke is
    an onset, but cutting on every one produces exactly the metronomic sameness
    Lieu warns is the amateur tell.  This yields a grid to choose FROM.
    """
    rises = np.diff(db)
    grid: list[float] = []
    for index in np.flatnonzero(rises >= threshold):
        when = float(times[index + 1])
        if not grid or when - grid[-1] >= min_gap:
            grid.append(when)
    return grid


def structural_impacts(times: np.ndarray, db: np.ndarray, count: int = 4,
                       min_gap: float = 4.0) -> list[float]:
    """The few biggest hits in the cue -- what a title card is cut to.

    Ranked by how far the music jumps, not by where a section plan said a hit
    would be.  The 5.29s title miss came from trusting the plan.
    """
    rises = np.diff(db)
    ranked = sorted(np.flatnonzero(rises >= IMPACT_DB),
                    key=lambda i: -rises[i])
    chosen: list[float] = []
    for index in ranked:
        when = float(times[index + 1])
        if all(abs(when - other) >= min_gap for other in chosen):
            chosen.append(when)
        if len(chosen) == count:
            break
    return sorted(chosen)


def stopdowns(times: np.ndarray, db: np.ndarray, hold: float = 0.4,
              depth: float = 12.0) -> list[float]:
    """Where the floor drops out and STAYS out -- room for a line over black.

    A stopdown is a duration, not an instant: the distinguishing feature is
    that the quiet is held.  Pryn puts it at one to two bars.
    """
    quiet = db < (float(np.median(db)) - depth)
    needed = max(1, int(hold / WINDOW))
    found: list[float] = []
    run = 0
    for index, is_quiet in enumerate(quiet):
        run = run + 1 if is_quiet else 0
        if run == needed:
            found.append(float(times[index - needed + 1]))
    return found


def title_moment(times: np.ndarray, db: np.ndarray) -> tuple[float, float] | None:
    """(stopdown, impact) for the title card: the late hit and the silence
    that sets it up.

    The corpus puts the loudness peak at 80-90% through and the quietest
    second-half moment at ~92%.  So the title is looked for in the last
    third, and it is only a title moment if a stopdown precedes it -- an
    impact with no silence in front of it has nothing to land against.
    """
    for impact in reversed(structural_impacts(times, db, count=6)):
        if not 0.6 <= impact / float(times[-1]) <= 0.95:
            continue
        before = [s for s in stopdowns(times, db) if impact - 6.0 <= s < impact]
        if before:
            return before[-1], impact
    return None


def trailer_fitness(times: np.ndarray, db: np.ndarray) -> float:
    """How usable a cue is as a trailer bed.  Higher is better.

    Loudness range alone is not enough -- it chose a 90-onset cue over one
    with a clean 20-point grid and a textbook stopdown-into-hit.  What a
    trailer needs is a late hit set up by silence, and a grid an editor can
    actually choose from.
    """
    if title_moment(times, db) is None:
        return 0.0
    grid = len(onsets(times, db))
    spread = float(db.max() - db.min())
    crowding = 1.0 if 8 <= grid <= 40 else 0.4
    return spread * crowding
