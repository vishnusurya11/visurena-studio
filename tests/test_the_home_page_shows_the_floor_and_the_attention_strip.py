"""The studio home (report D §5a): the first 120 px answer "running? stuck?
needs me?" -- the floor strip and the attention strip -- then a lane per
registered department, today's steps and the legend.  The strips are htmx
partials on a 2 s poll; the lanes swap every 10 s; nothing here spawns a server."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from board_html import polls
from command_center_fixtures import CODEX, RUN, make_app
from studio import registry
from studio.command_center import views


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_the_home_page_shows_the_running_row_and_what_needs_you(client):
    page = client.get("/").text
    assert "ON THE FLOOR" in page and "ep04" in page and "18/25" in page and "shoot" in page
    assert "NEEDS YOU" in page and "ep05" in page and "✕" in page and "ep07" in page and "↩" in page
    assert RUN in page


def test_the_strips_poll_every_two_seconds_and_the_lanes_every_ten(client):
    page = client.get("/").text
    assert polls(page, "/partials/floor") == "every 2s" and polls(page, "/partials/attention") == "every 2s"
    assert polls(page, "/partials/lanes") == "every 10s"
    assert "http-equiv" not in page and '/static/htmx.min.js' in page


def test_every_department_has_a_lane_that_links_to_its_page(client):
    page = client.get("/").text
    for stage in registry.stage_names():
        assert f'href="/d/{stage}"' in page
    assert "⚑1" in page and "●1" in page and "✕1" in page


def test_the_partials_render_the_same_rows_as_the_page(client):
    floor = client.get("/partials/floor").text
    attention = client.get("/partials/attention").text
    assert "ep04" in floor and "18/25" in floor and "ep05" not in floor
    assert "ep05" in attention and "ep07" in attention and "ep04" not in attention
    assert "<html" not in floor and "<html" not in attention


def test_today_and_the_legend_are_on_the_home_page(client):
    page = client.get("/").text
    assert "TODAY" in page and "refs" in page
    legend = page[page.index('data-testid="legend"'):]
    for state in views.GLYPHS:
        assert f'data-state="{state}"' in legend and f"{state}</span>" in legend


@pytest.mark.parametrize("route", ["/queue", "/floor"])
def test_the_queue_page_lists_now_next_and_held(client, route):
    page = client.get(route).text
    assert "NOW" in page and "NEXT" in page and "HELD" in page and "ep06" in page
    assert "derived" in page


def test_the_buttons_post_orders_since_c11(client):
    page = client.get("/d/episode").text
    assert 'title="C11"' not in page and 'hx-post="/act/hold"' in page


def test_the_org_chart_is_served_unchanged(client, tmp_path):
    response = client.get("/org")
    assert response.status_code == 200 and "Visurena Story Department" in response.text
