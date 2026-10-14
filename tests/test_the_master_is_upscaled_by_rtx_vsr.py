"""The master's one upscale: RTX Video Super Resolution, in process, on the joined 768 cut.

OWNER 2026-10-14: the highest quality that costs under 10 min per episode --
4x standard ULTRA delivered at 3072 (+3.8 min measured,
docs/audit/2026-10-14_rtx_vsr_test).  2x ULTRA to 1536 stays selectable;
Lanczos 2x is the fallback when the GPU or nvidia-vfx is missing, and the
fallback is SAID, never silent.  These tests run ffmpeg on testsrc and a CPU
stand-in for the GPU: free, no model, no GPU."""
from __future__ import annotations

import subprocess

import numpy as np
import pytest

from studio import master_upscale as mu


def test_the_default_is_rtx_4x_ultra():
    up = mu.choice({})
    assert (up.engine, up.factor, up.mode) == ("rtx", 4, "ULTRA")


def test_2x_and_lanczos_are_selectable():
    assert mu.choice({mu.SETTING: "rtx2x"}).factor == 2
    lz = mu.choice({mu.SETTING: "lanczos"})
    assert (lz.engine, lz.factor) == ("lanczos", 2)


def test_an_unknown_setting_is_refused_with_the_choices():
    with pytest.raises(SystemExit) as raised:
        mu.choice({mu.SETTING: "rtx8x"})
    assert "rtx4x" in str(raised.value) and "lanczos" in str(raised.value)


def test_4x_of_the_768_cut_is_3072():
    assert mu.size(768, 768, mu.choice({})) == (3072, 3072)


def test_a_missing_gpu_falls_back_to_lanczos_and_says_why():
    up, why = mu.settle(mu.choice({}), missing="nvvfx: no CUDA device")
    assert up == mu.LANCZOS and "no CUDA device" in why and "rtx4x" in why


def test_a_ready_gpu_keeps_the_choice():
    want = mu.choice({})
    assert mu.settle(want, missing="") == (want, "")


def test_lanczos_never_asks_for_the_gpu():
    assert mu.settle(mu.LANCZOS, missing="no GPU") == (mu.LANCZOS, "")


def test_the_lanczos_pass_is_the_old_master_encode(tmp_path):
    argv = " ".join(mu.lanczos_argv(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, mu.LANCZOS))
    assert "scale=1536:1536:flags=lanczos" in argv and "-preset slow -crf 14" in argv
    assert "-itsoffset -0.0416667" in argv and "asetpts=PTS-STARTPTS" in argv


def test_the_rtx_encode_reads_raw_frames_at_the_upscaled_size(tmp_path):
    argv = " ".join(mu.encode_argv(tmp_path / "l.txt", tmp_path / "o.mp4", 3072, 3072, 24))
    assert "-f rawvideo -pix_fmt rgb24 -s 3072x3072 -framerate 24 -i -" in argv
    assert "-map 0:v -map 1:a" in argv and "-preset slow -crf 14" in argv
    assert "asetpts=PTS-STARTPTS" in argv


def test_the_decode_hands_over_every_frame_as_it_is(tmp_path):
    argv = " ".join(mu.decode_argv(tmp_path / "l.txt", 768, 768))
    assert "-fps_mode passthrough" in argv and "-f rawvideo -pix_fmt rgb24 -" in argv
    assert "scale=768:768" in argv, "a part of another size would shear the raw stream"


def nearest(factor):
    """The GPU's stand-in: every pixel repeated, on the CPU."""
    return lambda f: f.repeat(factor, axis=0).repeat(factor, axis=1)


def test_the_pump_upscales_every_frame_whole():
    frames = [np.full((4, 6, 3), k, np.uint8).tobytes() for k in range(3)]
    feed, got = iter(frames + [b""]), []
    n = mu.pump(lambda size: next(feed), got.append, 6, 4, nearest(2))
    assert n == 3 and all(len(b) == 12 * 8 * 3 for b in got)
    assert [b[0] for b in got] == [0, 1, 2]


def clip(path, seconds, size="64x64", fps=24):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=s={size}:r={fps}:d={seconds}",
                    "-f", "lavfi", "-t", str(seconds), "-i", "sine=f=440:r=48000",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-ar", "48000", str(path)], check=True)
    return path


def probe(path):
    out = subprocess.run(["ffmpeg", "-v", "quiet", "-stats", "-i", str(path), "-map", "0:v", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    head = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    import re
    w, h = re.search(r", (\d{2,5})x(\d{2,5})[ ,]", head).groups()
    return int(out.rsplit("frame=", 1)[1].split()[0]), (int(w), int(h)), "Audio:" in head


def test_the_joined_cut_comes_out_4x_with_every_frame_and_its_sound(tmp_path):
    parts = [clip(tmp_path / "a.mp4", 1.0), clip(tmp_path / "b.mp4", 0.5)]
    listing = tmp_path / "l.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    out = mu.master(listing, tmp_path / "o.mp4", 64, 64, mu.choice({}), 24, upscaler=nearest(4))
    assert probe(out) == (36, (256, 256), True)


@pytest.mark.local
def test_the_real_effect_upscales_a_frame_4x():
    up = mu.Rtx(768, 768, mu.choice({}))
    try:
        out = up(np.full((768, 768, 3), 128, np.uint8))
    finally:
        up.close()
    assert out.shape == (3072, 3072, 3) and out.dtype == np.uint8


def test_resolved_settles_the_setting_against_this_machine(monkeypatch):
    monkeypatch.setattr(mu, "rtx_missing", lambda: "no CUDA device")
    assert mu.resolved({})[0] == mu.LANCZOS
    monkeypatch.setattr(mu, "rtx_missing", lambda: "")
    assert mu.resolved({mu.SETTING: "rtx2x"}) == (mu.CHOICES["rtx2x"], "")


def test_the_fallback_is_printed_never_swallowed(capsys):
    mu.say("rtx4x unavailable (no CUDA device); fell back to lanczos 2x")
    assert "UPSCALE FALLBACK" in capsys.readouterr().err
    mu.say("")
    assert capsys.readouterr().err == ""


def test_the_delivered_canvas_follows_the_default_upscale():
    from studio import canvas
    assert canvas.deliver("1:1") == (3072, 3072)
