"""QC's segment gate reads an RTX-upscaled master as the takes it was cut from.

MEASURED 2026-10-14, Jekyll ep01, the same cut both ways (grey 128x224 against
each take, per segment):

    master_iter1 (Lanczos 2x)  offset 0: 0.35-0.55   off by one: 0.78-4.73
    master_iter2 (RTX 4x)      offset 0: 0.97-1.48   off by one: 1.50-5.20

RTX VSR sharpens by design, so every segment sits ~0.9 grey levels further from
its take; per frame the worst was 1.56, far under SAME_FRAME's 4.0, and offset
0 was the best shift on all 23.  SEGMENT_MEAN (1.0) was calibrated on Lanczos
masters and failed 7 of 23 correct segments -- a constant that outlived its
world.  The master's own upscale is recorded beside it (cut/master_layout.json,
by sha8) and picks the cap; the offset, a frame of another picture and a held
run still fail exactly as before."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import book_compilation as bc  # noqa: E402
from studio import edit_gate as eg  # noqa: E402
from studio import youtube_publish as yp  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def frames(n, level=60.0, step=8.0):
    """n moving frames: each a different picture from the last."""
    return np.stack([np.full((8, 8), level + step * k, np.float64).clip(0, 255).astype(np.uint8) for k in range(n)])


def sharpened(take):
    """The take as an RTX master shows it: every frame 1.0-1.5 grey levels off, unevenly
    (mean 1.25, not a flat level shift)."""
    out = take.astype(np.int16) + 1
    out[1::2, :4, :] += 1                     # odd frames: half the pixels one level more
    return out.clip(0, 255).astype(np.uint8)


def test_an_rtx_master_takes_the_rtx_cap():
    assert eg.segment_cap("rtx4x") == eg.segment_cap("rtx2x") == eg.SEGMENT_MEAN_RTX == 2.0


def test_a_lanczos_or_unrecorded_master_keeps_the_old_cap():
    assert eg.segment_cap("lanczos") == eg.segment_cap("") == eg.SEGMENT_MEAN == 1.0


def test_a_sharpened_segment_is_its_take_under_the_rtx_cap():
    take = frames(20)
    master = sharpened(take)
    assert eg.segment_match(master, take, 0, 20)["mean"] > eg.SEGMENT_MEAN, "its mean is over the old cap"
    assert eg.segment_match(master, take, 0, 20, cap=eg.segment_cap("rtx4x"))["ok"]


def test_a_slipped_frame_still_fails_under_the_rtx_cap():
    take = frames(20)
    master = np.concatenate([take[:1], sharpened(take)])        # one frame late
    row = eg.segment_match(master, take, 0, 20, cap=eg.segment_cap("rtx4x"))
    assert not row["ok"] and row["offset"] != 0


def test_assemble_records_the_masters_upscale_beside_its_split(tmp_path):
    asm = _load("asm_upscale_layout", "scripts/episode/assemble.py")
    master = tmp_path / "master_r2v.mp4"
    master.write_bytes(b"short")
    asm.record_layout(tmp_path, master, main=3369, card=107, upscale="rtx4x")
    layout = json.loads((tmp_path / bc.LAYOUT).read_text(encoding="utf-8"))
    assert layout[yp.sha8(master)]["upscale"] == "rtx4x"
    assert bc.recorded_split(layout, yp.sha8(master)) == (3369, 107)


def test_qc_reads_the_upscale_of_these_bytes(tmp_path):
    qc = _load("qc_upscale_layout", "scripts/episode/qc.py")
    master = tmp_path / "master_r2v.mp4"
    master.write_bytes(b"short")
    (tmp_path / bc.LAYOUT).write_text(json.dumps({yp.sha8(master): {"upscale": "rtx4x"}}), encoding="utf-8")
    assert qc.upscale_of(master) == "rtx4x"


def test_qc_reads_no_upscale_for_older_bytes(tmp_path):
    qc = _load("qc_upscale_layout_old", "scripts/episode/qc.py")
    master = tmp_path / "master_r2v.mp4"
    master.write_bytes(b"older")
    assert qc.upscale_of(master) == ""
