"""Every sidebar item is a real address (panel ruling 1.4): `/inbox` is "Needs
you" as a page, listing exactly `views.inbox_count()` units, and every href in
`shell.PAGES` answers 200."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import make_app
from studio.command_center import app as cc_app
from studio.command_center import shell, views


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


@pytest.mark.parametrize("href", [p[0] for p in shell.PAGES] + ["/inbox"])
def test_every_page_in_the_sidebar_answers(client, href):
    assert client.get(href).status_code == 200


def test_the_inbox_lists_what_needs_you(client):
    page = client.get("/inbox").text
    for unit in ("ep05", "ep07", "ep03"):
        assert unit in page


def test_the_inbox_count_is_the_attention_list(client):
    conn = client.app.state.conn_factory()
    assert views.inbox_count(conn) == len(views.attention(conn)) == 3


def test_without_its_template_the_inbox_still_answers(client, monkeypatch):
    monkeypatch.setattr(cc_app, "INBOX_TEMPLATE", "no_such_inbox.html")
    response = client.get("/inbox")
    assert response.status_code == 200 and "ep05" in response.text and "Needs you" in response.text
