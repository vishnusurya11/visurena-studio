"""A state is never colour alone (plan F5, B9): each one has a Lucide icon in the
sprite and a word, and keeps its Unicode glyph as the text fallback for titles,
the tab's name and the JSON twins.  Every icon a template or the shell names is
in the sprite."""
from __future__ import annotations

import re

from fastapi.testclient import TestClient

from board_css import STATIC, TEMPLATES
from command_center_fixtures import make_app
from studio.command_center import shell, views

SPRITE = set(re.findall(r'<symbol id="([\w-]+)"', (STATIC / "icons.svg").read_text(encoding="utf-8")))


def test_every_state_has_an_icon_in_the_sprite_and_a_glyph():
    assert set(views.ICONS) == set(views.GLYPHS) == {word for _, word in views.LEGEND}
    for state, name in views.ICONS.items():
        assert name in SPRITE, (state, name)
        assert views.GLYPHS[state].strip(), state


def test_the_legend_draws_each_state_as_icon_and_word(tmp_path, monkeypatch):
    page = TestClient(make_app(tmp_path, monkeypatch)).get("/").text
    legend = page[page.index('data-testid="legend"'):]
    for state, name in views.ICONS.items():
        item = re.search(rf'data-state="{state}"[^>]*>(.*?)</span>', legend, re.S).group(1)
        assert f"#{name}" in item and item.rstrip().endswith(state), state


def test_every_icon_named_anywhere_is_in_the_sprite():
    named = set()
    for page in TEMPLATES.glob("*.html"):
        named |= set(re.findall(r"icon\('([\w-]+)'", page.read_text(encoding="utf-8")))
    named |= set(shell.DEPT_ICONS.values()) | {shell.DEFAULT_ICON} | {p[1] for p in shell.PAGES}
    assert named and not named - SPRITE, sorted(named - SPRITE)
