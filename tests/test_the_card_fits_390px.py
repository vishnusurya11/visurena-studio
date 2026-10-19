"""The live card at 390 px (phone): the rail folds to a list, the long loops and debt lines wrap
instead of widening the page, an earlier step is drawn dashed, and the palette stays the neutral
dark #0f1012 (owner: never beige).  A static read of the stylesheets; $0."""
from __future__ import annotations

import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "studio" / "command_center" / "static" / "css"


def _rule(text: str, selector: str) -> str:
    m = re.search(re.escape(selector) + r"\{([^}]*)\}", text)
    assert m, f"no rule for {selector}"
    return m.group(1)


def _pages() -> str:
    return (CSS / "pages.css").read_text(encoding="utf-8")


def test_the_loops_and_debt_line_wraps_instead_of_widening_the_page():
    body = _rule(_pages(), ".lv-loops")
    assert "overflow-wrap:anywhere" in body and "min-width:0" in body


def test_the_rail_folds_to_a_list_on_a_phone():
    phone = re.search(r"@media \(max-width:600px\)\{(.*?)\n\}", _pages(), re.S).group(1)
    assert ".lv-rail{display:none}" in phone and ".lv-railm{display:block}" in phone


def test_the_phone_list_wraps_a_long_history_line():
    assert "overflow-wrap:anywhere" in _rule(_pages(), ".lv-railm li span")


def test_an_earlier_step_is_drawn_dashed_in_the_rail_and_the_list():
    text = _pages()
    assert "dashed" in _rule(text, ".lv-rail .st-earlier i")
    assert ".lv-railm li.st-earlier b" in text


def test_the_palette_is_the_neutral_dark_never_beige():
    tokens = (CSS / "tokens.css").read_text(encoding="utf-8")
    assert "--paper:#0f1012" in tokens
