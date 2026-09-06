"""Settling a cue plan when takes are lost: the cue bends, the story does not.

Step 07 renders one take per picture span.  When a take is lost -- dropped
by QC, never rendered inside the ceiling -- the plan has a span with no
picture.  An editor settles that three ways, and this module does the same,
as pure functions on the CuePlan:

- a lost **accent** (an insert of a beat at most) is absorbed by the shot
  before it, which plays on through the beat; the music is untouched;
- a lost **phrase, sustain, trough or section door** is cut OUT of the
  music between its two events and everything after moves up -- no take
  can grow four bars, so the cue gives the seconds back instead;
- a lost **button** (the last picture span) moves the hard out: the card
  comes on the span's own start.

Every cut keeps the plan a plan: when two sustains would come to touch,
the later one is cut out too and its beat dropped.  `settle` works latest
loss first so every earlier second stays true while later ones move.
`removed` lists the ranges in application order on the progressively
edited timeline -- exactly the order `cue_edit.remove_range` applies them.

Design: docs/analysis/research/trailer-music-first.md, row 53.
"""
from __future__ import annotations

from pydantic import BaseModel, ValidationError

from studio import cue_spans
from studio.cue_plan import CuePlan, CueSection, CueSpan
from studio.music_events import CutMap

Range = tuple[float, float]


class Settled(BaseModel):
    """The plan after its losses, the beat ids that still fill it, and the
    seconds the cue must lose, in the order to cut them."""

    plan: CuePlan
    ids: list[str]
    removed: list[Range]


def lost_indices(ids: list[str], keep: set[str]) -> list[int]:
    """Picture indices whose beat has no take, latest first."""
    return [i for i in range(len(ids) - 1, -1, -1) if ids[i] not in keep]


def moved(t: float, start: float, end: float) -> float:
    """Where a moment lands once [start, end) is cut out: before the cut it
    stays, after it moves up by the cut, inside it lands on the join."""
    if t <= start:
        return t
    return round(max(start, t - (end - start)), 4)


def shifted_span(span: CueSpan, start: float, end: float, bar: float) -> CueSpan | None:
    """The span with the cut taken out of its timeline, or None when the
    cut swallowed it whole."""
    a, b = moved(span.start, start, end), moved(span.end, start, end)
    if b - a <= 1e-6:
        return None
    return cue_spans.stretched(span, a, b, bar)


def shifted_sections(sections: list[CueSection], start: float, end: float
                     ) -> tuple[list[CueSection], dict[int, int]]:
    """Sections moved with the cue; one the cut swallowed is dropped, and
    the map says which new index each surviving old index now has."""
    out, remap = [], {}
    for s in sections:
        a, b = moved(s.start, start, end), moved(s.end, start, end)
        if b - a > 1e-6:
            remap[s.index] = len(out)
            out.append(s.model_copy(update={"index": len(out), "start": a, "end": b}))
    return out, remap


def renumbered(spans: list[CueSpan]) -> list[CueSpan]:
    return [s.model_copy(update={"index": j}) for j, s in enumerate(spans)]


def cut_out(plan: CuePlan, i: int) -> CuePlan:
    """Span `i` cut out of the cue: later spans, sections, the hard out and
    the title hit all move up by its length.  Not re-validated -- the
    caller settles any sustains the cut brought together first."""
    gone = plan.spans[i]
    a, b = gone.start, gone.end
    sections, remap = shifted_sections(plan.sections, a, b)
    kept = [shifted_span(s, a, b, plan.bar) for j, s in enumerate(plan.spans) if j != i]
    spans = renumbered([s.model_copy(update={"section": remap[s.section]})
                        for s in kept if s is not None])
    title = None if plan.title_hit is None else moved(plan.title_hit, a, b)
    return plan.model_copy(update=dict(spans=spans, sections=sections, title_hit=title,
                                       seconds=round(plan.seconds - (b - a), 4),
                                       hard_out=moved(plan.hard_out, a, b)))


def validated(plan: CuePlan) -> CuePlan:
    """Every plan validator run again over a plan built by `model_copy`."""
    return CuePlan.model_validate(plan.model_dump())


def twin(plan: CuePlan) -> int | None:
    """The later sustain of the first two that touch, or None."""
    for j in range(1, len(plan.spans)):
        if plan.spans[j - 1].kind == plan.spans[j].kind == "sustain":
            return j
    return None


def absorb_back(plan: CuePlan, i: int) -> CuePlan:
    """The accent's beat given to the shot before it (at the head, after)."""
    return cue_spans.replaced(plan, cue_spans.absorbed(plan.spans, i, plan.bar))


def button_lost(plan: CuePlan) -> CuePlan:
    """The last picture span joins the tail: the card comes on its start."""
    last, tail = plan.spans[-2], plan.spans[-1]
    spans = renumbered(list(plan.spans[:-2])
                       + [cue_spans.stretched(tail, last.start, tail.end, plan.bar)])
    return cue_spans.replaced(plan.model_copy(update={"hard_out": last.start}), spans)


def cut_settled(plan: CuePlan, ids: list[str], i: int) -> Settled:
    """Span `i` cut out, then every later sustain the cut left touching an
    earlier one, each with its beat."""
    removed: list[Range] = []
    while True:
        gone = plan.spans[i]
        removed.append((gone.start, gone.end))
        plan, ids = cut_out(plan, i), ids[:i] + ids[i + 1:]
        j = twin(plan)
        if j is None:
            return Settled(plan=validated(plan), ids=ids, removed=removed)
        i = j


def settle_one(plan: CuePlan, ids: list[str], i: int) -> Settled:
    """One lost picture span settled the way its kind asks."""
    if i == len(ids) - 1:
        return Settled(plan=button_lost(plan), ids=ids[:-1], removed=[])
    if plan.spans[i].kind == "accent":
        try:
            return Settled(plan=absorb_back(plan, i), ids=ids[:i] + ids[i + 1:], removed=[])
        except ValidationError:
            pass  # the accent sat between two sustains; cut it and settle them
    return cut_settled(plan, ids, i)


def settle(plan: CuePlan, ids: list[str], keep: set[str]) -> Settled:
    """The plan settled over every beat without a take, latest first."""
    out = Settled(plan=plan, ids=list(ids), removed=[])
    for i in lost_indices(out.ids, keep):
        one = settle_one(out.plan, out.ids, i)
        out = Settled(plan=one.plan, ids=one.ids, removed=out.removed + one.removed)
    return out


def shifted_cut_map(doc: dict, start: float, end: float) -> dict:
    """The cut map with [start, end) cut out: events inside are gone, later
    ones move up; spans move, clip, or vanish with the cut."""
    events = [{**e, "t": moved(e["t"], start, end),
               "end": None if e.get("end") is None else moved(e["end"], start, end)}
              for e in doc["events"] if not start < e["t"] < end]
    spans = [{**s, "start": moved(s["start"], start, end), "end": moved(s["end"], start, end)}
             for s in doc["spans"]]
    spans = [s for s in spans if s["end"] - s["start"] > 1e-6]
    title = None if doc.get("title_hit") is None else moved(doc["title_hit"], start, end)
    out = {**doc, "events": events, "spans": spans, "title_hit": title,
           "hard_out": moved(doc["hard_out"], start, end),
           "seconds": round(doc["seconds"] - (end - start), 4)}
    return CutMap.model_validate(out).model_dump()
