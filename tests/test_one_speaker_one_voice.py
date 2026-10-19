"""A speaker's own lines must sound like each other, not just like the design clip."""
from studio.speaker_spread import SAME_SPEAKER_FLOOR, spread, worst_pair


def test_lines_that_agree_pass():
    sims = {("l05", "l24"): 0.92, ("l05", "l09"): 0.88, ("l09", "l24"): 0.90}
    assert spread(sims)["ok"]
    assert spread(sims)["worst"] == 0.88


def test_a_published_episodes_worst_pair_still_passes():
    assert spread({("l01", "l19"): 0.72})["ok"]


def test_two_men_under_one_name_fail():
    """ep05: the neighbour's l05 and l24 each passed against the design clip and
    measured 0.58 against EACH OTHER -- two different men in one part."""
    sims = {("l05", "l24"): 0.58, ("l05", "l09"): 0.91}
    out = spread(sims)
    assert not out["ok"] and out["worst"] == 0.58
    assert worst_pair(sims) == ("l05", "l24")


def test_one_line_is_always_consistent_with_itself():
    assert spread({})["ok"] and spread({})["worst"] is None


def test_the_floor_passes_every_episode_already_published():
    """ep01 0.76, ep02 0.76, ep03 0.72 were watched, approved and published;
    the one real split measured 0.58. The floor has to clear the first three."""
    assert SAME_SPEAKER_FLOOR < 0.72
    assert SAME_SPEAKER_FLOOR > 0.58


# ---- P11: a line under two seconds is unconfirmed by the pair measure; its register is checked

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

_spec = importlib.util.spec_from_file_location(
    "ep_speaker_check", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "speaker_check.py")
check = importlib.util.module_from_spec(_spec)
sys.modules["ep_speaker_check"] = check
_spec.loader.exec_module(check)


def tone(path, hz, seconds):
    t = np.arange(int(24000 * seconds)) / 24000
    sf.write(path, (0.3 * np.sin(2 * np.pi * hz * t)).astype("float32"), 24000)
    return path


def test_a_short_clip_six_semitones_off_the_register_is_not_ok(tmp_path):
    clip = tone(tmp_path / "a.wav", 150 * 2 ** (6 / 12), 1.8)
    assert check.short_register_ok(clip, 150.0) is False


def test_a_short_clip_on_the_register_is_ok(tmp_path):
    assert check.short_register_ok(tone(tmp_path / "a.wav", 150, 1.8), 150.0) is True


def test_the_register_is_the_median_of_the_speakers_long_lines(tmp_path):
    clips = [tone(tmp_path / f"{n}.wav", hz, 2.5) for n, hz in (("a", 140), ("b", 150), ("c", 160))]
    assert abs(check.register_hz(clips) - 150) < 3


def test_short_lines_and_far_keep_bests_are_rows_with_their_offset(tmp_path):
    home = tmp_path
    lines = home / "audio" / "lines"
    lines.mkdir(parents=True)
    tone(lines / "l00.wav", 150, 2.5)
    tone(lines / "l01.wav", 150 * 2 ** (6 / 12), 1.8)
    tone(lines / "l02.wav", 150, 3.0)
    rows = [{"index": 0, "speaker": "a", "seconds": 2.5}, {"index": 1, "speaker": "a", "seconds": 1.8},
            {"index": 2, "speaker": "a", "seconds": 3.0, "flagged": "keep_best_far"}]
    out = check.short_rows(home, rows)
    by = {r["line"]: r for r in out}
    assert set(by) == {"l01", "l02"}
    assert by["l01"]["short_register_ok"] is False and by["l02"]["short_register_ok"] is True
    assert by["l01"]["offset_st"] > 4.0


def test_the_report_carries_short_lines_and_a_flagged_row_without_a_voice_verdict(tmp_path):
    rows = [{"line": "l01", "speaker": "a", "short_register_ok": False},
            {"line": "l02", "speaker": "a", "short_register_ok": True}]
    doc = check.with_short_lines({"a": {"ok": True, "lines": 3}}, rows)
    assert doc["short_lines"] == rows and doc["short_flagged"] == ["l01"]
    assert doc["a"]["ok"] is True
