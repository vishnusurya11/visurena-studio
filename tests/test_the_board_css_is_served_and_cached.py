"""The board's CSS is three cached files, not a <style> in base.html (plan F2):
tokens, components and pages, each linked with `?v=<mtime>` and answered
immutable for a year; an unversioned request revalidates.  Every rule sits in
a cascade layer (tokens, base, components, pages), so a page's own rules win."""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from board_css import TEMPLATES, block, css
from command_center_fixtures import make_app

IMMUTABLE = "public,max-age=31536000,immutable"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_the_page_links_the_three_files_versioned(client):
    page = client.get("/").text
    for name in ("tokens", "components", "pages"):
        href = re.search(rf'href="(/static/css/{name}\.css\?v=[0-9a-f]+)"', page).group(1)
        r = client.get(href)
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/css")
        assert r.headers["cache-control"] == IMMUTABLE


def test_an_unversioned_file_revalidates_and_a_font_is_immutable(client):
    assert client.get("/static/css/tokens.css").headers["cache-control"] == "no-cache"
    assert client.get("/static/fonts/ibm-plex-mono-400-latin.woff2").headers["cache-control"] == IMMUTABLE


def test_no_template_carries_a_stylesheet():
    for page in TEMPLATES.glob("*.html"):
        if page.name != "404.html":
            assert "<style" not in page.read_text(encoding="utf-8"), page.name


def outside_layers(text: str) -> str:
    """What is left of a stylesheet once comments, layer blocks and registrations are cut."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    for head in ("@layer tokens {", "@layer base {", "@layer components {", "@layer pages {"):
        while head in text:
            text = text.replace(head + block(text, head) + "}", "", 1)
    text = re.sub(r"@(font-face|property\s+--[\w-]+)\{[^}]*\}", "", text)
    return re.sub(r"@layer [\w, ]+;", "", text).strip()


def test_the_cutter_leaves_a_stray_rule():
    assert outside_layers("@layer pages {a{b:c}}\nx{y:z}") == "x{y:z}"


def test_every_rule_is_in_a_layer():
    assert css("tokens").count("@layer tokens, base, components, pages;") == 1
    for name in ("tokens", "components", "pages"):
        assert outside_layers(css(name)) == "", name
