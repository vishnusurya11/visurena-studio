"""A36, measured on ep19 (2026-10-07): G-CROWD makes a wide over a setup whose
crowd prose stages people declare extras >= 1, its cure writes `extras=1`,
and the critic then flags "count 'extras=1' has no chapter span" -- one
judge's cure is another judge's fault (5 of 21 flags at 15:54Z).  A count of
ONE under a setup that stages a crowd is that setup's own declaration, not a
claim about the chapter; a larger count, or a count with no crowd staged, is
still a claim the chapter must back."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_gates


def _shot(extras: int, prose: str = "The pit from the rim.") -> SimpleNamespace:
    return SimpleNamespace(index=5, extras=extras, frame=prose, motion="", at_rest="", end="")


def test_one_extra_under_a_staged_crowd_is_the_setups_declaration():
    setup = SimpleNamespace(crowd="1 background person crouches beyond the doorway", props=[])
    assert plan_gates.claims(_shot(1), setup) == []


def test_six_extras_are_still_a_claim():
    setup = SimpleNamespace(crowd="a crowd of onlookers", props=[])
    assert plan_gates.claims(_shot(6), setup) == ["extras 6"]


def test_one_extra_with_no_crowd_staged_is_a_claim():
    setup = SimpleNamespace(crowd="", props=[])
    assert plan_gates.claims(_shot(1), setup) == ["extras 1"]


def test_the_critic_drops_a_cure_written_count_and_keeps_the_rest():
    from studio.judges import plan as critic
    plan = SimpleNamespace(
        shots=[SimpleNamespace(index=0, setup="pit", source=[]), SimpleNamespace(index=1, setup="lane", source=[])],
        setups={"pit": SimpleNamespace(crowd="onlookers at the rim"), "lane": SimpleNamespace(crowd="")})
    reading = SimpleNamespace(claims=[
        critic.Claim(shot=0, kind="count", claim="extras=1", span=""),
        critic.Claim(shot=1, kind="count", claim="extras=1", span=""),
        critic.Claim(shot=0, kind="count", claim="extras=6", span=""),
        critic.Claim(shot=0, kind="posture", claim="narrator kneels", span="")])
    notes = [f.note for f in critic.claim_faults(plan, [reading], "the chapter text")]
    assert not any("extras=1" in n and "shot_00" in n for n in notes)
    assert any("'extras=1'" in n for n in notes)             # shot 1: no crowd staged -> still a claim
    assert any("extras=6" in n for n in notes) and any("kneels" in n for n in notes)
