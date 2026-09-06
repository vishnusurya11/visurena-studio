"""The delivered cut graded against its cue's plan.

The music-first brick: the cue's measured spans ARE the shot list, so the
picture is graded against the CuePlan it was cut to -- never against a bar
count the pipeline typed.  Every function here is pure: detected cut times
in, the shipped plan in, one number out.  `measure` assembles the CueCut.
"""
from __future__ import annotations

from statistics import median

from studio.cue_plan import SUSTAIN_BARS, CuePlan
from studio.h3 import FPS
from studio.trailer_stage_spec import CueCut

EVENT_TOL = 0.1
"""How close a cut must land to the event it was cut for: 0.1 s is over two
frames at 24, the width a scene detector reports a cut within."""

HOLDS = ("sustain", "trough")
"""The spans the picture holds through: a sustain is one move, a trough
(the stopdown) a static answer.  Never cut inside either."""


def events_of(plan: CuePlan, cut_map: dict | None = None) -> list[float]:
    """Where the cue asked to be cut: the cut map's events of rank two or
    more when it shipped, else the plan's span starts after the first."""
    if cut_map:
        return [float(e["t"]) for e in cut_map["events"] if e["rank"] >= 2]
    return [s.start for s in plan.spans[1:]]


def near(t: float, times: list[float], tol: float = EVENT_TOL) -> bool:
    return any(abs(t - other) <= tol for other in times)


def cuts_on_events(cuts: list[float], events: list[float]) -> float:
    """Share of cuts that landed on an event.  Run 10: 0.28; chance 0.11."""
    if not cuts:
        return 0.0
    return sum(near(c, events) for c in cuts) / len(cuts)


def section_changes_cut(cuts: list[float], plan: CuePlan) -> float:
    """Share of section changes the picture cut on.  A change left inside a
    shot is the mistake run 10 made at 43.0 s."""
    changes = [s.start for s in plan.sections[1:]]
    return sum(near(c, cuts) for c in changes) / len(changes) if changes else 1.0


def cuts_inside_holds(cuts: list[float], plan: CuePlan) -> int:
    """Cuts strictly inside a sustain or a trough; the boundaries are the
    hold's own cuts."""
    holds = [s for s in plan.spans if s.kind in HOLDS]
    return sum(any(s.start + EVENT_TOL < c < s.end - EVENT_TOL for s in holds) for c in cuts)


def shots_of(cuts: list[float], plan: CuePlan) -> list[tuple[float, float]]:
    """The shots the cuts make, from the head to the hard out."""
    edges = [0.0] + sorted(c for c in cuts if 0.0 < c < plan.hard_out) + [plan.hard_out]
    return list(zip(edges, edges[1:]))


def span_at(t: float, plan: CuePlan):
    """The span a moment sits in, or None past the cue."""
    return next((s for s in plan.spans if s.start <= t < s.end), None)


def long_shots_on_holds(cuts: list[float], plan: CuePlan) -> float:
    """Share of the long shots -- as long as a sustain -- whose middle sits
    on a hold.  A long shot over a phrase reads as the picture running out."""
    long_s = SUSTAIN_BARS * plan.bar
    longs = [(a, b) for a, b in shots_of(cuts, plan) if b - a >= long_s]
    if not longs:
        return 1.0
    on = [span_at((a + b) / 2.0, plan) for a, b in longs]
    return sum(s is not None and s.kind in HOLDS for s in on) / len(longs)


def lines_in_troughs(lines: list[tuple[float, float]], plan: CuePlan) -> float:
    """Share of spoken lines that sit inside a window the plan offers."""
    if not lines:
        return 1.0
    windows = plan.line_windows()
    inside = [any(w.start - EVENT_TOL <= a and b <= w.end + EVENT_TOL for w in windows)
              for a, b in lines]
    return sum(inside) / len(lines)


def accents_cut(cuts: list[float], plan: CuePlan) -> float:
    """Share of accents cut on both edges: an insert is two cuts or nothing."""
    accents = [s for s in plan.spans if s.kind == "accent"]
    if not accents:
        return 1.0
    return sum(near(s.start, cuts) and near(s.end, cuts) for s in accents) / len(accents)


def movement_medians(cuts: list[float], plan: CuePlan) -> list[float]:
    """Median measured shot length per movement, in movement order."""
    by: dict[str, list[float]] = {}
    for a, b in shots_of(cuts, plan):
        span = span_at((a + b) / 2.0, plan)
        if span is not None:
            by.setdefault(span.movement, []).append(round(b - a, 3))
    return [round(median(v), 3) for _, v in sorted(by.items())]


def frames_rendered(clips: dict) -> int:
    """Frames step 07 rendered, summed off the takes that recorded theirs."""
    return sum(int(t.get("frames") or 0) for t in clips.get("takes", []))


def frames_played(plan: CuePlan) -> int:
    """Frames of picture the master plays: the cue up to its hard out."""
    return round(plan.hard_out * FPS)


def measure(cuts: list[float], plan: CuePlan, lines: list[tuple[float, float]] = (),
            clips: dict | None = None, cut_map: dict | None = None) -> CueCut:
    """The whole CueCut from the detected cuts and the shipped plan."""
    return CueCut(cuts_on_events=cuts_on_events(cuts, events_of(plan, cut_map)),
                  section_changes_cut=section_changes_cut(cuts, plan),
                  cuts_inside_sustain=cuts_inside_holds(cuts, plan),
                  long_shots_on_sustains=long_shots_on_holds(cuts, plan),
                  lines_in_troughs=lines_in_troughs(list(lines), plan),
                  accents_cut=accents_cut(cuts, plan),
                  movement_medians_s=movement_medians(cuts, plan),
                  frames_rendered=frames_rendered(clips or {}),
                  frames_played=frames_played(plan))
