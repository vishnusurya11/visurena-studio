"""What is joined after the last picture frame: the title card, then black.

MEASURED on the real card, 2026-09-12: the conform put 90 frames in and got 89
out, and left 3.80 s of sound over 3.71 s of picture -- so the join then HELD
the card's last frame for 0.09 s before the black.  The `fps=` filter is what
drops the frame; an output frame rate does the same conforming and keeps it.

The chip had its own bug: `-shortest` across two lavfi inputs is a race, and
the same code gave 6 frames one run and 48 the next.  A duration is not a race.

Free: ffmpeg's own testsrc, no GPU, no money.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from studio.master_upscale import LANCZOS, Upscale  # noqa: E402


def _assemble():
    spec = importlib.util.spec_from_file_location("ep_assemble", ROOT / "scripts" / "episode" / "assemble.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clip(path: Path, seconds: float, fps: int = 24, size: str = "768x1344") -> Path:
    """A short clip with picture and sound, both exactly `seconds` long.

    At the episode's own size: the concat demuxer will not join parts whose
    pictures differ, and a mismatched part is silently dropped rather than
    refused."""
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=s={size}:r={fps}:d={seconds}",
                    "-f", "lavfi", "-t", str(seconds), "-i", "sine=f=440:r=48000",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-ar", "48000", str(path)], check=True)
    return path


def frames(video: Path) -> int:
    out = subprocess.run(["ffmpeg", "-v", "quiet", "-stats", "-i", str(video), "-map", "0:v",
                          "-f", "null", "-"], capture_output=True, text=True)
    return int(out.stderr.rsplit("frame=", 1)[1].split()[0])


def test_the_card_keeps_every_frame_it_was_given(tmp_path):
    """90 frames in, 89 out, on the real card: the `fps=` filter drops one."""
    ep = _assemble()
    source = clip(tmp_path / "card.mp4", 1.0)
    out = ep.conform_card(source, tmp_path / "conformed.mp4")
    assert frames(out) == frames(source) == 24


def test_the_cards_sound_ends_with_its_picture(tmp_path):
    """Sound over the last frame is what the join holds that frame for."""
    ep = _assemble()
    out = ep.conform_card(clip(tmp_path / "card.mp4", 1.0), tmp_path / "conformed.mp4")
    from studio import trailer_assemble as ta
    assert abs(ta.clip_seconds(out) - frames(out) / ep.FPS) <= 0.5 / ep.FPS


def test_the_black_chip_is_the_length_it_says_every_time(tmp_path):
    """`-shortest` across two lavfi inputs gave 6 frames one run and 48 the next."""
    ep = _assemble()
    counts = {frames(ep.black_chip(tmp_path / f"black{k}.mp4")) for k in range(2)}
    assert counts == {round(ep.END_CHIP_SECONDS * ep.FPS)}


def test_the_master_starts_at_frame_zero_and_never_stalls(tmp_path):
    """MEASURED on the real cut: the mix's first frame sits at 0.000 and the
    concat's at 0.041 -- the whole picture joined one frame late, which is also
    why every cut in QC read a frame past the frame the plan named."""
    ep = _assemble()
    from studio import edit_gate as gate

    master = clip(tmp_path / "master.mp4", 1.0)
    card = clip(tmp_path / "card.mp4", 0.5)
    out = ep.tail(master, card, tmp_path / "out.mp4", tmp_path, upscale=LANCZOS)
    times = gate.frame_times(out)
    assert times[0] == 0.0
    assert gate.timestamp_holes(times) == []


def test_the_master_is_every_frame_of_every_part(tmp_path):
    ep = _assemble()
    master = clip(tmp_path / "master.mp4", 1.0)
    card = clip(tmp_path / "card.mp4", 0.5)
    out = ep.tail(master, card, tmp_path / "out.mp4", tmp_path, upscale=LANCZOS)
    chip = round(ep.END_CHIP_SECONDS * ep.FPS)
    assert frames(out) == frames(master) + frames(card) + chip


def test_a_part_of_another_size_is_conformed_not_dropped(tmp_path):
    """The old concat-demuxer join dropped a part whose picture did not match and
    reported success (a master four frames short shipped).  Since the master pass
    decodes every part through one scale (RTX/Lanczos path, 2026-10-14) a part of
    another size is conformed and kept; the loss itself is still refused by
    `join_lost` (tests/test_a_join_one_frame_long_is_not_a_lost_part.py)."""
    ep = _assemble()
    odd = clip(tmp_path / "master.mp4", 1.0, size="256x448")
    card = clip(tmp_path / "card.mp4", 0.5)
    out = ep.tail(odd, card, tmp_path / "out.mp4", tmp_path, upscale=LANCZOS)
    chip = round(ep.END_CHIP_SECONDS * ep.FPS)
    assert frames(out) == frames(odd) + frames(card) + chip


class Nearest:
    """The GPU's stand-in for `master_upscale.Rtx`: every pixel repeated, on the CPU."""

    def __init__(self, width, height, up):
        self.factor = up.factor

    def __call__(self, frame):
        return frame.repeat(self.factor, axis=0).repeat(self.factor, axis=1)

    def close(self):
        pass


def test_the_rtx_master_keeps_every_frame_from_zero_without_holes(tmp_path, monkeypatch):
    """OWNER 2026-10-14: the master is RTX VSR 4x.  The streamed path re-times
    raw frames; it must keep what ep15's vfr passthrough kept -- every frame of
    every part, first at 0.000, no hole."""
    ep = _assemble()
    from studio import edit_gate as gate, master_upscale as mu
    monkeypatch.setattr(ep, "W", 64)
    monkeypatch.setattr(ep, "H", 112)
    monkeypatch.setattr(mu, "Rtx", Nearest)
    master = clip(tmp_path / "master.mp4", 1.0, size="64x112")
    card = clip(tmp_path / "card.mp4", 0.5, size="64x112")
    out = ep.tail(master, card, tmp_path / "out.mp4", tmp_path, upscale=mu.CHOICES["rtx4x"])
    times = gate.frame_times(out)
    assert frames(out) == frames(master) + frames(card) + round(ep.END_CHIP_SECONDS * ep.FPS)
    assert times[0] == 0.0 and gate.timestamp_holes(times) == []
