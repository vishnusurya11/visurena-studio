"""The cut-opportunity map: where the cue CHANGES, measured on its audio.

A cut is a claim that something changed, and the music changes at three
scales.  A section boundary (new material, every 12-25 s) affords a movement;
a phrase start or a level step (every 5-9 s) affords a medium move; a strong
onset affords an insert; and a stretch with none of these affords a HOLD.  So
the rule is: cut on the highest-class event the cue offers, hold between.
Shot length is READ off the distance to the next event, never chosen.

`beatmap` stays the grid + envelope module.  This one adds what metre.json
cannot see: 67 % of section boundaries in the Scarlet cues lie more than a
second from every hit, stopdown, lift or drop, and every cue has 24-77 s of
holdable music the walk could never use because nothing measured it.

Two witnesses, one event.  Novelty says WHICH bar a change lands in (its
peaks sit 0.43-0.83 s from the nearest downbeat, no better than chance) and
the grid says WHERE that bar starts, so every novelty event is snapped to a
downbeat or a strong accent within 0.6 s.  Neither alone is a cut point.

Audio in, JSON out, librosa / scipy / numpy only: nothing here knows about
books or renders.  Numbers cited as MEASURED come from
docs/analysis/research/trailer-music-first.md and the audio-analysis report
behind it (ten cues of A Study in Scarlet).
"""
from __future__ import annotations

from typing import Literal

import numpy as np
import scipy.signal as sps
from pydantic import BaseModel, Field, model_validator

from studio.beatmap import RATE, WINDOW, envelope_of, structural_impacts
from studio.trailer_stage_spec import Metre

HOP = 512
"""librosa's hop at 22.05 kHz: 23.2 ms, the onset-strength frame."""

POOL = 11
FRAME = POOL * HOP / RATE
"""Structure features pool over 11 hops = 0.2554 s.  A 24 s kernel is then
94 frames square and a 145 s cue is 566 novelty windows: cheap, and finer
than the 0.6 s snap reach that decides the final position anyway.  Derived,
never typed as 0.25: the research scripts converted frames at a flat 0.25 s
and every event time drifted 2 % -- 3 s late by the end of a 145 s cue."""

SECTION_KERNEL = (12.0, 24.0)
"""The checkerboard width for sections is clip(seconds / 6, 12, 24) s.
MEASURED: 24 s scores F1 0.87 against 16 s and 0.85 against 32 s, but the
minimum (0.40) was the 102 s cue -- the kernel must scale with the cue."""

SECTION_GAP = 12.0
"""Two sections closer than this are one; a movement is at least this long."""

PHRASE_KERNEL = 8.0
"""MEASURED: phrase novelty at 8 s is F1 0.82 against 6 s and 0.92 against
10 s, and finds the 4-bar periodicity of a cue the beat tracker graded
rubato (gaps 11.0/10.5/11.25/11.25 s on a 2.72 s bar)."""

PHRASE_GAP = 5.0
"""Phrases arrive every 5-9 s; closer peaks are one phrase's two witnesses."""

PROMINENCE = 0.15
"""A novelty peak below this share of the curve's maximum is texture."""

STEP_SPAN = 2.0
STEP_DB = 6.0
"""A lift or drop is the mean of the next 2 s against the previous 2 s.
MEASURED: at 6 dB lifts are F1 0.83 against a 1.5 s span and 0.87 against
3 s; only 24 % coincide with `beatmap.hits`, so they are a different class
(swell against strike)."""

DROPOUT_DB = 12.0
DROPOUT_HOLD = 0.4
"""`beatmap.stopdowns` reshaped as (start, end): 12 dB under the median held
0.4 s.  As starts alone, 122.1 and 122.75 on cue-331107 read as two holes;
as spans they are one."""

SWELL_MIN = 4.0
SWELL_RISE = 6.0
SWELL_SLACK = 3.0
"""A swell climbs >= 6 dB over >= 4 s without falling back more than the
slack.  MEASURED: tremolo strings wobble +-1.5 dB, so at 1.5 dB slack the
17.6 dB crescendo of cue-331107 (75.6-101.3 s) went unfound; 3 dB finds it."""

BEAT_TOL = 0.07
"""Three onset frames: an accent this close to a tracked beat IS that beat."""

ONSET_MADS = 3.0
"""An onset peak counts when it stands this many MADs above the median."""

ACCENT_TOP = 0.10
ACCENT_FLOOR = 8
ACCENT_GAP = 0.25
"""The top tenth of onset peaks, never fewer than eight.  MEASURED: 85 % of
them sit on a beat (chance 19 %); they carry the STRENGTH the grid lacks."""

SNAP_TOL = 0.6
"""How far a novelty event moves to reach a downbeat or accent.  MEASURED:
novelty peaks sit a median 0.43-0.83 s from the nearest downbeat, so a
narrower reach leaves most of them off the grid."""

MERGE_WITHIN = 0.3
"""Detectors fire on the same instant (46.0 entry / 46.25 section; 52.40 hit
/ 52.45 lift): inside this they are one event with two witnesses."""

HOLD_MIN = 3.0
HOLD_STD_DB = 2.0
"""A hold is >= 3 s between rank >= 2 events with the 1 s-smoothed level
inside 2 dB of itself: the picture can carry one take there."""

SWELL_TRIM = 1.0
"""A swell is measured from where it leaves its trough by this much to where
it comes within this much of its peak."""

FLAT_DB = 0.1
"""Two levels inside a tenth of a dB are the same level: a swell's trough
advances along a flat floor instead of freezing on the first sample."""

SMOOTH = 1.0
"""The level is read through a 1 s window for holds, swells and the hard
out; 50 ms windows hear every bow stroke."""

LOUD_PERCENTILE = 70
"""A hard out needs the bar before it at or above this share of the cue."""

TAIL_DEFAULT = 6.0
"""FLAG: when no grid point qualifies, the tail opens this long before the
end (the register table's button runs 5-8 s).  Typed, unmeasured."""

RANK = {"section": 3, "hit": 3, "dropout": 3, "lift": 2, "drop": 2, "phrase": 2, "accent": 1}
"""3 = a new movement may open here; 2 = a medium move; 1 = an insert."""

STRUCTURE = ("section", "dropout", "hit", "lift", "drop", "phrase", "accent")
"""Tie-break between events of one rank: the more structural kind keeps
the merged event, since a hit on a section start IS that section landing."""

FIXED = ("dropout",)
"""Event kinds whose time is a fact of the envelope and is never snapped."""

EventKind = Literal["section", "hit", "dropout", "lift", "drop", "phrase", "accent"]
SpanKind = Literal["hold", "swell", "dropout"]


# --- contract ----------------------------------------------------------------

class CutEvent(BaseModel):
    """One moment the music changes, and the stretch it opens."""

    t: float = Field(ge=0.0)
    rank: Literal[1, 2, 3]
    kind: EventKind
    evidence: list[str] = Field(min_length=1)
    affords: float = Field(default=0.0, ge=0.0)
    level_db: float = 0.0
    onset_density: float = Field(default=0.0, ge=0.0)
    end: float | None = None


class CutSpan(BaseModel):
    """A stretch the picture holds, rides or sits in silence through."""

    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)
    kind: SpanKind
    level_db: float = 0.0
    rises_db: float = 0.0
    onset_density: float = Field(default=0.0, ge=0.0)


class CutMap(BaseModel):
    """The rendered cue as the cut opportunities it offers."""

    events: list[CutEvent]
    spans: list[CutSpan]
    hard_out: float = Field(ge=0.0)
    title_hit: float | None = None
    seconds: float = Field(gt=0.0)

    @model_validator(mode="after")
    def _events_in_order_inside_the_cue(self) -> "CutMap":
        ts = [e.t for e in self.events]
        if ts != sorted(ts):
            raise ValueError("events must be sorted by time")
        if self.hard_out >= self.seconds:
            raise ValueError(f"hard_out {self.hard_out} is past the cue end {self.seconds}")
        return self


# --- features ----------------------------------------------------------------

def coarse(feature: np.ndarray, hop_s: float, frame: float = FRAME) -> np.ndarray:
    """A (d, n) frame-rate feature mean-pooled to `frame` seconds."""
    step = max(1, int(round(frame / hop_s)))
    count = feature.shape[1] // step
    return feature[:, :count * step].reshape(feature.shape[0], count, step).mean(axis=2)


def zscore(feature: np.ndarray) -> np.ndarray:
    """Each dimension centred and scaled, with a floor under dead ones.

    A dimension the cue barely moves (an empty chroma bin on a synthetic
    tone) is numerical dust; scaled to unit variance it would outvote the
    dimensions that carry the change.  The floor is a tenth of the median
    spread, so such a dimension stays small instead."""
    std = feature.std(axis=1, keepdims=True)
    floor = 0.1 * float(np.median(std))
    return (feature - feature.mean(axis=1, keepdims=True)) / np.maximum(std, max(floor, 1e-9))


def structure_features(samples: np.ndarray, rate: int = RATE) -> np.ndarray:
    """MFCC 2-20 over CQT chroma, pooled to FRAME and z-scored: (31, n)."""
    import librosa
    mfcc = librosa.feature.mfcc(y=samples, sr=rate, hop_length=HOP, n_mfcc=20)[1:]
    chroma = librosa.feature.chroma_cqt(y=samples, sr=rate, hop_length=HOP)
    hop_s = HOP / rate
    return zscore(np.vstack([coarse(mfcc, hop_s), coarse(chroma, hop_s)]))


def onset_curve(samples: np.ndarray, rate: int = RATE) -> np.ndarray:
    """librosa onset strength, one value per HOP."""
    import librosa
    return librosa.onset.onset_strength(y=samples, sr=rate, hop_length=HOP)


# --- novelty -----------------------------------------------------------------

def self_similarity(feature: np.ndarray) -> np.ndarray:
    """Cosine similarity of every frame with every other: (n, n)."""
    unit = feature / (np.linalg.norm(feature, axis=0, keepdims=True) + 1e-9)
    return unit.T @ unit


def checkerboard(size: int) -> np.ndarray:
    """Foote's kernel: Hann-weighted quadrants signed +, -, -, +."""
    hann = np.hanning(2 * size)
    kernel = np.outer(hann, hann)
    kernel[:size, size:] *= -1
    kernel[size:, :size] *= -1
    return kernel


def novelty(ssm: np.ndarray, size: int) -> np.ndarray:
    """The checkerboard slid down the diagonal, clipped at 0, scaled to 1.

    Edge padding rather than zeros: a zero pad makes the first frames look
    like a change from silence and puts a false boundary at 0."""
    kernel = checkerboard(size)
    padded = np.pad(ssm, size, mode="edge")
    count = ssm.shape[0]
    out = np.empty(count)
    for i in range(count):
        out[i] = (padded[i:i + 2 * size, i:i + 2 * size] * kernel).sum()
    out = np.maximum(out, 0.0)
    return out / (out.max() + 1e-9)


def boundaries(curve: np.ndarray, frame: float, min_gap: float,
               prominence: float = PROMINENCE) -> list[tuple[float, float]]:
    """Peaks of a novelty curve as (seconds, strength), thinned by `min_gap`."""
    idx, _ = sps.find_peaks(curve, distance=max(1, int(min_gap / frame)), prominence=prominence)
    return [(round(float(i * frame), 3), round(float(curve[i]), 3)) for i in idx]


def section_kernel(seconds: float) -> float:
    """The checkerboard width in seconds for a cue this long."""
    return float(np.clip(seconds / 6.0, *SECTION_KERNEL))


def sections(feature: np.ndarray, seconds: float) -> list[tuple[float, float]]:
    """Section boundaries: novelty at the cue-scaled kernel, >= SECTION_GAP apart."""
    size = int(section_kernel(seconds) / FRAME / 2)
    return boundaries(novelty(self_similarity(feature), size), FRAME, SECTION_GAP)


def phrases(feature: np.ndarray) -> list[tuple[float, float]]:
    """Phrase starts: novelty at PHRASE_KERNEL, >= PHRASE_GAP apart."""
    size = int(PHRASE_KERNEL / FRAME / 2)
    return boundaries(novelty(self_similarity(feature), size), FRAME, PHRASE_GAP)


# --- envelope events ---------------------------------------------------------

def level_steps(db: np.ndarray, span: float = STEP_SPAN,
                step_db: float = STEP_DB) -> tuple[list, list]:
    """(lifts, drops) as (seconds, dB): the next `span` against the previous."""
    width = max(1, int(span / WINDOW))
    total = np.concatenate([[0.0], np.cumsum(db)])
    curve = np.zeros(len(db))
    i = np.arange(width, len(db) - width)
    curve[i] = (total[i + width] - total[i]) / width - (total[i] - total[i - width]) / width
    up, _ = sps.find_peaks(curve, distance=width, height=step_db)
    down, _ = sps.find_peaks(-curve, distance=width, height=step_db)
    return ([(round(float(j * WINDOW), 3), round(float(curve[j]), 1)) for j in up],
            [(round(float(j * WINDOW), 3), round(float(curve[j]), 1)) for j in down])


def dropout_spans(times: np.ndarray, db: np.ndarray, depth: float = DROPOUT_DB,
                  hold: float = DROPOUT_HOLD) -> list[tuple[float, float]]:
    """(start, end) of every run >= `hold` s at `depth` dB under the median."""
    quiet = list(db < float(np.median(db)) - depth) + [False]
    found, start = [], None
    for i, is_quiet in enumerate(quiet):
        if is_quiet and start is None:
            start = i
        elif not is_quiet and start is not None:
            if (i - start) * WINDOW >= hold:
                found.append((round(float(times[start]), 3), round(float(times[start] + (i - start) * WINDOW), 3)))
            start = None
    return found


def smoothed(db: np.ndarray, seconds: float = SMOOTH) -> np.ndarray:
    """The level read through a `seconds` moving average, same length.

    Edge-padded: a zero pad reads the first and last half second as a dip,
    and a swell or hold detector then finds a rise out of nothing."""
    width = max(1, int(seconds / WINDOW))
    padded = np.pad(db, (width // 2, width - 1 - width // 2), mode="edge")
    return np.convolve(padded, np.ones(width) / width, mode="valid")


def trimmed(level: np.ndarray, lo: int, hi: int, margin: float = SWELL_TRIM) -> tuple[int, int]:
    """The climb inside [lo, hi]: from the last point within `margin` of the
    trough to the first point within `margin` of the peak.  A level STEP has
    flat floors either side; trough-to-peak spans them, the climb does not."""
    floor, ceiling = level[lo] + margin, level[hi] - margin
    start = lo + int(np.flatnonzero(level[lo:hi + 1] <= floor)[-1])
    end = start + int(np.flatnonzero(level[start:hi + 1] >= ceiling)[0])
    return start, end


def swells(db: np.ndarray, min_len: float = SWELL_MIN, min_rise: float = SWELL_RISE,
           slack: float = SWELL_SLACK) -> list[tuple[float, float, float]]:
    """(start, end, rise_db) of every climb >= `min_rise` over >= `min_len` s.

    A fall-back of more than `slack` closes a climb, a new low restarts it;
    the climb is then trimmed to where the level actually moves."""
    level = smoothed(db)
    found, start, peak = [], 0, 0
    for i in range(1, len(level) + 1):
        closing = i == len(level) or level[peak] - level[i] > slack
        if closing and level[peak] - level[start] >= min_rise:
            a, b = trimmed(level, start, peak)
            if (b - a) * WINDOW >= min_len:
                found.append((round(a * WINDOW, 3), round(b * WINDOW, 3),
                              round(float(level[peak] - level[start]), 1)))
        if i == len(level):
            break
        if closing or level[i] <= level[start] + FLAT_DB:
            start = peak = i
        elif level[i] >= level[peak]:
            peak = i
    return found


def onset_peaks(strength: np.ndarray, hop_s: float,
                min_gap: float = ACCENT_GAP) -> list[tuple[float, float]]:
    """Every onset peak that stands out of the curve, `min_gap` apart.

    The floor is median + 3 MAD, the robust outlier line: on a click track
    95 % of frames are noise, so the median IS the noise and a floor at the
    median let 42 noise peaks through beside 59 clicks."""
    median = float(np.median(strength))
    spread = 1.4826 * float(np.median(np.abs(strength - median)))
    idx, props = sps.find_peaks(strength, distance=max(1, int(min_gap / hop_s)),
                                height=median + ONSET_MADS * spread)
    return [(round(float(i * hop_s), 3), round(float(h), 3))
            for i, h in zip(idx, props["peak_heights"])]


def accents(strength: np.ndarray, hop_s: float, top: float = ACCENT_TOP) -> list[tuple[float, float]]:
    """The strongest `top` share of onset peaks (>= ACCENT_FLOOR), in time order."""
    peaks = onset_peaks(strength, hop_s)
    keep = max(ACCENT_FLOOR, int(len(peaks) * top))
    return sorted(sorted(peaks, key=lambda p: -p[1])[:keep])


def beat_accents(found: list[tuple[float, float]], beats: list[float],
                 tol: float = BEAT_TOL) -> list[tuple[float, float]]:
    """Accents moved onto the tracked beat when one is within `tol`.

    MEASURED: librosa's onset frame lands 28-34 ms after a click (its lag
    padding assumes the onset is heard at the window's leading edge); the
    tracker's beat is the truer time, and an accent that is the grid must
    not sit 30 ms beside the downbeat it is."""
    if not beats:
        return found
    out = []
    for t, s in found:
        beat = min(beats, key=lambda b: abs(b - t))
        out.append((beat if abs(beat - t) <= tol else t, s))
    return out


# --- housekeeping ------------------------------------------------------------

def snap(events: list[dict], grid: list[float], tol: float = SNAP_TOL) -> list[dict]:
    """Each event moved to its nearest grid point within `tol`, evidence noted.

    Novelty says which bar; the grid says where it starts.  A dropout's
    start is the envelope's own fact and stays."""
    out = []
    for event in events:
        event = dict(event, evidence=list(event["evidence"]))
        if grid and event["kind"] not in FIXED:
            nearest = min(grid, key=lambda g: abs(g - event["t"]))
            if abs(nearest - event["t"]) <= tol and nearest != event["t"]:
                event["evidence"].append(f"snap:{nearest - event['t']:+.2f}")
                event["t"] = round(nearest, 3)
        out.append(event)
    return out


def weight(event: dict) -> tuple[int, int, float]:
    """Sort key: rank first, then how structural the kind is, then earliness."""
    return event["rank"], -STRUCTURE.index(event["kind"]), -event["t"]


def merge(events: list[dict], within: float = MERGE_WITHIN) -> list[dict]:
    """Events inside `within` of each other folded into the highest rank.

    The kept event keeps its own time; the folded ones become its evidence.
    Equal ranks: the more structural kind (STRUCTURE order), then the earlier."""
    out: list[dict] = []
    for event in sorted(events, key=lambda e: e["t"]):
        event = dict(event, evidence=list(event["evidence"]))
        if out and event["t"] - out[-1]["t"] <= within:
            keep, fold = sorted((out[-1], event), key=weight)[::-1]
            keep["evidence"] = keep["evidence"] + [w for w in fold["evidence"] if w not in keep["evidence"]]
            out[-1] = keep
        else:
            out.append(event)
    return out


def with_known(events: list[dict], known: list[dict], within: float = MERGE_WITHIN) -> list[dict]:
    """The arc's own events laid over the detectors': a known event keeps its
    time and kind, and a detector event inside `within` becomes its witness.

    MEASURED (run 14, cutmap-1001): the arc's stop at 76.399 s merged under
    a detected 'section' (equal rank, more structural), the bar-10 impact
    was no detected hit at all -- delivered 0.62 for events the arc cut."""
    out = [dict(k, evidence=list(k["evidence"])) for k in known]
    for event in events:
        near = [k for k in out if abs(k["t"] - event["t"]) <= within]
        if near:
            near[0]["evidence"] += [w for w in event["evidence"] if w not in near[0]["evidence"]]
        else:
            out.append(event)
    return sorted(out, key=lambda e: e["t"])


def known_hard_out(known: list[dict]) -> float | None:
    """The arc's stop, when it wrote one: the hard out is where the cut stops."""
    stops = [k["t"] for k in known if "arc:stop" in k["evidence"]]
    return stops[0] if stops else None


def affordances(events: list[dict], seconds: float) -> list[dict]:
    """Each event given `affords`: seconds to the next of rank >= its own."""
    out = []
    for i, event in enumerate(events):
        later = [f["t"] for f in events[i + 1:] if f["rank"] >= event["rank"] and f["t"] > event["t"]]
        out.append(dict(event, affords=round((later[0] if later else seconds) - event["t"], 3)))
    return out


def span_stats(start: float, end: float, times: np.ndarray, db: np.ndarray,
               onset_times: list[float]) -> dict:
    """Level, rise and onset density of one stretch of the cue."""
    lo, hi = int(start / WINDOW), max(int(start / WINDOW) + 1, int(end / WINDOW))
    level = smoothed(db)[lo:hi]
    inside = sum(1 for t in onset_times if start <= t < end)
    return dict(level_db=round(float(np.median(level)), 1),
                rises_db=round(float(level.max() - level.min()), 1),
                onset_density=round(inside / max(end - start, 1e-6), 3))


def hold_spans(events: list[dict], times: np.ndarray, db: np.ndarray, seconds: float,
               min_len: float = HOLD_MIN, std_db: float = HOLD_STD_DB) -> list[tuple[float, float]]:
    """Gaps >= `min_len` between rank >= 2 events where the level holds still."""
    cuts = sorted({0.0, seconds} | {e["t"] for e in events if e["rank"] >= 2})
    level = smoothed(db)
    found = []
    for a, b in zip(cuts, cuts[1:]):
        segment = level[int(a / WINDOW):int(b / WINDOW)]
        if b - a >= min_len and len(segment) and float(segment.std()) <= std_db:
            found.append((a, b))
    return found


def hard_outs(grid: list[float], times: np.ndarray, db: np.ndarray, strength: np.ndarray,
              hop_s: float, top: int = 5) -> list[tuple[float, float]]:
    """Grid points with a loud 2 s behind them and an accent on them, best first.

    Score = onset strength x (level + 60): loud AND struck.  MEASURED on
    cue-331107 the runner-up (126.2 s) was the one that mattered -- the
    winner sat after the title hit -- so `hard_out_of` chooses, this ranks."""
    loud = float(np.percentile(db, LOUD_PERCENTILE))
    found = []
    for g in grid:
        lo = max(0, int((g - 2.0) / WINDOW))
        before = float(np.median(db[lo:max(lo + 1, int(g / WINDOW))]))
        j = min(int(g / hop_s), len(strength) - 1)
        struck = float(strength[max(0, j - 2):j + 3].max()) if len(strength) else 0.0
        if before >= loud and struck > 0:
            found.append((float(g), round(struck * (before + 60.0), 3)))
    return sorted(found, key=lambda x: -x[1])[:top]


def hard_out_of(candidates: list[tuple[float, float]], title_hit: float | None,
                seconds: float, grid: list[float]) -> float:
    """The hard out: the best late candidate before the title hit, else the
    grid point nearest TAIL_DEFAULT before the end."""
    late = [(t, s) for t, s in candidates if t >= 0.6 * seconds]
    if title_hit is not None:
        late = [(t, s) for t, s in late if t < title_hit]
    if late:
        return max(late, key=lambda x: x[1])[0]
    fallback = seconds - TAIL_DEFAULT
    inside = [g for g in grid if 0.0 < g < seconds]
    return round(min(inside, key=lambda g: abs(g - fallback)) if inside else fallback, 3)


# --- the map -----------------------------------------------------------------

def event(t: float, kind: str, witness: str, **extra) -> dict:
    return dict(t=round(float(t), 3), rank=RANK[kind], kind=kind, evidence=[witness], **extra)


def raw_events(feature: np.ndarray, times: np.ndarray, db: np.ndarray, strength: np.ndarray,
               seconds: float, hop_s: float, beats: list[float] = ()) -> list[dict]:
    """Every detector's events, unsnapped and unmerged."""
    found = [event(t, "section", f"novelty{section_kernel(seconds):.0f}:{s}") for t, s in sections(feature, seconds)]
    found += [event(t, "phrase", f"novelty{PHRASE_KERNEL:.0f}:{s}") for t, s in phrases(feature)]
    found += [event(t, "hit", "rms_rise>=6dB") for t in structural_impacts(times, db)]
    found += [event(a, "dropout", f"rms<median-{DROPOUT_DB:.0f}dB", end=b) for a, b in dropout_spans(times, db)]
    lifts, drops = level_steps(db)
    found += [event(t, "lift", f"step:{s:+.1f}dB") for t, s in lifts]
    found += [event(t, "drop", f"step:{s:+.1f}dB") for t, s in drops]
    found += [event(t, "accent", f"onset:{s}") for t, s in beat_accents(accents(strength, hop_s), beats)]
    return sorted(found, key=lambda e: (e["t"], -e["rank"]))


def grid_of(metre: Metre, accent_times: list[float]) -> list[float]:
    """What events snap to: the downbeats and the strongest accents.

    A downbeat alone leaves most phrases unsnapped (half a 2.72 s bar is
    past the 0.6 s reach); accents are on the beat 85 % of the time and are
    the grid a rubato cue has."""
    return sorted(set(metre.downbeats) | set(accent_times))


def cue_spans(events: list[dict], times: np.ndarray, db: np.ndarray, seconds: float,
              onset_times: list[float]) -> list[dict]:
    """Hold, swell and dropout spans, each with its level statistics."""
    found = [(a, b, "hold", {}) for a, b in hold_spans(events, times, db, seconds)]
    found += [(a, b, "swell", {}) for a, b, _ in swells(db)]
    found += [(a, b, "dropout", {}) for a, b in dropout_spans(times, db)]
    out = []
    for a, b, kind, _ in sorted(found):
        out.append(dict(start=a, end=b, kind=kind, **span_stats(a, b, times, db, onset_times)))
    return out


def cut_map(samples: np.ndarray, rate: int, metre: Metre, known: list[dict] | None = None) -> dict:
    """The CutMap of one rendered cue, as a JSON-able dict; `known` are the
    events an arc wrote beside its bar lines, laid over the detectors'."""
    if rate != RATE:
        import librosa
        samples, rate = librosa.resample(samples, orig_sr=rate, target_sr=RATE), RATE
    hop_s = HOP / rate
    seconds = round(len(samples) / rate, 3)
    times, db = envelope_of(samples)
    strength = onset_curve(samples, rate)
    onset_times = [t for t, _ in onset_peaks(strength, hop_s)]
    raw = raw_events(structure_features(samples, rate), times, db, strength, seconds, hop_s, metre.beats)
    grid = grid_of(metre, [e["t"] for e in raw if e["kind"] == "accent"])
    events = affordances(with_known(merge(snap(raw, grid)), known or []), seconds)
    for e in events:
        e.update(span_stats(e["t"], e["t"] + e["affords"], times, db, onset_times))
    hard = known_hard_out(known or [])
    if hard is None:
        hard = hard_out_of(hard_outs(grid, times, db, strength, hop_s), metre.title_hit, seconds, grid)
    return CutMap(events=events, spans=cue_spans(events, times, db, seconds, onset_times),
                  hard_out=hard, title_hit=metre.title_hit, seconds=seconds).model_dump()
