"""G-SOURCE: a claim the chapter must back carries a `source` span.

The owner's refusals that no gate caught: a plan that guessed 6 extras where
the chapter gives 8, and one that wrote "sits astride" where the chapter says
"clambers over".  A count (`extras > 0`), a posture word in the shot's prose,
or a staged prop id is a CLAIM, and a claim with no chapter span is invented.
The contract keeps `source` optional so every plan on disk still loads; the
gate refuses only a plan that writes a span somewhere (`Episode.new_form`)."""
from types import SimpleNamespace

from studio import plan_gates as pg
from studio.episode_spec import Episode, Setup, Shot

SETUPS = {"lane": Setup(described="a lane at dusk", cast=["walker"], props=["carter_hammer"])}


def shot(i: int, frame: str, extras: int = 0, source: list[str] | None = None) -> Shot:
    return Shot(index=i, section="setup", setup="lane", size="medium", frame=frame,
                motion="The camera holds a locked-off frame; his hand lifts; his head turns",
                extras=extras, source=source or [])


def plan(*shots: Shot):
    return SimpleNamespace(shots=list(shots), setups=SETUPS)


def test_source_defaults_empty_so_a_plan_written_before_it_still_validates():
    assert shot(0, "Medium on the walker at the gate.").source == []


def test_a_count_with_no_span_is_a_refusal():
    faults = pg.source_faults(plan(shot(3, "Medium on the riders at the turn.", extras=6)), chapter="the road")
    assert faults == ["G-SOURCE shot 3: extras 6 has no chapter span, measured 0 against 1"]


def test_a_shot_that_claims_nothing_needs_no_span():
    assert pg.source_faults(plan(shot(0, "Medium on the walker at the gate, his hand on the post.")), "x") == []


def test_a_posture_word_is_a_claim():
    faults = pg.source_faults(plan(shot(1, "Close on the man as he kneels by the wheel.")), chapter="x")
    assert faults == ["G-SOURCE shot 1: posture 'kneels' has no chapter span, measured 0 against 1"]


def test_a_staged_prop_is_a_claim():
    faults = pg.source_faults(plan(shot(2, "Insert on the hammer against the spoke.")), chapter="x")
    assert faults == ["G-SOURCE shot 2: prop 'carter_hammer' has no chapter span, measured 0 against 1"]


def test_a_span_anywhere_is_what_makes_a_plan_the_new_form():
    assert Episode.new_form(SimpleNamespace(shots=[shot(0, "f"), shot(1, "g")])) is False
    assert Episode.new_form(SimpleNamespace(shots=[shot(0, "f"), shot(1, "g", source=["a span"])])) is True
