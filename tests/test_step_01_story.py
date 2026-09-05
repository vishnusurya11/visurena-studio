"""Step 01 of the trailer stage: the structure is DERIVED, three fields are judged.

Lead, figure, turn and the resolution come from the screenplay by code.  One
structured call judges narrator / register / thesis; every violation the
contract finds is quoted back to the model, and after three tries the step
ships the procedural fallback and writes why.
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from scripts.trailer import step_01_story as step
from studio import db, llm
from studio.learnings import load
from studio.trailer_run import RunContext
from studio.trailer_stage_spec import StorySpec


def scene(number, cast, text="He crosses the room."):
    return {"number": number, "cast": cast, "speaking": cast[:1],
            "slug": {"location_id": "room", "location_name": "Room"},
            "elements": [{"kind": "action", "text": text}]}


def screenplay():
    holmes, watson, hope = "sherlock_holmes", "john_watson", "jefferson_hope"
    scenes = [scene(1, [watson, holmes]), scene(2, [watson, holmes]), scene(3, [watson]),
              scene(4, [hope]), scene(5, [hope]), scene(6, [hope]),
              scene(7, [watson, holmes]), scene(8, [watson, holmes, hope])]
    return {"title": "A Study in Scarlet", "logline": "A doctor meets a detective.",
            "spine": "Watson witnesses Holmes.", "scenes": scenes}


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000001")
    book = tmp_path / "book"
    (book / "screenplay/feature").mkdir(parents=True)
    (book / "screenplay/feature/screenplay.json").write_text(
        json.dumps(screenplay()), encoding="utf-8")
    (book / "source/chapters").mkdir(parents=True)
    (book / "source/chapters/ch_01.json").write_text(json.dumps(
        {"paragraphs": [{"text": "I took my degree. I was attached to the Fifth."}]}),
        encoding="utf-8")
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs")
    context.open_step("01")
    return context


def judgement(**over):
    base = dict(narrator="john_watson", register="detective", thesis="nobody is who they say",
                setting="1881 London")
    base.update(over)
    return step.Judgement(**base)


class FakeLLM:
    def __init__(self, *answers):
        self.answers = list(answers)
        self.prompts = []

    def __call__(self, tier, prompt, schema, **kw):
        self.prompts.append(prompt)
        return self.answers.pop(0)


class TestDerive:
    def test_structure_comes_from_the_screenplay(self):
        derived = step.derive(screenplay()["scenes"])
        assert derived["lead"] == "john_watson"
        assert derived["figure"] == "jefferson_hope"
        assert derived["turn_scene"] == 4
        assert 8 in derived["resolution_scenes"]

    def test_lead_share_is_the_fraction_of_scenes(self):
        assert step.lead_share(screenplay()["scenes"], "john_watson") == 5 / 8


class TestNarratorFallback:
    def test_first_person_text_names_the_lead(self):
        text = "I went to the door. I saw him. He was pale. I knew."
        assert step.narrator_by_pronouns(text, "john_watson") == "john_watson"

    def test_third_person_text_is_omniscient(self):
        text = "He went to the door. She saw him. He was pale."
        assert step.narrator_by_pronouns(text, "john_watson") == "omniscient"


class TestRun:
    def test_writes_story_json_from_derivation_plus_judgement(self, ctx, monkeypatch):
        monkeypatch.setattr(llm, "structured", FakeLLM(judgement()))
        step.run(ctx.codex_id, ctx)
        spec = StorySpec.model_validate_json((ctx.out_dir / "story.json").read_text())
        assert spec.lead == "john_watson" and spec.register == "detective"
        assert spec.thesis == "nobody is who they say"

    def test_a_violation_is_quoted_back_and_retried(self, ctx, monkeypatch):
        fake = FakeLLM(judgement(thesis="nobody is ever who they say they are"), judgement())
        monkeypatch.setattr(llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        assert "syllables" in fake.prompts[1]
        assert len(fake.prompts) == 2

    def test_three_violations_ship_procedural_and_learn(self, ctx, monkeypatch):
        bad = judgement(thesis="the truth about Holmes")
        monkeypatch.setattr(llm, "structured", FakeLLM(bad, bad, bad))
        step.run(ctx.codex_id, ctx)
        spec = StorySpec.model_validate_json((ctx.out_dir / "story.json").read_text())
        assert spec.register == "procedural" and spec.thesis is None
        assert spec.narrator == "john_watson"
        rows = load(ctx.learnings_path)
        assert rows[-1].terminal and rows[-1].action == "procedural"

    def test_a_register_outside_the_enum_never_validates(self):
        with pytest.raises(ValidationError):
            judgement(register="moody")


class TestThesisIsNeverDroppedForLength:
    """R11.  Run 10 shipped `thesis: null` because the model answered with
    eight syllables and `fallback` preferred silence to arithmetic.  The
    thesis is the one sentence the trailer can put on a card or read as
    voice-over, so a refrain that is too long is CUT BACK, never dropped."""

    def test_clauses_are_the_pieces_a_refrain_cuts_back_to(self):
        found = step.clauses("nobody is ever who they say they are")
        assert "nobody is ever" in found
        assert found == sorted(found, key=lambda c: (len(c.split()), c))

    def test_a_refused_refrain_yields_its_shortest_accepted_clause(self):
        derived = step.derive(screenplay()["scenes"])
        assert step.thesis_from("nobody is ever who they say they are", derived) == "nobody is ever"

    def test_a_refrain_that_names_somebody_still_yields_nothing(self):
        """Length is arithmetic; a name is a different refusal and cutting
        does not fix it."""
        derived = step.derive(screenplay()["scenes"])
        assert step.thesis_from("the truth about Holmes", derived) is None

    def test_eight_syllables_then_six_is_taken_on_the_retry(self, ctx, monkeypatch):
        fake = FakeLLM(judgement(thesis="every secret is a debt"),
                        judgement(thesis="each secret is a debt"))
        monkeypatch.setattr(llm, "structured", fake)
        step.run(ctx.codex_id, ctx)
        spec = StorySpec.model_validate_json((ctx.out_dir / "story.json").read_text())
        assert spec.thesis == "each secret is a debt"
        assert "syllables" in fake.prompts[1]

    def test_three_over_long_answers_still_ship_a_refrain(self, ctx, monkeypatch):
        long = judgement(thesis="nobody is ever who they say they are")
        monkeypatch.setattr(llm, "structured", FakeLLM(long, long, long))
        step.run(ctx.codex_id, ctx)
        spec = StorySpec.model_validate_json((ctx.out_dir / "story.json").read_text())
        assert spec.thesis == "nobody is ever"
        assert spec.register == "procedural"
