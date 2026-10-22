"""A cure's tilt up runs from the ground to the height (shot framework D-f).

ep01 shot 8 was cured to "The camera tilts up from the man to the cobbles": the aims went in `at_rest`
order, so the camera was told to tilt UP from a standing man DOWN to the cobbles.  A tilt up's first aim is
the ground noun the cell holds, its second the thing above it.  tilt_up stays "unmeasured" on Kawajiri
(the gavel, ruling 4); the cures keep offering it, so its words must at least point the right way.
Fixture: tests/fixtures/shot_framework/episodes/ep01/plan.json."""
from __future__ import annotations

import shot_framework_fixtures as sf
from studio import move_rebalance as mr


def shot(index: int) -> dict:
    return next(s for s in sf.plan()["shots"] if s["index"] == index)


def test_the_cure_wrote_the_tilt_downward_into_ep01():
    assert "tilts up from the man to the cobbles" in shot(8)["motion"]


def test_shot_8_tilts_from_cobbles_to_man():
    aims = mr.aims_for("tilt_up", shot(8), sf.plan()["setups"]["night_corner"])
    assert "tilts up from the cobbles to the man" in mr.render_head("tilt_up", aims, "a forearm")


def test_a_move_that_is_no_tilt_keeps_the_focus_first():
    aims = mr.aims_for("push_slow", shot(8), sf.plan()["setups"]["night_corner"])
    assert aims[0] == "man"
