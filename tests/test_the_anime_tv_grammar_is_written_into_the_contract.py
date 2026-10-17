"""The anime-TV grammar's contract half (owner 2026-10-17: "I like the face
improvements a lot in wide shots, and reframe. Go ahead with changes").

Research 04 (screenplay) and 05 (framing), tested on the GPU in part 2
(docs/audit/2026-10-16_model_tests): a plan now names the grammar it was
written under, an act-out beat, an optional picture-only tease after the
button, the book's motif, and a fourth line kind -- the inner voice, a
character thinking in his own voice with no lips, at most 8 words.  Every
field defaults so every plan on disk still loads.  $0."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio import episode_spec as spec
from studio.episode_spec import Episode, Line
from tests.test_episode_writer import canned_plan


def test_an_inner_line_is_a_line_kind_of_at_most_eight_words():
    assert Line(index=0, kind="inner", speaker="lead", text="Hyde. I know that name.", shot=0).kind == "inner"
    with pytest.raises(ValidationError, match="inner"):
        Line(index=0, kind="inner", speaker="lead", text="one two three four five six seven eight nine", shot=0)


def test_every_new_field_defaults_so_an_old_plan_loads():
    ep = Episode.model_validate(canned_plan())
    assert (ep.grammar, ep.motif, ep.tease) == ("", "", "")


def test_a_plan_declares_the_anime_tv_grammar():
    ep = Episode.model_validate({**canned_plan(), "grammar": "anime_tv", "motif": "the blind door"})
    assert ep.grammar == "anime_tv" and ep.motif == "the blind door"


def test_one_act_out_at_most():
    doc = canned_plan()
    doc["shots"][8]["section"] = "act_out"
    assert Episode.model_validate(doc).shots[8].section == "act_out"
    doc["shots"][9]["section"] = "act_out"
    with pytest.raises(ValidationError, match="act_out"):
        Episode.model_validate(doc)


def _with_tease(doc: dict) -> dict:
    """A picture-only tease shot after the button: no line, a coda."""
    tease = dict(doc["shots"][-1], index=len(doc["shots"]), section="tease", faces=[], size="wide",
                 beat_s=0.0, coda_s=2.0)
    return {**doc, "shots": doc["shots"] + [tease], "tease": "the lawyer alone at his desk"}


def test_a_tease_is_the_last_shot_after_the_button():
    ep = Episode.model_validate(_with_tease(canned_plan()))
    assert ep.shots[-1].section == "tease"


def test_a_tease_before_the_button_is_refused():
    doc = _with_tease(canned_plan())
    doc["shots"][5]["section"], doc["shots"][-1]["section"] = "tease", "runout"
    with pytest.raises(ValidationError, match="tease"):
        Episode.model_validate(doc)


def test_the_contract_ceiling_on_dialogue_is_the_widest_a_chapter_may_ask():
    """The chapter's own ceiling is the battery's (`plan_gates.dial_ceiling`): the
    contract cannot see the chapter, so it holds only the widest band."""
    assert spec.DIALOGUE_SHARE[1] == 0.20 and spec.DIALOGUE_CEILING_MAX == 0.35
    doc = canned_plan()
    for line, shot in zip(doc["lines"][1:5], doc["shots"][1:5]):
        line.update(kind="dialogue", speaker="other")
        shot.update(size="close", faces=["other"])
    assert 0.20 < Episode.model_validate(doc).dialogue_share() <= 0.35
