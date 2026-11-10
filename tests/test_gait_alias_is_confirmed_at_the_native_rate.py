"""Jekyll ep07 retro S7 (brick 18): G-GAIT read every second frame (12 fps), and the H3 render's 8 Hz
pulse folds there to |12 - 8| = 4 Hz, inside the step band: T00, T19 and T21 all read "shuffle: 4.0
steps/s ... HARD" and were re-rolled 6 times each.  At 24 fps their legs peak at 7.95-8.04 Hz with no
step in band.  A 12 fps shuffle stands only when the 24 fps read finds the same cadence (within
ALIAS_HZ, prominence >= PROMINENCE); otherwise it is `unmeasured: alias`, both numbers printed."""
from __future__ import annotations

import math

from studio import gait


def series(hz: float, fps: float, n: int, travel: float = 0.5) -> list[dict]:
    """Legs articulating at `hz`, sampled at `fps`, a slow torso: the shape of a shuffle read."""
    return [{"feet": True, "h": 100.0, "travel": travel, "art": 10.0 + 5.0 * math.sin(2 * math.pi * hz * i / fps)}
            for i in range(n)]


def test_an_8_hz_pulse_reads_as_a_4_hz_shuffle_at_12_fps():
    at24 = series(8.0, 24, 144)
    m = gait.judge(at24[::2])
    assert m["state"] == "shuffle" and abs(m["freq"] - 4.0) < 0.3


def test_the_native_read_names_the_alias():
    at24 = series(8.0, 24, 144)
    got = gait.alias(at24, 4.0)
    assert got["state"] == "unmeasured: alias" and abs(got["peak_24"] - 4.0) > gait.ALIAS_HZ
    assert got["freq_12"] == 4.0


def test_a_true_4_hz_shuffle_stands():
    assert gait.alias(series(3.9, 24, 144), 3.9) is None


def test_too_short_a_native_run_cannot_overturn_the_shuffle():
    assert gait.alias(series(8.0, 24, 30), 4.0) is None


def test_cadence_reads_at_the_rate_it_is_given():
    f, p = gait.cadence(series(1.8, 24, 144), fps=24)
    assert abs(f - 1.8) < 0.2 and p >= gait.PROMINENCE


def test_the_take_gate_row_passes_an_alias_and_says_both_numbers():
    row = gait.row({"state": "unmeasured: alias", "freq_12": 4.0, "peak_24": 1.2}, "He walks to the door.")
    assert row.ok and "alias" in row.note and "4.0" in row.note and "1.2" in row.note


def test_measure_reads_the_native_rate_only_for_a_shuffle(monkeypatch):
    asked = []
    pulse = series(8.0, 24, 144)

    def rows(frames, detect, stride):
        asked.append(stride)
        return pulse[::stride]
    monkeypatch.setattr(gait, "frame_rows", rows)
    assert gait.measure(["f"], detect=lambda x: [])["state"] == "unmeasured: alias"
    assert asked == [2, 1]


def test_measure_never_rereads_a_walk(monkeypatch):
    asked = []
    walk = series(1.8, 24, 144, travel=8.0)

    def rows(frames, detect, stride):
        asked.append(stride)
        return walk[::stride]
    monkeypatch.setattr(gait, "frame_rows", rows)
    assert gait.measure(["f"], detect=lambda x: [])["state"] == "walk"
    assert asked == [2]
