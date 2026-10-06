"""The unit page lives on the one heartbeat (refresh fix A5; panel ruling C1-C3, 5.3, 5.8):
the pulse key the page waits on byte-matches a key the server's fingerprint map serves, the
head, orders and tails carry a server-drawn data-v so a quiet pulse costs a 204 and nothing
more, a finished unit keeps no tails poll yet its head still listens for the pulse that
brings a new master iteration, and media.js's pure badge core shows the new master once
without ever touching the playing player.  TestClient over the tmp fixtures; the JS core
runs under node when it is on the PATH (no browser, no network, $0)."""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio.command_center import pulse, viz

ROOT = Path(__file__).resolve().parents[1] / "studio" / "command_center"
MEDIA = ROOT / "static" / "media.js"
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node is not on the PATH")
RUNNING = f"unit:episode/{CODEX}/ep04"
FINISHED = f"unit:episode/{CODEX}/ep03"


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    a = make_app(tmp_path_factory.mktemp("unitpulse"), mp)
    a.state.procs = lambda: []
    home = a.state.library / f"{CODEX}_a-book" / "episodes" / "ep03"
    for n, rel in enumerate(("cut/master_iter1.mp4", "cut/master_iter2.mp4")):
        f = home / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"x" * 16)
        os.utime(f, (1700000000 + n, 1700000000 + n))
    yield a
    mp.undo()


@pytest.fixture()
def client(app):
    return TestClient(app)


def request_for(app):
    return SimpleNamespace(app=app)


def fetcher(page: str, unit: str, part: str) -> str:
    """The one tag on the page that hx-gets this unit partial."""
    return next(t for t in re.findall(r"<[a-z]+\b[^>]*hx-get=\"[^\"]*\"[^>]*>", page)
                if f'/{unit}/{part}"' in t)


# --- the key byte-matches the server's (a typo on either side fails here) ---


def served_keys(app) -> dict:
    conn = app.state.conn_factory()
    try:
        return pulse.fingerprints(conn, time.time())
    finally:
        conn.close()


def test_the_pages_pulse_key_is_byte_for_byte_a_key_the_server_serves(app, client):
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    keys = set(re.findall(r'hx-trigger="pulse:(unit:[^"\[ ]+)', page))
    assert keys == {RUNNING}
    assert RUNNING in served_keys(app)


def test_a_finished_units_key_is_the_same_shape_and_still_served_while_recent(app, client):
    page = client.get(f"/d/episode/{CODEX}/ep03").text
    keys = set(re.findall(r'hx-trigger="pulse:(unit:[^"\[ ]+)', page))
    assert keys == {FINISHED}
    assert FINISHED in served_keys(app)


# --- data-v on every polled wrapper: the first pulse after a load costs a 204 ---


def test_head_orders_and_tails_carry_the_servers_fingerprint(app, client):
    before = viz.fp(request_for(app), RUNNING)
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    after = viz.fp(request_for(app), RUNNING)
    for part in ("head", "orders", "tails"):
        tag = fetcher(page, "ep04", part)
        assert any(f'data-v="{v}"' in tag for v in {before, after}), part


def test_a_quiet_pulse_costs_a_204_per_partial(app, client):
    for part in ("head", "orders", "tails"):
        v = viz.fp(request_for(app), RUNNING)
        r = client.get(f"/partials/unit/episode/{CODEX}/ep04/{part}?v={v}")
        if r.status_code != 204:                 # the minute bucket turned under us: once more
            v = viz.fp(request_for(app), RUNNING)
            r = client.get(f"/partials/unit/episode/{CODEX}/ep04/{part}?v={v}")
        assert r.status_code == 204 and not r.content, part


def test_a_stale_fingerprint_is_answered_with_the_section(client):
    r = client.get(f"/partials/unit/episode/{CODEX}/ep04/head?v=00000000")
    assert r.status_code == 200 and "ep04" in r.text


# --- a finished unit: no tails poll, but the head still hears the pulse (5.8) ---


def test_a_finished_unit_polls_no_tails_but_its_head_still_listens(client):
    page = client.get(f"/d/episode/{CODEX}/ep03").text
    tails = re.search(r'<div id="tails"[^>]*>', page).group(0)
    assert "hx-get" not in tails
    for part in ("head", "orders"):
        tag = fetcher(page, "ep03", part)
        assert f"pulse:{FINISHED} from:body" in tag and 'hx-swap="morph:innerHTML"' in tag, part


def test_the_screen_and_the_head_agree_on_the_latest_master(client):
    page = client.get(f"/d/episode/{CODEX}/ep03").text
    assert 'data-latest="cut/master_iter2.mp4"' in page
    assert 'data-latest-master="cut/master_iter2.mp4"' in page
    assert 'data-latest-short="v2"' in page
    badge = re.search(r'<span class="q vnew"[^>]*>', page).group(0)
    assert "hidden" in badge


def test_a_new_iteration_reaches_the_head_partial_for_the_badge(app, client):
    f = app.state.library / f"{CODEX}_a-book" / "episodes" / "ep03" / "cut" / "master_iter3.mp4"
    f.write_bytes(b"x" * 16)
    os.utime(f, (1700009999, 1700009999))
    try:
        head = client.get(f"/partials/unit/episode/{CODEX}/ep03/head").text
        assert 'data-latest-master="cut/master_iter3.mp4"' in head
        assert 'data-latest-short="v3"' in head
    finally:
        f.unlink()


# --- the pure JS badge core of media.js, under node ---


def node(expr: str):
    """Evaluate `expr` against media.js's pure core under node; its JSON result
    (base64 on the wire, so no console code page touches the glyphs)."""
    script = (f"const M = require({json.dumps(str(MEDIA))});"
              f" process.stdout.write(Buffer.from(JSON.stringify({expr})).toString('base64'));")
    out = subprocess.run([NODE, "-e", script], capture_output=True, timeout=30, check=True)
    raw = base64.b64decode(out.stdout).decode("utf-8")
    return json.loads(raw) if raw else None


@needs_node
def test_the_badge_core_badges_a_new_master_once_and_never_the_shown_one():
    latest = json.dumps({"rel": "cut/master_iter3.mp4", "short": "v3"})
    b = node(f"M.newMaster({latest}, 'cut/master_iter2.mp4', null)")
    assert b["rel"] == "cut/master_iter3.mp4" and b["text"] == "v3 •"
    assert "keeps playing" in b["say"] and "v3" in b["say"]
    assert node(f"M.newMaster({latest}, 'cut/master_iter3.mp4', null)") is None
    assert node(f"M.newMaster({latest}, 'cut/master_iter2.mp4', 'cut/master_iter3.mp4')") is None
    assert node("M.newMaster({rel: '', short: ''}, 'cut/master_iter2.mp4', null)") is None
    assert node("M.newMaster(null, 'cut/master_iter2.mp4', null)") is None


def test_media_js_exports_its_core_before_touching_the_document():
    js = MEDIA.read_text(encoding="utf-8")
    assert "module.exports" in js and js.index("module.exports") < js.index("document.")
    assert "newMaster(" in js and "checkNewMaster" in js and "t.id === 'head'" in js
