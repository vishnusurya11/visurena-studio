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
    out = ep.tail(master, card, tmp_path / "out.mp4", tmp_path)
    times = gate.frame_times(out)
    assert times[0] == 0.0
    assert gate.timestamp_holes(times) == []


def test_the_master_is_every_frame_of_every_part(tmp_path):
    ep = _assemble()
    master = clip(tmp_path / "master.mp4", 1.0)
    card = clip(tmp_path / "card.mp4", 0.5)
    out = ep.tail(master, card, tmp_path / "out.mp4", tmp_path)
    chip = round(ep.END_CHIP_SECONDS * ep.FPS)
    assert frames(out) == frames(master) + frames(card) + chip


def test_a_part_the_join_silently_drops_is_refused(tmp_path):
    """The concat demuxer does not refuse a part whose picture does not match:
    it drops it and reports success, which is how a master four frames short
    shipped without anyone seeing it.  So the join counts its own frames."""
    ep = _assemble()
    # the card is rescaled on the way in, so the part that can mismatch is the
    # cut itself: a master at the wrong size takes the chip down with it
    odd = clip(tmp_path / "master.mp4", 1.0, size="256x448")
    card = clip(tmp_path / "card.mp4", 0.5)
    try:
        ep.tail(odd, card, tmp_path / "out.mp4", tmp_path)
    except RuntimeError as raised:
        assert "frames" in str(raised)
    else:
        raise AssertionError("a dropped part was joined without complaint")
