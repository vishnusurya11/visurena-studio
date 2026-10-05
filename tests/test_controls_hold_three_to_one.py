"""A control's edge reads (ruling PKG-3, row 3.8; P07.7, WCAG 1.4.11).

`--rule` (1.29:1) and `--rule-2` (1.57:1) were the only borders on inputs, buttons
and the waiting tiles; a boundary that means something needs 3:1.  `--ctl-line`
holds 3:1 on the page and every raised surface in both themes, and the controls
and waiting states draw with it (decorative dividers keep `--rule`)."""
from __future__ import annotations

import pytest

from board_css import contrast, css, themes
from board_css_rules import rules

THEMES = themes()
GROUNDS = ("paper", "paper-2", "surface", "surface-2")


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("bg", GROUNDS)
def test_the_control_line_holds_3_to_1(theme, bg):
    t = THEMES[theme]
    assert contrast(t["ctl-line"], t[bg]) >= 3.0, (theme, bg, t["ctl-line"], t[bg])


@pytest.mark.parametrize("selector", [".btn", "input", ".lt.st-waiting", ".frame.waiting"])
def test_the_control_draws_its_edge_with_the_control_line(selector):
    bodies = [r.body for name in ("components", "pages") for r in rules(css(name))
              if selector in [s.strip() for s in r.selector.split(",")]]
    assert any("var(--ctl-line)" in b for b in bodies), selector
