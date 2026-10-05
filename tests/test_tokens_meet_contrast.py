"""Every text and state colour the board sets reads (plan P0.3/F4, WCAG 2.1 AA):
4.5:1 for each text and state token on the page and on the raised surfaces, and
for each state's colour on its own tint, in both themes -- Studio black (the
default) and Graphite (data-theme="light")."""
from __future__ import annotations

import pytest

from board_css import contrast, themes

THEMES = themes()
TEXT = ("ink", "ink-2", "ink-3", "accent", "st-running", "st-done", "st-flagged", "st-deferred",
        "st-failed", "st-held", "st-escalated", "st-idle")
GROUNDS = ("paper", "paper-2", "surface", "surface-2")
PAIRS = [(fg, bg) for fg in TEXT for bg in GROUNDS] + [
    (f"st-{s}", f"st-{s}-bg") for s in ("running", "done", "flagged", "deferred", "failed")] + [
    ("code-ink", "code"), ("hot-ink", "hot"), ("accent-ink", "accent"), ("paper", "ink")]


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("fg,bg", PAIRS)
def test_the_pair_holds_4_5(theme, fg, bg):
    t = THEMES[theme]
    ratio = contrast(t[fg], t[bg])
    assert ratio >= 4.5, (theme, fg, t[fg], bg, t[bg], round(ratio, 2))


def test_both_themes_resolve_every_colour_to_a_hex():
    for name, t in THEMES.items():
        for token in {x for pair in PAIRS for x in pair}:
            assert t[token].startswith("#") and len(t[token]) == 7, (name, token, t[token])


def test_studio_black_is_the_default_and_graphite_the_light_option():
    assert THEMES["dark"]["paper"] == "#0f1012" and THEMES["light"]["paper"] == "#f4f5f7"
