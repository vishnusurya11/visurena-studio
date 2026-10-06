"""ONE llm.structured call writes the prose; everything else is mechanical.
The agent is a fake (house rule: no test calls a paid API, no key is read);
what is tested is the CONTRACT: one call, the AI-disclosure block verbatim,
privacy private, synthetic true, the plan binding, and yp.spec's walls."""
from __future__ import annotations

import json

from scripts.publish import metadata
from studio import plan_verdict
from studio import youtube_publish as yp
from tests.publish_fixtures import FakeCaller, book_with, episode_with, prior_with, publish_seeded

GROUNDED = metadata.ShortMetadata(
    synopsis_paragraphs=["The narrator walks Horsell common at dawn.",
                         "At the pit, Ogilvy warns him back."],
    attribution_line='"The Red Weed", from The Test Book by A. B. Author, in the public domain.',
    tags=["the test book", "horsell common"])


def episode(tmp_path):
    book = book_with(tmp_path)
    publish_seeded(book)
    prior_with(book, 1, description="The narrator sees the first cylinder on Horsell common.",
               tags=("the test book", "horsell common", "serial"))
    prior_with(book, 2, description="Ogilvy leads the crowd to the pit.",
               tags=("the test book", "ogilvy", "serial"))
    home, _sha8 = episode_with(book, 3)
    return book, home


def test_one_call_assembles_a_youtube_json_that_passes_the_walls(tmp_path):
    book, home = episode(tmp_path)
    fake = FakeCaller([GROUNDED])
    doc = metadata.generate(book, home, 3, _agent=fake)
    assert len(fake.prompts) == 1
    assert metadata.disclosure("A. B. Author") in doc["description"]
    assert doc["privacy"] == "private" and doc["synthetic"] is True
    assert doc["_for"] == {"plan_sha8": plan_verdict.plan_sha8(home / "plan.json")}
    assert "_fallback" not in doc
    yp.spec(doc["title"], doc["description"], doc["tags"], synthetic=doc["synthetic"],
            privacy=doc["privacy"])  # raises if any wall is crossed


def test_the_synthetic_note_carries_the_cuts_measured_facts(tmp_path):
    book, home = episode(tmp_path)
    doc = metadata.generate(book, home, 3, _agent=FakeCaller([GROUNDED]))
    _engine, master, _qc = yp.deliverable(home, "")
    assert f"Cut {yp.sha8(master)}" in doc["_synthetic_note"]
    assert "2/2 takes" in doc["_synthetic_note"]


def test_ensure_writes_the_file_and_skips_when_current(tmp_path):
    book, home = episode(tmp_path)
    path = metadata.ensure(home, book, 3, _agent=FakeCaller([GROUNDED]))
    assert json.loads(path.read_text(encoding="utf-8"))["synthetic"] is True
    again = FakeCaller([GROUNDED])
    metadata.ensure(home, book, 3, _agent=again)
    assert again.prompts == []  # current file, zero calls, zero spend
