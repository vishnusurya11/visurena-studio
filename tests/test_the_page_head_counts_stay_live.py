"""The numbers over a list refresh with the list (owner, 2026-10-06: "you still did not fix
it" -- the department rows morphed while the unit counts, the need-you count and the state
tally above them froze).  The department and inbox pages hold ONE live region that contains
the header counts, the tally and the rows; nothing inside it polls on its own (no double
fetch); a focused form holds the morph off.  TestClient over the tmp fixtures, $0."""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import make_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def region(page: str, wrapper: str) -> str:
    start = page.index(f'id="{wrapper}"')
    return page[start:page.index("{% endblock %}") if "{% endblock" in page else len(page)]


def test_the_department_counts_tally_and_rows_share_one_live_region(client):
    page = client.get("/d/episode").text
    live = region(page, "dept-live")
    assert 'data-testid="dept-sub"' in live and 'class="segmented"' in live and 'id="rows"' in live
    assert 'hx-select="#dept-live"' in live and 'pulse:dept:episode' in live


def test_nothing_inside_the_department_region_polls_on_its_own(client):
    page = client.get("/d/episode").text
    live = region(page, "dept-live")
    assert len(re.findall(r"hx-trigger=", live)) == 1


def test_the_inbox_counts_and_cards_share_one_live_region(client):
    page = client.get("/inbox").text
    live = region(page, "inbox-live")
    assert "waiting" in live and 'id="attention"' in live and 'hx-select="#inbox-live"' in live
    assert len(re.findall(r"hx-trigger=", live)) == 1


def test_a_focused_filter_holds_the_morph_off(client):
    page = client.get("/d/episode").text
    assert "[!document.activeElement.closest('#dept-live form,#dept-live select')]" in page
