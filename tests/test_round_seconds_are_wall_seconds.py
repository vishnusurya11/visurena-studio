"""A retake round records the wall seconds it took, not the 0.0 the call itself clocked: the
rung's own measure when longer than the climb's clock (ep01: attempts.json read
`retakes {rounds: 2, seconds: 0.0}`)."""
from __future__ import annotations

from studio import judged_gate as jg


def test_the_round_takes_the_longer_of_the_rung_and_the_climb_clock():
    assert jg.round_seconds(jg.RungResult(True, "", 310.0), 12.0) == 310.0
    assert jg.round_seconds(jg.RungResult(True, "", 0.0), 12.0) == 12.0


def test_a_legacy_none_keeps_the_climbs_clock():
    assert jg.round_seconds(None, 7.5) == 7.5


def test_take_ladder_times_a_round_by_the_wall(tmp_path, monkeypatch):
    from studio import take_ladder as tl
    from tests.test_a_rung_that_renders_nothing_spends_no_round import shot_ctx, thirteen
    ctx, _sent = shot_ctx(tmp_path, monkeypatch, left=9000.0)
    clock = iter([100.0, 400.0])
    monkeypatch.setattr(tl, "wall", lambda: next(clock))
    got = tl.rungs(ctx, None, "--approved=render").take(tl.BATCH, 0, thirteen())
    assert got.changed and got.seconds == 300.0
