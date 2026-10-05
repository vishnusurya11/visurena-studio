"""A running unit's Activity morphs on every pulse; a fold the owner opened stays open (lead,
after PKG-5 left it open): media.js remembers the open <details> by their summary text before
the swap and re-opens them after it.  Text checks on media.js, $0."""
from pathlib import Path

JS = (Path(__file__).parent.parent / "studio" / "command_center" / "static" / "media.js").read_text(encoding="utf-8")


def test_the_open_folds_are_remembered_before_the_tails_swap():
    assert "function openFolds(" in JS and "htmx:beforeSwap" in JS


def test_the_remembered_folds_are_reopened_after_it():
    assert "function reopenFolds(" in JS and "reopenFolds(t" in JS
