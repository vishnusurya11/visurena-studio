"""The unit page (panel ruling PKG-5 5.1, 5.3-5.8; SPEC_v3): every picture, take,
grid, master, verdict and file is a [data-view] element the in-page Viewer opens;
polled regions refresh on the unit's pulse and morph, never on a timer and never
by outerHTML; no player sits inside a polled region and the master player is
preserved, unmuted and drawn with nothing over it; the page knows its siblings;
templates write no JS; media.js owns playback (one at a time, every dialog's
close stops its media).  TestClient over the tmp fixtures, $0."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app

ROOT = Path(__file__).resolve().parents[1] / "studio" / "command_center"
TEMPLATES = ROOT / "templates"
UNIT_TEMPLATES = ["unit.html", "_unit_head.html", "_tails.html", "_unit_orders.html"]
MEDIA = (ROOT / "static" / "media.js").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    home = tmp_path / "library" / f"{CODEX}_a-book" / "episodes" / "ep04"
    for rel in ("takes/r2v/T00.mp4", "takes/work/content/T00_0.png", "storyboard/grids/ep04_road_2x2.png"):
        (home / rel).parent.mkdir(parents=True, exist_ok=True)
        (home / rel).write_bytes(b"x")
    return TestClient(app)


@pytest.fixture()
def page(client):
    return client.get(f"/d/episode/{CODEX}/ep04").text


def tags(html: str, attr: str) -> list[str]:
    return re.findall(rf"<[a-z]+\b[^>]*\b{attr}=\"[^\"]*\"[^>]*>", html)


# --- 5.3 pulse, morph, no timers ---


@pytest.mark.parametrize("name", UNIT_TEMPLATES)
def test_no_unit_template_polls_on_a_timer_or_swaps_outer_html(name):
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    assert "every " not in text and "outerHTML" not in text


@pytest.mark.parametrize("name", UNIT_TEMPLATES)
def test_templates_write_no_js(name):
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    assert not re.search(r"<script(?![^>]*\bsrc=)", text)


def test_the_head_orders_and_tails_refresh_on_the_units_pulse(page):
    key = f'hx-trigger="pulse:unit:episode/{CODEX}/ep04'
    for part in ("head", "orders", "tails"):
        tag = next(t for t in tags(page, "hx-get") if f"/ep04/{part}\"" in t)
        assert key in tag and "from:body" in tag and 'hx-swap="morph:innerHTML"' in tag, part


def test_the_head_partial_is_the_inside_of_the_head(client):
    head = client.get(f"/partials/unit/episode/{CODEX}/ep04/head").text
    assert "<html" not in head and '<section id="head"' not in head and "09 shoot" in head


def test_no_player_sits_inside_a_polled_region(page):
    for m in re.finditer(r"<(section|div)\b[^>]*hx-get=\"[^\"]*\"[^>]*>", page):
        tag = m.group(1)
        depth, i, end = 1, m.end(), m.end()
        for t in re.finditer(rf"<(/?){tag}\b", page[m.end():]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                end = m.end() + t.start()
                break
        assert "<video" not in page[m.end():end]


def test_the_master_player_is_preserved_unmuted_and_bare(page):
    player = re.search(r'<div class="player[^"]*" id="master-player"[^>]*>(.*?)</div>', page, re.S)
    assert player and 'hx-preserve' in player.group(0)
    video = re.search(r"<video\b[^>]*>", player.group(1)).group(0)
    assert " muted" not in video and "controls" in video
    assert re.sub(r"<video\b.*?</video>", "", player.group(1), flags=re.S).strip() == ""


# --- the Viewer opens everything ---


def test_the_body_names_the_unit_for_the_viewer(page):
    assert f'data-codex="{CODEX}"' in page and 'data-stage="episode"' in page and 'data-unit="ep04"' in page


def test_shot_cards_open_the_shots_sequence(page):
    card = re.search(r'<article class="shot[^"]*" id="shot-00".*?</article>', page, re.S).group(0)
    assert 'data-view="takes/r2v/T00.mp4" data-set="shots" data-shot="0" data-depth="take"' in card
    assert 'data-view="storyboard/shot_00.png" data-set="shots" data-shot="0" data-depth="panel"' in card
    assert f"/thumb/{CODEX}/320/episodes/ep04/takes/work/content/T00_0.png" in card


def test_grids_masters_verdicts_and_files_are_viewer_links(page):
    assert 'data-view="storyboard/grids/ep04_road_2x2.png" data-set="grids"' in page
    assert 'data-view="cut/master_iter2.mp4" data-set="masters"' in page
    assert 'data-view="plan.verdict.json" data-set="files"' in page
    assert 'data-view="learnings.jsonl" data-set="files"' in page


def test_the_activity_window_keeps_a_full_log_button(page):
    act = page[page.index('id="activity"'):]
    assert 'id="act-full"' in act and 'data-view="_logs/' in act


def test_the_files_section_groups_the_folder(page):
    files = page[page.index('id="files"'):page.index('id="activity"')]
    assert "Storyboard" in files and "Master" in files and "Run records and logs" in files


# --- 5.4 siblings ---


def test_the_sibling_nav_links_the_neighbours(page):
    assert f'rel="prev" href="/d/episode/{CODEX}/ep03" data-key="["' in page
    assert f'rel="next" href="/d/episode/{CODEX}/ep05" data-key="]"' in page
    assert f'<link rel="prefetch" href="/d/episode/{CODEX}/ep05">' in page


# --- 5.8 a new master iteration ---


def test_the_head_names_the_newest_master_for_the_badge(client):
    head = client.get(f"/partials/unit/episode/{CODEX}/ep04/head").text
    assert 'data-latest-master="cut/master_iter' in head


# --- 5.1 media.js ---


def test_media_js_keeps_one_player_and_stops_media_on_every_dialog_close():
    assert "addEventListener('play'" in MEDIA and "addEventListener('close'" in MEDIA
    assert "checkVisibility" in MEDIA and "'waiting'" in MEDIA and "'ended'" in MEDIA
    assert "sound blocked" in MEDIA and "NotAllowedError" in MEDIA


def test_the_live_master_is_not_muted():
    live = (TEMPLATES / "_unit_live.html").read_text(encoding="utf-8")
    video = re.search(r"<video\b[^>]*>", live).group(0)
    assert " muted" not in video


def test_media_js_is_loaded_once(page):
    assert page.count("/static/media.js") == 1
