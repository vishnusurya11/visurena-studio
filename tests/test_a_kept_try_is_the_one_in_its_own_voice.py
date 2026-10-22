"""The try a line keeps is chosen by the voice gate's own discriminator, not by raw score.

2026-10-21 (two reviews of the 16 kHz voice fix, 68079e2): the cast margin decides whether
a try is its own character, but the two places that choose WHICH try to keep -- the best
failing try (`remember_best`, read by the terminal) and a redo's two tries (`keep_best`) --
still ranked by similarity alone.  A try in another character's voice that scored higher
beat a genuine one, and the terminal shipped it as passed; a redo that failed the margin
replaced a passing take and deleted its file.  A try that leads its cast now ranks above
one that does not, a passing try above a failing one, and "far" reads the same margin test
the gate does (a line under SIM_MEASURABLE_S is not measurable, so not far on it).
"""
from __future__ import annotations

from scripts.episode import say_lines as say
from studio import voice_ear

NEW = voice_ear.RULER


def take(sim, margin, seconds=3.0, passed=False, ruler=NEW, **more):
    row = {"index": 7, "speaker": "utterson", "similarity": sim, "floor": 0.55, "seconds": seconds,
           "margin": margin, "rival": "lanyon", "words_ok": True, "passed": passed, "tries": 4}
    return dict(row, ruler=ruler, **more) if ruler else dict(row, **more)


def test_a_higher_score_in_another_voice_never_replaces_the_genuine_best(tmp_path):
    wav = tmp_path / "l07.wav"
    wav.write_bytes(b"genuine")
    best = say.remember_best(take(0.58, 0.15), wav, None, tmp_path)
    wav.write_bytes(b"lanyon")
    kept = say.remember_best(take(0.65, -0.02), wav, best, tmp_path)
    assert kept["margin"] == 0.15 and (tmp_path / "l07.best.wav").read_bytes() == b"genuine"


def test_a_try_that_leads_its_cast_replaces_a_best_that_does_not(tmp_path):
    wav = tmp_path / "l07.wav"
    wav.write_bytes(b"lanyon")
    best = say.remember_best(take(0.65, -0.02), wav, None, tmp_path)
    wav.write_bytes(b"genuine")
    kept = say.remember_best(take(0.50, 0.12), wav, best, tmp_path)
    assert kept["margin"] == 0.12 and (tmp_path / "l07.best.wav").read_bytes() == b"genuine"


def test_the_terminal_flags_far_a_best_that_does_not_lead_by_the_cast_margin():
    best = take(0.58, say.CAST_MARGIN - 0.03)
    out = say.terminal(take(0.40, 0.0, tries=say.TERMINAL_TRIES), best)
    assert out["flagged"] == "keep_best_far"


def test_a_short_best_is_not_far_on_a_margin_the_gate_cannot_measure():
    best = take(0.45, -0.05, seconds=say.SIM_MEASURABLE_S - 0.6, floor=0.0)
    out = say.terminal(take(0.40, 0.0, tries=say.TERMINAL_TRIES), best)
    assert out["flagged"] == "keep_best"


def redo(tmp_path):
    wav = tmp_path / "l07.wav"
    wav.write_bytes(b"new")
    wav.with_suffix(".prev.wav").write_bytes(b"old")
    return wav


def test_a_redo_that_fails_the_margin_never_replaces_a_passing_take(tmp_path):
    wav = redo(tmp_path)
    kept = say.keep_best(take(0.72, -0.03), take(0.70, 0.20, passed=True), wav)
    assert kept["margin"] == 0.20 and wav.read_bytes() == b"old"


def test_a_failing_new_ruler_try_never_replaces_a_passing_old_ruler_take(tmp_path):
    wav = redo(tmp_path)
    kept = say.keep_best(take(0.55, -0.03), take(0.80, None, passed=True, ruler=None), wav)
    assert kept["similarity"] == 0.80 and wav.read_bytes() == b"old"


def test_a_passing_redo_beats_a_failing_take_that_scored_higher(tmp_path):
    wav = redo(tmp_path)
    kept = say.keep_best(take(0.62, 0.10, passed=True), take(0.80, -0.04), wav)
    assert kept["similarity"] == 0.62 and wav.read_bytes() == b"new"
