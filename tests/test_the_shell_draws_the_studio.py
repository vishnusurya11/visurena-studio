"""The shell (plan G1, the v2 sidebar mockup): every page sits inside one server-
rendered sidebar -- Home first, the Inbox with what needs you, Queue, Books,
Architecture, a row per registered department with its count and state dots,
the running units pinned, the live GPU card -- a slim header with the page's
crumbs, phone tabs, the ⌘K palette and the `?` sheet.  /queue is the queue
(/floor keeps answering), /books the shelf, /architecture the org chart inside
the shell."""
from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from board_html import sidebar, text_of
from command_center_fixtures import CODEX, OTHER, make_app, make_library, seed
from studio import db, registry
from studio.command_center import shell, views


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


# --- the data ---


def test_a_path_names_its_sidebar_item():
    assert shell.section("/") == "home" and shell.section("/queue") == shell.section("/floor") == "queue"
    assert shell.section("/books") == shell.section(f"/b/{CODEX}") == "books"
    assert shell.section("/architecture") == "architecture"
    assert shell.section("/d/episode") == shell.section(f"/d/episode/{CODEX}/ep04") == "d:episode"
    assert shell.section("/org") == ""


def test_the_dots_say_running_failed_flagged_or_all_done():
    assert shell.dots({"running": 1, "flagged": 5, "done": 3}, 9) == [("run", 1, "1 running"), ("flag", 5, "5 flagged")]
    assert shell.dots({"done": 30}, 30) == [("done", 30, "all 30 done")]
    assert shell.dots({"queued": 4}, 4) == []


def test_every_registered_department_is_an_item_with_its_count(conn):
    items = shell.department_items(views.lanes(conn[0]))
    assert [d["stage"] for d in items] == registry.stage_names()
    episode = next(d for d in items if d["stage"] == "episode")
    assert episode["icon"] == "clapperboard" and episode["total"] == 5 and episode["lead"] == "run"


def test_a_face_is_the_units_newest_panel_as_a_thumb(conn, tmp_path):
    row = {"codex_id": CODEX, "home": "episodes/ep99"}
    assert shell.face(conn[1], row) is None
    panels = conn[1] / f"{CODEX}_a-book" / "episodes" / "ep99" / "storyboard"
    panels.mkdir(parents=True)
    (panels / "shot_00.png").write_bytes(b"png")
    assert shell.face(conn[1], row).startswith(f"/thumb/{CODEX}/160/episodes/ep99/storyboard/shot_00.png?v=")


def test_the_gpu_card_is_the_running_row_that_holds_the_gpu(conn):
    running = views.floor(conn[0])["running"]
    pins = [shell.pin(conn[1], r, views.book_names(conn[0])) for r in running]
    card = shell.gpu(pins, running)
    assert card["unit"] == "ep04" and card["href"] == f"/d/episode/{CODEX}/ep04"
    assert card["progress_url"] == f"/api/progress/episode/{CODEX}/ep04.json" and "18/25" in card["step"]
    assert shell.gpu([], []) is None


def test_the_shelf_lists_every_book_with_its_units(conn):
    shelf = {b["codex_id"]: b for b in views.shelf(conn[0])}
    assert set(shelf) == {CODEX, OTHER} and shelf[OTHER]["units"] == 0
    assert shelf[CODEX]["name"] == "A Book" and shelf[CODEX]["running"] == 1


def test_a_static_url_carries_the_files_mtime():
    url = shell.static_url("css/tokens.css")
    assert re.fullmatch(r"/static/css/tokens\.css\?v=[0-9a-f]+", url)
    assert shell.static_url("no/such.css") == "/static/no/such.css"


def test_the_palette_indexes_pages_units_books_and_departments(conn):
    sh = shell.shell(conn[0], conn[1], "/")
    groups = {e["g"] for e in sh["palette"]}
    assert groups == {"Pages", "Units", "Books", "Departments"}
    assert sh["palette"][0]["h"] == "/" and any(e["h"] == "/architecture" for e in sh["palette"])


# --- the page ---


def test_home_is_the_first_item_and_links_to_the_root(client):
    side = sidebar(client.get("/d/episode").text)
    items = re.findall(r'data-testid="nav-([a-z]+)"', side)
    assert items == ["home", "inbox", "queue", "books", "architecture"]
    assert re.search(r'<a class="sb-item" href="/" data-testid="nav-home"', side) and "Home" in side


def test_architecture_sits_between_books_and_the_departments(client):
    side = sidebar(client.get("/").text)
    assert side.index('data-testid="nav-books"') < side.index('data-testid="nav-architecture"') \
        < side.index('data-testid="sidebar-departments"')
    assert 'href="/architecture"' in side and "#network" in side


def test_the_sidebar_lists_every_department_with_its_count(client):
    side = sidebar(client.get("/").text)
    for stage in registry.stage_names():
        item = re.search(rf'<a [^>]*data-testid="dept-{stage}".*?</a>', side, re.S).group(0)
        total = sum(json.loads(client.get(f"/api/d/{stage}.json").text)["counts"].values())
        assert f'href="/d/{stage}"' in item and f'data-testid="dept-count">{total}<' in item, stage


def test_the_inbox_badge_is_what_needs_you(client):
    page = client.get("/").text
    shown = text_of(sidebar(page), "inbox-badge")
    assert shown == client.get("/partials/needs-you-count").text.strip() == "3"


def test_the_gpu_card_shows_the_running_unit(client):
    side = sidebar(client.get("/books").text)
    card = re.search(r'data-testid="gpu-card".*?</a>', side, re.S).group(0)
    assert "On the GPU" in card and "ep04" in card and "18/25" in card
    assert f'data-progress="/api/progress/episode/{CODEX}/ep04.json"' in card
    assert 'data-testid="pin"' in side


def test_the_current_page_is_marked_in_the_sidebar(client):
    side = sidebar(client.get("/d/refs").text)
    assert re.search(r'data-testid="dept-refs" aria-current="page"', side)
    assert not re.search(r'data-testid="nav-home" aria-current', side)


def test_the_running_units_page_lights_its_pin_not_its_department(client):
    side = sidebar(client.get(f"/d/episode/{CODEX}/ep04").text)
    assert re.search(r'data-testid="pin" aria-current="page"', side)
    assert not re.search(r'data-testid="dept-episode" aria-current', side)


@pytest.mark.parametrize("route", ["/queue", "/floor"])
def test_the_queue_answers_at_both_names(client, route):
    response = client.get(route)
    assert response.status_code == 200 and "NEXT" in response.text
    assert re.search(r'data-testid="nav-queue" aria-current="page"', sidebar(response.text))


def test_the_books_page_lists_every_codex_row(client):
    page = client.get("/books").text
    shelf = text_of(page, "shelf")
    assert "A Book" in shelf and "Other Book" in shelf and f'href="/b/{OTHER}"' in page


def test_the_architecture_page_is_the_org_chart_inside_the_shell(client):
    response = client.get("/architecture")
    assert response.status_code == 200 and 'data-testid="sidebar"' in response.text
    frame = re.search(r'<iframe[^>]*data-testid="org-frame"[^>]*>', response.text).group(0)
    assert 'src="/org?theme=' in frame
    assert re.search(r'data-testid="nav-architecture" aria-current="page"', sidebar(response.text))
    assert "Architecture" in response.text[response.text.index('class="crumbs"'):]
    assert client.get("/org").status_code == 200


def test_the_org_chart_takes_the_boards_theme_from_its_query():
    from board_css import ROOT
    head = (ROOT / "architecture" / "index.html").read_text(encoding="utf-8")[:600]
    assert "URLSearchParams(location.search).get('theme')" in head and "dataset.theme" in head


def test_every_page_has_the_header_the_phone_tabs_and_the_dialogs(client):
    for route in ("/", "/queue", "/books", "/architecture", "/d/episode", f"/b/{CODEX}", f"/d/episode/{CODEX}/ep04"):
        page = client.get(route).text
        assert 'class="ph"' in page and 'aria-label="Breadcrumb"' in page, route
        assert 'aria-label="Phone"' in page and 'id="palette"' in page and 'id="keysheet"' in page, route
        assert 'data-theme-toggle' in page and 'data-keys' in page and "/static/board.js?v=" in page, route


def test_the_root_page_is_called_home(client):
    page = client.get("/").text
    assert "<title>Home · Visurena Studio</title>" in page and "<h1>Home</h1>" in page
