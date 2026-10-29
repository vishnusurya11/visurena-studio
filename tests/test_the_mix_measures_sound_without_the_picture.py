"""The mix's loudness analysis reads the sound only (Jekyll ep06, 2026-10-29).

Step 10 refused with "loudness analysis produced no measurement ... ffmpeg reported: nothing": the analysis
opened picture.mp4 (never mapped -- it measures audio) while another process rewrote it, ffmpeg failed in a
second, and the refusal threw ffmpeg's own words away.  The same command over the same sound files measured
fine minutes later.  So: no picture input, one retry of an empty answer, and a refusal carries ffmpeg's text."""
from __future__ import annotations

import pytest

from studio import trailer_assemble as ta

GOOD = {"input_i": "-20.0", "input_tp": "-3.0"}


def run_mix(tmp_path, monkeypatch, answers):
    asked = []

    def measure(argv):
        asked.append(argv)
        return answers.pop(0)
    monkeypatch.setattr(ta, "_measure_loudness", measure)
    monkeypatch.setattr(ta, "_ffmpeg", lambda argv, what: None)
    monkeypatch.setattr(ta.time, "sleep", lambda s: None)
    picture, bed, cue = tmp_path / "picture.mp4", tmp_path / "bed.wav", tmp_path / "line.wav"
    ta.mix(picture, bed, [(1.5, cue)], tmp_path / "mixed.mp4", seconds=10.0)
    return asked, picture, bed, cue


def test_the_analysis_never_opens_the_picture(tmp_path, monkeypatch):
    asked, picture, bed, cue = run_mix(tmp_path, monkeypatch, [dict(GOOD)])
    argv = asked[0]
    assert str(picture) not in argv
    assert argv[argv.index("-i") + 1] == str(bed)
    graph = argv[argv.index("-filter_complex") + 1]
    assert graph.startswith("[0:a]aresample=48000,apad[bedpad];[1:a]aresample=48000,adelay=1500|1500[cue0]")


def test_an_empty_answer_is_asked_once_more(tmp_path, monkeypatch):
    asked, *_ = run_mix(tmp_path, monkeypatch, [{}, dict(GOOD)])
    assert len(asked) == 2


def test_a_refusal_carries_ffmpegs_own_words(tmp_path, monkeypatch):
    with pytest.raises(RuntimeError, match="Permission denied"):
        run_mix(tmp_path, monkeypatch, [{"_stderr": "picture.mp4: Permission denied"},
                                        {"_stderr": "picture.mp4: Permission denied"}])


def test_the_measure_keeps_ffmpegs_tail_when_no_report_comes(monkeypatch):
    class Done:
        stderr = "line one\nbed.wav: Invalid data found when processing input\n"
    monkeypatch.setattr(ta.subprocess, "run", lambda *a, **k: Done())
    assert "Invalid data" in ta._measure_loudness(["ffmpeg"])["_stderr"]
