"""The speaker check pairs only lines long enough to measure a voice in.

ep13 (2026-09-28): the publish lock stopped on "curate is not one voice (worst
pair 0.304: l16/l23)" and "narrator (0.096: l09/l14)" -- l23 is "Listen!" and
l14 "What are we?", both under 2 s.  Finding 40 measured that slices of one
man's own voice score 0.07-0.58 under 2 s; say_lines records such a line and
gates nothing on it (SIM_MEASURABLE_S).  The speaker check now does the same.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("speaker_check_short", ROOT / "scripts/episode/speaker_check.py")
sc = importlib.util.module_from_spec(_spec)
sys.modules["speaker_check_short"] = sc
_spec.loader.exec_module(sc)


def test_a_line_under_two_seconds_is_left_out(tmp_path):
    room = tmp_path / "audio" / "lines"
    room.mkdir(parents=True)
    for i, seconds in ((0, 3.0), (1, 1.2), (2, 2.5)):
        sf.write(room / f"l{i:02d}.wav", np.zeros(int(16000 * seconds)), 16000)
    (room / "lines.json").write_text(json.dumps([{"index": i, "speaker": "curate"} for i in range(3)]),
                                     encoding="utf-8")
    got = sc.lines_by_speaker(tmp_path)
    assert [name for name, _ in got["curate"]] == ["l00", "l02"]


def test_an_emotional_pair_gets_the_floor_say_lines_gives_each_line():
    """ep13's curate: l12 grieving and l16 shouting each passed their
    delivery-aware floor against his design (0.48, 0.54) and measured 0.37
    against each other.  Each emotional line lowers the pair's floor by
    FEELING_FLOOR_DROP; a calm pair keeps 0.70 (ep05's real split was 0.58)."""
    from studio import speaker_spread as sp
    sims = {("l12", "l16"): 0.37}
    assert sp.spread(sims, allow={("l12", "l16"): 0.4})["ok"]
    assert not sp.spread({("a", "b"): 0.58})["ok"]
    assert not sp.spread({("a", "b"): 0.58}, allow={("a", "b"): 0.0})["ok"]
