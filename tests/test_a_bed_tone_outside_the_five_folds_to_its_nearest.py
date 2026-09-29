"""ep14 (2026-09-29): the writer's beds said alarm, dread, panic, flight and
stark; the contract read none of them, and assemble.py refused the whole
episode at step 10, eight hours in.  A tone outside the five folds to its
nearest at the bed; the battery names an unknown one before anything renders;
the brief tells the writer the five words."""
import pytest

from studio import episode_bed as bed, plan_brief


def test_a_synonym_folds_to_its_tone_and_the_five_stand():
    assert bed.tone_of("alarm") == "thrilling" and bed.tone_of("panic") == "thrilling"
    assert bed.tone_of("dread") == "grave" and bed.tone_of("stark") == "grave"
    assert bed.tone_of("tense") == "uneasy" and bed.tone_of("calm") == "plain"
    assert bed.tone_of(" Grave ") == "grave"
    for name in bed.TONES:
        assert bed.tone_of(name) == name


def test_a_word_that_is_no_tone_is_still_refused():
    with pytest.raises(ValueError, match="not a bed tone"):
        bed.tone_of("purple")


def test_the_spans_and_the_style_read_through_the_fold():
    at = {0: 0.0, 5: 20.0, 8: 32.0}
    spans = bed.spans([{"from_shot": 0, "tone": "calm"}, {"from_shot": 8, "tone": "alarm"}], at, 60.0)
    assert [s.tone for s in spans] == ["plain", "thrilling"]
    assert bed.tone_style("flight") == bed.TONES["thrilling"].style
    assert bed.tone_lufs("dread") == bed.TONES["grave"].lufs


def test_the_writer_is_told_the_five_words():
    assert plan_brief.band()["bed_tones"] == list(bed.TONES)


def test_the_battery_refuses_an_unknown_tone_and_advises_on_a_synonym():
    from studio import plan_gates
    from tests.test_episode_writer import canned_plan
    from studio.episode_spec import Episode
    ep = Episode(**{**canned_plan(4), "beds": [{"from_shot": 0, "tone": "plain"}, {"from_shot": 3, "tone": "alarm"},
                                              {"from_shot": 9, "tone": "purple"}]})
    hard, soft = plan_gates.bed_faults(ep)
    assert len(hard) == 1 and "purple" in hard[0] and hard[0].startswith("G-BED")
    assert soft == ["G-BED shot 3: bed tone 'alarm' folds to 'thrilling'"]
