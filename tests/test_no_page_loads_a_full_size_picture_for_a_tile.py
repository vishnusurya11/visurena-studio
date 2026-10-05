"""Every picture the board draws as a tile, a take poster or a contact strip
comes through `/thumb/{codex}/{160|320}/…` (premium board plan P0.1, research
08 §2 and 10 §3): the ep12 unit page pulled 36.4 MB of full-size PNG for
24 panels and 24 posters of 120 px.  `/lib/` stays only for the one `<video
src>`, downloads and "open file" links.  A lightbox's full picture sits in a
`<template>`: the browser fetches nothing from it until it is opened."""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio.command_center import library_paths, unit_view

TEMPLATES = Path(__file__).resolve().parents[1] / "studio" / "command_center" / "templates"
IMG_LIB = re.compile(r"""<img\b[^>]*\bsrc=["']/lib/""", re.I)
POSTER_LIB = re.compile(r"""\bposter=["']/lib/""", re.I)
PICTURE_URLS = re.compile(r"""<img\b[^>]*\bsrc=["']([^"']*)|\bposter=["']([^"']*)""", re.I)
LIGHTBOX = re.compile(r"<template\b.*?</template>", re.S | re.I)


def test_no_template_points_an_img_or_a_poster_at_lib():
    offenders = [p.name for p in sorted(TEMPLATES.glob("*.html"))
                 if IMG_LIB.search(p.read_text(encoding="utf-8")) or POSTER_LIB.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


@pytest.fixture()
def page(tmp_path, monkeypatch):
    """ep04 rendered like ep12: panels, a contact strip, masters, and two takes."""
    app = make_app(tmp_path, monkeypatch)
    takes = tmp_path / "library" / f"{CODEX}_a-book" / "episodes" / "ep04" / "takes" / "r2v"
    takes.mkdir(parents=True)
    for name in ("T00.mp4", "T01.mp4"):
        (takes / name).write_bytes(b"mp4")
    return TestClient(app).get(f"/d/episode/{CODEX}/ep04").text


def picture_urls(html: str) -> list[str]:
    """Every <img src> and poster= outside a lightbox <template>."""
    return [a or b for a, b in PICTURE_URLS.findall(LIGHTBOX.sub("", html))]


def test_every_tile_poster_and_strip_on_the_unit_page_is_a_thumb(page):
    urls = picture_urls(page)
    assert len(urls) == 4  # 2 panels, 2 posters; with takes on disk the strip is a link
    assert [u for u in urls if not u.startswith(f"/thumb/{CODEX}/")] == []
    assert f'poster="/thumb/{CODEX}/320/episodes/ep04/storyboard/shot_00.png?v=' in page


def test_the_video_and_the_open_file_links_stay_on_lib(page):
    assert f'src="/lib/{CODEX}/episodes/ep04/takes/r2v/T00.mp4"' in page
    assert f'src="/lib/{CODEX}/episodes/ep04/cut/master_iter2.mp4"' in page


@pytest.mark.parametrize(("tile_px", "width"), [(40, 160), (80, 160), (81, 320), (120, 320), (400, 320)])
def test_the_thumb_width_is_160_for_a_small_tile_else_320(tile_px, width):
    assert library_paths.thumb_width(tile_px) == width


def test_the_thumb_url_names_the_codex_the_width_and_the_picture():
    assert library_paths.thumb_url(CODEX, "episodes/ep04/storyboard/shot_00.png", 120, "?v=1") == \
        f"/thumb/{CODEX}/320/episodes/ep04/storyboard/shot_00.png?v=1"
    assert library_paths.thumb_url(CODEX, "a/b.png", 64) == f"/thumb/{CODEX}/160/a/b.png"


def test_the_stamp_changes_when_the_picture_does(tmp_path):
    pic = tmp_path / "p.png"
    pic.write_bytes(b"a")
    first = library_paths.stamp(pic)
    os.utime(pic, ns=(1, 10**18))
    assert first.startswith("?v=") and library_paths.stamp(pic) != first
    assert library_paths.stamp(tmp_path / "missing.png") == ""


def test_a_tile_gets_a_versioned_thumb_and_keeps_its_lib_url(tmp_path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "shot_00.png").write_bytes(b"png")
    [t] = unit_view.with_thumbs(CODEX, tmp_path, [{"rel": "s/shot_00.png", "url": f"/lib/{CODEX}/s/shot_00.png"}])
    assert t["thumb"].startswith(f"/thumb/{CODEX}/320/s/shot_00.png?v=") and t["url"].startswith("/lib/")
