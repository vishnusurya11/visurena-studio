"""Board review 2026-10-12, part 04 (speed), the low-risk top fixes:
#1 read-only connections map the DB (786 ReadFile ops per pulse -> 18);
#2 the publish lookups (uploads.jsonl, the library listing) are read once per mtime;
#4 no sibling prefetch, and hover speculation only on pointerdown;
#5 a page answers 204 before it computes when its fingerprint has not moved;
#6 the Ctrl K unit index is fetched on open, not embedded in every page;
#11 the thumbnail cache is pruned to a size cap.  $0."""
from __future__ import annotations

import json
import os
import time

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio import backfill
from studio.command_center import app as cc_app
from studio.command_center import library_paths, pulse, thumbs, views


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch)), tmp_path


def test_1_a_read_connection_maps_the_db(tmp_path):
    import sqlite3
    sqlite3.connect(tmp_path / "x.db").close()
    conn = cc_app.readonly_factory(tmp_path / "x.db")()
    assert conn.execute("PRAGMA mmap_size").fetchone()[0] >= cc_app.MMAP_BYTES // 2


def test_2_the_library_is_listed_once_per_mtime(tmp_path, monkeypatch):
    (tmp_path / f"{CODEX}_a-book").mkdir()
    calls = []
    real = library_paths._scan
    monkeypatch.setattr(library_paths, "_scan", lambda lib: calls.append(1) or real(lib))
    library_paths._FOLDERS.clear()
    assert library_paths.book_folder(tmp_path, CODEX) == library_paths.book_folder(tmp_path, CODEX)
    assert len(calls) == 1
    time.sleep(0.02)
    (tmp_path / "20990101000000_new").mkdir()
    os.utime(tmp_path, None)
    library_paths.book_folder(tmp_path, CODEX)
    assert len(calls) == 2


def test_2_the_upload_ledger_is_parsed_once_per_mtime(tmp_path, monkeypatch):
    path = tmp_path / "uploads.jsonl"
    path.write_text(json.dumps({"episode": 1, "video_id": "a", "sha8": "x"}) + "\n", encoding="utf-8")
    calls = []
    real = backfill._parse_uploads
    monkeypatch.setattr(backfill, "_parse_uploads", lambda p: calls.append(1) or real(p))
    backfill._UPLOADS.clear()
    assert backfill.upload_rows(tmp_path, 1) == backfill.upload_rows(tmp_path, 1) and len(calls) == 1
    path.write_text(path.read_text() + json.dumps({"episode": 1, "video_id": "b", "sha8": "y"}) + "\n",
                    encoding="utf-8")
    os.utime(path, (time.time() + 5, time.time() + 5))
    assert len(backfill.upload_rows(tmp_path, 1)) == 2 and len(calls) == 2


def test_4_no_page_prefetches_its_siblings(client):
    c, _ = client
    html = c.get(f"/d/episode/{CODEX}/ep04").text
    assert 'rel="prefetch"' not in html and '"eagerness":"conservative"' in html


def test_5_a_department_answers_204_before_it_computes(client, monkeypatch):
    c, tmp_path = client
    conn = c.app.state.conn_factory()
    fp = pulse.fingerprint(conn, "dept:episode", time.time())
    book_fp = pulse.fingerprint(conn, f"book:{CODEX}", time.time())
    conn.close()
    monkeypatch.setattr(views, "department", lambda *a, **k: (_ for _ in ()).throw(AssertionError("computed")))
    monkeypatch.setattr(views, "book", lambda *a, **k: (_ for _ in ()).throw(AssertionError("computed")))
    assert c.get(f"/d/episode?v={fp}").status_code == 204
    assert c.get(f"/b/{CODEX}?v={book_fp}").status_code == 204
    assert c.get("/d/nope?v=abc").status_code == 404 and c.get("/b/20990101000000?v=abc").status_code == 404


def test_6_the_page_embeds_no_unit_index(client):
    c, _ = client
    html = c.get("/").text
    embedded = json.loads(html.split('id="pal-data">', 1)[1].split("</script>", 1)[0])
    assert {e["g"] for e in embedded} == {"Pages", "Books", "Departments"}
    assert any(e["g"] == "Units" for e in c.get("/api/palette.json").json())


def test_11_the_thumb_cache_is_pruned_oldest_first_to_its_cap(tmp_path):
    for i in range(5):
        f = tmp_path / f"t{i}.webp"
        f.write_bytes(b"x" * 100)
        os.utime(f, (1000 + i, 1000 + i))
    assert thumbs.prune(tmp_path, cap_bytes=250) == 3
    assert sorted(p.name for p in tmp_path.iterdir()) == ["t3.webp", "t4.webp"]
    assert thumbs.prune(tmp_path / "absent", cap_bytes=1) == 0


def test_11_the_board_prunes_its_thumb_cache_when_it_starts(tmp_path, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("cc_cli", cc_app.HERE.parents[1] / "command_center.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    seen = []
    monkeypatch.setattr(thumbs, "prune", lambda folder, *a, **k: seen.append(folder) or 0)
    (tmp_path / "library").mkdir()
    cli.main(["--db", str(tmp_path / "x.db"), "--library", str(tmp_path / "library"), "--read-only"],
             serve=lambda *a, **k: None)
    assert seen == [tmp_path / ".cache" / "thumbs"]


@pytest.mark.parametrize("part", ["head", "tails", "orders"])
def test_3_a_unit_partial_never_walks_the_unit_folder(client, monkeypatch, part):
    """04 #3: each unit partial rebuilt the whole unit, Files walk and all."""
    c, _ = client
    from studio.command_center import unit_view
    monkeypatch.setattr(unit_view.viewer_model, "index_files",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("walked the folder")))
    monkeypatch.setattr(unit_view, "pictures_band", lambda *a, **k: (_ for _ in ()).throw(AssertionError("globbed")))
    assert c.get(f"/partials/unit/episode/{CODEX}/ep04/{part}").status_code == 200


def test_3_the_unit_page_still_draws_every_band(client):
    c, _ = client
    html = c.get(f"/d/episode/{CODEX}/ep04").text
    assert 'id="files"' in html
