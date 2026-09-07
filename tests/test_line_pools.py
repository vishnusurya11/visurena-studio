"""The four pools a trailer line can come from, and who may be said to have
spoken it.

The title sentence of A Study in Scarlet ("the scarlet thread of murder...")
is in the source text and nowhere in the screenplay; a finder that reads only
the screenplay is blind to it.  Its paragraph carries no speech tag, but a
sibling sentence ("I shall have him, Doctor") is a screenplay line of Holmes,
and that is how it gets a speaker.  Two rules that disagree do not vote; the
line is refused (research 7.5).
"""
from __future__ import annotations

import json

import pytest

from studio import trailer_story as story

RING = ("“The ring, man, the ring: that was what he came back for. I shall have "
        "him, Doctor—I’ll lay you two to one that I have him. There’s the "
        "scarlet thread of murder running through the colourless skein of life, and "
        "our duty is to unravel it, and isolate it, and expose every inch of it.”")
INTRO = "“Dr. Watson, Mr. Sherlock Holmes,” said Stamford, introducing us."
SPLIT = ("“I shall have him, Doctor.” He turned. “It is nothing at all "
         "to me,” said Stamford.")
TAGGED = "“Whatever have you been doing with yourself?” asked Stamford."
UNTAGGED = "“You are wrong, sir,” he said, taking a seat."
NARRATION = "I had neither kith nor kin in England. I gravitated to London."


def registry():
    return {"characters": [
        {"id": "john_watson", "name": "Dr. John Watson", "aliases": ["I", "Dr. Watson"]},
        {"id": "sherlock_holmes", "name": "Sherlock Holmes", "aliases": ["Holmes"]},
        {"id": "stamford", "name": "Stamford", "aliases": ["young Stamford"]}]}


def screenplay():
    return {"scenes": [
        {"number": 1, "elements": [
            {"kind": "action", "text": "A hansom rolls."},
            {"kind": "dialogue", "character": "stamford",
             "text": "Whatever have you been doing with yourself, Watson?"}]},
        {"number": 4, "elements": [
            {"kind": "dialogue", "character": "sherlock_holmes",
             "text": "I shall have him, Doctor. I'll lay you two to one that I have him."},
            {"kind": "dialogue", "character": "sherlock_holmes",
             "text": "I shall have him, Doctor. I'll lay you two to one that I have him."}]},
        {"number": 5, "elements": [
            {"kind": "dialogue", "character": "Dr. Watson",
             "text": "Do you consider that there is immediate danger?"},
            {"kind": "dialogue", "character": "Police Inspector",
             "text": "The case is closed, gentlemen."}]}]}


@pytest.fixture()
def book(tmp_path):
    book = tmp_path / "book"
    (book / "screenplay/feature").mkdir(parents=True)
    (book / "screenplay/feature/screenplay.json").write_text(json.dumps(screenplay()),
                                                             encoding="utf-8")
    (book / "analysis/characters").mkdir(parents=True)
    (book / "analysis/registry.json").write_text(json.dumps(registry()), encoding="utf-8")
    (book / "analysis/characters/sherlock_holmes.json").write_text(json.dumps(
        {"id": "sherlock_holmes", "quotes": [
            {"chapter": 1, "quote": "“You have been in Afghanistan, I perceive.”"}]}),
        encoding="utf-8")
    (book / "source/chapters").mkdir(parents=True)
    (book / "source/chapters/ch_04.json").write_text(json.dumps({"n": 4, "paragraphs": [
        {"n": 1, "text": NARRATION}, {"n": 2, "text": INTRO}, {"n": 3, "text": TAGGED},
        {"n": 4, "text": UNTAGGED}, {"n": 5, "text": RING}, {"n": 6, "text": SPLIT}]}),
        encoding="utf-8")
    return book


def by_text(pool, fragment):
    return [line for line in pool if fragment in line["text"]]


class TestPools:
    def test_scarlet_thread_line_is_in_pool(self, book):
        pool = story.line_pools(book)
        hits = by_text(pool, "scarlet thread of murder")
        assert len(hits) == 1
        assert hits[0]["speaker"] == "sherlock_holmes"
        assert hits[0]["pool"] == "source" and hits[0]["scene"] is None

    def test_split_attribution_is_refused(self, book):
        """The sibling rule says Holmes, the tag says Stamford: nobody."""
        pool = story.line_pools(book)
        assert by_text(pool, "nothing at all to me") == []
        assert by_text(pool, "He turned") == []

    def test_a_tag_naming_one_alias_attributes(self, book):
        pool = story.line_pools(book)
        assert by_text(pool, "Dr. Watson, Mr. Sherlock Holmes")[0]["speaker"] == "stamford"

    def test_a_pronoun_tag_is_a_card(self, book):
        assert by_text(story.line_pools(book), "You are wrong, sir")[0]["speaker"] is None

    def test_a_screenplay_cue_is_resolved_to_the_cast_id_it_names(self, book):
        """A character cue is written for a READER -- "Dr. Watson" -- while every
        other pool keys on the analysis id.  Step 05 can only clone a voice
        from a cast card, which is filed under the id."""
        assert by_text(story.line_pools(book), "immediate danger")[0]["speaker"] == "john_watson"

    def test_a_cue_naming_nobody_in_the_cast_is_a_card(self, book):
        """MEASURED, run 19: the slate's stakes line was spoken by "Police
        Inspector", which matches none of the 23 ids on disk, so step 05 carded
        it and the trailer spoke 4 of 5 lines -- while four castable stakes
        spares sat unused in the same pool.  A line nobody in the cast can
        speak enters as a card, and the slate then knows it is choosing one."""
        line = by_text(story.line_pools(book), "The case is closed")[0]
        assert line["speaker"] is None

    def test_every_pool_is_present_and_deduplicated(self, book):
        pool = story.line_pools(book)
        assert {line["pool"] for line in pool} >= {"screenplay", "quotes", "source"}
        same = [l for l in pool if l["text"] == "I shall have him, Doctor."]
        assert len(same) == 1
        assert same[0]["pool"] == "screenplay" and same[0]["scene"] == 4

    def test_narration_needs_a_character_narrator(self, book):
        assert by_text(story.line_pools(book), "kith nor kin") == []
        pool = story.line_pools(book, narrator="john_watson")
        kith = by_text(pool, "kith nor kin")[0]
        assert kith["pool"] == "narration" and kith["speaker"] is None

    def test_long_lines_are_sentence_split(self, book):
        pool = story.line_pools(book)
        assert by_text(pool, "The ring, man, the ring")[0]["text"].endswith("came back for.")
        assert by_text(pool, "Whatever have you been doing")[0]["speaker"] == "stamford"


class TestAttribution:
    def test_tag_names_exactly_one(self):
        index = story.alias_index(registry()["characters"])
        assert story.tag_speakers(INTRO, index) == {"stamford"}
        assert story.tag_speakers(UNTAGGED, index) == set()
        assert story.tag_speakers("“No.” Holmes looked at Stamford and said so.",
                                  index) == {"sherlock_holmes", "stamford"}

    def test_sibling_speaker_needs_a_close_match(self):
        known = story.known_speech(screenplay()["scenes"], {})
        assert story.sibling_speaker(["I shall have him, Doctor."], known) == "sherlock_holmes"
        assert story.sibling_speaker(["I shall have a sandwich."], known) is None
