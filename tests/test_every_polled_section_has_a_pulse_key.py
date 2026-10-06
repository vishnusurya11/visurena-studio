"""Every polled section names a pulse key the server serves (refresh fix A3, C1/C3):
a section refreshes only when pulse.js fires `pulse:<key>`, and pulse.js fires only
the keys `pulse.fingerprints` returns -- so a typo'd key is a section that never
refreshes.  These tests parse the rendered pages, collect every `hx-trigger`
pulse key, and compare against the fingerprints on the fixture DB; they also hold
each such section to its contract: an `hx-get` to fetch and a server-drawn
`data-v` so the first refetch can answer 204 (C2)."""
from __future__ import annotations

import re
import time

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio.command_center import pulse

PAGES = {"/": {"floor", "attention", "lanes", "orders"},
         "/queue": {"floor"},
         "/d/episode": {"dept:episode"},
         f"/b/{CODEX}": {f"book:{CODEX}"},
         "/books": {"lanes"},
         "/inbox": {"attention"}}
"""Each page and the pulse keys its live sections must wait on."""

UNIT = f"/d/episode/{CODEX}/ep04"
UNIT_KEY = f"unit:episode/{CODEX}/ep04"


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    a = make_app(tmp_path_factory.mktemp("pulsekeys"), mp)
    a.state.procs = lambda: []
    yield a
    mp.undo()


@pytest.fixture()
def client(app):
    return TestClient(app)


def served_keys(app) -> dict[str, str]:
    """The fingerprint map the pulse would answer now (the keys pulse.js can fire)."""
    conn = app.state.conn_factory()
    try:
        return pulse.fingerprints(conn, time.time())
    finally:
        conn.close()


def polled(page: str) -> list[tuple[str, str]]:
    """[(key, tag)] for every element whose hx-trigger waits on a pulse key."""
    out = []
    for tag in re.findall(r"<[a-z][^>]*>", page):
        trigger = re.search(r'hx-trigger="([^"]*)"', tag)
        if trigger and "pulse:" in trigger.group(1):
            out += [(k, tag) for k in re.findall(r'pulse:([^\s,"\[]+)', trigger.group(1))]
    return out


@pytest.mark.parametrize("route", [*PAGES, UNIT])
def test_every_polled_key_is_one_the_pulse_serves(app, client, route):
    """A typo'd key is a key fingerprints() never returns: this fails on it."""
    keys = served_keys(app)
    found = polled(client.get(route).text)
    assert found, f"{route} has no pulse-polled section"
    for key, tag in found:
        assert key in keys, f"{route} waits on pulse:{key} but the pulse serves no such key: {tag}"


@pytest.mark.parametrize("route, wanted", PAGES.items())
def test_each_page_waits_on_its_required_keys(client, route, wanted):
    """No listed section is missing its trigger (the Books shelf included)."""
    found = {key for key, _ in polled(client.get(route).text)}
    assert wanted <= found, f"{route} polls {sorted(found)}, missing {sorted(wanted - found)}"


@pytest.mark.parametrize("route", list(PAGES))
def test_every_polled_section_fetches_and_carries_its_fingerprint(app, client, route):
    """Each pulse-polled section has an hx-get and a data-v equal to the server's
    fingerprint (drawn just before or just after the render: the minute bucket may tick)."""
    before = served_keys(app)
    page = client.get(route).text
    after = served_keys(app)
    for key, tag in polled(page):
        assert 'hx-get="' in tag, f"{route}: the pulse:{key} section has no hx-get: {tag}"
        v = re.search(r'data-v="([^"]*)"', tag)
        assert v and v.group(1), f"{route}: the pulse:{key} section has no data-v: {tag}"
        assert v.group(1) in (before.get(key), after.get(key)), \
            f"{route}: data-v {v.group(1)!r} is not the pulse's {key} fingerprint"


@pytest.mark.parametrize("route, hooks", [("/", ["data-running", "data-needs", "data-queue"]),
                                          ("/queue", ["data-running", "data-queue"])])
def test_the_header_tallies_carry_the_hooks_the_pulse_patches(client, route, hooks):
    """A count outside every polled section stays fresh only if pulse.js can find it:
    the running / needs / queued tallies expose the data-* hooks the shell patch reads."""
    page = client.get(route).text
    head = page[page.index('class="title-row"'):page.index("</div>", page.index('class="title-row"'))]
    for hook in hooks:
        assert hook in head, f"{route}: the header tally has no {hook} hook"


def test_the_checker_itself_catches_a_typo(app):
    """The guard the suite stands on: a misspelled key is found and is unserved."""
    snippet = '<div hx-get="/partials/attention" hx-trigger="pulse:atention from:body" data-v="x">'
    assert polled(snippet) == [("atention", snippet)]
    assert "atention" not in served_keys(app)
