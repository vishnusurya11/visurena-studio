"""HARD REQUIREMENT (owner, 2026-09-30: "it has to be short .. the format has
to be 1*1"): every episode master is a YouTube SHORT -- square, and at most
3:00 of delivered runtime, because YouTube files anything longer as a regular
video.  ep14 shipped as a video at 182.6 s: every runtime wall in the pipeline
capped the PICTURE at 180 s, and assemble then appended the ~4.46 s animated
title card and the 0.25 s black chip AFTER the picture.  The constant outlived
its world.

The fix is one derivation: the contract owns SHORT_WALL_S (YouTube's limit)
and TAIL_ALLOWANCE_S (what assemble appends past the picture, plus margin),
and MAX_SECONDS -- the picture's budget, already enforced by the contract
validator and the timeline refusal -- is DERIVED as wall minus tail, never
restated.  `short_refusal` is the one sentence every later wall (assemble, qc,
upload) speaks about a delivered master."""
from __future__ import annotations

from studio import episode_spec as spec


def test_the_picture_budget_is_derived_from_the_shorts_wall():
    assert spec.SHORT_WALL_S == 180.0
    assert spec.TAIL_ALLOWANCE_S >= 4.71          # card 4.46 s + chip 0.25 s, measured on ep14
    assert spec.MAX_SECONDS == spec.SHORT_WALL_S - spec.TAIL_ALLOWANCE_S
    assert spec.MAX_SECONDS < 180.0               # the old restated 180 is what shipped ep14 as a video
    assert spec.MIN_SECONDS == 120.0              # the floor is untouched


def test_ep14s_placed_runtime_is_now_refused():
    # 177.88 s of picture passed the old 180 band and delivered 182.6 s.
    assert not spec.MIN_SECONDS <= 177.88 <= spec.MAX_SECONDS


def test_short_refusal_names_the_overrun_and_passes_a_short():
    assert spec.short_refusal(178.1) == ""
    assert spec.short_refusal(spec.SHORT_WALL_S) == ""
    said = spec.short_refusal(182.58)
    assert "182.6" in said and "180" in said and "Short" in said


def qc_module():
    import importlib.util
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    loader = importlib.util.spec_from_file_location("ep_qc_short", root / "scripts" / "episode" / "qc.py")
    qc = importlib.util.module_from_spec(loader)
    sys.modules["ep_qc_short"] = qc
    loader.loader.exec_module(qc)
    return qc


def test_both_doors_read_the_file_itself_past_every_override():
    """--override waives qc.passed at upload, and ep14 went up at 182.58 s
    through exactly that door.  The file's own facts -- a Short, and square --
    are judged at upload AND at the public flip, off the master, unwaivable."""
    from studio import youtube_publish as yp
    assert yp.file_refusals(178.1, 1536, 1536) == []
    said = yp.file_refusals(182.58, 1536, 1536)
    assert len(said) == 1 and "Short" in said[0]
    said = yp.file_refusals(160.0, 1536, 2688)
    assert len(said) == 1 and "1536x2688" in said[0] and "1:1" in said[0]
    assert len(yp.file_refusals(182.58, 1536, 2688)) == 2
    assert "unmeasured" in yp.file_refusals(0.0, 0, 0)[0]


def test_a_master_past_the_wall_is_not_a_qc_pass():
    """ep14's qc passed at 182.58 s because no gate read the delivered length
    against the wall; `report['seconds']` was measured and judged by nothing."""
    qc = qc_module()
    good = {"title_card": True, "lufs_ok": True, "tp_ok": True, "missing_cuts": [],
            "lines": [{"passed": True}], "edit": {"ok": True, "measured": True}, "seconds": 178.1}
    assert qc.verdict(good)
    assert not qc.verdict({**good, "seconds": 182.58})
    assert not qc.verdict({k: v for k, v in good.items() if k != "seconds"})  # unmeasured is not a pass
