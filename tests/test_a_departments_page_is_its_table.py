"""A department page (report D §5c) is ITS table: every unit across books,
attention first, with the state glyph, step and progress, attempts, gpu and
the gates.yaml verdict strip.  The table is an htmx partial on a 10 s poll;
a stage the registry does not know is a plain 404."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio.command_center import views


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_the_page_is_the_departments_rows_in_attention_order(client):
    page = client.get("/d/episode").text
    assert page.index("ep05") < page.index("ep04") < page.index("ep07") < page.index("ep03") < page.index("ep06")
    assert "5 units" in page and "shoot" in page and "18/25" in page


def test_the_rows_carry_the_verdict_strip_in_gates_order(client):
    page = client.get("/d/episode").text
    for gate in views.gate_order("episode"):
        assert gate in page
    assert "judge:plan@1" in page and "⚑1" in page


def test_the_table_polls_every_ten_seconds_and_keeps_its_filters(client):
    page = client.get("/d/episode?book=" + CODEX + "&state=failed").text
    assert 'hx-trigger="every 10s [' in page  # paused while a row's form has the focus (C11)
    assert "document.activeElement.closest(&#39;#rows form&#39;)" in page or "activeElement.closest('#rows form')" in page
    assert f'hx-get="/partials/d/episode?book={CODEX}&amp;state=failed"' in page
    assert "ep05" in page and "ep04" not in page


def test_the_partial_and_the_page_render_the_same_rows(client):
    page = client.get("/d/episode").text
    partial = client.get("/partials/d/episode").text
    assert "<html" not in partial
    for unit in ("ep03", "ep04", "ep05", "ep06", "ep07"):
        assert unit in page and unit in partial


def test_a_unit_links_to_its_page_and_wraps_for_a_phone(client):
    page = client.get("/d/episode").text
    assert f'href="/d/episode/{CODEX}/ep04"' in page and 'class="tbl-wrap"' in page


def test_an_unknown_department_is_a_plain_404(client):
    response = client.get("/d/publish")
    assert response.status_code == 404 and "not a department" in response.text
    assert client.get("/partials/d/publish").status_code == 404
