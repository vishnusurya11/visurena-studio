"""Where a spoken line may sit, read from the cue plan when step 03 wrote one.

Design (docs/analysis/research/trailer-music-first.md): a line sits in a
trough the cue has or a sustain the mix ducks under, and ends at least a
beat before the span does, so the cut lands on music and never on a word.
`CuePlan.line_windows` is that rule; this module chooses between it and the
metre's own windows (`trailer_dialogue.windows_of`), which stand for a
production that predates the plan.
"""
from __future__ import annotations

from pathlib import Path

from studio.cue_plan import CuePlan
from studio.trailer_dialogue import windows_of
from studio.trailer_stage_spec import Metre, Slot

PLAN_REL = "music/plan.json"
"""Where step 03 ships the plan, beside `music/metre.json`."""

BEATS_PER_BAR = 4.0
"""The plan counts a bar as four beats (`CueSpan.beat`, `CuePlan.line_windows`)."""


def load_plan(out_dir: Path) -> CuePlan | None:
    """The shipped cue plan, or None for a production step 03 cut before it
    wrote one."""
    path = out_dir / PLAN_REL
    if not path.exists():
        return None
    return CuePlan.model_validate_json(path.read_text(encoding="utf-8"))


def windows_for(metre: Metre, plan: CuePlan | None) -> list[Slot]:
    """The plan's troughs and sustains, a beat short of the span; the metre's
    troughs and ducked phrases when there is no plan."""
    if plan is not None:
        return plan.line_windows()
    return windows_of(metre)


def beat_for(metre: Metre, plan: CuePlan | None) -> float | None:
    """The beat a line is measured in.  A plan's spans lie on its bars, so
    its beat holds even over a cue the metre calls rubato; without a plan
    only a metric grid has one."""
    if plan is not None:
        return round(plan.bar / BEATS_PER_BAR, 4)
    return metre.beat if metre.grid == "metre" else None
