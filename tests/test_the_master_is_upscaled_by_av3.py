"""The master's one upscale is a light temporal denoise at 768 (`hqdn3d=0:0:4:4`), then
Real-ESRGAN realesr-animevideov3 x4 to 3072 (main session 2026-10-18, measured:
docs/audit/2026-10-18_upscale/UPSCALE.md -- background jitter -51..-58 % against RTX VSR,
face crispness +21..+33 %, ~4.7 min per episode).

The denoise is temporal, so it runs PER SHOT: no frame blends across a hard cut.  The
frame loop runs under ComfyUI's embedded python (CUDA torch + spandrel); the repo venv's
torch is CPU-only.  These tests run ffmpeg on synthetic frames and a CPU stand-in for
the model: free, no GPU, no weights."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from studio import face_paste as fp
from studio import master_av3 as av
from studio import master_upscale as mu


def nearest(frame):
    return frame.repeat(4, axis=0).repeat(4, axis=1)


# -- the setting --------------------------------------------------------------------------

def test_the_default_is_av3_x4_to_3072():
    up = mu.choice({})
    assert (up.engine, up.factor) == ("av3", 4) and mu.name_of(up) == "av3"
    assert mu.size(768, 768, up) == (3072, 3072)


def test_rtx_and_lanczos_stay_selectable():
    assert mu.choice({mu.SETTING: "rtx4x"}).engine == "rtx"
    assert mu.choice({mu.SETTING: "rtx2x"}).factor == 2
    assert mu.choice({mu.SETTING: "lanczos"}) == mu.LANCZOS


def test_the_av3_runtime_is_the_portable_python_and_the_comfy_model_folder():
    python, weights = mu.av3_paths({"COMFY_PORTABLE": "X:/portable"})
    assert python == Path("X:/portable/python_embeded/python.exe")
    assert weights == Path("X:/portable/ComfyUI/models/upscale_models/realesr-animevideov3.pth")


def test_missing_weights_fall_back_to_lanczos_and_say_why(tmp_path):
    python = tmp_path / "python.exe"
    python.write_bytes(b"")
    why = mu.av3_missing((python, tmp_path / "realesr-animevideov3.pth"))
    assert "realesr-animevideov3.pth" in why
    up, said = mu.settle(mu.choice({}), why)
    assert up == mu.LANCZOS and "av3" in said


def test_a_ready_runtime_keeps_av3(tmp_path):
    for name in ("python.exe", "w.pth"):
        (tmp_path / name).write_bytes(b"")
    assert mu.av3_missing((tmp_path / "python.exe", tmp_path / "w.pth")) == ""


def test_resolved_asks_the_av3_runtime_not_the_rtx_one(monkeypatch):
    monkeypatch.setattr(mu, "rtx_missing", lambda: "should not be asked")
    monkeypatch.setattr(mu, "av3_missing", lambda paths: "")
    assert mu.resolved({}) == (mu.choice({}), "")


# -- the denoise runs per shot -----------------------------------------------------------

def test_cuts_become_segment_lengths_with_an_open_tail():
    assert av.lengths([50, 120]) == [50, 70, None]
    assert av.lengths([]) == [None]
    assert av.lengths([0, 50, 50, 120]) == [50, 70, None], "a cut at 0 or twice is one cut"


def grey_frames(levels, width=32, height=32, seed=7):
    """Raw rgb24 frames: a grey level per frame plus grain, the way H3's walls boil."""
    rng = np.random.default_rng(seed)
    out = []
    for level in levels:
        y = np.clip(level + rng.normal(0, 3, (height, width)), 0, 255).astype(np.uint8)
        out.append(np.repeat(y[..., None], 3, axis=2).tobytes())
    return out


def filtered(frames, width, height, cuts, filt):
    feed = iter(frames + [b""])
    seg = av.Segmented(lambda n: next(feed), width, height, av.lengths(cuts), filt)
    size, got = width * height * 3, []
    while len(buf := seg.read(size)) == size:
        got.append(np.frombuffer(buf, np.uint8).reshape(height, width, 3).astype(int))
    return got


def test_the_cut_frame_stays_clean_when_the_denoise_runs_per_shot():
    frames = grey_frames([100] * 6 + [110] * 6)
    plain = filtered(frames, 32, 32, [6], "null")
    per_shot = filtered(frames, 32, 32, [6], av.PREFILTER)
    one_stream = filtered(frames, 32, 32, [], av.PREFILTER)
    alone = filtered(frames[6:], 32, 32, [], av.PREFILTER)
    assert len(per_shot) == len(plain) == 12
    assert np.array_equal(per_shot[6], alone[0]), "the cut frame is the second shot's own, as if filtered alone"
    assert np.abs(per_shot[6] - plain[6]).max() <= 2, "hqdn3d's first frame is the source, to its 16-bit rounding"
    assert np.abs(one_stream[6] - alone[0]).mean() > 0.3, "the ruler sees the trace a joined stream leaves"
    assert np.abs(per_shot[8] - plain[8]).mean() > 0.3, "inside a shot the denoise still works"


def test_every_frame_comes_through_once_in_order():
    frames = grey_frames([20 * k for k in range(9)])
    got = filtered(frames, 32, 32, [3, 5], "null")
    means = [f.mean() for f in got]
    assert len(got) == 9 and means == sorted(means) and len(set(np.round(means))) == 9


# -- the paste rides the av3 pass at master scale -------------------------------------------

def solid(path, colour, seconds=0.5, size="64x64"):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c={colour}:s={size}:r=24:d={seconds}",
                    "-f", "lavfi", "-t", str(seconds), "-i", "sine=f=440:r=48000",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-ar", "48000", str(path)], check=True)
    return path


def first_frame(path, size):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(size, size, 3)


def a_span(crop: Path) -> fp.Span:
    track = fp.Track([(16, 8, 24)] * 12, (0, 11), 0, str(crop))
    return fp.Span(0, 0, 12, 0, 1.0, None, (track,))


def test_spans_cross_to_the_worker_unchanged(tmp_path):
    spans = [a_span(tmp_path / "c.mp4")]
    assert av.spans_back(json.loads(json.dumps(av.spans_json(spans)))) == spans


def test_the_worker_pastes_the_crop_where_the_rtx_pass_did(tmp_path):
    listing = tmp_path / "l.txt"
    listing.write_text(f"file '{solid(tmp_path / 'a.mp4', 'black').as_posix()}'\n", encoding="utf-8")
    crop = solid(tmp_path / "crop.mp4", "white", size="32x32")
    job = mu.av3_job(listing, tmp_path / "o.mp4", 64, 64, mu.choice({}), 24, [a_span(crop)], [], Path("w.pth"))
    av.run(json.loads(json.dumps(job)), upscaler=nearest)
    img = first_frame(tmp_path / "o.mp4", 256)
    x, y, s = fp.to_master((16, 8, 24), None, 64, 64, 4)
    assert (x, y, s) == (64, 32, 96)
    centre = img[y + s // 2, x + s // 2]
    assert centre.mean() > 30, "the white crop fades in from frame 0 at master scale"
    assert img[y + s // 2, 8].mean() < 20 and img[240, 240].mean() < 20


def test_the_in_process_path_keeps_every_frame_and_the_sound(tmp_path):
    parts = [solid(tmp_path / "a.mp4", "red", 1.0), solid(tmp_path / "b.mp4", "blue", 0.5)]
    listing = tmp_path / "l.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    out = mu.master(listing, tmp_path / "o.mp4", 64, 64, mu.choice({}), 24, upscaler=nearest, cuts=[24])
    head = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(out)], capture_output=True, text=True).stderr
    count = subprocess.run(["ffmpeg", "-v", "quiet", "-stats", "-i", str(out), "-map", "0:v", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    assert "256x256" in head and "Audio:" in head
    assert int(count.rsplit("frame=", 1)[1].split()[0]) == 36


def test_the_worker_runs_under_the_portable_python_isolated(tmp_path):
    argv = mu.worker_argv(Path("X:/py/python.exe"), tmp_path / "job.json")
    assert argv[0] == str(Path("X:/py/python.exe")) and argv[1] == "-I"
    assert argv[2].replace("\\", "/").endswith("studio/master_av3.py") and argv[3] == str(tmp_path / "job.json")


def test_the_wrap_hands_its_spans_to_the_worker(tmp_path):
    import functools
    spans = [a_span(tmp_path / "c.mp4")]
    wrap = functools.partial(fp.Paster, spans=spans, width=64, height=64, factor=4)
    assert mu.spans_of(wrap) == spans and mu.spans_of(None) == []


def test_the_cut_hands_the_upscale_every_shot_start(tmp_path):
    from scripts.episode import assemble
    solid(tmp_path / "seg01.mp4", "red", 0.5)
    solid(tmp_path / "seg02.mp4", "blue", 0.25)
    (tmp_path / "layout.json").write_text(json.dumps([{"index": 1}, {"index": 2}]), encoding="utf-8")
    parts = [solid(tmp_path / "mixed.mp4", "red", 0.75), solid(tmp_path / "card.mp4", "white", 0.25),
             solid(tmp_path / "black.mp4", "black", 0.5)]
    assert assemble.cut_frames(tmp_path, parts) == [12, 18, 24]


def test_no_layout_still_cuts_at_the_card_and_the_chip(tmp_path):
    from scripts.episode import assemble
    parts = [solid(tmp_path / "mixed.mp4", "red", 0.75), solid(tmp_path / "card.mp4", "white", 0.25)]
    assert assemble.cut_frames(tmp_path, parts) == [18]


def test_qc_reads_an_av3_master_under_the_sharpened_cap():
    """MEASURED 2026-10-18 on C|M|W: av3 segments 1.50-1.77 against their takes (RTX 4x
    1.64-1.69, Lanczos 0.33-0.51); the old 1.0 cap would fail every av3 master.  C1 (ada8fda,
    Jekyll ep01's 28 segments 1.47-2.10) gave av3 its own cap above RTX's 2.0."""
    from studio import edit_gate as eg
    assert eg.segment_cap("av3") == eg.SEGMENT_MEAN_AV3 == 2.5 > eg.SEGMENT_MEAN_RTX == 2.0


@pytest.mark.local
def test_the_real_model_upscales_a_frame_4x():
    _, weights = mu.av3_paths()
    up = av.Av3(weights)
    out = up(np.full((768, 768, 3), 128, np.uint8))
    assert out.shape == (3072, 3072, 3) and out.dtype == np.uint8
