"""The board's tokens live in one file (plan F2/F4).  Until 2026-10-04 the board
copied the org chart's `:root{...}` blocks byte for byte into base.html; then the
owner retired the beige ("the bg is shit colour") and moved the board to Studio
black (#0f1012) with Graphite as the light option, so the board no longer
shares the org chart's palette -- `architecture/index.html` keeps its own tokens.
What stays from the old test is its point: one source of truth, byte for byte.
`static/css/tokens.css` is the only place a token is declared, every page
links exactly that file, and the board serves it unchanged."""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from board_css import CSS, TEMPLATES, css
from command_center_fixtures import make_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_no_template_declares_a_palette():
    for page in TEMPLATES.glob("*.html"):
        if page.name == "404.html":   # the bare refusal page: no shell, no stylesheet
            continue
        text = page.read_text(encoding="utf-8")
        assert ":root{" not in text and "--paper:" not in text, page.name


def test_only_the_tokens_file_declares_the_colours():
    for name in ("components", "pages"):
        assert not re.search(r"--(paper|ink|st-[a-z]+|surface)\s*:", css(name)), name


def test_the_page_links_the_tokens_file_and_it_is_served_byte_for_byte(client):
    page = client.get("/").text
    href = re.search(r'href="(/static/css/tokens\.css\?v=[0-9a-f]+)"', page).group(1)
    assert client.get(href).content == (CSS / "tokens.css").read_bytes()


def test_the_board_never_meta_refreshes():
    for page in TEMPLATES.glob("*.html"):
        assert "http-equiv" not in page.read_text(encoding="utf-8"), page.name
