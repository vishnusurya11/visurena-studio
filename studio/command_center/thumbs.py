"""Small pictures for the live card (progress tracker spec §3, §6): a panel
shrunk to 160, 320 or 1024 (the lightbox) px WebP inside the board process, kept
in an in-process LRU keyed by (path, mtime_ns, size, width) and served under a
versioned URL as immutable -- opening a running episode drops from ~77 MB to
well under one.  A miss renders on a worker thread under a limiter of two
(panel ruling 1.5), so a cold episode's thumbs never take every threadpool slot
from the pages.  The render shrinks an RGB picture before it converts it
(no full-size copy; measured 2026-10-11 on a 1024 px, 1.4 MB poster: 26 -> 21 ms,
of which the PNG decode is 18 -- the decode, not the convert, is the cost).  With a cache folder
(the board passes <repo>/.cache/thumbs) a thumbnail is also kept on disk under
its key's hash, so a restarted board is not cold; without one nothing is
written."""
from __future__ import annotations

import hashlib
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
REDUCING_GAP = 2.0
DIRECT = frozenset({"RGB", "L"})
"""Modes that shrink as they are and convert after."""


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
    """The picture fitted inside width x width, as RGB WebP.  An RGB or grey
    picture (every poster and panel) shrinks first and converts only the small
    one; any other mode converts first, as before (a resize would premultiply
    an RGBA whole or sample a palette nearest-neighbour).  A JPEG drafts at a
    reduced scale before it decodes."""
    from PIL import Image
    with Image.open(path) as im:
        im.draft("RGB", (width, width))
        small = im if im.mode in DIRECT else im.convert("RGB")
        small.thumbnail((width, width), reducing_gap=REDUCING_GAP)
        out = io.BytesIO()
        small.convert("RGB").save(out, "WEBP", quality=QUALITY, method=METHOD)
    return out.getvalue()


DISK_CAP_BYTES = 256 * 1024 * 1024
"""The on-disk thumbnail cache's ceiling (04 #11: a redraw orphans every old thumb)."""


def prune(folder: Path, cap_bytes: int = DISK_CAP_BYTES) -> int:
    """Delete the oldest kept thumbnails until the folder fits under the cap; how many went."""
    files = sorted(Path(folder).glob("*.webp"), key=lambda p: p.stat().st_mtime) if Path(folder).is_dir() else []
    total, removed = sum(p.stat().st_size for p in files), 0
    for p in files:
        if total <= cap_bytes:
            break
        total -= p.stat().st_size
        p.unlink(missing_ok=True)
        removed += 1
    return removed


def disk_path(folder: Path, k: tuple) -> Path:
    """Where a key's thumbnail is kept on disk: its hash, as .webp."""
    return Path(folder) / (hashlib.sha1(repr(k).encode()).hexdigest()[:20] + ".webp")


def from_disk(folder: Path | None, k: tuple) -> bytes | None:
    """The kept thumbnail, or None without a folder or a file."""
    if folder is None:
        return None
    try:
        return disk_path(folder, k).read_bytes()
    except OSError:
        return None


def to_disk(folder: Path | None, k: tuple, data: bytes) -> None:
    """Keep a thumbnail on disk (written whole, then renamed); never a stop."""
    if folder is None:
        return
    target = disk_path(folder, k)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_suffix(f".{threading.get_ident()}.part")
        part.write_bytes(data)
        part.replace(target)
    except OSError:
        return


def rendered(path: Path, width: int, k: tuple, folder: Path | None) -> bytes:
    """The thumbnail from the disk cache, else rendered and kept there."""
    data = from_disk(folder, k)
    if data is None:
        data = render(path, width)
        to_disk(folder, k, data)
    return data


def thumb(path: Path, rel: str, width: int, lru: Lru, folder: Path | None = None) -> bytes:
    """The cached thumbnail: memory, then disk, then a render."""
    k = key(rel, path, width)
    data = lru.get(k)
    if data is None:
        data = rendered(path, width, k, folder)
        lru.put(k, data)
    return data


async def thumb_async(path: Path, rel: str, width: int, lru: Lru, limiter: anyio.CapacityLimiter,
                      folder: Path | None = None) -> bytes:
    """The cached thumbnail; a miss renders on a worker thread, at most
    `limiter`'s tokens at once (looked up again under the token, so a burst for
    one picture renders it once)."""
    k = key(rel, path, width)
    data = lru.get(k)
    if data is None:
        async with limiter:
            data = lru.get(k)
            if data is None:
                data = await anyio.to_thread.run_sync(rendered, path, width, k, folder)
                lru.put(k, data)
    return data
