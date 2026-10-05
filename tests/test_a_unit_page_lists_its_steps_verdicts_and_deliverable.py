"""A unit page (report D §5d, redesigned in research F) is one row opened with
its folder read from disk: the twelve steps in registry order, the verdicts with
their signers, the deliverable, the pictures the steps already wrote, and the
learnings, log and timing rows in the Activity window.  The head refreshes on the
unit's pulse (panel ruling 5.3, no timer); the tails refresh only while running."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from board_html import polls
from command_center_fixtures import CODEX, RUN, make_app
from studio import registry


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_the_steps_are_chips_in_registry_order(client):
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    names = [e["name"] for e in registry.steps("episode")]
    positions = [page.index(f">{name}<") for name in names]
    assert positions == sorted(positions)
    assert "STEPS" in page and "VERDICTS" in page and "TIMING" in page


def test_the_verdicts_name_their_judge_and_their_file(client):
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    assert "PLAN" in page and "judge:plan@1" in page
    assert f"/lib/{CODEX}/episodes/ep04/plan.verdict.json" in page
    assert "MASTER" in page and "not yet signed" in page


def test_the_pictures_are_thumbs_and_the_master_is_a_lib_url(client):
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    assert f'src="/thumb/{CODEX}/320/episodes/ep04/storyboard/shot_00.png?v=' in page
    assert 'data-view="reports/strip_T00_T05.png" data-set="files"' in page
    assert f'src="/lib/{CODEX}/episodes/ep04/cut/master_iter2.mp4"' in page and "<video" in page
    assert f'src="/lib/{CODEX}/episodes/ep04/cut/master_iter1.mp4"' not in page
    assert 'data-view="cut/master_iter1.mp4" data-set="masters"' in page or "cut/master_iter1.mp4" in page


def test_the_deliverable_is_shown_when_the_row_names_one(client):
    page = client.get(f"/d/episode/{CODEX}/ep03").text
    assert "episodes/ep03/manifest.json" in page and "missing on disk" in page


def test_the_tails_poll_only_while_running(client):
    running = client.get(f"/d/episode/{CODEX}/ep04").text
    assert polls(running, f"/partials/unit/episode/{CODEX}/ep04/tails").startswith(f"pulse:unit:episode/{CODEX}/ep04")
    assert polls(running, f"/partials/unit/episode/{CODEX}/ep04/head").startswith(f"pulse:unit:episode/{CODEX}/ep04")
    assert "MASTER: measured 3.0" in running and RUN in running
    done = client.get(f"/d/episode/{CODEX}/ep03").text
    assert polls(done, f"/partials/unit/episode/{CODEX}/ep03/tails") is None and "/ep03/tails" not in done


def test_the_tails_partial_is_the_same_fragment(client):
    partial = client.get(f"/partials/unit/episode/{CODEX}/ep04/tails").text
    assert "<html" not in partial and "MASTER: measured 3.0" in partial and "keep_best" in partial


def test_an_unknown_unit_is_a_plain_404(client):
    assert client.get(f"/d/episode/{CODEX}/ep99").status_code == 404
    assert client.get(f"/d/publish/{CODEX}/ep04").status_code == 404
    assert client.get(f"/partials/unit/episode/{CODEX}/ep99/tails").status_code == 404
    assert client.get(f"/partials/unit/episode/{CODEX}/ep99/head").status_code == 404
    assert client.get(f"/partials/unit/episode/{CODEX}/ep99/orders").status_code == 404


def test_the_book_page_is_units_across_departments_down(client):
    page = client.get(f"/b/{CODEX}").text
    assert "A Book" in page and "ep04" in page and "main" in page
    for stage in registry.stage_names():
        assert f'href="/d/{stage}"' in page
    assert "▲" in page and "file" in page
    assert client.get("/b/20260901000009").status_code == 404
