"""Conforming a verified cue to the frames step 07 affords: one render, a
shorter length cut from it.

Step 03 used to answer `ShorterCue` by asking the music model again with
fewer bars -- a second render (a batch of four, minutes each) for a cue that
had already passed the ask.  A shorter cue is an edit, not a composition:
the fit rule folds what it can (accents into the shot before, phrases into
phrases), and past that the smallest interior span leaves the music between
its two measured events (row 53's cut) and everything after moves up.  The
opening image and the button are never cut; only when nothing interior is
left does step 03 ask for a shorter cue.

`cut_files` is the audio side, shared with step 08's settle: the cue cut,
its metre and its cut map moved with it, written beside the original.

Design: docs/analysis/research/trailer-music-first.md, rows 48 and 56.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from pydantic import ValidationError

from studio import cue_edit, cue_settle, cue_spans, frame_budget
from studio.cue_plan import CuePlan
from studio.cue_settle import Range, Settled
from studio.cue_spans import ShorterCue
from studio.trailer_stage_spec import Metre


def indices(plan: CuePlan) -> list[str]:
    """Step 03 has no beat ids yet; the picture spans stand in for them."""
    return [str(i) for i in range(len(plan.picture_spans()))]


def folded(out: Settled) -> Settled | None:
    """One fold of the fit rule, or None when it has none left."""
    i = cue_spans.next_removal(out.plan.spans)
    if i is None:
        return None
    spans = cue_spans.absorbed(out.plan.spans, i, out.plan.bar)
    return Settled(plan=cue_spans.replaced(out.plan, spans),
                   ids=out.ids[:i] + out.ids[i + 1:], removed=out.removed)


def smallest_interior(plan: CuePlan) -> int | None:
    """The interior picture span with the fewest bars, the latest among
    equals; the opening image and the button are never cut."""
    picture = plan.picture_spans()
    inner = range(1, len(picture) - 1)
    if not inner:
        return None
    return min(inner, key=lambda i: (picture[i].bars, -i))


def cut(out: Settled) -> Settled:
    """The smallest interior span cut out of the cue, or ShorterCue when
    none is left or the cut would leave no plan."""
    picture = out.plan.picture_spans()
    j = smallest_interior(out.plan)
    if j is None:
        raise ShorterCue(cue_spans.bars_needed(picture, len(picture) - 1))
    try:
        one = cue_settle.cut_settled(out.plan, out.ids, j)
    except ValidationError as exc:
        raise ShorterCue(cue_spans.bars_needed(picture, len(picture) - 1)) from exc
    return Settled(plan=one.plan, ids=one.ids, removed=out.removed + one.removed)


def shorter(out: Settled) -> Settled:
    """One picture span fewer: a fold when the fit rule has one, else a cut."""
    one = folded(out)
    return cut(out) if one is None else one


def conform_to_budget(plan: CuePlan, remaining_s: float, cycle: frame_budget.Cycle,
                      reserve: float = frame_budget.RETRY_RESERVE) -> Settled:
    """The plan one span shorter at a time until its takes render inside the
    seconds kept; the ranges the cue must lose come back with it."""
    out = Settled(plan=plan, ids=indices(plan), removed=[])
    while not frame_budget.fits(out.plan, remaining_s, cycle, reserve):
        out = shorter(out)
    return out


# --- the audio side -----------------------------------------------------------

def cut_map_name(rel_path: str) -> str:
    """The cut map beside a cue: `cue-1003.flac` -> `cutmap-1003.json`, and
    the settled cue's beside it, so qc grades against the cue that plays."""
    return f"cutmap-{Path(rel_path).stem.removeprefix('cue-')}.json"


def settled_rel(cue: CuePlan) -> str:
    """The settled cue's path beside the original, one file however many
    passes settle it."""
    path = Path(cue.rel_path)
    seed = path.stem.removeprefix("cue-").removesuffix("-settled")
    return (path.parent / f"cue-{seed}-settled{path.suffix}").as_posix()


def read_cue(path: Path) -> tuple[np.ndarray, int]:
    import soundfile
    samples, rate = soundfile.read(path, dtype="float32")
    return samples, int(rate)


def write_cue(path: Path, samples: np.ndarray, rate: int) -> None:
    import soundfile
    soundfile.write(path, samples, rate, subtype="PCM_16")


def cut_files(music: Path, book: Path, cue: CuePlan, removed: list[Range]) -> str:
    """Every removed range cut out of the cue in order, the metre and the cut
    map moved with it, all three written beside the original; the settled
    cue's rel_path.  A join the cue refuses raises before anything is written."""
    metre = Metre.model_validate_json((music / "metre.json").read_text(encoding="utf-8"))
    cut_map = json.loads((music / cut_map_name(cue.rel_path)).read_text(encoding="utf-8"))
    samples, rate = read_cue(book / cue.rel_path)
    for start, end in removed:
        samples, recut = cue_edit.remove_range(samples, rate, metre, start, end)
        metre, cut_map = recut.metre, cue_settle.shifted_cut_map(cut_map, start, end)
    rel = settled_rel(cue)
    write_cue(book / rel, samples, rate)
    (music / "metre.json").write_text(metre.model_copy(update={"rel_path": rel})
                                      .model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    (music / cut_map_name(rel)).write_text(json.dumps(cut_map, indent=2), encoding="utf-8")
    return rel
