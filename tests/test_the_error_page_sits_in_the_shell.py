"""The error page is a page of the board (ruling PKG-3, row 3.10; P09.4).

It extends base.html -- the three stylesheets, Studio black by default -- and
draws one card: the code, a plain sentence, the reason, the path that was asked
for, and links to Home and the asked path's parent.  No inline style, no hex: the
retired beige cannot come back through it.  `_icon.html`'s `no_picture` is the
clapperboard slot a tile shows when it has no picture yet (row 3.9)."""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader

from board_css import TEMPLATES
from command_center_fixtures import make_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_the_error_page_has_no_hex_and_no_style():
    text = (TEMPLATES / "404.html").read_text(encoding="utf-8")
    assert "<style" not in text and not re.search(r"#[0-9a-fA-F]{3,6}\b", text)
    assert text.startswith('{% extends "base.html" %}')


def test_a_missing_page_is_the_shell_card_with_the_path(client):
    r = client.get("/d/episode/x/ep99")
    assert r.status_code == 404
    assert "/static/css/tokens.css" in r.text and 'data-theme="dark"' in r.text
    assert 'data-testid="error"' in r.text and "/d/episode/x/ep99" in r.text


def test_the_card_links_home_and_the_parent(client):
    r = client.get("/d/episode/x/ep99")
    assert 'href="/"' in r.text and 'href="/d/episode/x"' in r.text


def test_the_card_keeps_the_reason(client):
    assert "not a department" in client.get("/d/publish").text


def test_the_top_level_parent_is_home(client):
    r = client.get("/nope")
    assert r.status_code == 404 and 'data-testid="error-up"' not in r.text


def _icons():
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    env.globals["static_url"] = lambda p: f"/static/{p}"
    return env.get_template("_icon.html").module


def test_no_picture_is_a_clapperboard_with_its_reason():
    html = str(_icons().no_picture("not rendered yet"))
    assert "#clapperboard" in html and "not rendered yet" in html and 'class="nopic' in html


def test_an_icon_is_hidden_from_assistive_tech():
    assert 'aria-hidden="true"' in str(_icons().icon("check"))
