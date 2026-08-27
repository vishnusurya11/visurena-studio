"""Agreement between independent judges. Pure arithmetic; no agents, no spend.

Two DIFFERENT questions, and conflating them would waste the whole exercise:

  * do the judges agree with EACH OTHER?  -> is this scene knowable from the text
  * do they agree with the PIPELINE?      -> is the pipeline right

A scene where judges split is not a pipeline bug; it is a scene the book does not place.
A scene where judges are unanimous AND disagree with the pipeline is a pipeline bug, and
that is the only combination that should cost anyone time.
"""

from __future__ import annotations

from studio import consensus


def test_unanimous_judges_are_reported_as_unanimous():
    assert consensus.agreement(["a", "a", "a"])["level"] == "unanimous"


def test_a_majority_is_reported_as_majority():
    assert consensus.agreement(["a", "a", "b"])["level"] == "majority"


def test_a_three_way_split_is_reported_as_split():
    assert consensus.agreement(["a", "b", "c"])["level"] == "split"


def test_an_even_split_is_not_a_majority():
    """Two against two is not agreement, however tempting the arithmetic."""
    assert consensus.agreement(["a", "a", "b", "b"])["level"] == "split"


def test_the_winner_is_the_modal_answer():
    assert consensus.agreement(["a", "b", "b"])["answer"] == "b"


def test_a_split_has_no_winner():
    assert consensus.agreement(["a", "b", "c"])["answer"] is None


def test_agreement_counts_are_reported():
    assert consensus.agreement(["a", "a", "b"])["counts"] == {"a": 2, "b": 1}


def test_one_judge_is_unanimous_but_flagged_as_unreplicated():
    """A single opinion is not a consensus, and must not be presented as one."""
    result = consensus.agreement(["a"])
    assert result["level"] == "unanimous" and result["judges"] == 1


def test_no_judges_is_not_a_crash():
    assert consensus.agreement([])["level"] == "none"


# --- the verdict against the pipeline ----------------------------------------------

def test_unanimous_and_matching_is_confirmed():
    assert consensus.verdict(["a", "a", "a"], "a")["verdict"] == "confirmed"


def test_unanimous_and_differing_is_a_pipeline_error():
    """The only combination that is definitely a bug."""
    result = consensus.verdict(["b", "b", "b"], "a")
    assert result["verdict"] == "wrong" and result["should_be"] == "b"


def test_a_majority_differing_is_disputed_not_wrong():
    assert consensus.verdict(["b", "b", "a"], "a")["verdict"] == "disputed"


def test_judges_splitting_is_about_the_SCENE_not_the_pipeline():
    """The book does not place this scene. Blaming the pipeline would be wrong."""
    assert consensus.verdict(["a", "b", "c"], "a")["verdict"] == "unknowable"


def test_all_judges_saying_ambiguous_is_unknowable():
    assert consensus.verdict(["ambiguous"] * 3, "a")["verdict"] == "unknowable"


def test_all_judges_saying_unlisted_is_a_registry_gap():
    """Not a pipeline error - the place is real and the registry lacks it."""
    assert consensus.verdict(["unlisted"] * 3, "a")["verdict"] == "registry_gap"


def test_a_pipeline_location_of_none_still_reports():
    assert consensus.verdict(["a", "a", "a"], None)["verdict"] == "wrong"


def test_summary_counts_every_verdict_kind():
    rows = [consensus.verdict(["a", "a", "a"], "a"),
            consensus.verdict(["b", "b", "b"], "a"),
            consensus.verdict(["a", "b", "c"], "a")]
    got = consensus.summarise(rows)
    assert got["confirmed"] == 1 and got["wrong"] == 1 and got["unknowable"] == 1


def test_summary_reports_the_confirmation_rate_over_decidable_scenes():
    """Unknowable scenes are excluded from the rate: a scene the book does not place
    cannot count for or against the pipeline."""
    rows = [consensus.verdict(["a", "a", "a"], "a"),
            consensus.verdict(["b", "b", "b"], "a"),
            consensus.verdict(["a", "b", "c"], "a")]
    assert consensus.summarise(rows)["confirmed_rate"] == 0.5
