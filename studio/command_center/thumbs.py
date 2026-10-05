"""Small pictures for the live card (progress tracker spec §3, §6): a panel
shrunk to 160, 320 or 1024 (the lightbox) px WebP inside the board process, kept
in an in-process LRU keyed by (path, mtime_ns, size, width) and served under a
versioned URL as immutable -- opening a running episode drops from ~77 MB to
well under one.  A miss renders on a worker thread under a limiter of two
(panel ruling 1.5), so a cold episode's thumbs never take every threadpool slot
from the pages.  Nothing is written to disk."""
from __future__ import annotations

import io
import threading
from collections import OrderedDict
from pathlib import Path

import anyio

WIDTHS = frozenset({160, 320, 1024})
IMAGES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
CAP_BYTES = 64 * 1024 * 1024
QUALITY = 75
METHOD = 2
CONCURRENT = 2


class Lru:
    """Bytes by key, the least recently used evicted past a byte budget; safe
    across the worker threads that fill it."""

    def __init__(self, cap_bytes: int = CAP_BYTES):
        self.cap, self.size, self.items = cap_bytes, 0, OrderedDict()
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.items:
                return None
            self.items.move_to_end(key)
            return self.items[key]

    def put(self, key, data: bytes) -> None:
        with self.lock:
            if key in self.items:
                self.size -= len(self.items.pop(key))
            self.items[key] = data
            self.size += len(data)
            while self.size > self.cap and len(self.items) > 1:
                self.size -= len(self.items.popitem(last=False)[1])


def key(rel: str, path: Path, width: int) -> tuple:
    """The cache key: a new mtime or size is a new picture."""
    st = Path(path).stat()
    return (rel, st.st_mtime_ns, st.st_size, width)


def render(path: Path, width: int) -> bytes:
    """The picture fitted inside width x width, as WebP."""
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((width, width))
        out = io.BytesIO()
        im.save(out, "WEBP", quality=QUALITY, method=METHOD)
    return out.getvalue()


def thumb(path: Path, rel: str, width: int, lru: Lru) -> bytes:
    """The cached thumbnail, rendering it on a miss."""
    k = key(rel, path, width)
    data = lru.get(k)
    if data is None:
        data = render(path, width)
        lru.put(k, data)
    return data


async def thumb_async(path: Path, rel: str, width: int, lru: Lru, limiter: anyio.CapacityLimiter) -> bytes:
    """The cached thumbnail; a miss renders on a worker thread, at most
    `limiter`'s tokens at once (looked up again under the token, so a burst for
    one picture renders it once)."""
    k = key(rel, path, width)
    data = lru.get(k)
    if data is None:
        async with limiter:
            data = lru.get(k)
            if data is None:
                data = await anyio.to_thread.run_sync(render, path, width)
                lru.put(k, data)
    return data
