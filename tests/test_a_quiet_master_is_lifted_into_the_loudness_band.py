"""ep20 (2026-10-08): a finished master at -17.49 LUFS was refused by QC's
(-15.5, -12.5) wall after four hours of pictures; the lines were levelled as
ep19's, the quiet chapter's beds were not.  The master is lifted to -14 LUFS
through a true-peak limiter before it is named; one inside the band is left
alone.  $0: ffmpeg is a seam here."""
from __future__ import annotations

from pathlib import Path

import pytest

from studio import master_loudness as ml


def test_no_gain_inside_the_band_and_the_step_to_the_target_outside():
    assert ml.gain_for(-14.2) == 0.0
    assert ml.gain_for(-15.5) == 0.0 and ml.gain_for(-12.5) == 0.0
    assert ml.gain_for(-17.49) == pytest.approx(3.49)
    assert ml.gain_for(-11.0) == pytest.approx(-3.0)


def test_the_lift_copies_the_video_and_limits_the_true_peak():
    argv = ml.lift_argv(Path("m.mp4"), Path("m.lifted.mp4"), 3.49)
    assert argv[:2] == ["ffmpeg", "-y"] and "-c:v" in argv and argv[argv.index("-c:v") + 1] == "copy"
    af = argv[argv.index("-af") + 1]
    assert "volume=+3.49dB" in af and "alimiter=limit=0.8414" in af


def test_a_quiet_master_is_lifted_and_re_measured(tmp_path, capsys):
    readings = iter([-17.49, -14.05])
    runs = []
    got = ml.into_band(tmp_path / "m.mp4", tmp_path, measure=lambda p: next(readings), run=lambda argv, **kw: runs.append(argv))
    assert got == tmp_path / "m.lifted.mp4" and len(runs) == 1
    assert "lifted +3.49 dB" in capsys.readouterr().out


def test_a_master_in_the_band_is_untouched(tmp_path):
    runs = []
    got = ml.into_band(tmp_path / "m.mp4", tmp_path, measure=lambda p: -14.2, run=lambda argv, **kw: runs.append(argv))
    assert got == tmp_path / "m.mp4" and runs == []


def test_qc_and_the_lift_share_one_band():
    import importlib
    qc = importlib.import_module("scripts.episode.qc")
    assert qc.LUFS_BAND == ml.LUFS_BAND
