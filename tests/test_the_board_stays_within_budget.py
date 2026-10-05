"""The board's performance budget (panel ruling 1.10, P08.9): every page answers
warm within 50 ms, every partial is at most 6 KB, the queue page stays under
1 400 elements, and every <img> outside a <template> has a width and a height
(no layout shift).  Element counts are printed for the record (`-s`)."""
from __future__ import annotations

import re
import time

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio import registry

UNIT = f"episode/{CODEX}/ep04"
PAGES = (["/", "/queue", "/books", "/architecture", "/inbox", f"/b/{CODEX}", f"/d/{UNIT}", f"/d/refs/{CODEX}/main"]
         + [f"/d/{s}" for s in registry.stage_names()])
# Lead's ruling 2026-10-05: a department row keeps its hold / bump / retry controls (the owner acts
# from the row), so the department grid has its own budget; a quiet pulse answers 204 anyway.
GRID_BYTES = 12 * 1024
PARTIALS = ["/partials/floor", "/partials/attention", "/partials/needs-you-count", "/partials/orders",
            "/partials/lanes", "/partials/d/episode", f"/partials/unit/{UNIT}/tails",
            f"/partials/unit/{UNIT}/head", f"/partials/unit/{UNIT}/orders", f"/partials/unit/{UNIT}/live",
            "/api/pulse.json"]
WARM_MS, PARTIAL_BYTES, FLOOR_ELEMENTS = 50.0, 6 * 1024, 1400


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    app = make_app(tmp_path_factory.mktemp("budget"), mp)
    app.state.procs = lambda: []
    yield TestClient(app)
    mp.undo()


def warm_ms(client, url: str) -> float:
    """The best of three answers after one cold one, in ms."""
    assert client.get(url).status_code == 200, url
    best = float("inf")
    for _ in range(3):
        t = time.perf_counter()
        client.get(url)
        best = min(best, (time.perf_counter() - t) * 1000)
    return best


def elements(html: str) -> int:
    """How many elements a page opens."""
    return len(re.findall(r"<[a-zA-Z][^>]*>", html))


def bare_images(html: str) -> list[str]:
    """Every <img> outside a <template> missing its width or height."""
    outside = re.sub(r"<template\b.*?</template>", "", html, flags=re.S)
    return [tag for tag in re.findall(r"<img\b[^>]*>", outside)
            if not (re.search(r"\swidth=", tag) and re.search(r"\sheight=", tag))]


@pytest.mark.parametrize("url", PAGES)
def test_every_page_answers_warm_within_budget(client, url):
    ms = warm_ms(client, url)
    print(f"{url}: {ms:.1f} ms, {elements(client.get(url).text)} elements")
    assert ms <= WARM_MS, f"{url} took {ms:.1f} ms"


@pytest.mark.parametrize("url", PARTIALS)
def test_every_partial_is_small(client, url):
    response = client.get(url)
    budget = GRID_BYTES if url.startswith("/partials/d/") and url.count("/") == 3 else PARTIAL_BYTES
    assert response.status_code == 200 and len(response.content) <= budget, (url, len(response.content))


def test_the_queue_page_stays_under_its_element_budget(client):
    assert elements(client.get("/queue").text) <= FLOOR_ELEMENTS


@pytest.mark.parametrize("url", PAGES)
def test_every_picture_reserves_its_box(client, url):
    assert bare_images(client.get(url).text) == []


def test_the_helpers_count_and_find():
    html = '<div><img src="a" width="1" height="2"><img src="b"></div><template><img src="c"></template>'
    assert elements(html) == 5 and bare_images(html) == ['<img src="b">']
