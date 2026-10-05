"""Thumbnails never starve the page (panel ruling 1.5): the `/thumb/` route is
async and renders through a worker thread under a limiter of two, so a cold
episode's 48 thumbs cannot take every threadpool slot from the page; WebP at
method 2; the lightbox's 1024 width is served and an unlisted width is not."""
from __future__ import annotations

import io
import threading
import time

import anyio
import httpx
from fastapi.testclient import TestClient
from PIL import Image

from command_center_fixtures import CODEX, make_app
from studio.command_center import thumbs

PANELS = [f"episodes/ep04/storyboard/shot_{i:02d}.png" for i in range(2)] + ["episodes/ep04/reports/strip_T00_T05.png"]


def real_pngs(app) -> None:
    """The fixture's panels as real pictures."""
    for rel in PANELS:
        target = next(app.state.library.glob(f"{CODEX}_*")) / rel
        Image.new("RGB", (1600, 900), (40, 50, 60)).save(target, "PNG")


def test_the_widths_are_160_320_and_1024(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    real_pngs(app)
    client = TestClient(app)
    for width in (160, 320, 1024):
        response = client.get(f"/thumb/{CODEX}/{width}/{PANELS[0]}")
        assert response.status_code == 200 and response.headers["content-type"] == "image/webp"
        assert Image.open(io.BytesIO(response.content)).width == width
    assert client.get(f"/thumb/{CODEX}/777/{PANELS[0]}").status_code == 404


def test_webp_is_encoded_at_method_two(monkeypatch, tmp_path):
    seen = {}
    original = Image.Image.save

    def spy(self, fp, format=None, **params):
        seen.update(params)
        return original(self, fp, format, **params)
    monkeypatch.setattr(Image.Image, "save", spy)
    path = tmp_path / "a.png"
    Image.new("RGB", (64, 64)).save(path, "PNG")
    thumbs.render(path, 160)
    assert seen["method"] == 2


def test_at_most_two_thumbs_render_at_once(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    live, peak, lock = [0], [0], threading.Lock()

    def slow_render(path, width):
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.15)
        with lock:
            live[0] -= 1
        return b"webp"
    monkeypatch.setattr(thumbs, "render", slow_render)

    async def burst():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://board") as client:
            urls = [f"/thumb/{CODEX}/{w}/{p}" for w in (160, 320, 1024) for p in PANELS]
            return await _gather(client, urls)
    codes = anyio.run(burst)
    assert codes == [200] * 9 and peak[0] == 2


async def _gather(client, urls):
    codes = [0] * len(urls)

    async def one(i, url):
        codes[i] = (await client.get(url)).status_code
    async with anyio.create_task_group() as tg:
        for i, url in enumerate(urls):
            tg.start_soon(one, i, url)
    return codes


def test_the_lru_is_safe_across_threads():
    lru = thumbs.Lru(cap_bytes=1000)

    def fill(n):
        for i in range(200):
            lru.put((n, i), b"x" * 10)
            lru.get((n, i - 1))
    workers = [threading.Thread(target=fill, args=(n,)) for n in range(4)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    assert lru.size == sum(len(v) for v in lru.items.values()) <= 1000
