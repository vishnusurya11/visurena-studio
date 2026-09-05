"""The frame budget: frames buy picture seconds, picture seconds bound the cue.

The base case of the music-first brick (docs/analysis/research/
trailer-music-first.md, S1 and S3).  Step 07's share of the wall clock is a
number of H3 frames once the cycle -- seconds per take as `a + b * frames` --
is known; a take is its shot plus the head trim the cut skips and the handle
it seeks inside, snapped UP onto H3's legal ladder; so a list of spans has a
frame cost, and a remaining number of seconds has a longest cue it can pay
for.  Nothing else in the pipeline sizes anything.

Every constant nobody has measured is marked FLAG with what measures it.
"""
from __future__ import annotations

import math
from statistics import median

from pydantic import BaseModel, Field

from studio.cue_plan import MIN_FORM_BARS, CuePlan, CueSpan
from studio.h3 import FPS, FRAME_MODULUS, legal_frames
from studio.trailer_assemble import HANDLE, HEAD_TRIM

MAX_FRAMES = 362
"""FLAG: the longest take H3 renders, the top of the ladder f = 5 (mod 17).
Taken from the node's trained range (124-362, the AICU measurement); a
379-frame render attempt on the local node measures it."""

TAKE_TAX = HEAD_TRIM + HANDLE
"""Seconds every take renders that the cut never plays: the reference leak
at the head (2.6 s, measured) and the seek handle at the tail (0.25 s)."""

TAX_FRAMES = math.ceil(TAKE_TAX * FPS)
"""The tax in frames, 69, before legal rounding adds its own 0-16."""

LEGAL_ROUNDING_MEAN = (FRAME_MODULUS - 1) / 2
"""Frames the ladder adds on average, 8: an ask lands anywhere in a rung of
17, so the snap UP costs 0..16 with mean 8.  Derived from the grid."""

LONGEST_SHOT = math.floor((MAX_FRAMES / FPS - TAKE_TAX) * 10) / 10
"""The longest shot a take can hold, 12.2 s: 362 frames less the tax."""

B_TYPED = 2.49
"""FLAG: seconds per frame.  One measurement on this machine -- 09-03, a
175-frame take finishing 7.25 min after the one before it with no read
between, at 8 steps, read off file mtimes (trailer-render-cycle.md).  The
AICU figures for H3 (124 / 243 / 362 frames = 16.4 / 48.1 / 97.2 min at 20
steps) say render time is SUPERLINEAR in frames -- 2.9x the time for 2.0x
the frames -- so one point is not a line; the 124-to-362 chord of that curve
is ~8x steeper than this.  Round 1 of the next run measures one 243-frame
take; `Cycle.from_rows` replaces this the moment two frame counts exist."""

A_TYPED = 0.0
"""FLAG: fixed seconds per take with H3 resident.  Never measured; run 10's
15.76 min per take included a 4.6 min reload per take the round renderer no
longer pays, so its rows are not this number.  Cycle rows with `frames` fit it."""

RETRY_RESERVE = 0.15
"""FLAG: the share of the remaining budget held back for rerolls.  The
reroll count per round, over the first music-first runs, measures it."""

CORPUS_MIX = (8.0,) * 4 + (2.0,) * 10 + (1.0,) * 8
"""FLAG: sixty seconds of picture as the corpus cuts it -- per movement one to
two sustains of 8 s, phrases of 2 s, accents of 1 s; 22 takes.  The spans of
the first music-first master measure the real mix."""


def take_seconds(shot: float) -> float:
    """What a shot of `shot` seconds costs to render: the shot plus the tax."""
    return shot + TAKE_TAX


def take_frames(shot: float) -> int:
    """The legal frame count that COVERS the take, or a refusal when no take can.

    Ceil then snap UP: a take one frame short leaves a hole in the cut."""
    if shot <= 0:
        raise ValueError(f"a shot must have length, got {shot}")
    frames = legal_frames(math.ceil(take_seconds(shot) * FPS))
    if frames > MAX_FRAMES:
        raise ValueError(f"a {shot}s shot needs {frames} frames; H3 renders at most "
                         f"{MAX_FRAMES} ({LONGEST_SHOT}s of shot)")
    return frames


class Cycle(BaseModel):
    """Seconds one take costs as a line in its frames: `a + b * frames`."""

    a: float = Field(ge=0.0)
    b: float = Field(gt=0.0)

    def cost_seconds(self, frames: int, takes: int = 1) -> float:
        """Render seconds for `frames` spread over `takes` takes."""
        return takes * self.a + self.b * frames

    @classmethod
    def from_rows(cls, rows: list) -> "Cycle":
        """The cycle the learnings measured, or the typed one where they did not.

        Two distinct frame counts fit a line; one keeps the typed slope and
        reads the offset off the medians; none is the typed curve."""
        points = cycle_points(rows)
        if len({f for f, _ in points}) >= 2:
            a, b = fit_line(points)
            if a >= 0.0:
                return cls(a=a, b=b)
        if points:
            return typed_slope(points)
        return cls(a=A_TYPED, b=B_TYPED)


TYPED = Cycle(a=A_TYPED, b=B_TYPED)
"""The curve to price on until a round writes a cycle row with `frames`."""


def _field(row, name: str):
    return row.get(name) if isinstance(row, dict) else getattr(row, name, None)


def cycle_points(rows: list) -> list[tuple[int, float]]:
    """(frames per take, seconds per take) from every gate="cycle" row that
    recorded its frames.  A row without `frames` is a point on no line."""
    out = []
    for row in rows:
        frames, seconds = _field(row, "frames"), _field(row, "measured")
        if _field(row, "gate") != "cycle" or frames is None:
            continue
        if isinstance(seconds, (int, float)) and not isinstance(seconds, bool):
            out.append((int(frames), float(seconds)))
    return out


def fit_line(points: list[tuple[int, float]]) -> tuple[float, float]:
    """Least squares `(a, b)` for seconds = a + b * frames."""
    n = len(points)
    mean_f = sum(f for f, _ in points) / n
    mean_s = sum(s for _, s in points) / n
    var = sum((f - mean_f) ** 2 for f, _ in points)
    if var == 0:
        raise ValueError("a line needs two distinct frame counts")
    cov = sum((f - mean_f) * (s - mean_s) for f, s in points)
    b = cov / var
    return mean_s - b * mean_f, b


def typed_slope(points: list[tuple[int, float]]) -> Cycle:
    """The typed slope through the medians: the offset is what one frame
    count can say, and the median so a stalled round cannot resize the plan."""
    frames = median(f for f, _ in points)
    seconds = median(s for _, s in points)
    return Cycle(a=max(0.0, seconds - B_TYPED * frames), b=B_TYPED)


def plan_frames(spans: list[CueSpan]) -> int:
    """Frames a list of spans renders: one take per span."""
    return sum(take_frames(span.seconds) for span in spans)


def affordable_frames(remaining_s: float, cycle: Cycle, takes: int,
                      reserve: float = RETRY_RESERVE) -> int:
    """Frames `takes` takes may total inside `remaining_s`, less the reserve
    and each take's fixed cost.  `remaining_s` is net of the reader session."""
    spendable = remaining_s * (1.0 - reserve) - takes * cycle.a
    return max(0, math.floor(spendable / cycle.b))


def picture_seconds(frames: int, takes: int) -> float:
    """Seconds of picture `frames` hold once every take has paid its tax and
    its expected legal rounding; zero when the tax alone exceeds them."""
    picture = frames - takes * (TAX_FRAMES + LEGAL_ROUNDING_MEAN)
    return max(0.0, picture / FPS)


def cue_seconds_for(remaining_s: float, cycle: Cycle, mix: list[float],
                    reserve: float = RETRY_RESERVE) -> float:
    """Picture seconds the budget affords when shots come in the proportions of
    `mix` (a list of shot seconds): the mix's picture per render second, scaled."""
    if not mix:
        raise ValueError("a mix needs at least one shot")
    frames = sum(take_frames(shot) for shot in mix)
    cost = cycle.cost_seconds(frames, takes=len(mix))
    return sum(mix) * remaining_s * (1.0 - reserve) / cost


def bars_for(seconds: float, bar: float) -> int:
    """Whole bars inside `seconds`, never rounded up, never under the shortest form."""
    bars = math.floor(seconds / bar)
    if bars < MIN_FORM_BARS:
        raise ValueError(f"{seconds:.1f}s is {bars} bars of {bar}s; the shortest form "
                         f"is {MIN_FORM_BARS} bars")
    return bars


def fits(plan: CuePlan, remaining_s: float, cycle: Cycle,
         reserve: float = RETRY_RESERVE) -> bool:
    """Whether the plan's picture spans render inside the budget kept."""
    spans = plan.picture_spans()
    cost = cycle.cost_seconds(plan_frames(spans), takes=len(spans))
    return cost <= remaining_s * (1.0 - reserve)
