"""The contract's rules refuse INSIDE the structured call: the gateway re-asks
the writer with the rule quoted, up to its retries, before the plan ladder
spends a rung.  Episode 13 (2026-09-25) burned two whole ladders -- ten
from-scratch drafts -- on rules the skill states (no 'slowly', 18 words a line,
rule 5, shot numbering), because every rung rewrote from nothing.

When the re-asks run out, the refusal reaches the ladder as pending lines; a
provider failure with no contract line in it is still a failure."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from strands.types.exceptions import StructuredOutputException

from agents import episode_writer as ew
from studio import plan_ladder
from tests.test_episode_writer import BRIEF, FakeModel, canned_draft


def test_a_draft_the_contract_refuses_is_re_asked_with_the_rule_and_the_fix_is_taken():
    broken = {**canned_draft(), "lines": []}
    fake = FakeModel(broken, canned_draft())
    episode = ew.write(BRIEF, _agent=fake)
    assert episode.title == "The Yard" and len(fake.prompts) == 2
    assert "CONTRACT" in fake.prompts[1] and "no button" in fake.prompts[1]


def test_a_draft_refused_on_every_re_ask_surfaces_the_rule():
    from pydantic import ValidationError
    broken = {**canned_draft(), "lines": []}
    fake = FakeModel(broken)
    with pytest.raises(ValidationError, match="no button"):
        ew.write(BRIEF, _agent=fake)
    assert len(fake.prompts) == ew.CONTRACT_RETRIES


def test_contract_lines_are_read_out_of_the_gateways_refusal():
    said = ("output did not match schema: 1 validation error for Draft\n  Value error, "
            "CONTRACT lines.6: line 6 is 19 words; the wall is 18\nCONTRACT : the last line is the "
            "protagonist's (lead); the button is another voice's line (rule 5) [type=value_error]")
    assert plan_ladder.contract_lines(said) == [
        "CONTRACT lines.6: line 6 is 19 words; the wall is 18",
        "CONTRACT : the last line is the protagonist's (lead); the button is another voice's line (rule 5)"]
    assert plan_ladder.contract_lines("model returned no structured output") == []


def _desk(tmp_path, writer):
    ctx = SimpleNamespace(book_dir=tmp_path, number=3)
    desk = plan_ladder.Desk(ctx, tmp_path / "plan.json", writer=writer)
    desk.brief = {}
    return desk


def test_a_spent_re_ask_is_a_pending_refusal_for_the_next_rung(tmp_path):
    class Writer:
        def write(self, brief, refusals, **kw):
            raise StructuredOutputException("output did not match schema: Value error, "
                                            "CONTRACT lines.6: line 6 is 19 words; the wall is 18")
    desk = _desk(tmp_path, Writer())
    desk.write(None)
    assert desk.pending == ["CONTRACT lines.6: line 6 is 19 words; the wall is 18"]
    assert not (tmp_path / "plan.json").exists()


def test_a_field_rule_refusing_inside_the_schema_is_a_pending_refusal(tmp_path):
    """Pass 3 of episode 13: a Shot's own validator ('slowly') refused inside the
    gateway; its message carries no CONTRACT line, only the pydantic cause."""
    from pydantic import ValidationError
    from studio.episode_spec import Shot
    try:
        Shot.model_validate({"index": 8, "section": "setup", "setup": "room", "size": "medium",
                             "faces": ["lead"], "frame": "Medium on the lead.",
                             "motion": "He walks slowly to the door.", "camera": "level",
                             "at_rest": "He stands.", "end": "He is at the door.", "changed": "he reaches the door"})
    except ValidationError as bad:
        cause = bad

    class Writer:
        def write(self, brief, refusals, **kw):
            raise StructuredOutputException(f"output did not match schema: {cause}") from cause
    desk = _desk(tmp_path, Writer())
    desk.write(None)
    assert len(desk.pending) == 1 and desk.pending[0].startswith("CONTRACT : ")
    assert "slowly" in desk.pending[0] and "motion: 'He walks slowly to the door.'" in desk.pending[0]


def test_a_refusal_line_quotes_the_field_it_names():
    from pydantic import ValidationError
    from studio.episode_spec import Line, refusal_lines
    try:
        Line.model_validate({"index": 6, "kind": "narration", "speaker": "lead", "shot": 6,
                             "text": " ".join(["word"] * 19)})
    except ValidationError as bad:
        lines = refusal_lines(bad)
    assert lines == ["CONTRACT : line 6 is 19 words; the wall is 18 -- text: '" + " ".join(["word"] * 19) + "'"]


def test_a_provider_failure_with_no_contract_line_is_still_raised(tmp_path):
    class Writer:
        def write(self, brief, refusals, **kw):
            raise StructuredOutputException("model returned no structured output")
    with pytest.raises(StructuredOutputException):
        _desk(tmp_path, Writer()).write(None)
