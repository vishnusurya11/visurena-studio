"""The Viewer's read routes on a tmp book: JSON slices, run-log pages, a unit's
files and its sequences -- and every way out of the book refused with a 404."""
from __future__ import annotations

import gzip
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from studio import db
from studio.command_center import app as cc_app
from studio.command_center import viewer_routes as vr
from viewer_fixtures import CODEX, RUN, UNIT, make_book


def make_viewer_app(tmp_path) -> FastAPI:
    """The router alone over the tmp book, tmp logs and a DB with one run of ep04."""
    library, logs = make_book(tmp_path)
    path = tmp_path / "t.db"
    conn = db.get_connection(path)
    db.init_db(conn)
    db.insert_codex(conn, "A Book", codex_id=CODEX)
    db.add_event(conn, CODEX, "episode", "01", "started", run_id=RUN, unit=UNIT)
    conn.close()
    app = FastAPI()
    app.state.library, app.state.logs = library, logs
    app.state.conn_factory = cc_app.readonly_factory(path)
    app.include_router(vr.router)
    return app


@pytest.fixture(scope="module")
def viewer_app(tmp_path_factory) -> FastAPI:
    """One app per module: every route here only reads (init_db alone takes seconds)."""
    return make_viewer_app(tmp_path_factory.mktemp("viewer"))


@pytest.fixture
def client(viewer_app) -> TestClient:
    return TestClient(viewer_app)


# --- /json ---


def test_json_answers_the_file_as_it_is(client):
    r = client.get(f"/json/{CODEX}/episodes/{UNIT}/plan.json")
    assert r.status_code == 200 and r.json()["shots"][0]["setup"] == "woods"


def test_json_slices_by_pointer(client):
    r = client.get(f"/json/{CODEX}/episodes/{UNIT}/plan.json", params={"ptr": "/shots/2/faces"})
    assert r.json() == ["captain"]


def test_json_pointer_to_nothing_is_a_404(client):
    assert client.get(f"/json/{CODEX}/episodes/{UNIT}/plan.json", params={"ptr": "/shots/9"}).status_code == 404


def test_jsonl_slices_by_rows(client):
    r = client.get(f"/json/{CODEX}/refs/pack.jsonl", params={"rows": "2-4"})
    assert [json.loads(l)["seed"] for l in r.text.splitlines()] == [2, 3, 4]


def test_a_malformed_row_range_is_a_404(client):
    assert client.get(f"/json/{CODEX}/refs/pack.jsonl", params={"rows": "4-2"}).status_code == 404


def test_json_over_the_cap_is_413_with_the_raw_link(client):
    r = client.get(f"/json/{CODEX}/episodes/{UNIT}/big.json")
    assert r.status_code == 413 and r.json()["raw"] == f"/lib/{CODEX}/episodes/{UNIT}/big.json"


def test_a_slice_of_a_big_file_is_served(client):
    r = client.get(f"/json/{CODEX}/episodes/{UNIT}/big.json", params={"ptr": ""})
    assert r.status_code == 413
    assert client.get(f"/json/{CODEX}/episodes/{UNIT}/plan.json", params={"ptr": ""}).status_code == 200


def test_json_is_gzipped_when_asked(client):
    r = client.get(f"/json/{CODEX}/refs/pack.jsonl", headers={"Accept-Encoding": "gzip"})
    assert r.headers.get("content-encoding") == "gzip" and len(r.text.splitlines()) == 50


@pytest.mark.parametrize("path", [
    f"/json/{CODEX}/episodes/{UNIT}/../../../20260901000002_other/secret.json",
    f"/json/{CODEX}/episodes/{UNIT}/%2e%2e/%2e%2e/%2e%2e/20260901000002_other/secret.json",
    f"/json/{CODEX}/episodes/{UNIT}/plan.py",
    f"/json/{CODEX}/episodes/{UNIT}/storyboard/shot_00.png",
    "/json/2026/episodes/ep04/plan.json",
    f"/json/{CODEX}/episodes/{UNIT}/nope.json",
])
def test_json_refuses_anything_but_a_json_file_of_the_book(client, path):
    assert client.get(path).status_code == 404


# --- /log ---


def test_log_answers_the_last_500_lines(client):
    r = client.get(f"/log/{CODEX}/{RUN}.log")
    lines = r.text.splitlines()
    assert len(lines) == 500 and json.loads(lines[-1])["msg"] == "row 1199"
    assert r.headers["x-log-first"] == "700" and r.headers["x-log-total"] == "1200"


def test_log_pages_back_with_before(client):
    r = client.get(f"/log/{CODEX}/{RUN}.log", params={"before": 700, "n": 10})
    assert json.loads(r.text.splitlines()[0])["msg"] == "row 690" and r.headers["x-log-first"] == "690"


def test_log_cuts_a_long_line(client):
    line = client.get(f"/log/{CODEX}/{CODEX}__episode__20260926090000.log").text.splitlines()[0]
    assert len(line) < 2100 and line.endswith("more chars]")


def test_log_reads_a_unit_log_in_the_book(client):
    assert client.get(f"/log/{CODEX}/episodes/{UNIT}/drive_run01.log").text.splitlines()[-1] == "line 29"


@pytest.mark.parametrize("name", [
    f"20260901000002__episode__20260926010203.log",
    f"{CODEX}__episode__20260926010203.txt",
    f"{CODEX}__..__20260926010203.log",
    f"{CODEX}__episode__20990101000000.log",
    f"episodes/{UNIT}/plan.json",
    "../logs/x.log",
])
def test_log_refuses_a_name_off_the_log_root(client, name):
    assert client.get(f"/log/{CODEX}/{name}").status_code == 404


# --- /files ---


def test_files_group_the_unit_by_kind_with_book_paths(client):
    body = client.get(f"/files/{CODEX}/episodes/{UNIT}").json()
    g = body["groups"]
    assert f"episodes/{UNIT}/storyboard/shot_00.png" in [f["rel"] for f in g["image"]]
    assert f"episodes/{UNIT}/takes/r2v/T00.mp4" in [f["rel"] for f in g["video"]]
    assert [f["rel"] for f in g["log"]] == [f"episodes/{UNIT}/drive_run01.log"]


@pytest.mark.parametrize("rel", ["", "..", "episodes/ep99", f"episodes/{UNIT}/plan.json", "episodes/../.."])
def test_files_refuse_anything_but_a_folder_of_the_book(client, rel):
    assert client.get(f"/files/{CODEX}/{rel}").status_code == 404


# --- /viewer ---


def test_viewer_answers_the_five_sequences(client):
    body = client.get(f"/viewer/{CODEX}/episode/{UNIT}.json").json()
    assert body["home"] == f"episodes/{UNIT}" and [s["id"] for s in body["seqs"]] == \
        ["shots", "takes", "grids", "masters", "files"]
    assert body["logs"][0]["name"] == f"{RUN}.log" and body["seqs"][4]["items"][-1]["id"] == f"_logs/{RUN}.log"


def test_viewer_is_gzipped_when_asked(client):
    r = client.get(f"/viewer/{CODEX}/episode/{UNIT}.json", headers={"Accept-Encoding": "gzip"})
    assert r.headers.get("content-encoding") == "gzip" and r.json()["unit"] == UNIT


@pytest.mark.parametrize("path", ["/viewer/{c}/episode/ep99.json", "/viewer/{c}/nostage/ep04.json",
                                  "/viewer/2026/episode/ep04.json", "/viewer/{c}/episode/..%2f..%2fx.json"])
def test_viewer_refuses_an_unknown_unit(client, path):
    assert client.get(path.format(c=CODEX)).status_code == 404


# --- helpers ---


def test_json_pointer_unescapes_tokens():
    assert vr.json_pointer({"a/b": {"~": [1, 2]}}, "/a~1b/~0/1") == 2
    with pytest.raises(KeyError):
        vr.json_pointer({"a": 1}, "a")


def test_parse_rows_reads_a_closed_and_an_open_range():
    assert vr.parse_rows("2-4") == (2, 5) and vr.parse_rows("3-") == (3, 3 + vr.ROWS_MAX)
    with pytest.raises(ValueError):
        vr.parse_rows("x")


def test_jsonl_rows_skip_blank_lines():
    assert vr.jsonl_rows("a\n\nb\nc\n", 1, 2) == "b\n"


def test_log_page_clamps_before():
    assert vr.log_page(["a", "b", "c"], 99, 2) == (["b", "c"], 1) and vr.log_page(["a"], 0, 5) == ([], 0)


def test_clip_keeps_a_short_line():
    assert vr.clip("short") == "short" and vr.clip("x" * 2500).endswith("[500 more chars]")


def test_tail_text_drops_the_partial_first_line(tmp_path):
    p = tmp_path / "x.log"
    p.write_bytes(b"aaaa\nbbbb\ncccc\n")
    assert vr.tail_text(p, cap=8) == ("cccc\n", True) and vr.tail_text(p)[1] is False


def test_grouped_prefixes_book_paths():
    out = vr.grouped([{"rel": "a.png", "kind": "image"}], "episodes/ep04")
    assert out["image"] == [{"rel": "episodes/ep04/a.png", "kind": "image"}] and out["video"] == []


def test_gzipped_leaves_a_small_body_alone():
    class R:
        headers = {"accept-encoding": "gzip"}
    assert "Content-Encoding" not in vr.gzipped(R(), b"{}", "application/json").headers
    big = vr.gzipped(R(), b"x" * 5000, "text/plain")
    assert gzip.decompress(big.body) == b"x" * 5000


def test_resolve_in_book_refuses_a_symlink_out(tmp_path):
    library, _ = make_book(tmp_path)
    link = library / f"{CODEX}_a-book" / "out.json"
    try:
        link.symlink_to(library / "20260901000002_other" / "secret.json")
    except OSError:
        pytest.skip("no symlink rights on this machine")
    assert vr.resolve_in_book(library, CODEX, "out.json", vr.JSON_SUFFIXES) is None


def test_unit_run_ids_reads_the_events(viewer_app):
    conn = viewer_app.state.conn_factory()
    try:
        assert vr.unit_run_ids(conn, CODEX, "episode", UNIT) == [RUN]
    finally:
        conn.close()


def test_the_board_serves_the_viewer_routes(tmp_path, monkeypatch):
    from command_center_fixtures import CODEX as BOOK, make_app
    board = TestClient(make_app(tmp_path, monkeypatch))
    assert len(board.get(f"/json/{BOOK}/episodes/ep04/learnings.jsonl").text.splitlines()) == 10
    assert board.get(f"/viewer/{BOOK}/episode/ep04.json").json()["seqs"][3]["items"][0]["label"] == "v2"
    assert board.get(f"/json/{BOOK}/../20260901000002_other-book/secret.png").status_code == 404
