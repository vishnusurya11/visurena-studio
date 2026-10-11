"""A cold department page rendered every poster again after each restart, and
copied each one whole (convert('RGB') before thumbnail()).  An RGB picture now
shrinks first and converts only the small one -- the same size, the same
format -- and a thumbnail is kept on disk under a cache folder keyed by
(rel, mtime_ns, size, width), so a restarted board is not cold."""
from __future__ import annotations

import io

from PIL import Image

from studio.command_center import thumbs


def _png(path, size=(1600, 900), mode="RGBA"):
    colour = {"RGBA": (40, 50, 60, 255), "RGB": (40, 50, 60)}.get(mode, 7)
    Image.new(mode, size, colour).save(path, "PNG")
    return path


def test_a_render_is_the_same_size_and_format_as_before(tmp_path):
    for mode in ("RGB", "RGBA", "P", "L"):
        data = thumbs.render(_png(tmp_path / f"a_{mode}.png", mode=mode), 320)
        im = Image.open(io.BytesIO(data))
        assert (im.format, im.size, im.mode) == ("WEBP", (320, 180), "RGB")


def test_the_whole_picture_is_never_converted(tmp_path, monkeypatch):
    sizes = []
    original = Image.Image.convert

    def spy(self, *a, **k):
        sizes.append(self.size)
        return original(self, *a, **k)
    monkeypatch.setattr(Image.Image, "convert", spy)
    thumbs.render(_png(tmp_path / "big.png", (2000, 2000), "RGB"), 160)
    assert sizes and max(w for w, _ in sizes) <= 160


def test_a_thumb_kept_on_disk_survives_a_restart(tmp_path, monkeypatch):
    pic, cache = _png(tmp_path / "p.png"), tmp_path / "cache"
    first = thumbs.thumb(pic, "episodes/ep01/p.png", 160, thumbs.Lru(), cache)
    assert list(cache.glob("*.webp"))
    monkeypatch.setattr(thumbs, "render", lambda *a: (_ for _ in ()).throw(AssertionError("rendered")))
    assert thumbs.thumb(pic, "episodes/ep01/p.png", 160, thumbs.Lru(), cache) == first


def test_a_new_mtime_is_a_new_file_on_disk(tmp_path):
    import os
    pic, cache = _png(tmp_path / "p.png"), tmp_path / "cache"
    a = thumbs.disk_path(cache, thumbs.key("r.png", pic, 160))
    os.utime(pic, ns=(1, 1))
    b = thumbs.disk_path(cache, thumbs.key("r.png", pic, 160))
    assert a != b and a.parent == cache and a.suffix == ".webp"


def test_without_a_cache_folder_nothing_is_written(tmp_path):
    pic = _png(tmp_path / "p.png")
    thumbs.thumb(pic, "p.png", 160, thumbs.Lru())
    assert sorted(p.name for p in tmp_path.iterdir()) == ["p.png"]


def test_the_board_keeps_its_thumbs_beside_the_library(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from command_center_fixtures import CODEX, make_app
    from studio.command_center import app as cc_app
    assert cc_app.thumb_dir(tmp_path / "library") == tmp_path / ".cache" / "thumbs"
    app = make_app(tmp_path, monkeypatch)
    rel = "episodes/ep04/storyboard/shot_00.png"
    _png(next(app.state.library.glob(f"{CODEX}_*")) / rel)
    assert TestClient(app).get(f"/thumb/{CODEX}/160/{rel}").status_code == 200
    assert list((tmp_path / ".cache" / "thumbs").glob("*.webp"))

