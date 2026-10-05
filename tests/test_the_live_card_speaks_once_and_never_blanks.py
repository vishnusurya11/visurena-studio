"""The live card's additive fixes (panel ruling 5.9, tracker files, behaviour kept):
the progressbar's words follow every poll, the step change is spoken once before
the card is replaced, the replacement morphs, a new panel is decoded before it is
shown, the trace carries the step's stall budget as a marker, the vital turns
amber when the card's own poll is two beats late, and every clock freezes while
the board says it is stale.  File reads and pure functions only, $0."""
from __future__ import annotations

import re
from pathlib import Path

from studio.command_center import progress_view

JS = (Path(__file__).resolve().parents[1] / "studio" / "command_center" / "static" / "progress.js").read_text(encoding="utf-8")
VITAL = (Path(__file__).resolve().parents[1] / "studio" / "command_center" / "templates" / "_live_vital.html").read_text(encoding="utf-8")


def fn(name: str) -> str:
    """The body of one function in progress.js (up to the next top-level function)."""
    m = re.search(rf"function {name}\(.*?\n  }}\n", JS, re.S)
    assert m, name
    return m.group(0)


def test_the_progressbar_words_are_patched_every_poll():
    assert "aria-valuetext" in fn("patchHero") and "valuetext(p)" in fn("patchHero")
    assert "' of '" in fn("valuetext") and "done around" in fn("valuetext")


def test_the_step_change_is_announced_before_the_swap():
    body = fn("apply")
    assert body.index("say(p, prev)") < body.index("swap(p, prev)")
    assert "board.announce" in fn("say")


def test_the_swap_morphs_when_idiomorph_is_there():
    body = fn("swap")
    assert "Idiomorph.morph" in body and "replaceWith" in body


def test_a_new_panel_is_decoded_before_it_is_shown():
    assert "reveal(img" in fn("patchSheet") and ".decode()" in fn("reveal")


def test_the_card_goes_late_after_two_missed_beats_and_clocks_freeze_when_stale():
    assert "data-late" in fn("watchLate") or "dataset.late" in fn("watchLate")
    assert "data-stale" in fn("tick")


def test_the_stall_budget_marker_sits_on_the_trace():
    assert 'data-k="budget"' in VITAL and "p.budget_x" in VITAL


def test_budget_x_is_the_budgets_place_on_the_thirty_minute_trace():
    assert progress_view.budget_x({"budget_s": 600.0}) == 160.0
    assert progress_view.budget_x({"budget_s": 3600.0}) == 0.0
    assert progress_view.budget_x({"budget_s": None}) is None
