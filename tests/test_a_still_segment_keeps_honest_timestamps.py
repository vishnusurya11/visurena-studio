"""ep15 (2026-10-01): shot 3's still segment -- a single-image zoompan with no
explicit output cadence -- muxed all 205 of its frames on broken timestamps,
and the master join dropped them SILENTLY (8.5 s of picture gone; join_lost
caught the count, nothing named the cause).  A still segment now carries
`-fps_mode cfr -r` like every take segment, and a cfr re-pipe drops zero of
its frames.  Local ffmpeg only; no GPU, no credit."""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("asm", ROOT / "scripts" / "episode" / "assemble.py")
asm = importlib.util.module_from_spec(loader)
sys.modules["asm"] = asm
loader.loader.exec_module(asm)


def ffmpeg_missing() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return False
    except (OSError, subprocess.CalledProcessError):
        return True


@pytest.mark.skipif(ffmpeg_missing(), reason="no ffmpeg on PATH")
def test_a_cfr_re_pipe_drops_none_of_a_stills_frames(tmp_path):
    from PIL import Image
    panel = tmp_path / "panel.png"
    Image.new("RGB", (768, 768), (40, 80, 120)).save(panel)
    seg = asm.still_segment(panel, 2.0, tmp_path / "seg.mp4", 256, 256, 24)
    out = subprocess.run(["ffmpeg", "-y", "-v", "info", "-i", str(seg),
                          "-vf", "setpts=PTS-STARTPTS,scale=64:64",
                          "-fps_mode", "cfr", "-r", "24", "-an",
                          "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
                          str(tmp_path / "probe.mp4")],
                         capture_output=True, text=True)
    stats = [l for l in (out.stderr or "").splitlines() if "drop=" in l or "frame=" in l]
    said = stats[-1] if stats else (out.stderr or "")[-300:]
    drops = re.search(r"drop=(\d+)", said)
    assert drops is None or drops.group(1) == "0", said[-220:]   # ffmpeg omits drop= when zero
    frames = re.findall(r"frame=\s*(\d+)", said)
    assert frames and int(frames[-1]) == 48, said[-220:]
