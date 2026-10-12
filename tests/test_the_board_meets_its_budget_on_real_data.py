"""Board review 2026-10-12 (04 #12, #13): the budget test ran on a tiny fixture and
passed while the real board missed its budget (unit page 91 ms, unit partials
57-61 ms, a 50.9 KB department partial).  This one runs the board over the real
DB (read-only) and the real library, warm, and holds the measured pages to a
ceiling.  `local`: it reads the HDD; skipped where the library or the DB is absent.
Opt in with `uv run pytest -m local tests/test_the_board_meets_its_budget_on_real_data.py`."""
from __future__ import annotations

import statistics
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from studio.command_center import app as cc_app

REPO = Path(__file__).resolve().parents[1]
LIBRARY, DB = REPO / "library", REPO / "db" / "visurena_studio.db"
WOTW = "20260827135508"
pytestmark = [pytest.mark.local,
              pytest.mark.skipif(not (LIBRARY.is_dir() and DB.is_file()), reason="no real library or DB here")]

# measured warm on 2026-10-12 after the fixes (before -> after): / 37 -> 20 ms, pulse 16 -> 13,
# /d/episode 53 -> 35, /b/WotW 56 -> 26, ep18 91 -> 77, the department partial 51 -> 54 KB (titles)
WARM_MS = {"/api/pulse.json": 30, "/": 80, "/books": 80, "/d/episode": 100, f"/b/{WOTW}": 100,
           f"/d/episode/{WOTW}/ep18": 200, "/partials/d/episode": 60,
           # the unit partials draw only their own bands (04 #3): 57 -> 19 ms
           **{f"/partials/unit/episode/{WOTW}/ep18/{p}": 40 for p in ("head", "tails", "orders")}}
PARTIAL_KB = {"/partials/d/episode": 64}


@pytest.fixture(scope="module")
def client():
    return TestClient(cc_app.make_app(cc_app.readonly_factory(DB), LIBRARY))


def warm_ms(client, url: str, n: int = 5) -> float:
    """The median of n timed GETs after one warming GET."""
    assert client.get(url).status_code == 200, url
    times = []
    for _ in range(n):
        t = time.perf_counter()
        client.get(url)
        times.append((time.perf_counter() - t) * 1000)
    return statistics.median(times)


@pytest.mark.parametrize("url", sorted(WARM_MS))
def test_a_page_answers_warm_within_its_budget(client, url):
    assert warm_ms(client, url) <= WARM_MS[url], url


@pytest.mark.parametrize("url", sorted(PARTIAL_KB))
def test_a_partial_stays_within_its_size(client, url):
    assert len(client.get(url).content) / 1024 <= PARTIAL_KB[url], url
