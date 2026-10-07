"""ep23 (2026-10-07): the signed plan carried lines spoken by `narrator` beside
the cast's `unnamed_first_person_narrator`; nothing refused it at the plan, and
step 04 died casting a voice for a character that does not exist.  G-SPEAKER
refuses a speaker outside the cast; the free cure aliases the one obvious case
(a narrator-like id when the cast has exactly one), before the contract and in
the ladder.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures, plan_gates

CAST = ["unnamed_first_person_narrator", "curate", "artilleryman"]


def _ep(*speakers):
    return SimpleNamespace(lines=[SimpleNamespace(index=i, speaker=s, kind="narration", shot=0) for i, s in enumerate(speakers)])


def test_a_speaker_outside_the_cast_is_a_fault_and_a_cast_one_is_not():
    assert plan_gates.speaker_faults(_ep("narrator", "curate"), CAST) == [
        "G-SPEAKER line 0: speaker 'narrator' is not in the cast (unnamed_first_person_narrator, curate, artilleryman), measured 0 against 1"]
    assert plan_gates.speaker_faults(_ep("curate", "unnamed_first_person_narrator"), CAST) == []


def test_the_cure_aliases_a_narrator_like_id_to_the_one_narrator_in_the_cast():
    doc = {"lines": [{"index": 0, "speaker": "narrator"}, {"index": 1, "speaker": "the narrator"},
                     {"index": 2, "speaker": "curate"}, {"index": 3, "speaker": "stranger"}]}
    out = plan_cures.alias_speakers(doc, CAST)
    assert [l["speaker"] for l in out["lines"]] == ["unnamed_first_person_narrator", "unnamed_first_person_narrator", "curate", "stranger"]
    assert plan_cures.cure_for("G-SPEAKER line 0: speaker 'narrator' is not in the cast") == "alias_speakers"


def test_no_alias_when_the_cast_has_two_narrator_like_ids():
    doc = {"lines": [{"index": 0, "speaker": "narrator"}]}
    out = plan_cures.alias_speakers(doc, ["narrator_a", "narrator_b"])
    assert out["lines"][0]["speaker"] == "narrator"


def test_the_writer_aliases_before_the_contract():
    from agents import episode_writer as ew
    from tests.test_episode_writer import BRIEF, canned_draft
    doc = canned_draft()
    doc["lines"][0]["speaker"] = "narrator"
    brief = {**BRIEF, "cast": [{"entity_id": "lead", "physical": "x"}, {"entity_id": "unnamed_first_person_narrator", "physical": "y"},
                               {"entity_id": "other", "physical": "z"}]}
    ep = ew.to_episode(ew.Draft.model_validate(doc), brief)
    assert ep.lines[0].speaker == "unnamed_first_person_narrator"
