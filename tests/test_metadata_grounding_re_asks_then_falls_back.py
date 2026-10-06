"""G-META's grounding cure: an invented proper noun is re-asked (cap 2) with
the exact failed check quoted under llm.REFUSED; a caller that never grounds
ends in the MECHANICAL narration-lines fallback -- the pipeline never blocks
on prose, and the fallback says what it is with `_fallback: true`."""
from __future__ import annotations

from scripts.publish import metadata
from studio import llm
from tests.publish_fixtures import FakeCaller
from tests.test_metadata_one_call_through_the_fake_model import GROUNDED, episode

UNGROUNDED = metadata.ShortMetadata(
    synopsis_paragraphs=["The narrator meets Professor Moriarty at the pit."],
    attribution_line='"The Red Weed", from The Test Book by A. B. Author, in the public domain.',
    tags=["the test book"])


def test_an_ungrounded_noun_is_re_asked_with_the_refusal(tmp_path):
    book, home = episode(tmp_path)
    fake = FakeCaller([UNGROUNDED, GROUNDED])
    doc = metadata.generate(book, home, 3, _agent=fake)
    assert len(fake.prompts) == 2
    assert llm.REFUSED in fake.prompts[1] and "Moriarty" in fake.prompts[1]
    assert "_fallback" not in doc


def test_a_caller_that_never_grounds_ends_in_the_narration_fallback(tmp_path):
    book, home = episode(tmp_path)
    fake = FakeCaller([UNGROUNDED])
    doc = metadata.generate(book, home, 3, _agent=fake)
    assert len(fake.prompts) == 3  # the ask + two grounding re-asks, cap 2
    assert doc["_fallback"] is True
    assert "I walk the Horsell common at dawn." in doc["description"]
    assert metadata.disclosure("A. B. Author") in doc["description"]
    assert "public domain" in doc["description"]
