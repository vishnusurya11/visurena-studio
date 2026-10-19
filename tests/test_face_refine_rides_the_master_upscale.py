"""The paste rides the master's one upscale pass (studio/master_upscale.master,
`wrap=`): each cut frame is pasted, then upscaled, then encoded -- no second encode
(owner 2026-10-18: the upscale is the last picture operation).
The Lanczos fallback has no frame loop, so it pastes nothing and SAYS so.  And
assemble records the cut's layout (`work/layout.json`) so the paste can find
where every take sits.  ffmpeg on testsrc, a CPU stand-in for RTX VSR."""
from __future__ import annotations

import json
import subprocess

import numpy as np

from studio import master_upscale as mu


def nearest(f):
    return f.repeat(4, axis=0).repeat(4, axis=1)


def clip(path, seconds, size="64x64", fps=24):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s={size}:r={fps}:d={seconds}",
                    "-f", "lavfi", "-t", str(seconds), "-i", "sine=f=440:r=48000",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-ar", "48000", str(path)], check=True)
    return path


def listing_of(tmp_path, parts):
    listing = tmp_path / "l.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    return listing


def test_a_wrap_pastes_every_cut_frame_before_the_upscale(tmp_path):
    """Owner 2026-10-18: the paste is at cut scale, ahead of the one upscale."""
    listing = listing_of(tmp_path, [clip(tmp_path / "a.mp4", 0.5)])
    seen = []

    def wrap(up):
        def paste(frame):
            out = up(frame).copy()
            out[25:37, 25:37] = 255
            seen.append(out.shape)
            return out
        return paste

    out = mu.master(listing, tmp_path / "o.mp4", 64, 64, mu.CHOICES["rtx4x"], 24, upscaler=nearest, wrap=wrap)
    assert seen and set(seen) == {(64, 64, 3)}
    frame = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-frames:v", "1", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    img = np.frombuffer(frame, np.uint8).reshape(256, 256, 3)
    assert img[125, 125].mean() > 200 and img[20, 20].mean() < 40


def test_no_wrap_is_the_upscale_as_it_was(tmp_path):
    listing = listing_of(tmp_path, [clip(tmp_path / "a.mp4", 0.25)])
    assert mu.master(listing, tmp_path / "o.mp4", 64, 64, mu.choice({}), 24, upscaler=nearest).exists()


def test_the_lanczos_fallback_pastes_nothing_and_says_so(tmp_path, capsys):
    listing = listing_of(tmp_path, [clip(tmp_path / "a.mp4", 0.25)])
    mu.master(listing, tmp_path / "o.mp4", 64, 64, mu.LANCZOS, 24, wrap=lambda up: up)
    assert "FACE REFINE" in capsys.readouterr().err


def test_the_cut_writes_where_every_take_sits(tmp_path):
    from scripts.episode import assemble
    rows = assemble.layout_rows([(0, 2.0), (3, 1.5)], {3: 0.25}, {0: 1.0, 3: 1.2}, {})
    assert rows == [{"index": 0, "seconds": 2.0, "head": 0.0, "slow": 1.0, "still": False},
                    {"index": 3, "seconds": 1.5, "head": 0.25, "slow": 1.2, "still": False}]
    assert json.loads(json.dumps(rows)) == rows


def test_no_refine_file_gives_the_upscale_no_wrap(tmp_path):
    from scripts.episode import assemble
    (tmp_path / "layout.json").write_text("[]")
    assert assemble.face_paste_wrap(tmp_path, tmp_path, 4) is None


def test_a_kept_current_refine_wraps_the_upscale(tmp_path):
    from scripts.episode import assemble
    from studio import face_paste
    work, room = tmp_path / "work", tmp_path / "room"
    (room / "refine").mkdir(parents=True)
    work.mkdir()
    clip(work / "seg03.mp4", 0.5)
    clip(room / "T03.mp4", 0.5)
    (work / "layout.json").write_text(json.dumps([{"index": 3, "seconds": 0.5, "head": 0.0, "slow": 1.0,
                                                   "still": False}]))
    (room / "refine" / "T03_p0.json").write_text(json.dumps({"windows": [[0, 0, 32]] * 12, "life": [0, 11],
                                                             "start": 0}))
    (room / "refine.json").write_text(json.dumps({"T03": {"take_sha8": face_paste.sha8(room / "T03.mp4"), "people": [
        {"who": "a", "crop": "refine/T03_p0.mp4", "track": "refine/T03_p0.json", "kept": True}]}}))
    wrap = assemble.face_paste_wrap(work, room, 4)
    assert wrap is not None and isinstance(wrap(nearest), face_paste.Paster)
    assert len(wrap(nearest).spans) == 1 and wrap(nearest).spans[0].frames == 12
