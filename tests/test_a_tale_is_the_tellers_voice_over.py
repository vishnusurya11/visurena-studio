"""A `tale` line (Jekyll ep01 review, 2026-10-13): Enfield's own telling of the
night he saw Hyde trample a child, in HIS voice, over pictures of what he
tells.  The dialogue dial and the 8-word quote wall turned the chapter's
1,300-word tale into third-person paraphrase in another man's mouth.  A tale
keeps the book's words, is voice-over (no driven lips), and counts against
neither the dialogue ceiling nor the quote wall.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import episode_ref_official as ro
from studio import episode_spec as spec
from studio import plan_gates
from studio.episode_spec import Episode, Line
from tests.test_episode_writer import canned_plan

BOOK = "It sounds nothing to hear, but it was hellish to see. It wasn't like a man; it was like some damned Juggernaut."


def test_a_tale_is_a_line_kind():
    assert Line(index=0, kind="tale", speaker="richard_enfield", text="It was hellish to see.", shot=0).kind == "tale"


def test_a_tale_keeps_the_books_words_past_the_quote_wall():
    lines = [{"index": 0, "kind": "tale", "text": "It sounds nothing to hear, but it was hellish to see."},
             {"index": 1, "kind": "narration", "text": "It sounds nothing to hear, but it was hellish to see."}]
    hard, soft = spec.quoted_lines(lines, BOOK)
    assert [l["index"] for l in hard] == [1]
    assert [l["index"] for l in soft] == [0]


def _with_tales(doc: dict, n: int) -> dict:
    for line in doc["lines"][:n]:
        if line["kind"] == "narration":
            line["kind"], line["speaker"] = "tale", doc["lines"][-1]["speaker"]
    return doc


def test_a_tale_counts_against_neither_the_dialogue_ceiling():
    doc = _with_tales(canned_plan(), 6)
    ep = Episode.model_validate(doc)
    assert ep.dialogue_share() <= spec.DIALOGUE_SHARE[1]


def test_a_tale_meets_the_chapters_speech_floor():
    ep = SimpleNamespace(lines=[SimpleNamespace(kind="tale", text="one two three"),
                                SimpleNamespace(kind="narration", text="four five six seven eight nine ten")])
    assert plan_gates.dial_faults(ep, speech=0.5) == []
    ep.lines[0].kind = "narration"
    assert plan_gates.dial_faults(ep, speech=0.5)


def test_a_tale_is_voice_over_with_the_mouth_closed():
    line = SimpleNamespace(index=0, kind="tale", speaker="richard_enfield", text="It was hellish to see.")
    said = ro.voice_events([line], {0: (0.5, 2.0)}, 0.0, {"richard_enfield": "S1"}, ["richard_enfield"], {},
                           "the man about town", "he walks", 0, 6, set())
    assert "mouth is closed" in said and "<d>" not in said


def test_a_tale_breaks_a_narration_only_run_and_opens_the_speech():
    """A character telling his own story is drama, not exposition: G-STORY's
    narration-run and first-speech walls count it as a character speaking."""
    doc = _with_tales(canned_plan(), 2)
    ep = Episode.model_validate(doc)
    assert plan_gates.first_dialogue_at(ep)[1] == doc["lines"][0]["shot"]
