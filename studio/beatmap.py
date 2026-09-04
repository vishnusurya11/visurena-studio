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
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from studio.trailer_stage_spec import Metre, Slot

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
    return envelope_of(decode(audio))


def envelope_of(samples: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(times, dBFS) of windowed RMS across decoded samples."""
    width = int(RATE * WINDOW)
    count = len(samples) // width
    if count < 2:
        raise RuntimeError("too few samples to have an envelope")
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


def late_density(grid: list[float], seconds: float,
                 low: float = 0.80, high: float = 0.95) -> int:
    """Onsets in the window where the arc cuts fastest.

    The corpus arc reaches its shortest shots at 85-90%, and `cut_points` can
    only land on onsets the cue actually contains.  A cue that empties out
    there cannot be cut to the arc no matter how good its numbers are
    elsewhere, and the picture silently loses.
    """
    return sum(1 for onset in grid if low * seconds <= onset <= high * seconds)


def trailer_fitness(times, db, grid: list[float] | None = None,
                    metre: "Grid | Metre | None" = None,
                    threat_seconds: float = 0.0) -> float:
    """How cuttable this cue is.

    `dynamic_range * crowding` scored the whole piece and never asked WHERE
    the events were, so a cue with a hole exactly where the trailer needs its
    fastest cutting scored as well as one without.  The late-density term is
    the missing half: it is the difference between a cue you can cut to and a
    cue you have to fight.

    With a measured `metre` the structural terms multiply in: a rubato seed,
    a tempo outside the 80-140 band, a pre-title trough too short for the
    threat line, no lift into the hit, and too few slots each cost a factor.
    Without one the score is the shipped envelope-only formula.
    """
    events = len(grid) if grid is not None else 0
    crowding = 1.0 if grid is None or 15 <= events <= 120 else 0.5
    late = late_density(grid or [], float(times[-1]))
    reach = min(late, 4) / 4.0 if grid is not None else 1.0
    base = dynamic_range(db) * crowding * (0.4 + 0.6 * reach)
    if metre is None:
        return base
    return base * structure_terms(times, db, metre, threat_seconds)


def structure_terms(times, db, metre: "Grid | Metre", threat_seconds: float = 0.0) -> float:
    """The product of the metre-aware fitness terms (03-music SKILL)."""
    return (metric_term(metre.bars_in_mode) * tempo_term(metre.bpm)
            * title_term(times, db, metre, threat_seconds) * lift_term(times, db, metre)
            * slot_term(len(slots(times, db, metre))))


def metric_term(bars_in_mode: float) -> float:
    """A rubato seed is cut on onsets, so it is worth less than a metric one."""
    if bars_in_mode >= 0.85:
        return 1.0
    return 0.7 if bars_in_mode >= Metre.METRIC_FLOOR else 0.4


def tempo_term(bpm: float, band: tuple[float, float] = (80.0, 140.0)) -> float:
    """80-140 BPM is where whole-beat shots land inside 0.4 s and the cap."""
    if band[0] <= bpm <= band[1]:
        return 1.0
    return 0.8 if band[0] - 20 <= bpm <= band[1] + 20 else 0.5


def beat_length(metre: "Grid | Metre") -> float:
    return metre.bar / max(metre.beats_per_bar, 1)


def title_term(times, db, metre: "Grid | Metre", threat_seconds: float = 0.0) -> float:
    """The pre-title trough must hold the threat line plus two beats."""
    moment = title_moment(times, db)
    if moment is None:
        return 0.3
    stop, hit = moment
    needed = max(metre.bar, threat_seconds + 2 * beat_length(metre))
    return 1.0 if hit - stop >= needed else 0.3


def lift_term(times, db, metre: "Grid | Metre") -> float:
    """A hit that rises >= 6 dB over the two bars before it reads as a lift."""
    moment = title_moment(times, db)
    if moment is None:
        return 0.7
    per_bar = max(1, int(metre.bar / WINDOW))
    at = min(int(moment[1] / WINDOW), len(db) - 1)
    before = db[max(0, at - 2 * per_bar):max(1, at - per_bar)]
    peak = float(np.percentile(db[at:at + per_bar], 95))
    return 1.0 if peak - float(np.median(before)) >= 6.0 else 0.7


def slot_term(count: int) -> float:
    """Two slots beat one: a hook AND a threat each get a trough of their own."""
    return 1.0 if count >= 2 else (0.7 if count == 1 else 0.4)


SLOT_DB = 6.0
"""A trough this far under the cue's median is where a spoken line lives."""


def slots(times, db, metre: "Grid | Metre", depth: float = SLOT_DB,
          band: tuple[float, float] = (0.2, 0.8)) -> list[Slot]:
    """Troughs >= `depth` dB under the median held >= 1 bar, starting in `band`."""
    quiet = list(db < (float(np.median(db)) - depth)) + [False]
    needed = int(np.ceil(metre.bar / WINDOW)) + 1
    total = float(times[-1])
    found: list[Slot] = []
    start = None
    for index, is_quiet in enumerate(quiet):
        if is_quiet and start is None:
            start = index
        elif not is_quiet and start is not None:
            begins = float(times[start])
            if index - start >= needed and band[0] * total <= begins <= band[1] * total:
                found.append(Slot(start=begins, end=round(begins + (index - start) * WINDOW, 3)))
            start = None
    return found


# --- metre: the grid MEASURED from the audio -------------------------------

HOP = 0.01
"""Onset-strength resolution.  Ten ms puts a 60 ms beat tolerance at six
frames either side, fine enough that the tracker, not the grid, sets the
error."""
TEMPO_BAND = (50.0, 220.0)
MIN_TRACKED = 8
"""Fewer beats than this from the model means it found nothing to hold on
to (a bare click at 60 BPM returned zero), and the autocorrelation tracker
takes over rather than shipping an empty grid."""


def onset_strength(samples: np.ndarray, rate: int = RATE, hop: float = HOP) -> np.ndarray:
    """Positive spectral flux per `hop`: how much NEW energy each frame brings.

    Smoothed over three frames so a period that is not a whole number of
    frames (180 BPM is 33.3) still autocorrelates at its own lag instead of
    only at a multiple that happens to be whole.
    """
    width = int(rate * hop)
    count = len(samples) // width
    if count < 4:
        raise RuntimeError("too short to track a pulse")
    blocks = samples[:count * width].reshape(count, width) * np.hanning(width)
    spectrum = np.log1p(1000.0 * np.abs(np.fft.rfft(blocks, axis=1)))
    flux = np.maximum(np.diff(spectrum, axis=0, prepend=spectrum[:1]), 0.0).sum(axis=1)
    return np.convolve(flux, [0.5, 1.0, 0.5], mode="same")


def autocorrelation(strength: np.ndarray) -> np.ndarray:
    """Normalised autocorrelation of the onset strength via FFT."""
    x = strength - strength.mean()
    size = 1 << (2 * len(x) - 1).bit_length()
    spectrum = np.fft.rfft(x, size)
    ac = np.fft.irfft(spectrum * np.conj(spectrum), size)[:len(x)]
    return ac / max(float(ac[0]), 1e-9)


def beat_period(strength: np.ndarray, hop: float = HOP,
                band: tuple[float, float] = TEMPO_BAND) -> float:
    """The beat period in seconds: the autocorrelation peak in `band`.

    A log-Gaussian weight around 120 BPM breaks octave ties the way a
    listener does; then the half period wins if the beats BETWEEN carry
    onsets too -- a 180 BPM click autocorrelates at 90 as strongly as at
    180, and the faster level is the one that is actually there.
    """
    ac = autocorrelation(strength)
    low, high = int(round(60 / band[1] / hop)), int(round(60 / band[0] / hop))
    lags = np.arange(low, min(high, len(ac) - 1) + 1)
    weight = np.exp(-0.5 * np.log2(60 / (lags * hop) / 120.0) ** 2)
    lag = float(lags[np.argmax(ac[lags] * weight)])
    if lag / 2 >= low and between_beats(strength, lag / 2 * hop, hop) >= 0.85:
        lag = lag / 2
    return lag * hop


def between_beats(strength: np.ndarray, period: float, hop: float = HOP) -> float:
    """How strong the odd beats of a comb at `period` are against the even.

    Near 1.0 the in-between beats are as real as the on-beats and `period`
    is the pulse; well under it they are the gaps of a pulse twice as long.
    """
    beats = track_comb(strength, period, hop)
    level = np.array([strength[min(int(round(b / hop)), len(strength) - 1)] for b in beats])
    even, odd = float(np.median(level[0::2])), float(np.median(level[1::2]))
    return min(even, odd) / max(even, odd, 1e-9)


def comb_phase(strength: np.ndarray, lag: int) -> int:
    """The offset whose comb collects the most onset strength."""
    return int(np.argmax([strength[k::lag].sum() for k in range(lag)]))


def track_comb(strength: np.ndarray, period: float, hop: float = HOP,
               tolerance: float = 0.15) -> list[float]:
    """Walk the pulse, snapping each beat to the strongest onset within reach."""
    lag = period / hop
    reach = max(1, int(tolerance * lag))
    at = float(comb_phase(strength, int(round(lag))))
    beats: list[float] = []
    while at < len(strength):
        low = max(0, int(round(at)) - reach)
        high = min(len(strength), int(round(at)) + reach + 1)
        index = low + int(np.argmax(strength[low:high]))
        beats.append(round(index * hop, 3))
        at = index + lag
    return beats


def confirmed(beats: list[float], strength: np.ndarray, hop: float = HOP,
              floor: float = 0.2) -> list[float]:
    """The comb's beats that sit on something: silence at either end is dropped.

    The comb keeps walking through a silent intro or tail and every step it
    takes there is a fiction.  This is a floor, not a rubato detector -- a
    log-compressed spectrum puts broadband noise within a factor of two of a
    click, so the numpy tracker reads most audio as metric; the model-backed
    tracker is what measures `bars_in_mode` on a real cue.
    """
    level = [float(strength[min(int(round(b / hop)), len(strength) - 1)]) for b in beats]
    return [b for b, v in zip(beats, level) if v >= floor * float(np.median(level))]


def downbeats_of(beats: list[float], strength: np.ndarray,
                 hop: float = HOP) -> tuple[list[float], int]:
    """The accent phase over 4 then 3 beats per bar; 3 must clearly win."""
    level = np.array([strength[min(int(round(b / hop)), len(strength) - 1)] for b in beats])
    mean = max(float(level.mean()), 1e-9)
    best: dict[int, tuple[float, int]] = {}
    for per_bar in (4, 3):
        ratios = [(float(level[k::per_bar].mean()) / mean, k) for k in range(per_bar)]
        best[per_bar] = max(ratios)
    per_bar = 3 if best[3][0] > 1.1 * best[4][0] else 4
    return beats[best[per_bar][1]::per_bar], per_bar


def track_autocorrelation(samples: np.ndarray, rate: int = RATE) -> tuple[list[float], list[float]]:
    """The numpy tracker: onset flux -> autocorrelation period -> comb walk."""
    strength = onset_strength(samples, rate)
    beats = confirmed(track_comb(strength, beat_period(strength)), strength)
    downbeats, _ = downbeats_of(beats, strength)
    return beats, downbeats


_BEAT_THIS = None


def track_beat_this(samples: np.ndarray, rate: int = RATE) -> tuple[list[float], list[float]]:
    """Beat This! (CPJKU, MIT): joint beat + downbeat, ~4 s per cue on CPU.

    The checkpoint is cached under torch hub after the first download; the
    `music` dependency group installs the model.
    """
    global _BEAT_THIS
    from beat_this.inference import Audio2Beats
    if _BEAT_THIS is None:
        _BEAT_THIS = Audio2Beats(checkpoint_path="final0", device="cpu", dbn=False)
    beats, downbeats = _BEAT_THIS(samples, rate)
    return ([round(float(b), 3) for b in beats], [round(float(d), 3) for d in downbeats])


def track_beats(samples: np.ndarray, rate: int = RATE) -> tuple[list[float], list[float]]:
    """The model when the `music` group is installed, else the numpy tracker."""
    try:
        import beat_this  # noqa: F401
    except ImportError:
        return track_autocorrelation(samples, rate)
    return track_beat_this(samples, rate)


def tempo_of(beats: list[float]) -> float:
    """BPM from the SPAN, first to last beat over the count.

    The median inter-beat interval on a 20 ms tracker grid quantises to
    3000/n and carries octave doubles; the span averages the jitter out.
    """
    if len(beats) < 2:
        return 0.0
    return 60.0 * (len(beats) - 1) / (beats[-1] - beats[0])


def bars_in_mode(downbeats: list[float], tolerance: float = 0.05) -> float:
    """The fraction of bars within `tolerance` of the modal bar length."""
    bars = np.diff(downbeats)
    if len(bars) < 2:
        return 0.0
    counts = [int(np.sum(np.abs(bars - bar) <= tolerance * bar)) for bar in bars]
    return max(counts) / len(bars)


def phrases(downbeats: list[float]) -> list[float]:
    """Every fourth downbeat: where a four-bar phrase begins."""
    return list(downbeats[::4])


def beats_per_bar(beats: list[float], downbeats: list[float]) -> int:
    """The modal count of beats between consecutive downbeats; 4 if unknown."""
    if len(downbeats) < 2:
        return 4
    counts = [sum(1 for b in beats if a <= b < z) for a, z in zip(downbeats, downbeats[1:])]
    return max(set(counts), key=counts.count) or 4


def snap_to(beats: list[float], downbeats: list[float]) -> list[float]:
    """Each downbeat replaced by its nearest beat so the grid stays one set."""
    if not beats:
        return []
    return sorted({min(beats, key=lambda b: abs(b - d)) for d in downbeats})


@dataclass(frozen=True)
class Grid:
    """What a tracker measured, before the cue's envelope is read against it."""

    beats: list[float]
    downbeats: list[float]
    bpm: float
    bar: float
    beats_per_bar: int
    bars_in_mode: float

    @classmethod
    def of(cls, beats: list[float], downbeats: list[float]) -> "Grid":
        downbeats = snap_to(beats, downbeats)
        per_bar = beats_per_bar(beats, downbeats)
        bpm = tempo_of(beats)
        if len(downbeats) > 1:
            bar = float(np.median(np.diff(downbeats)))
        else:
            bar = per_bar * 60.0 / bpm if bpm else 0.0
        return cls(beats, downbeats, bpm, bar, per_bar, bars_in_mode(downbeats))


Tracker = Callable[[np.ndarray, int], tuple[list[float], list[float]]]


def metre(audio: Path, seed: int = 0, rel_path: str = "", track: Tracker | None = None) -> Metre:
    """Measure one rendered seed: its grid, events, slots and fitness."""
    samples = decode(audio)
    beats, downbeats = (track or track_beats)(samples, RATE)
    if len(beats) < MIN_TRACKED or len(downbeats) < 2:
        beats, downbeats = track_autocorrelation(samples, RATE)
    grid = Grid.of(beats, downbeats)
    if grid.bpm <= 0 or grid.bar <= 0:
        raise RuntimeError(f"no pulse found in {audio.name}")
    times, db = envelope_of(samples)
    return metre_of(grid, times, db, seed, rel_path or audio.name)


def metre_of(grid: Grid, times, db, seed: int, rel_path: str) -> Metre:
    """The Metre contract from a tracked grid and the cue's envelope."""
    metric = grid.bars_in_mode >= Metre.METRIC_FLOOR
    moment = title_moment(times, db)
    grid_onsets = onsets(times, db)
    return Metre(
        seed=seed, rel_path=rel_path, seconds=round(float(times[-1]) + WINDOW, 3),
        bpm=round(grid.bpm, 2), bar=round(grid.bar, 4), beats_per_bar=grid.beats_per_bar,
        beats=grid.beats if metric else grid_onsets, downbeats=grid.downbeats if metric else [],
        bars_in_mode=round(grid.bars_in_mode, 4), grid="metre" if metric else "onsets",
        fitness=round(trailer_fitness(times, db, grid_onsets, metre=grid), 3),
        hits=structural_impacts(times, db), stopdowns=stopdowns(times, db),
        phrase_starts=phrases(grid.downbeats) if metric else [],
        title_hit=moment[1] if moment else None, slots=slots(times, db, grid))
