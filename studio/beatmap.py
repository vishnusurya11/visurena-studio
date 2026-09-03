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

GRID_DB = 4.0
"""The threshold for the CUT grid, which is a different question.

An impact is a hit you build a title card around; a cut point only has to be a
moment the music moves.  At 6.0 dB the grid held 20 onsets over 100s -- one
every 5s -- so a 2.6s shot looking for its nearest onset had to jump seconds to
find one, and only 6% of the delivered cuts landed on the music at all.  At
4.0 dB the same cue yields 59, one every 1.7s, which is roughly 1.5 candidates
per shot: enough to choose from, not so many that "on the grid" stops meaning
anything."""
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
           threshold: float = GRID_DB) -> list[float]:
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
    """(stopdown, impact) for the title card: the late hit and its silence.

    The corpus puts the loudness peak at 80-90% and the quietest second-half
    moment at ~92%, so the title is looked for in the last third -- and only
    where a stopdown precedes it, because an impact with no silence in front of
    it has nothing to land against.

    The hit must also BE one.  `structural_impacts()` ranks by how far the
    music jumps, which favours a rise out of the intro floor: one shipped cue's
    title landed on its fourth-loudest event, 2.6 dB BELOW its own P95, because
    a big rise from near-silence outranked a real braam.  Requiring the moment
    to reach within 3 dB of P95 asks whether it is loud, not merely sudden.
    """
    ceiling = float(np.percentile(db, 95))
    for impact in reversed(structural_impacts(times, db, count=6)):
        if not 0.6 <= impact / float(times[-1]) <= 0.95:
            continue
        window = int(impact / WINDOW)
        if float(db[window:window + 20].max()) < ceiling - 3.0:
            continue
        before = [s for s in stopdowns(times, db) if impact - 6.0 <= s < impact]
        if before:
            return before[-1], impact
    return None


def dynamic_range(db: np.ndarray) -> float:
    """Loud-to-quiet spread that is not just the peak.

    `db.max() - db.min()` looked like dynamic range and was not.  The digital
    noise floor of every MiniMax cue measures -52.5 to -53.9 dBFS -- a 1.4 dB
    spread across five cues -- so subtracting the minimum subtracts a constant
    and the score reduces to `peak + 53`.  The cue selector was ranking by
    LOUDNESS, which is the wall-of-sound bug it was written to prevent,
    reappearing inside its own fix.

    P95 - P5 ignores both the floor and the single loudest window: measured on
    the same five cues it spans 26.1 to 35.9 dB instead of 43.7 to 48.5, and it
    independently ranks the two cues that were actually shipped first and
    second.
    """
    return float(np.percentile(db, 95) - np.percentile(db, 5))


def trailer_fitness(times: np.ndarray, db: np.ndarray) -> float:
    """How usable a cue is as a trailer bed.  Higher is better.

    A trailer needs a late hit set up by silence, and a grid an editor can
    actually choose from.
    """
    if title_moment(times, db) is None:
        return 0.0
    grid = len(onsets(times, db))
    crowding = 1.0 if 15 <= grid <= 120 else 0.5
    return dynamic_range(db) * crowding
