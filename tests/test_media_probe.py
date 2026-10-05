"""The media probe (panel ruling 5.2, P05): on a running board, every play path of a
unit page presents three frames (requestVideoFrameCallback) on a visible element
with a picture, and every close leaves no media playing.  Drives the gstack browse
daemon against BOARD_URL (default http://127.0.0.1:8700) on real units; marked
`local` -- it needs a live board and the library, so the default run skips it.
Run: `BOARD_URL=http://127.0.0.1:8705 uv run pytest -m local tests/test_media_probe.py`."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

BROWSE = Path.home() / ".claude" / "skills" / "gstack" / "browse" / "dist" / "browse.exe"
BOARD = os.environ.get("BOARD_URL", "http://127.0.0.1:8700")
UNITS = os.environ.get("PROBE_UNITS", "episode/20260827135508/ep12,episode/20260827135508/ep17").split(",")

FRAMES = """new Promise(res => {{ const v = {pick};
  if (!v) return res(JSON.stringify({{none: true}}));
  v.muted = true; v.play().then(() => {{ let n = 0; const f = () => {{ n++; if (n < 3) v.requestVideoFrameCallback(f); else {{
    const b = v.getBoundingClientRect(), top = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
    res(JSON.stringify({{frames: n, w: v.videoWidth, vis: v.checkVisibility(), top: top === v || v.contains(top)}})); }} }};
    v.requestVideoFrameCallback(f); }}).catch(e => res(JSON.stringify({{error: String(e)}}))); }})"""
PLAYING = ("new Promise(r => setTimeout(() => r(String([...document.querySelectorAll('video,audio')]"
           ".filter(v => !v.paused).length)), 400))")


def chain(steps: list) -> list[str]:
    """Run a browse chain; the [js] results in order."""
    out = subprocess.run([str(BROWSE), "chain"], input=json.dumps(steps), capture_output=True, text=True, timeout=180).stdout
    lines = out.splitlines() + [""]
    return [js_value(lines, i) for i, line in enumerate(lines) if line.startswith("[js]")]


def js_value(lines: list[str], i: int) -> str:
    """The value printed after `[js]`, on its own line or the next."""
    same = lines[i][4:].strip()
    return same or lines[i + 1].strip()


def frames_ok(raw: str) -> bool:
    got = json.loads(raw)
    return got.get("none") or (got.get("frames") == 3 and got.get("w", 0) > 0 and got.get("vis") and got.get("top"))


@pytest.mark.local
@pytest.mark.parametrize("unit", UNITS)
def test_every_play_path_shows_a_picture_and_every_close_stops_it(unit):
    page = f"{BOARD}/d/{unit}"
    master = FRAMES.format(pick="document.getElementById('master-video')")
    viewer = FRAMES.format(pick="document.querySelector('dialog#viewer[open] video.vw-video')")
    js = chain([["viewport", "1440x900"], ["goto", page], ["wait", "--networkidle"], ["scroll", "#master"],
                ["js", master], ["js", "document.getElementById('master-video') && document.getElementById('master-video').pause()"],
                ["click", ".shot .frame.tk[data-depth='take'], .shot .frame.tk"], ["wait", "dialog#viewer[open]"], ["wait", "1500"],
                ["js", viewer], ["press", "Escape"], ["press", "Escape"], ["js", PLAYING]])
    assert frames_ok(js[0]), js[0]
    assert frames_ok(js[2]), js[2]
    assert js[-1] == "0", f"{js[-1]} media still playing after the Viewer closed"
