"""C8 (Jekyll Kawajiri ep01 close-out): three pieces built but never called, now called.

1. master QC hears each line's window once: scripts/episode/qc.py goes through voice_qc.heard_on_master.
2. G-LOOK-PANEL's advisory reads a bowler seen as a plain hat as one family (look_table advisory=True).
3. step_attempts has a public refund, and panel_ladder uses it instead of its private lock/read/write.
"""
import numpy as np
import soundfile as sf

from scripts.episode import qc
from studio import panel_content as pc, panel_ladder, step_attempts


def fake_window(master, at, seconds, out):
    sf.write(str(out), np.full(240, int(at * 100) + 1, dtype="int16"), 24000, subtype="PCM_16")
    return out


def test_the_master_qc_listens_once_per_identical_window(tmp_path, monkeypatch):
    monkeypatch.setattr(qc, "window", fake_window)
    calls = []
    def listen(clip):
        calls.append(clip)
        return "gold and a cheque"
    lines = [{"index": 1, "at": 1.0, "seconds": 2.0, "text": "gold and a cheque"}]
    first = qc.heard_on_master(tmp_path / "m.mp4", lines, tmp_path, listen)
    again = qc.heard_on_master(tmp_path / "m.mp4", lines, tmp_path, listen)
    assert first == again and first[0]["passed"] and len(calls) == 1


class Seen:
    def __init__(self, said):
        self.subjects = [said]


def test_a_bowler_listed_as_a_hat_is_no_look_advisory():
    markers = [{"headwear": "bowler"}]
    assert pc.look_advisories(Seen("a man in a hat"), markers) == []


def test_a_boater_against_a_bowler_is_still_an_advisory():
    markers = [{"headwear": "bowler"}]
    assert pc.look_advisories(Seen("a man in a boater"), markers)


def test_the_refund_gives_back_one_round_and_keeps_the_seconds(tmp_path):
    step_attempts.spend(tmp_path, "regrid", 30.0)
    step_attempts.spend(tmp_path, "regrid", 20.0)
    step_attempts.refund(tmp_path, "regrid")
    assert step_attempts.count(tmp_path, "regrid") == 1
    assert step_attempts.seconds(tmp_path, "regrid") == 50.0


def test_a_refund_never_goes_below_zero(tmp_path):
    step_attempts.refund(tmp_path, "regrid")
    assert step_attempts.count(tmp_path, "regrid") == 0


def test_the_ladder_refunds_through_the_public_api(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(step_attempts, "refund", lambda home, key: seen.append((home, key)))
    panel_ladder.refund_round(tmp_path)
    assert seen == [(tmp_path, panel_ladder.REGRID)]
