"""Partials answer 204 on an unchanged fingerprint (panel ruling C2, 1.2): a
client that already holds a section sends `?v=<fp>`; when it equals the
section's fingerprint now, the answer is 204 with no body -- htmx swaps
nothing -- and a stale `v` gets the fragment."""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio.command_center import app as cc_app
from studio.command_center import pulse

NOW = time.time()

UNIT = f"episode/{CODEX}/ep04"
PARTIALS = [("/partials/floor", "floor"), ("/partials/attention", "attention"),
            ("/partials/needs-you-count", "attention"), ("/partials/orders", "orders"),
            ("/partials/lanes", "lanes"), ("/partials/d/episode", "dept:episode"),
            (f"/partials/unit/{UNIT}/tails", f"unit:{UNIT}"), (f"/partials/unit/{UNIT}/head", f"unit:{UNIT}"),
            (f"/partials/unit/{UNIT}/orders", f"unit:{UNIT}"), (f"/partials/unit/{UNIT}/live", f"unit:{UNIT}")]


@pytest.fixture()
def board(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    app.state.procs = lambda: []
    monkeypatch.setattr(cc_app, "time", SimpleNamespace(time=lambda: NOW))   # no minute boundary mid-test
    return TestClient(app), app


def current(app, key: str) -> str:
    conn = app.state.conn_factory()
    try:
        return pulse.fingerprint(conn, key, NOW)
    finally:
        conn.close()


@pytest.mark.parametrize("route, key", PARTIALS)
def test_an_equal_fingerprint_is_204_and_empty(board, route, key):
    client, app = board
    response = client.get(route, params={"v": current(app, key)})
    assert response.status_code == 204 and response.content == b""


@pytest.mark.parametrize("route, key", PARTIALS)
def test_a_stale_fingerprint_gets_the_fragment(board, route, key):
    response = board[0].get(route, params={"v": "00000000"})
    assert response.status_code == 200


@pytest.mark.parametrize("route, key", PARTIALS[:6])
def test_no_fingerprint_gets_the_fragment(board, route, key):
    response = board[0].get(route)
    assert response.status_code == 200 and response.content


def test_every_partial_route_is_covered():
    routes = {r.path for r in cc_app.router.routes if r.path.startswith("/partials/")}
    covered = {p.replace(UNIT, "{stage}/{codex}/{unit}").replace("/d/episode", "/d/{stage}")
               .replace("unit/{stage}/{codex}/{unit}/live", "unit/episode/{codex}/{unit}/live") for p, _ in PARTIALS}
    assert routes <= covered, routes - covered
