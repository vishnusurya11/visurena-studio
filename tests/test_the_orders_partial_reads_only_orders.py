"""The unit's orders partial reads the orders and nothing else (page experts 2026-10-18, D4 /
backend #6): it ran the whole light unit compute (thumbnail globs, learnings and the run log at
512 KB, every verdict file) on every unit pulse to draw a list from one table."""
from __future__ import annotations

from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio.command_center import app as cc_app


def test_the_orders_partial_never_builds_the_unit(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)

    def boom(*a, **k):
        raise AssertionError("the orders partial built the whole unit")

    monkeypatch.setattr(cc_app, "_unit", boom)
    r = TestClient(app).get(f"/partials/unit/episode/{CODEX}/ep04/orders")
    assert r.status_code == 200 and "Orders for ep04" in r.text
