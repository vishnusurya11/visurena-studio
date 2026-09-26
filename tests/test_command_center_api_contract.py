"""The JSON twins are the contract (report D §3): each `/api/*.json` route
answers with a pydantic response model over the same view-model its partial
renders, so a page, its partial and its JSON show the same rows.  The
top-level `command_center.py --check` builds the app and prints its routes
without serving; the DB it opens is read-only."""
from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app, make_db, make_library, make_logs
from studio.command_center import app as cc_app, models

ROOT = Path(__file__).resolve().parents[1]


def _load_command_center_py():
    spec = importlib.util.spec_from_file_location("command_center_cli", ROOT / "command_center.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_the_floor_json_validates_and_matches_its_partial(client):
    body = client.get("/api/floor.json").json()
    floor = models.Floor.model_validate(body)
    assert [r.unit for r in floor.running] == ["ep04"] and floor.running[0].progress == "18/25"
    assert [r.unit for r in floor.next] == ["ep06"]
    partial = client.get("/partials/floor").text
    assert floor.running[0].run_id in partial


def test_the_department_json_validates_and_carries_the_strip(client):
    body = client.get("/api/d/episode.json").json()
    dept = models.Department.model_validate(body)
    assert dept.stage == "episode" and [r.unit for r in dept.rows] == ["ep05", "ep04", "ep07", "ep03", "ep06"]
    ep04 = dept.rows[1]
    assert ep04.strip[0].gate == "PLAN" and ep04.strip[0].by == "judge:plan@1"
    assert ep04.glyph == "●" and ep04.css == "blue" and ep04.step_name == "shoot"
    assert client.get("/api/d/publish.json").status_code == 404


def test_the_department_json_takes_the_same_filters_as_the_page(client):
    body = client.get("/api/d/episode.json?state=failed").json()
    assert [r["unit"] for r in body["rows"]] == ["ep05"]


def test_the_unit_json_validates(client):
    body = client.get(f"/api/unit/episode/{CODEX}/ep04.json").json()
    unit = models.Unit.model_validate(body)
    assert unit.row.unit == "ep04" and unit.running is True
    assert [s.step_id for s in unit.steps][:3] == ["01", "02", "03"]
    assert unit.verdicts[0].gate == "PLAN" and unit.thumbnails[0].kind == "panels"
    assert len(unit.learnings) == 8 and unit.log[0]["level"] == "WARNING"
    assert client.get(f"/api/unit/episode/{CODEX}/ep99.json").status_code == 404


def test_the_json_and_the_page_show_the_same_rows(client):
    rows = [r["unit"] for r in client.get("/api/d/episode.json").json()["rows"]]
    page = client.get("/d/episode").text
    positions = [page.index(f">{unit}<") for unit in rows]
    assert positions == sorted(positions)


def test_the_factory_opens_the_db_read_only(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    conn = cc_app.readonly_factory(make_db(tmp_path, library))()
    assert conn.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 6
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM work_orders")
    conn.close()


def test_check_prints_the_routes_without_serving(tmp_path, monkeypatch, capsys):
    library = make_library(tmp_path, monkeypatch)
    path = make_db(tmp_path, library)
    cli = _load_command_center_py()
    served = []
    code = cli.main(["--check", "--db", str(path), "--library", str(library)], serve=served.append)
    out = capsys.readouterr().out
    assert code == 0 and served == []
    for route in ("GET /", "GET /floor", "GET /d/{stage}", "GET /d/{stage}/{codex}/{unit}", "GET /b/{codex}",
                  "GET /org", "GET /partials/floor", "GET /api/floor.json", "GET /lib/{codex}/{path:path}"):
        assert route in out, route


def test_serving_binds_the_loopback_only(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    path = make_db(tmp_path, library)
    cli = _load_command_center_py()
    calls = []
    cli.main(["--port", "8701", "--db", str(path), "--library", str(library)],
             serve=lambda app, **kw: calls.append(kw))
    assert calls == [{"host": "127.0.0.1", "port": 8701, "log_level": "warning"}]


def test_an_included_router_is_listed_route_by_route():
    from fastapi import APIRouter, FastAPI
    cli = _load_command_center_py()
    inner = APIRouter()
    inner.get("/x")(lambda: 1)
    app = FastAPI()
    app.include_router(inner)
    assert "GET /x" in cli.routes(app)
