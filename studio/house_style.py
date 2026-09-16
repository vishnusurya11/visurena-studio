"""The one sentence that tells every drawer and the renderer WHERE this is.

MEASURED, episode 8. `Episode.palette` was added because the book's palette ends
"1881 London" and put Georgian terraced streets into the Utah desert. It was
wired into `frames.py` -- the location plate -- and the fix was called done. It
reached nothing else:

    "1881 London" in the paid storyboard prompts   13 of 13 sheets
    "1881 London" in the take prompts sent to H3   28 of 28 takes

because the sentence was a hard-coded constant in four modules at once
(`episode_seq_board.STYLE`, `episode_ref_official.STYLE`,
`episode_take_prompt.STYLE`, `episode_board.STILL`). Episode 8 was DRAWN and
RENDERED under an instruction naming 1881 London over an 1847 desert.

That is this repo's most expensive habit -- a change that looks right, passes
its own test, and reaches no artefact -- and the test written beside that fix
only exercised `location_prompt`, which was the one path already working.

So the place lives HERE, in one module, set once per run from the plan. The
pattern is `canvas.adopt` and the `W, H` globals that `assemble` and `takes_r2v`
already rebind: a run declares its world before it makes anything.

The palette says WHERE and WHEN. The style says HOW IT IS PHOTOGRAPHED, and that
does not change between episodes -- it is the series' own look.
"""
from __future__ import annotations

HOUSE = ("1881 London, muted soot-black and gaslight-amber palette")
"""The book this pipeline was built for, and the floor when a plan says nothing.

Seven episodes were made against it and must keep being made against it, so an
episode that declares no palette is unchanged."""

STILLS = "Photoreal cinematic 35 mm film stills, {where}, natural film grain."
LIVE = "Photoreal cinematic live-action, {where}, 35 mm film grain, natural weight and pace."

_where = HOUSE


def adopt(palette: str) -> None:
    """Declare the place for this run. Empty puts the book's own back.

    Called once, from the script's `main`, off `episode.palette` -- never
    guessed per call site, because four call sites guessing is how the last one
    went wrong."""
    global _where
    _where = palette.strip() or HOUSE


def where() -> str:
    """The place as adopted."""
    return _where


def stills() -> str:
    """The style line for a DRAWN sheet or board."""
    return STILLS.format(where=_where)


def live() -> str:
    """The style line for a RENDERED take."""
    return LIVE.format(where=_where)
