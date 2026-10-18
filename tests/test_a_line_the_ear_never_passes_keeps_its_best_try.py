"""The record step parks on nothing: a line said right that never reaches its voice floor
keeps its best try, flagged (Jekyll ep01 HEL, 2026-10-14).

The narrator's l15 ("The lawyer walks on, weighing every word.", ~3 s) was heard word for
word on every one of ten tries and scored 0.42-0.63 against a 0.65 floor; the step
refused, the brain found no order, and the episode parked.  Every other taste gate ends
its ladder in keep_best flagged.  After TERMINAL_TRIES the best try whose words were
heard right and whose voice sits within TERMINAL_MARGIN of its floor is kept, flagged;
a try under that margin, or one whose words were wrong, still refuses.
"""
from __future__ import annotations

from scripts.episode import say_lines as say


def rec(sim, tries, words=True, floor=0.65):
    return {"index": 15, "speaker": "narrator", "similarity": sim, "floor": floor, "tries": tries,
            "words_ok": words, "passed": False, "rel_path": "l15.wav"}


def test_the_best_try_is_remembered(tmp_path):
    wav = tmp_path / "l15.wav"
    wav.write_bytes(b"a")
    best = say.remember_best(rec(0.59, 2), wav, None, tmp_path)
    assert best["similarity"] == 0.59 and (tmp_path / "l15.best.wav").read_bytes() == b"a"
    wav.write_bytes(b"b")
    assert say.remember_best(rec(0.53, 4), wav, best, tmp_path)["similarity"] == 0.59
    assert (tmp_path / "l15.best.wav").read_bytes() == b"a"
    wav.write_bytes(b"c")
    assert say.remember_best(rec(0.61, 6), wav, best, tmp_path)["similarity"] == 0.61
    assert (tmp_path / "l15.best.wav").read_bytes() == b"c"


def test_a_misheard_try_is_never_the_best(tmp_path):
    wav = tmp_path / "l15.wav"
    wav.write_bytes(b"a")
    assert say.remember_best(rec(0.70, 2, words=False), wav, None, tmp_path) is None


def test_the_terminal_keeps_the_best_try_flagged(tmp_path):
    best = rec(0.61, 8)
    assert say.terminal(rec(0.50, say.TERMINAL_TRIES), best) == dict(
        best, passed=True, flagged="keep_best", tries=say.TERMINAL_TRIES)


def test_no_terminal_before_the_cap_or_without_a_rightly_heard_try():
    assert say.terminal(rec(0.50, say.TERMINAL_TRIES - 1), rec(0.61, 4)) is None
    assert say.terminal(rec(0.50, say.TERMINAL_TRIES), None) is None


def test_a_best_try_far_under_the_floor_is_kept_flagged_far_never_a_park():
    """Jekyll Kawajiri ep01 l11 (2026-10-18): Enfield's 'Gold and a cheque.' (~2.1 s) was
    heard word for word and scored 0.24-0.44 against 0.65 on every try; the step exited 1
    and parked the episode.  Step caps (owner 2026-10-18): voice is tier 2, so at the cap
    the best rightly heard try is kept and the run goes on -- flagged `keep_best_far` so
    QC and the owner see a voice the encoder could not confirm."""
    best = rec(0.44, 6)
    out = say.terminal(rec(0.30, say.TERMINAL_TRIES), best)
    assert out["passed"] is True and out["flagged"] == "keep_best_far"


def test_a_redo_between_tries_reads_the_parked_previous_file(tmp_path):
    """A --redo round moves the kept try to l{NN}.prev.wav before its next attempt
    (ep01 l15's revoice round crashed on the missing l15.wav)."""
    wav = tmp_path / "l15.wav"
    wav.with_suffix(".prev.wav").write_bytes(b"p")
    best = say.remember_best(rec(0.63, 16), wav, None, tmp_path)
    assert best["similarity"] == 0.63 and (tmp_path / "l15.best.wav").read_bytes() == b"p"


def test_a_new_render_keeps_the_lines_best_try():
    """Every render built a fresh record and dropped `best_try`: ep01 l15 reached 8 tries
    with its best at the LAST try's 0.56, its 0.63 forgotten."""
    old = dict(rec(0.56, 6), best_try=rec(0.63, 1))
    new = rec(0.0, 7)
    assert say.carried(old, new)["best_try"]["similarity"] == 0.63
    assert "best_try" not in say.carried({}, new)
