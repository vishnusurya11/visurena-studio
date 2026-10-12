"""Board review 2026-10-12, part 01 (bugs B01-B13, S1) and part 04's question on
`acknowledge`.  Each test names the bug it pins.  $0: tmp DB, tmp library."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, OTHER, make_app, make_writable_app
from studio import db
from studio.command_center import app as cc_app
from studio.command_center import unit_parse as up
from studio.command_center import unit_view, views, viz

LOCAL = {"Origin": "http://127.0.0.1:8700"}
STATIC = Path(cc_app.__file__).parent / "static"
TEMPLATES = Path(cc_app.__file__).parent / "templates"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def _sql(tmp_path, *statements):
    conn = sqlite3.connect(tmp_path / "t.db")
    for s in statements:
        conn.execute(s)
    conn.commit()
    conn.close()


# B01: the side panel lists only the unit's own files


def test_b01_a_book_unit_offers_no_episode_files(client):
    html = client.get(f"/d/refs/{CODEX}/main").text
    assert 'data-view="plan.json"' not in html and 'data-view="timing.jsonl"' not in html


def test_b01_an_episode_offers_the_files_it_has(client):
    html = client.get(f"/d/episode/{CODEX}/ep04").text
    assert 'data-view="learnings.jsonl"' in html and 'data-view="timing.jsonl"' in html


# B02: the state chips count the book shown


def test_b02_the_counts_follow_the_book_filter(tmp_path, monkeypatch):
    make_app(tmp_path, monkeypatch)
    conn = db.get_connection(tmp_path / "t.db")
    assert views.department(conn, "episode", book=OTHER)["counts"] == {}
    assert sum(views.department(conn, "episode", book=CODEX)["counts"].values()) == 5


# B03, B04: one clock, the machine's


def test_b03_a_unit_stamp_is_printed_in_local_time():
    ts = "2026-10-10T23:13:06Z"
    local = datetime(2026, 10, 10, 23, 13, 6, tzinfo=timezone.utc).astimezone()
    assert unit_view.day_hhmm(ts) == local.strftime("%d %b %H:%M") and unit_view.hhmm(ts) == local.strftime("%H:%M")


def test_b04_today_starts_at_local_midnight():
    pdt = timezone(timedelta(hours=-7))
    assert views.local_day_start(datetime(2026, 10, 12, 18, 0, tzinfo=pdt)) == "2026-10-12T07:00:00"
    assert views.local_day_start(datetime(2026, 10, 12, 1, 0, tzinfo=pdt)) == "2026-10-12T07:00:00"


# B05, B06, B07: the error page


@pytest.mark.parametrize("path,parent", [("/d/episode/x/ep99", "/d/episode"), ("/d/episode/x", "/d/episode"),
                                         ("/d/nope", None), ("/api/x/y", None), ("/b/123", "/books"), ("/zzz", None)])
def test_b05_up_goes_only_to_a_page_that_exists(path, parent):
    assert cc_app.error_parent(path) == parent


def test_b05_the_404_card_offers_the_department(client):
    html = client.get(f"/d/episode/{CODEX}/ep99").text
    assert f'href="/d/episode"' in html and f'href="/d/episode/{CODEX}"' not in html


@pytest.mark.parametrize("path", ["/api/unit/episode/{c}/ep99.json", "/viewer/{c}/episode/ep99.json"])
def test_b06_a_json_route_answers_json_when_missing(client, path):
    r = client.get(path.format(c=CODEX))
    assert r.status_code == 404 and r.headers["content-type"].startswith("application/json") and "detail" in r.json()


def test_b07_the_palette_does_not_remember_an_error_page():
    js = (STATIC / "board.js").read_text(encoding="utf-8")
    body = js[js.index("function remember()"):js.index("function pool()")]
    assert "data-testid=error" in body.replace('"', "").replace("'", "")


# B08, B09, B10, B11


def test_b08_a_chip_title_reads_as_a_sentence():
    assert viz.chip_title("takes", 1, "flagged") == "1 fault, flagged"
    assert viz.chip_title("panels", 531, "") == "531 faults"
    assert viz.chip_title("master", 0, "reject") == "reject"


def test_b09_one_unit_is_one_unit(client):
    html = client.get("/d/refs").text
    assert "<b>1</b> units" not in html and "<b>1</b> unit" in html


def test_b09_every_count_template_pluralises():
    for name in ("_rows.html", "department.html", "books.html", "unit.html"):
        text = (TEMPLATES / name).read_text(encoding="utf-8")
        assert "</b> units ·" not in text and "}} files ·" not in text, name


def test_b10_a_pass_without_a_wall_has_no_empty_slot():
    text = (TEMPLATES / "unit.html").read_text(encoding="utf-8")
    assert "{{ p.day }} · {{ p.wall }} ·" not in text and "{% if p.wall %}" in text


def test_b11_a_value_that_rose_is_worse_and_one_that_held_is_stuck():
    rows = [{"started": f"2026-09-2{i}T00:00:00+00:00", "ended": f"2026-09-2{i}T12:00:00+00:00"} for i in range(1, 4)]

    def trend(values):
        learn = [{"gate": "budget", "measured": v, "ts": f"2026-09-2{i + 1}T06:00:00Z"} for i, v in enumerate(values)]
        return up.gate_trend(learn, rows)[0]["direction"]
    assert (trend([5.0, 4.0]), trend([4.0, 4.0]), trend([-2992.81, 402.61])) == ("improving", "stuck", "worse")


# B13 / A7: no red zero


def test_b13_an_empty_needs_you_is_not_red(tmp_path, monkeypatch):
    c = TestClient(make_app(tmp_path, monkeypatch))
    _sql(tmp_path, "UPDATE work_orders SET state = 'done', flags = 0, lease_until = NULL")
    html = c.get("/").text
    assert 'class="count hot"' not in html and 'data-n="0"' in html


# S1: a thumb without its version is not cached for a year


def _png(path):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), (40, 80, 120)).save(path)


def test_s1_only_a_versioned_thumb_is_immutable(tmp_path, monkeypatch):
    c = TestClient(make_app(tmp_path, monkeypatch))
    _png(tmp_path / "library" / f"{CODEX}_a-book" / "refs" / "sheet.png")
    plain = c.get(f"/thumb/{CODEX}/320/refs/sheet.png")
    versioned = c.get(f"/thumb/{CODEX}/320/refs/sheet.png?v=123")
    assert plain.status_code == 200 and "immutable" not in plain.headers["cache-control"]
    assert "immutable" in versioned.headers["cache-control"]


# 04 side note: does /act/acknowledge persist under the live table's old CHECK?


def test_an_acknowledge_persists_through_the_route_under_the_old_check(tmp_path, monkeypatch):
    app, path = make_writable_app(tmp_path, monkeypatch)
    _sql(tmp_path, "DROP TABLE orders",
         "CREATE TABLE orders (id INTEGER PRIMARY KEY, ts TEXT NOT NULL,"
         " kind TEXT NOT NULL CHECK (kind IN ('hold','lift','redo','bump','retry','requeue')),"
         " scope TEXT NOT NULL CHECK (scope IN ('studio','book','unit')), codex_id TEXT, stage TEXT, unit TEXT,"
         " step_id TEXT, note TEXT, by TEXT NOT NULL DEFAULT 'owner', taken_ts TEXT, taken_by_run TEXT)")
    r = TestClient(app).post("/act/acknowledge", data={"codex": CODEX, "stage": "episode", "unit": "ep03"},
                             headers=LOCAL)
    assert r.status_code == 200, r.text
    conn = sqlite3.connect(path)
    assert conn.execute("SELECT kind, unit FROM orders").fetchall() == [("acknowledge", "ep03")]
    assert "'acknowledge'" not in conn.execute("SELECT sql FROM sqlite_master WHERE name = 'orders'").fetchone()[0]
