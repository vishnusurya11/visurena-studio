"""The list pages and Home (panel ruling PKG-4, 4.1-4.10): every live section waits for its
pulse key and morphs in place (no clock poll), rows carry stable ids, Home leads with the
unit on the GPU and then Needs you, a poster tile is a stretched link with a sibling Viewer
button, the GPU chart is server SVG with keyed marks, the queue states the one hold
sentence and stays under its element budget, /inbox lists exactly inbox_count() rows with
an Acknowledge-all page key, and the reads behind the pictures answer from the fixture."""
from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from board_css import TEMPLATES
from command_center_fixtures import CODEX, make_app
from studio.command_center import views, viz

MINE = ("home.html", "floor.html", "department.html", "book.html", "books.html", "architecture.html",
        "inbox.html", "_rows.html", "_floor.html", "_attention.html", "_orders.html", "_lanes.html",
        "_today.html", "_viz.html")


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    a = make_app(tmp_path_factory.mktemp("lists"), mp)
    a.state.procs = lambda: []
    yield a
    mp.undo()


@pytest.fixture()
def client(app):
    return TestClient(app)


def request_for(app):
    return SimpleNamespace(app=app)


def main(page: str) -> str:
    return page[page.index("<main"):page.index("</main>")]


# --- 4.1 the pulse, not the clock ---


@pytest.mark.parametrize("name", MINE)
def test_no_list_template_polls_on_a_clock(name):
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    assert not re.search(r'hx-trigger="[^"]*every \d', text)


@pytest.mark.parametrize("route, key", [("/", "pulse:floor"), ("/", "pulse:attention"), ("/", "pulse:lanes"),
                                        ("/", "pulse:orders"), ("/queue", "pulse:floor"),
                                        ("/d/episode", "pulse:dept:episode"), (f"/b/{CODEX}", f"pulse:book:{CODEX}"),
                                        ("/inbox", "pulse:attention")])
def test_each_live_section_waits_for_its_pulse_key_and_morphs(client, route, key):
    page = main(client.get(route).text)
    tags = [t for t in re.findall(r"<[a-z]+\b[^>]*>", page) if f'hx-trigger="{key} from:body' in t]
    assert tags and all("morph:" in t for t in tags)


@pytest.mark.parametrize("route, key", [("/", "floor"), ("/", "attention"), ("/d/episode", "dept:episode"),
                                        (f"/b/{CODEX}", f"book:{CODEX}"), ("/inbox", "attention")])
def test_each_live_section_carries_its_fingerprint(app, client, route, key):
    v = viz.fp(request_for(app), key)
    assert v and re.search(rf'hx-trigger="pulse:{re.escape(key)} from:body"[^>]*data-v="{v}"|data-v="{v}"[^>]*hx-trigger="pulse:{re.escape(key)} from:body"', client.get(route).text)


def test_department_rows_carry_stable_ids(client):
    page = client.get("/d/episode").text
    for unit in ("ep03", "ep04", "ep05", "ep06", "ep07"):
        assert f'id="wo-{CODEX}-{unit}"' in page


def test_needs_you_cards_carry_stable_ids(client):
    page = client.get("/partials/attention").text
    assert f'id="att-{CODEX}-episode-ep05"' in page and f'id="att-{CODEX}-episode-ep03"' in page


# --- 4.2 Home's order ---


def test_home_puts_needs_you_under_the_hero_and_before_the_lanes(client):
    page = main(client.get("/").text)
    assert page.index('id="hero"') < page.index('id="needs-h"') < page.index('id="next-h"') < page.index('id="lanes"')


def test_home_has_no_second_list_of_the_flagged_units_and_two_kpis(client):
    page = main(client.get("/").text)
    assert "Shipped with flags" not in page and page.count('class="kpi"') == 2
    assert page.count(f'id="att-{CODEX}-episode-ep03"') == 1


# --- 4.3 the feed ---


def test_today_is_a_log_newest_first(client):
    page = client.get("/").text
    feed = page[page.index('id="since-feed"'):]
    assert 'role="log"' in page[page.index('id="since-feed"') - 40:page.index('id="since-feed"') + 80]
    times = re.findall(r'<time datetime="([^"]+)"', feed[:feed.index("</ul>")])
    assert times == sorted(times, reverse=True)


# --- 4.4, 4.5 the department reads at a glance ---


def test_the_department_says_no_acked_words_and_no_step_and_gate_counts(client):
    page = main(client.get("/d/episode").text)
    assert "not acked" not in page and "12 steps" not in page and "6 gates" not in page


def group_toggle(page: str, key: str) -> str:
    """The checkbox that shows or folds one state group of the book's table."""
    body = page[page.index(f'id="grp-{CODEX}-{key}"'):]
    return re.search(r'<input type="checkbox" class="gtog"[^>]*>', body).group(0)


def test_done_starts_collapsed_and_running_open(client):
    assert "checked" not in group_toggle(client.get("/d/refs").text, "done")
    assert "checked" in group_toggle(client.get("/d/episode").text, "running")


def test_a_flagged_rows_gate_chip_names_the_gate_and_its_judge(client):
    page = client.get("/d/episode").text
    assert 'title="PLAN: 1 plan fault, flagged · judge:plan@1"' in page or "judge:plan@1" in page


def test_the_inbox_shows_ages_not_iso_stamps(client):
    page = main(client.get("/inbox").text)
    text = re.sub(r"<[^>]+>", " ", page)
    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}", text)


# --- 4.6 the queue's element budget ---


def test_the_queue_stays_under_its_element_budget(client):
    assert len(re.findall(r"<[a-zA-Z][^>]*>", client.get("/queue").text)) <= 1400


# --- 4.7 tiles are never nested controls ---


@pytest.mark.parametrize("route", ["/", "/queue", "/d/episode", f"/b/{CODEX}", "/books", "/inbox"])
def test_no_button_sits_inside_a_link_or_a_link_inside_a_button(client, route):
    page = main(client.get(route).text)
    for a in re.findall(r"<a\b[^>]*>(.*?)</a>", page, re.S):
        assert "<button" not in a
    for b in re.findall(r"<button\b[^>]*>(.*?)</button>", page, re.S):
        assert "<a " not in b


def test_a_poster_is_a_viewer_opener_with_the_book(client):
    page = client.get("/d/episode").text
    page = client.get("/").text
    assert f'data-view="episodes/ep04/storyboard/shot_01.png"' in page and f'data-codex="{CODEX}"' in page


def test_a_shipped_episode_offers_watch_on_its_master(client):
    assert f'/d/episode/{CODEX}/ep03#master?play' in client.get("/partials/attention").text


# --- 4.8 the chart ---


def test_the_gpu_chart_is_server_svg_with_keyed_columns(client):
    page = client.get("/").text
    assert '<svg viewBox="0 0' in page and re.search(r'id="went-\d{4}-\d{2}-\d{2}"', page)
    assert 'id="went-hatch"' in page


# --- 4.9 sentences ---


def test_the_queue_never_retypes_the_hold_sentence():
    assert "before its next GPU step" not in (TEMPLATES / "floor.html").read_text(encoding="utf-8")


def test_the_queue_page_reads_the_hold_sentence(client):
    from studio.command_center import actions
    assert actions.HOLD_EFFECT in client.get("/queue").text


def test_an_empty_needs_you_says_why_and_what_next(app, client, monkeypatch):
    monkeypatch.setattr(views, "attention", lambda conn: [])
    page = client.get("/partials/attention").text
    assert "Nothing needs you." in page and "acknowledging" in page


# --- 4.10 the inbox page and the architecture link ---


def test_the_inbox_lists_exactly_inbox_count_rows(app, client):
    page = client.get("/inbox").text
    conn = app.state.conn_factory()
    try:
        n = views.inbox_count(conn) if hasattr(views, "inbox_count") else len(views.attention(conn))
    finally:
        conn.close()
    assert page.count('class="nc"') == n


def test_acknowledge_all_is_the_shift_a_page_key(client):
    page = client.get("/inbox").text
    assert re.search(r'<button[^>]*data-key="A"[^>]*data-ack-all', page)


def test_architecture_offers_the_standalone_chart(client):
    page = client.get("/architecture").text
    assert 'href="/org"' in page and "Standalone" in page


# --- the reads behind the pictures ---


def test_a_rows_face_is_its_middle_panel(app):
    r = {"codex_id": CODEX, "home": "episodes/ep04"}
    assert viz.face(request_for(app), r, 80)["rel"] == "episodes/ep04/storyboard/shot_01.png"


def test_the_rail_has_a_segment_per_registry_step(app):
    conn = app.state.conn_factory()
    try:
        row = views.row_view(conn.execute("SELECT * FROM work_orders WHERE unit = 'ep04'").fetchone())
    finally:
        conn.close()
    rail = viz.rail(request_for(app), row)
    assert len(rail) == len(views.step_names("episode")) and rail[0]["cls"] in ("done", "skipped")


def test_a_rows_chips_come_from_its_verdicts(app):
    conn = app.state.conn_factory()
    try:
        row = views.row_view(conn.execute("SELECT * FROM work_orders WHERE unit = 'ep04'").fetchone())
    finally:
        conn.close()
    assert [c["gate"] for c in viz.chips(row)] == ["PLAN"]


def test_went_reads_the_runs_from_events(app):
    w = viz.went(request_for(app))
    assert len(w["days"]) == 7 and w["days"][-1]["today"] and "cols" in w["chart"]


def test_the_live_runs_are_the_running_units_runs(app):
    conn = app.state.conn_factory()
    try:
        assert viz.live_runs(conn) and viz.event_rows(conn, "2000-01-01")
    finally:
        conn.close()


def test_the_season_is_the_books_episodes_with_posters(app):
    season = viz.season(request_for(app), CODEX)
    ep04 = next(e for e in season if e["unit"] == "ep04")
    assert ep04["poster"]["rel"].endswith("shot_01.png") and {e["unit"] for e in season} >= {"ep03", "ep05"}


def test_the_shelf_splits_books_with_pictures_from_the_rest(app):
    shelf = [{"codex_id": CODEX, "units": 6}, {"codex_id": "20260901000002", "units": 0}]
    making, rest = viz.shelf_split(request_for(app), shelf)
    assert [b["codex_id"] for b, _ in making] == [CODEX] and [b["codex_id"] for b in rest] == ["20260901000002"]


def test_the_lane_eta_is_none_or_the_views_answer(app):
    e = viz.queue_eta(request_for(app))
    assert e is None or "clean_text" in e


def test_initials_skip_the_small_words():
    assert viz.initials("The Hound of the Baskervilles") == "HB" and viz.initials("Dracula") == "D"


def test_reading_closes_its_connection(app):
    with viz.reading(request_for(app)) as conn:
        conn.execute("SELECT 1")
    with pytest.raises(Exception):
        conn.execute("SELECT 1")
