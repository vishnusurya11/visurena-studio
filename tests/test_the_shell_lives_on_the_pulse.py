"""The living shell (panel ruling PKG-2, contracts C1/C3/C4/C5): one 2 s pulse
(`static/pulse.js`) patches the sidebar, the GPU card, the badges and the title
on every page and fires `pulse:<key>` for the sections whose fingerprint
changed; a heartbeat chip says how old the data is; one KEYS registry is the
`?` sheet, the titles and the key map; one pair of live regions speaks
(`board.announce`); a held studio shows in the header; the crumbs start at
Home; the Viewer is loaded once on every page.  The pure JS functions are run
under node when it is on the PATH (no browser, no network, $0)."""
from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from board_html import sidebar
from command_center_fixtures import CODEX, OTHER, make_app, make_library, seed
from studio import db
from studio.command_center import app as cc_app
from studio.command_center import shell, views

STATIC = Path(shell.__file__).resolve().parent / "static"
TEMPLATES = Path(shell.__file__).resolve().parent / "templates"
NODE = shutil.which("node")
PULSE = {"boot": 1000, "now": 2000, "cursor": 7, "events": [],
         "fp": {"shell": "s1", "floor": "f1", "attention": "a1", "orders": "o1", "lanes": "l1",
                "dept:episode": "d1", f"book:{CODEX}": "b1", f"unit:episode/{CODEX}/ep04": "u1"},
         "shell": {"needs": 3, "queue": 1, "dept_dots": {"episode": {"running": 1, "flagged": 5}},
                   "pins": [{"href": f"/d/episode/{CODEX}/ep04", "label": "ep04", "state": "running"}],
                   "gpu": {"href": f"/d/episode/{CODEX}/ep04", "unit": "ep04", "step": "07 board",
                           "frac": 0.4, "finish": "21:35", "vital": "working", "held": False},
                   "hold": None}}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    db.insert_codex(connection, "Other Book", codex_id=OTHER)
    seed(connection, library)
    return connection, library


def hold_studio(tmp_path, reason="checking the grids"):
    """A studio hold written straight into the fixture DB the client reads."""
    connection = db.get_connection(tmp_path / "t.db")
    connection.execute("INSERT INTO holds (scope, reason, held_by, held_at) VALUES ('studio', ?, 'owner',"
                       " '2026-10-04T19:21:00Z')", (reason,))
    connection.commit()
    connection.close()


def node(expr: str):
    """Evaluate `expr` against pulse.js's pure core under node; its JSON result
    (base64 on the wire, so no console code page touches the glyphs)."""
    script = (f"const P = require({json.dumps(str(STATIC / 'pulse.js'))});"
              f" process.stdout.write(Buffer.from(JSON.stringify({expr})).toString('base64'));")
    out = subprocess.run([NODE, "-e", script], capture_output=True, timeout=30, check=True)
    return json.loads(base64.b64decode(out.stdout).decode("utf-8"))


needs_node = pytest.mark.skipif(NODE is None, reason="node is not on the PATH")


# --- the data (shell.py) ---


def test_the_inbox_is_a_real_address_called_needs_you():
    assert shell.section("/inbox") == "inbox"
    page = next(p for p in shell.PAGES if p[0] == "/inbox")
    assert page[2] == "Needs you" and not any(p[0].startswith("/#") for p in shell.PAGES)


def test_every_key_is_one_registry_row():
    for k in shell.KEYS:
        assert set(k) >= {"keys", "does", "group"} and sum(x in k for x in ("go", "act", "click")) == 1, k
    assert shell.key_for("/inbox") == "g i" and shell.key_for("/") == "g h"
    assert {"[", "]", "w", "A"} <= {k["keys"] for k in shell.KEYS if "click" in k}


@pytest.mark.parametrize("keys, parts", [("g h", ["G", "H"]), ("ctrl+k", ["Ctrl", "K"]), ("A", ["Shift", "A"]),
                                         ("?", ["?"]), ("t", ["T"]), ("[", ["["])])
def test_a_chord_is_drawn_as_its_keycaps(keys, parts):
    assert shell.keycaps(keys) == parts


@pytest.mark.parametrize("keys, aria", [("t", "T"), ("ctrl+k", "Control+K"), ("A", "Shift+A"), ("g h", "")])
def test_aria_keyshortcuts_names_single_keys_and_never_a_chord(keys, aria):
    assert shell.aria_keys(keys) == aria


@pytest.mark.parametrize("path, crumbs", [
    ("/", [("Home", None)]),
    ("/queue", [("Home", "/"), ("Queue", None)]),
    ("/floor", [("Home", "/"), ("Queue", None)]),
    ("/inbox", [("Home", "/"), ("Needs you", None)]),
    ("/books", [("Home", "/"), ("Books", None)]),
    ("/architecture", [("Home", "/"), ("Architecture", None)]),
    (f"/b/{CODEX}", [("Home", "/"), ("Books", "/books"), ("A Book", None)]),
    ("/d/episode", [("Home", "/"), ("episode", None)]),
    (f"/d/episode/{CODEX}/ep04", [("Home", "/"), ("Books", "/books"), ("A Book", f"/b/{CODEX}"),
                                  ("episode", f"/d/episode?book={CODEX}"), ("ep04", None)]),
])
def test_the_crumbs_start_at_home(path, crumbs):
    assert shell.crumbs(path, {CODEX: "A Book"}) == crumbs


@pytest.mark.parametrize("item, name", [
    ({"stage": "episode", "total": 9, "dots": [("run", 1, "1 running"), ("flag", 5, "5 flagged")]},
     "episode, 1 running, 5 flagged"),
    ({"stage": "refs", "total": 3, "dots": [("done", 3, "all 3 done")]}, "refs, all 3 done"),
    ({"stage": "trailer", "total": 4, "dots": []}, "trailer, 4 units"),
])
def test_a_departments_accessible_name_is_its_moving_dots(item, name):
    assert shell.dept_label(item) == name


def test_a_studio_hold_is_the_banners_data(conn):
    assert shell.studio_hold(conn[0]) is None
    conn[0].execute("INSERT INTO holds (scope, reason, held_at) VALUES ('unit', 'x', '2026-10-04T19:00:00Z')")
    assert shell.studio_hold(conn[0]) is None
    conn[0].execute("INSERT INTO holds (scope, reason, held_at) VALUES ('studio', 'grids', '2026-10-04T19:21:00Z')")
    hold = shell.studio_hold(conn[0])
    assert hold["reason"] == "grids" and hold["since"] == "2026-10-04T19:21:00Z" and hold["id"] > 0


def test_a_hold_time_is_read_in_local_time():
    from datetime import datetime, timezone
    local = datetime(2026, 10, 4, 19, 21, tzinfo=timezone.utc).astimezone().strftime("%H:%M")
    assert shell.hm("2026-10-04T19:21:00Z") == shell.hm("2026-10-04T19:21:00") == local
    assert shell.hm(None) == shell.hm("soon") == ""


@pytest.mark.parametrize("age, err, boot_changed, state", [
    (0, False, False, "live"), (5, False, False, "live"), (6, False, False, "stale"),
    (40, False, False, "stale"), (1, True, False, "offline"), (90, True, False, "offline"),
    (1, False, True, "restart"), (90, True, True, "restart")])
def test_the_heartbeat_chip_reads_the_age_of_the_last_good_pulse(age, err, boot_changed, state):
    assert shell.chip_state(age, err, boot_changed) == state


def test_the_palette_indexes_every_unit_running_first_then_what_needs_you(conn):
    units = [e for e in shell.palette_index(conn[0], conn[1]) if e["g"] == "Units"]
    names = [e["l"].split(" · ")[0] for e in units]
    assert names[0] == "ep04" and {"ep03", "ep05", "ep06", "ep07", "main"} <= set(names)
    assert names.index("ep05") < names.index("ep06") and names.index("ep03") < names.index("ep06")
    ep03 = units[names.index("ep03")]
    assert ep03["st"] == "flagged" and ep03["h"] == f"/d/episode/{CODEX}/ep03" and "A Book" in ep03["s"]


def test_the_palettes_actions_are_hold_lift_and_acknowledge_only(conn, tmp_path):
    acts = [e for e in shell.palette_index(conn[0], conn[1]) if e["g"] == "Actions"]
    assert {e["a"] for e in acts} == {"hold", "ack"}
    assert [e["unit"] for e in acts if e["a"] == "ack"] == ["ep03"]
    conn[0].execute("INSERT INTO holds (scope, reason, held_at) VALUES ('studio', 'grids', '2026-10-04T19:21:00Z')")
    acts = [e for e in shell.palette_index(conn[0], conn[1]) if e["g"] == "Actions"]
    assert {e["a"] for e in acts} == {"lift", "ack"}


def test_the_shell_counts_what_needs_you_once(conn):
    sh = shell.shell(conn[0], conn[1], "/")
    assert sh["needs"] == len(views.attention(conn[0])) == 3 and sh["hold"] is None
    assert sh["crumbs"][0] == ("Home", None) and [k["keys"] for k in sh["key_rows"]] == [k["keys"] for k in shell.KEYS]


def test_a_key_row_carries_its_keycaps_and_aria_name():
    rows = {k["keys"]: k for k in shell.key_rows()}
    assert rows["A"]["caps"] == ["Shift", "A"] and rows["A"]["aria"] == "Shift+A" and rows["A"]["click"] == "A"
    assert rows["g i"]["caps"] == ["G", "I"] and rows["g i"]["aria"] == "" and rows["g i"]["go"] == "/inbox"


# --- the page (base.html + _shell.html) ---


def scripts(page: str) -> list[str]:
    return re.findall(r'<script[^>]*src="([^"?]+)', page)


def test_pulse_morph_and_the_viewer_load_once_in_order(client):
    src = scripts(client.get("/").text)
    for name in ("htmx.min.js", "idiomorph-ext.min.js", "board.js", "pulse.js",
                 "viewer/docview.js", "viewer/viewer.js", "viewer/prov.js"):
        assert src.count(f"/static/{name}") == 1, name
    order = [src.index(f"/static/{n}") for n in ("htmx.min.js", "idiomorph-ext.min.js")]
    assert order == sorted(order)
    order = [src.index(f"/static/viewer/{n}") for n in ("docview.js", "viewer.js", "prov.js")]
    assert order == sorted(order)
    assert client.get("/").text.count("/static/viewer/viewer.css?v=") == 1


def test_no_shell_template_polls_on_a_timer():
    for name in ("base.html", "_shell.html"):
        assert not re.search(r"every \d", (TEMPLATES / name).read_text(encoding="utf-8")), name
    assert "setInterval" not in (STATIC / "board.js").read_text(encoding="utf-8")


def test_the_body_morphs_and_main_is_the_skip_target(client):
    page = client.get("/").text
    body = re.search(r"<body[^>]*>", page).group(0)
    assert 'hx-ext="morph"' in body and '<main id="main"' in page
    first = re.search(r"<(a|button|input|select|textarea)\b[^>]*>", page[page.index("<body"):]).group(0)
    assert 'href="#main"' in first and "skip" in first


def test_the_live_regions_are_in_the_shell_once_and_in_no_partial(client):
    page = client.get("/").text
    assert page.count('id="sr-status"') == 1 and page.count('id="sr-alert"') == 1
    assert re.search(r'id="sr-status"[^>]*aria-live="polite"', page)
    assert re.search(r'id="sr-alert"[^>]*role="alert"', page)
    for route in ("/partials/attention", "/partials/floor", "/partials/orders", "/partials/lanes"):
        assert "sr-status" not in client.get(route).text, route


def test_the_receipt_region_is_once_and_outside_every_polled_block(client):
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    assert page.count('data-testid="receipts"') == 1
    tag = re.search(r'<div[^>]*data-testid="receipts"[^>]*>', page).group(0)
    assert "hx-trigger" not in tag and page.index("</main>") < page.index('data-testid="receipts"')


def test_the_held_studio_shows_in_the_header_and_the_gpu_card(client, tmp_path):
    assert re.search(r'<div[^>]*data-testid="holdbar"[^>]*hidden', client.get("/books").text)
    hold_studio(tmp_path)
    page = client.get("/books").text
    bar = re.search(r'<div[^>]*data-testid="holdbar"[^>]*>.*?</div>', page, re.S).group(0)
    assert "hidden" not in bar.split(">")[0] and "checking the grids" in bar and "Lift" in bar
    card = re.search(r'data-testid="gpu-card".*?</a>', sidebar(page), re.S).group(0)
    assert "Held · finishing its step" in card and "idle" not in card


def test_the_gpu_card_dot_is_its_own_class(client):
    shell_html = (TEMPLATES / "_shell.html").read_text(encoding="utf-8")
    assert 'class="live"' not in shell_html
    card = re.search(r'data-testid="gpu-card".*?</a>', sidebar(client.get("/").text), re.S).group(0)
    assert "gc-dot" in card and "data-gc-step" in card and "data-gc-unit" in card


def test_the_departments_name_their_dots_and_hide_the_drawing(client):
    side = sidebar(client.get("/").text)
    row = re.search(r'<a [^>]*data-testid="dept-episode"[^>]*>', side).group(0)
    assert 'aria-label="episode, 1 running, 1 failed, 1 flagged"' in row and 'data-dept="episode"' in row
    dots = re.search(r'data-testid="dept-episode".*?<span class="sb-dots"([^>]*)>', side, re.S).group(1)
    assert 'aria-hidden="true"' in dots


def test_needs_you_is_the_one_name_and_lives_at_inbox(client):
    side = sidebar(client.get("/").text)
    item = re.search(r'<a [^>]*data-testid="nav-inbox".*?</a>', side, re.S).group(0)
    assert 'href="/inbox"' in item and "Needs you" in item and "Inbox" not in item
    tabs = re.search(r'<nav class="btabs".*?</nav>', client.get("/").text, re.S).group(0)
    assert 'href="/inbox"' in tabs and "data-needs" in tabs


def test_the_key_sheet_and_the_key_map_are_the_same_table(client):
    page = client.get("/").text
    keymap = json.loads(re.search(r'<script type="application/json" id="keys-data">(.*?)</script>', page, re.S).group(1))
    sheet = re.search(r'<dialog id="keysheet".*?</dialog>', page, re.S).group(0)
    drawn = re.findall(r'<dt data-keys="([^"]+)"', sheet)
    assert len(drawn) == len(sheet.split("<dt")) - 1 and sorted(drawn) == sorted(k["keys"] for k in keymap)
    assert {"[", "]", "w", "A", "g i"} <= set(drawn) and 'data-testid="keys-switch"' in sheet


def test_the_sidebar_titles_come_from_the_key_registry(client):
    side = sidebar(client.get("/").text)
    assert re.search(r'data-testid="nav-inbox"[^>]*title="Needs you \(G I\)"', side)
    assert re.search(r'data-theme-toggle[^>]*aria-keyshortcuts="T"', side)


def test_the_crumbs_are_drawn_from_the_shell_by_default(conn):
    page = cc_app.templates.env.from_string('{% extends "base.html" %}').render(
        shell=shell.shell(conn[0], conn[1], "/queue"), legend=views.LEGEND, state_icons=views.ICONS)
    nav = re.search(r'<nav class="crumbs".*?</nav>', page, re.S).group(0)
    assert '<a href="/">Home</a>' in nav and '<span aria-current="page">Queue</span>' in nav


def test_a_page_hands_the_viewer_its_book_stage_and_unit():
    page = cc_app.templates.env.from_string(
        '{% extends "base.html" %}{% block view_codex %}C1{% endblock %}'
        '{% block view_stage %}episode{% endblock %}{% block view_unit %}ep04{% endblock %}').render(
        shell=None, legend=[], state_icons={})
    body = re.search(r"<body[^>]*>", page).group(0)
    assert 'data-codex="C1"' in body and 'data-stage="episode"' in body and 'data-unit="ep04"' in body
    bare = cc_app.templates.env.from_string('{% extends "base.html" %}').render(shell=None, legend=[], state_icons={})
    assert "data-unit" not in re.search(r"<body[^>]*>", bare).group(0)


def test_navigation_prefetches_and_never_prerenders(client):
    page = client.get("/").text
    rules = re.findall(r'<script type="speculationrules">(.*?)</script>', page, re.S)
    assert len(rules) == 1
    spec = json.loads(rules[0])
    assert set(spec) == {"prefetch"} and spec["prefetch"][0]["eagerness"] == "moderate"
    assert {"/d/*", "/b/*"} <= {m["href_matches"] for m in spec["prefetch"][0]["where"]["or"]}
    assert page.count('rel="preload"') == 2 and 'as="font"' in page


def test_the_phone_sheet_lists_departments_and_pins_first(client):
    sheet = re.search(r'<dialog class="sheet" id="sheet".*?</dialog>', client.get("/").text, re.S).group(0)
    assert sheet.index('data-testid="sheet-departments"') < sheet.index('data-testid="sheet-pinned"') \
        < sheet.index('data-testid="sheet-pages"')


def test_the_heartbeat_chip_and_its_thresholds_are_on_every_page(client):
    page = client.get("/queue").text
    assert re.search(r'<button[^>]*id="hb"[^>]*data-hb="live"', page)
    cfg = json.loads(re.search(r'<script type="application/json" id="pulse-cfg">(.*?)</script>', page, re.S).group(1))
    assert cfg == shell.HEARTBEAT


# --- the pure JS core of pulse.js, under node ---


@needs_node
@pytest.mark.parametrize("age, err, boot_changed, state", [
    (0, False, False, "live"), (5, False, False, "live"), (6, False, False, "stale"),
    (1, True, False, "offline"), (1, False, True, "restart")])
def test_chip_state_in_js_matches_python(age, err, boot_changed, state):
    cfg = json.dumps(shell.HEARTBEAT)
    assert node(f"P.chipState({age}, {json.dumps(err)}, {json.dumps(boot_changed)}, {cfg})") == state


@needs_node
def test_chip_text_says_live_old_offline_or_restarted():
    assert node("['live','stale','offline','restart'].map((s) => P.chipText(s, 34, 8))") == [
        "● live", "◌ 34 s old", "✕ offline · retrying in 8 s", "↻ board restarted · reload"]
    assert node("P.chipText('offline', 9, 0.2)") == "✕ offline · retrying now"


@needs_node
def test_the_backoff_doubles_from_two_to_thirty_seconds():
    cfg = json.dumps(shell.HEARTBEAT)
    assert node(f"[0,1,2,3,4,5,9].map((n) => P.delay(n, false, {cfg}))") == [2, 2, 4, 8, 16, 30, 30]
    assert node(f"P.delay(0, true, {cfg})") == 10


@needs_node
def test_only_changed_fingerprints_fire():
    nxt = dict(PULSE["fp"], attention="a2", **{"dept:refs": "r1"})
    assert node(f"P.changedKeys({json.dumps(PULSE['fp'])}, {json.dumps(nxt)})") == ["attention", "dept:refs"]
    assert node(f"P.changedKeys(null, {json.dumps(PULSE['fp'])}).length") == len(PULSE["fp"])


@needs_node
def test_the_live_title_from_a_pulse():
    held = dict(PULSE["shell"], gpu=None, hold={"id": 1, "since": "x", "reason": "r"})
    idle = dict(PULSE["shell"], gpu=None)
    assert node(f"P.liveTitle({json.dumps(PULSE['shell'])}, 'Home · Visurena Studio')") == \
        "● ep04 · 07 board · ~21:35 · Home"
    assert node(f"P.liveTitle({json.dumps(held)}, 'Queue · Visurena Studio')") == "⏸ held · Queue"
    assert node(f"P.liveTitle({json.dumps(idle)}, 'Books · Visurena Studio')") == "Books · Visurena Studio"


@needs_node
@pytest.mark.parametrize("counts, total", [({"running": 1, "flagged": 5, "done": 3}, 9), ({"done": 30}, 30),
                                           ({"queued": 4}, 4), ({"failed": 2, "running": 1}, 5)])
def test_the_dots_in_js_match_the_server(counts, total):
    py = [list(d) for d in shell.dots(counts, total)]
    assert node(f"P.dots({json.dumps(counts)}, {total})") == py
    label = shell.dept_label({"stage": "episode", "total": total, "dots": shell.dots(counts, total)})
    assert node(f"P.deptLabel('episode', P.dots({json.dumps(counts)}, {total}), {total})") == label


@needs_node
def test_the_held_bar_reads_the_same_local_time_as_the_server():
    assert node("[P.hhmm('2026-10-04T19:21:00Z'), P.hhmm('2026-10-04T19:21:00'), P.hhmm('soon')]") == [
        shell.hm("2026-10-04T19:21:00Z"), shell.hm("2026-10-04T19:21:00"), ""]
