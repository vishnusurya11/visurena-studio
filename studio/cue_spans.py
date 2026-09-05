"""From the cut map to the cue plan: the music's spans become the shot list.

`music_events` measures WHERE the cue changes; this module decides what the
picture does between two changes.  One rule generates the plan (design
§1, docs/analysis/research/trailer-music-first.md): a cut lands where the
music has an event of rank >= 2 and nowhere else.  A hold between two cuts
is then classed by what opens it and how long it runs, and the fit rule
shortens the PLAN to the frames the budget affords by removing the cuts
that carry the least -- never a section bound, a sustain or a trough --
and, when that is not enough, asks for a shorter cue rather than a worse one.
"""
from __future__ import annotations

import math
from statistics import fmean, median

from studio import frame_budget
from studio.cue_plan import ACCENT_BEATS, SUSTAIN_BARS, CuePlan, CueSection, CueSpan, SpanKind
from studio.music_events import CutEvent, CutMap
from studio.trailer_edit import MIN_SHOT
from studio.trailer_spec import Movement
from studio.trailer_stage_spec import Metre
from studio.trailer_story import MOVEMENTS, movement_quota

PULSE_DENSITY = 0.6
"""FLAG: onsets per second at or above which a section is pulsed.  Typed:
the research cue's pulsed sections measured 1.5-3.5 onsets/s and its drones
under 0.3/s (cut_map_331107.json), so any value between separates them;
no listener has confirmed where the pulse is first HEARD."""

OPENS_TOL = 0.05
"""A span starting within this of a beat opens ON it: one frame at 24 fps
plus the grid's own rounding."""

MERGEABLE = ("phrase", "section")
"""Span kinds a following phrase may be folded into.  A sustain's length IS
its claim and a trough's is the line it holds room for; those never grow by
merging.  An accent is removed, never grown."""

LONGEST_HOLD = frame_budget.LONGEST_SHOT
"""A hold no take can render is cut where the grid says: one generation per
span, never two stitched (design section 5), so the span must fit a take."""

FIXED_KINDS = ("section", "sustain", "trough", "tail")
"""Spans the fit rule never removes: the section bound is the movement's
door, the sustain and trough are what the cue was asked to have."""


class ShorterCue(Exception):
    """No cut can be removed and the plan is still over budget: step 03 must
    ask for a cue `bars_needed` bars shorter."""

    def __init__(self, bars_needed: int):
        super().__init__(f"ask for a cue {bars_needed} bars shorter")
        self.bars_needed = bars_needed


# --- cuts --------------------------------------------------------------------

def cut_times(cut_map: CutMap, metre: Metre) -> list[float]:
    """0, every rank >= 2 event before the hard out, and the hard out.

    Two cuts inside MIN_SHOT would be a flash frame: the higher rank stays
    (a section outranks a hit at the same rank), the hard out always stays."""
    end = cut_map.hard_out
    kept: list[tuple[float, float]] = [(0.0, math.inf)]
    for e in cut_map.events:
        if e.rank < 2 or e.t <= 0.0 or e.t > end - MIN_SHOT:
            continue
        rank = e.rank + (0.5 if e.kind == "section" else 0.0)
        if e.t - kept[-1][0] < MIN_SHOT:
            if rank > kept[-1][1]:
                kept[-1] = (e.t, rank)
        else:
            kept.append((e.t, rank))
    return within_a_take([t for t, _ in kept] + [end], cut_map, metre)


def split_point(start: float, end: float, cut_map: CutMap, metre: Metre) -> float:
    """Where a hold too long for one take is cut: the rank-1 event nearest
    its middle, else the downbeat, else the beat, a shot clear of both ends."""
    mid = (start + end) / 2.0
    pools = ([e.t for e in cut_map.events if e.rank == 1], metre.downbeats, metre.beats)
    for pool in pools:
        inside = [t for t in pool if start + MIN_SHOT <= t <= end - MIN_SHOT]
        if inside:
            return min(inside, key=lambda t: abs(t - mid))
    return round(mid, 3)


def within_a_take(cuts: list[float], cut_map: CutMap, metre: Metre) -> list[float]:
    """The cuts with every hold over LONGEST_HOLD split until none is."""
    out, i = list(cuts), 0
    while i < len(out) - 1:
        if out[i + 1] - out[i] > LONGEST_HOLD:
            out.insert(i + 1, split_point(out[i], out[i + 1], cut_map, metre))
        else:
            i += 1
    return out


def opening_event(cut_map: CutMap, t: float) -> CutEvent | None:
    """The highest-ranked event at `t`, if the cue has one there."""
    here = [e for e in cut_map.events if abs(e.t - t) <= 1e-6]
    return max(here, key=lambda e: e.rank) if here else None


def bars_of(start: float, end: float, bar: float) -> float:
    """Length in bars, unrounded so the class tests and the CueSpan
    validators see the same number."""
    return (end - start) / bar


def kind_of(start: float, end: float, cut_map: CutMap, metre: Metre) -> SpanKind:
    """The class a hold takes from what opens it and how long it runs.

    Order: tail > trough > section > accent > sustain > phrase.  A section
    event's span is a section however short, so the fit rule can never
    absorb a movement's opening shot into the one before it."""
    opener = opening_event(cut_map, start)
    kind = opener.kind if opener else ""
    bars = bars_of(start, end, metre.bar)
    if start == cut_map.hard_out:
        return "tail"
    if kind == "dropout" and (cut_map.title_hit is None or start < cut_map.title_hit):
        return "trough"
    if kind == "section":
        return "section"
    if bars * 4.0 <= ACCENT_BEATS:
        return "accent"
    return "sustain" if bars >= SUSTAIN_BARS else "phrase"


def untwinned(kinds: list[SpanKind], bounds: list[float]) -> list[SpanKind]:
    """Of two sustains side by side the shorter reads as a phrase: a long
    shot reads long only against a short one (the CuePlan rule)."""
    out = list(kinds)
    for i in range(1, len(out)):
        if out[i] == out[i - 1] == "sustain":
            before, here = bounds[i] - bounds[i - 1], bounds[i + 1] - bounds[i]
            out[i - 1 if before < here else i] = "phrase"
    return out


# --- span fields -------------------------------------------------------------

def opens_on(start: float, metre: Metre, tol: float = OPENS_TOL) -> str:
    """downbeat, beat, or event: what the picture cuts on at `start`."""
    if any(abs(d - start) <= tol for d in metre.downbeats):
        return "downbeat"
    if any(abs(b - start) <= tol for b in metre.beats):
        return "beat"
    return "event"


def swell_rise(cut_map: CutMap, start: float, end: float) -> float:
    """The largest climb of any swell the span overlaps; 0 when level."""
    rises = [s.rises_db for s in cut_map.spans
             if s.kind == "swell" and s.start < end and s.end > start]
    return max(rises, default=0.0)


def trough_room(opener: CutEvent | None, end: float) -> float:
    """Seconds of the dropout a line may sit in, no further than the span."""
    if opener is None or opener.kind != "dropout":
        return 0.0
    close = end if opener.end is None else min(opener.end, end)
    return round(close - opener.t, 3)


def density_in(cut_map: CutMap, start: float, end: float) -> tuple[float, float]:
    """Median level and mean onset density of the events inside [start, end)."""
    inside = [e for e in cut_map.events if start <= e.t < end]
    if not inside:
        return 0.0, 0.0
    return (round(float(median(e.level_db for e in inside)), 1),
            round(fmean(e.onset_density for e in inside), 3))


def span_of(index: int, start: float, end: float, kind: SpanKind, section: CueSection,
            cut_map: CutMap, metre: Metre) -> CueSpan:
    """One span, its texture read off the event that opens it (or, when
    nothing does, off the events inside it)."""
    opener = opening_event(cut_map, start)
    level, density = ((opener.level_db, opener.onset_density) if opener
                      else density_in(cut_map, start, end))
    return CueSpan(index=index, start=start, end=end, kind=kind, section=section.index,
                   movement=section.movement, bars=bars_of(start, end, metre.bar),
                   opens_on=opens_on(start, metre), level_db=level, onset_density=density,
                   rises_db=swell_rise(cut_map, start, end),
                   line_room=trough_room(opener, end) if kind == "trough" else 0.0)


# --- sections ----------------------------------------------------------------

def movements_of(count: int) -> dict[int, Movement]:
    """Section index -> movement: the story quota laid over the sections in
    order.  BY COUNT, not by time: the ask (CueAsk.for_bars) split its bars
    by the same quota, so the plan reads the cue the way it was asked for,
    and every movement keeps a section whenever the cue has three.  (By
    time, a 60 s cue with sections at 0, 10 and 20 s would have no M3.)"""
    quota = movement_quota(count)
    return dict(enumerate(m for m in MOVEMENTS for _ in range(quota[m])))


def section_starts(cut_map: CutMap, cuts: list[float]) -> list[float]:
    """0 and every section event that survived as a cut."""
    survived = {e.t for e in cut_map.events if e.kind == "section"} & set(cuts[1:-1])
    return [0.0] + sorted(survived)


def sections_of(cut_map: CutMap, cuts: list[float],
                movements: dict[int, Movement]) -> list[CueSection]:
    """The cue's sections between its section cuts, textured by their events."""
    starts = section_starts(cut_map, cuts)
    out = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else cut_map.seconds
        level, density = density_in(cut_map, start, end)
        out.append(CueSection(index=i, start=start, end=end, movement=movements[i],
                              pulse=density >= PULSE_DENSITY, level_db=level))
    return out


def section_at(sections: list[CueSection], t: float) -> CueSection:
    """The section `t` falls in."""
    return [s for s in sections if s.start <= t][-1]


# --- the plan ----------------------------------------------------------------

def spans_of(cut_map: CutMap, metre: Metre, movements: dict[int, Movement]) -> list[CueSpan]:
    """Contiguous spans 0 -> seconds: one per hold between cuts, then the tail."""
    cuts = cut_times(cut_map, metre)
    sections = sections_of(cut_map, cuts, movements)
    bounds = cuts + [cut_map.seconds]
    kinds = untwinned([kind_of(a, b, cut_map, metre) for a, b in zip(bounds, bounds[1:])], bounds)
    return [span_of(i, a, b, kinds[i], section_at(sections, a), cut_map, metre)
            for i, (a, b) in enumerate(zip(bounds, bounds[1:]))]


def plan_of(cut_map: CutMap, metre: Metre, rel_path: str, seed: int, asked=None) -> CuePlan:
    """The rendered cue as the shot list it affords."""
    cuts = cut_times(cut_map, metre)
    movements = movements_of(len(section_starts(cut_map, cuts)))
    return CuePlan(rel_path=rel_path, seed=seed, seconds=cut_map.seconds, bpm=metre.bpm,
                   bar=metre.bar, sections=sections_of(cut_map, cuts, movements),
                   spans=spans_of(cut_map, metre, movements), hard_out=cut_map.hard_out,
                   title_hit=cut_map.title_hit, asked=asked)


# --- fit ---------------------------------------------------------------------

def stretched(span: CueSpan, start: float, end: float, bar: float) -> CueSpan:
    """The span over new bounds; an accent grown past a beat is a phrase."""
    bars = bars_of(start, end, bar)
    kind = "phrase" if span.kind == "accent" and bars * 4.0 > ACCENT_BEATS else span.kind
    return CueSpan.model_validate({**span.model_dump(), "start": start, "end": end,
                                   "bars": bars, "kind": kind})


def absorbed(spans: list[CueSpan], i: int, bar: float) -> list[CueSpan]:
    """Span `i` removed, its time given to its predecessor (at the head, to
    its successor), indices renumbered.  Section bounds never move: a span
    that opens a section is never `i` (see `removable`)."""
    gone = spans[i]
    out = [s for j, s in enumerate(spans) if j != i]
    if i == 0:
        out[0] = stretched(out[0], gone.start, out[0].end, bar)
    else:
        out[i - 1] = stretched(out[i - 1], out[i - 1].start, gone.end, bar)
    return [s.model_copy(update={"index": j}) for j, s in enumerate(out)]


def removable(spans: list[CueSpan], i: int) -> bool:
    """A span the fit rule may take out without moving a section bound."""
    if spans[i].kind in FIXED_KINDS:
        return False
    return i > 0 or spans[1].kind != "section"


def latest_accent(spans: list[CueSpan]) -> int | None:
    """The last accent: an insert is the cheapest cut to lose, and the
    latest one sits where the cutting is already fastest."""
    found = [i for i, s in enumerate(spans) if s.kind == "accent" and removable(spans, i)]
    return found[-1] if found else None


def earliest_pair(spans: list[CueSpan], into: tuple[str, ...]) -> int | None:
    """The first phrase whose predecessor is of a kind in `into` and in the
    same section: its index, the span that gets folded back."""
    for i in range(1, len(spans)):
        a, b = spans[i - 1], spans[i]
        if b.kind == "phrase" and a.kind in into and a.section == b.section and removable(spans, i):
            return i
    return None


def bars_needed(picture: list[CueSpan], affordable: int) -> int:
    """Bars a shorter cue must lose: the excess spans at their shortest,
    rounded up to whole bars for the next ask."""
    excess = max(0, len(picture) - affordable)
    return max(1, math.ceil(sum(sorted(s.bars for s in picture)[:excess])))


def replaced(plan: CuePlan, spans: list[CueSpan]) -> CuePlan:
    """The plan over new spans, every validator run again."""
    return CuePlan.model_validate({**plan.model_dump(), "spans": [s.model_dump() for s in spans]})


def next_removal(spans: list[CueSpan]) -> int | None:
    """Which span goes next: the latest accent; else the earliest phrase
    after a phrase; else the earliest phrase after its section's opening
    shot.  Phrases fold into phrases before they fold into the section's
    door, so the movement's first image keeps its length as long as it can."""
    i = latest_accent(spans)
    if i is None:
        i = earliest_pair(spans, ("phrase",))
    if i is None:
        i = earliest_pair(spans, MERGEABLE)
    return i


def plan_fit(plan: CuePlan, affordable: int) -> CuePlan:
    """The plan cut down to `affordable` picture spans, or ShorterCue with
    the bars the cue must lose.  Section bounds, sustains and troughs never
    move: those are what the cue was asked for."""
    spans = list(plan.spans)
    while len(spans) - 1 > affordable:
        i = next_removal(spans)
        if i is None:
            raise ShorterCue(bars_needed(spans[:-1], affordable))
        spans = absorbed(spans, i, plan.bar)
    return plan if len(spans) == len(plan.spans) else replaced(plan, spans)


def fit_to_budget(plan: CuePlan, remaining_s: float, cycle: frame_budget.Cycle,
                  reserve: float = frame_budget.RETRY_RESERVE) -> CuePlan:
    """The plan trimmed one span at a time until its takes render inside the
    seconds kept, or ShorterCue when the spans that never move exceed them."""
    while not frame_budget.fits(plan, remaining_s, cycle, reserve):
        plan = plan_fit(plan, len(plan.picture_spans()) - 1)
    return plan
