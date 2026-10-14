"""A drawn look is judged by the HOUSE stillness rule (owner ruling, 2026-10-14).

9ea1304 made a drawn (cel) take HARD-still only past a 2.5 s held run, and 85ef81c
never HARD when it was a speaking dialogue take.  Both were fitted on Jekyll HEL
ep01 (T14 76 % static, run 1.08 s; T01 82 %, run 4.08 s) and both shipped holds the
owner reads as dead: T01, T02, T19, T20.  The ruling drops them: a drawn take that
is static for WALL of its placed length fails HARD exactly as a painted one does,
and the cure is a retake (move type) or the cut, never the exemption.
"""
from __future__ import annotations

import inspect

from studio import stillness as st, take_verdict as tv


def m(share: float, run: float) -> dict:
    return {"static_share": share, "longest_static_run_s": run}


def test_a_take_is_judged_by_its_share_alone():
    assert st.is_still(m(0.76, 1.08), 5.9) is True
    assert st.is_still(m(0.82, 4.08), 6.6) is True
    assert st.is_still(m(0.60, 4.08), 6.6) is False


def test_the_drawn_and_speaking_relaxations_are_gone():
    for fn in (st.is_still, st.measure, tv.stillness_row):
        params = inspect.signature(fn).parameters
        assert "drawn" not in params and "speaking" not in params, fn.__name__
    assert not hasattr(st, "DRAWN_RUN")
    assert not hasattr(tv, "drawn_book") and not hasattr(tv, "speaking")


def test_a_planned_still_stays_exempt():
    assert st.is_still(m(0.92, 4.33), 6.6, exempt=True) is False


def test_the_take_verdict_hands_no_look_to_the_stillness_row(monkeypatch, tmp_path):
    seen = {}

    def fake(video, seconds, **kw):
        seen.update(kw)
        return {"static_share": 0.8, "longest_static_run_s": 1.0, "seconds": seconds, "exempt": False,
                "still": True, "advisory": True, "mean_global": 0.0, "mean_subject": 0.0}
    monkeypatch.setattr(st, "measure", fake)
    monkeypatch.setattr(st, "gate_args", lambda got: {"name": "frozen-whole", "value": got["static_share"],
                                                      "ok": not got["still"], "hard": True, "note": ""})
    g = tv.stillness_row(tmp_path / "t.mp4", 6.0, {"lane": "dialogue"})
    assert set(seen) == {"exempt"} and g.ok is False
