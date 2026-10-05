"""The board's fonts are its own (plan F3): Barlow Condensed, IBM Plex Sans and
IBM Plex Mono as woff2 under static/fonts with the SIL OFL beside them; no page
asks Google (or anyone) for a font, a stylesheet or a script."""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from board_css import STATIC, css
from command_center_fixtures import CODEX, make_app

ROUTES = ("/", "/queue", "/books", "/architecture", "/d/episode", f"/b/{CODEX}", f"/d/episode/{CODEX}/ep04")


@pytest.fixture()
def pages(tmp_path, monkeypatch):
    client = TestClient(make_app(tmp_path, monkeypatch))
    return {r: client.get(r).text for r in ROUTES}


def test_no_page_names_a_remote_font_or_asset(pages):
    for route, page in pages.items():
        assert "fonts.googleapis" not in page and "fonts.gstatic" not in page, route
        assert not re.search(r'<(link|script)[^>]+(href|src)="(https?:)?//', page), route


def test_every_face_is_a_local_woff2_on_disk():
    faces = re.findall(r'@font-face\{font-family:"([^"]+)".*?src:url\("([^"]+)"\)', css("tokens"))
    assert {f for f, _ in faces} == {"Barlow Condensed", "IBM Plex Sans", "IBM Plex Mono"}
    for _, url in faces:
        assert url.startswith("../fonts/") and url.endswith(".woff2")
        assert (STATIC / "css" / url).resolve().is_file(), url


def test_the_licence_ships_with_the_fonts():
    assert "SIL Open Font License" in (STATIC / "fonts" / "OFL.txt").read_text(encoding="utf-8")
