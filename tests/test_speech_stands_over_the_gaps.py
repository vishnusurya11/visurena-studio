"""QC's sound row gets a ceiling: speech stands at least SPEECH_OVER_GAP_DB over the gaps.

OWNER 2026-09-27 on ep13 master_iter8: "the sound effects are good but too
loud".  QC's sound row had only a floor (each cue heard, 6 dB).  Measured:
iter8 speech 10.9 dB over the gaps between lines; WotW ep10-12 11.3-13.5;
Sherlock 9.8-16.5 (median 14.9); iter11 after the duck and trim 12.0.
"""
import numpy as np

from studio import speech_gap


def test_speech_over_gaps_is_measured_from_the_placed_lines():
    sr = 1000
    a = np.full(10 * sr, 0.01)
    a[2 * sr:4 * sr] = 0.1          # a line, 20 dB over the room
    lines = [{"at": 2.0, "seconds": 2.0}]
    got = speech_gap.speech_over_gaps(a, sr, lines, until=10.0)
    assert 19.5 < got < 20.5


def test_the_band_holds_eleven_db():
    assert speech_gap.band_ok(12.0) and not speech_gap.band_ok(10.9)


def test_qc_fails_a_master_whose_speech_does_not_stand_over_the_gaps():
    import importlib.util
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("qc_band", root / "scripts/episode/qc.py")
    qc = importlib.util.module_from_spec(spec)
    sys.modules["qc_band"] = qc
    spec.loader.exec_module(qc)
    ok = {"lufs_ok": True, "tp_ok": True, "missing_cuts": [], "internal_cuts": [], "longest_gap_s": 5.0,
          "lines": [], "edit": {"ok": True, "measured": True}, "takes": {}, "title_card": True, "sound": [],
          "speech_over_gap_db": 12.0}
    assert qc.verdict(ok)
    assert not qc.verdict({**ok, "speech_over_gap_db": 10.9})
