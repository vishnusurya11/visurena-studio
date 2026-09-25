"""The plan critic LISTS in a closed shape and the code JUDGES: the reader is
handed the plan as plain text with the writer's rationale stripped and the
chapter's rows numbered, returns `PlanReading`s through the gateway with a
fake caller, and `studio.judges.plan` turns them into a signed verdict.  No
model is ever asked whether the plan is right."""
from __future__ import annotations

from agents import plan_reader
from studio.judges import plan as plan_judge
from studio.judges.plan import PlanReading
from tests.plan_reader_fixtures import BRIEF, reading, reading_dict
from tests.test_episode_writer import FakeModel, canned_plan


def test_the_reader_lists_k_readings_in_the_closed_shape():
    fake = FakeModel(reading_dict("good"))
    got = plan_reader.read(plan_reader.plain_text(canned_plan()), ["scene 1: two people meet"],
                           k=3, chapter_text="the cup", _agent=fake)
    assert len(got) == 3 and all(isinstance(r, PlanReading) for r in got)
    assert len(fake.prompts) == 3
    prompt = fake.prompts[0]
    assert "plan reader" in prompt.lower()
    assert "0: scene 1: two people meet" in prompt and "the cup" in prompt


def test_the_plain_plan_carries_the_picture_and_never_the_writers_rationale():
    doc = canned_plan()
    doc["shots"][14]["why"] = "RATIONALEWORD"
    doc["shots"][14]["turn"] = "alone -> seen"
    doc["answer"] = "line 23"
    text = plan_reader.plain_text(doc)
    assert "Medium on the lead at the table by the window." in text
    assert "setup room" in text and "lead, other" in text
    assert "line 10 (dialogue, other, on shot 10)" in text
    for hidden in ("RATIONALEWORD", "alone -> seen", "section", "answer", "hook", "button"):
        assert hidden not in text, hidden


def test_the_code_judges_the_listing_and_signs_as_the_plan_judge():
    verdict = plan_judge.judge(canned_plan(), BRIEF, [reading("good")] * 3)
    assert verdict.passed and verdict.faults == []
    assert verdict.signer == "judge:plan@1" and verdict.reads == 3 and verdict.confidence == 1.0


def test_no_reading_is_an_unread_fault_never_a_pass():
    verdict = plan_judge.judge(canned_plan(), BRIEF, [])
    assert not verdict.passed and verdict.faults[0].kind == "unread" and verdict.confidence == 0.0


def test_the_skill_lists_and_never_asks_for_a_verdict():
    text = plan_reader.load_skill().lower()
    assert "plan reader" in text
    for word in ("is this right", "is the plan good", "approve", "score"):
        assert word not in text, word


def test_the_skill_is_book_neutral():
    text = plan_reader.load_skill().lower()
    for word in ("holmes", "watson", "scarlet", "martian", "wells", "doyle", "ep0", "ep1", "london"):
        assert word not in text, word


def test_the_critic_reuses_the_workhorse_tier_and_says_why():
    """models.yaml configures one model family today; the family rule is written
    at the constant so the flip is a yaml line and a word."""
    assert plan_reader.TIER == "workhorse"
    assert "family" in plan_reader.__doc__.lower()
