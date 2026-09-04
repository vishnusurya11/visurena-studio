"""The book's own portrait of a character, read off the SOURCE, not the dossier.

Scarlet run 6: `profile.physical` for Holmes said "the dossier gives limited
physical description" and the card invented white hair worn long and a full
dark beard -- while chapter 2 says over six feet, excessively lean, sharp
piercing eyes, a thin hawk-like nose.  The dossier is prose about scenes; the
portrait paragraph names nobody, it says "he".  So the candidates are the
paragraphs that name the person OR follow one that does, and carry a look
word; the model quotes the sentences about this one person, and a quote that
is not verbatim in those paragraphs is refused -- an agent's output is input.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio import cast_card, portrait
from studio.distinguish import coarse
from studio.portrait import Passage, Portrait

NAMING = ("I had begun to think that my tall companion was as friendless a man as I was myself. "
          "When any of these nondescript individuals put in an appearance, Sherlock Holmes "
          "used to beg for the use of the sitting-room.")
LOOK = ("His very person and appearance were such as to strike the attention of the most "
        "casual observer. In height he was rather over six feet, and so excessively lean "
        "that he seemed to be considerably taller. His eyes were sharp and piercing.")
CALLERS = ("There was one little sallow rat-faced, dark-eyed fellow who was introduced to me "
           "as Mr. Lestrade, and who came three or four times in a single week. On another "
           "occasion an old white-haired gentleman had an interview with my companion.")
PLAIN = "We met next day as he had arranged, and inspected the rooms at No. 221B, Baker Street."


def chapter(n, *texts):
    return {"n": n, "paragraphs": [{"n": i + 1, "text": t} for i, t in enumerate(texts)]}


CHAPTERS = [chapter(1, PLAIN), chapter(2, NAMING, LOOK, PLAIN, CALLERS), chapter(6, LOOK)]
HOLMES = {"id": "sherlock_holmes", "name": "Sherlock Holmes", "aliases": ["Holmes", "Mr. Holmes"],
          "first_chapter": 1}


class TestCandidates:
    def test_names_are_the_name_and_its_aliases_longest_first(self):
        assert portrait.names_of(HOLMES) == ["Sherlock Holmes", "Mr. Holmes", "Holmes"]

    def test_a_relational_alias_names_nobody(self):
        """Watson's aliases carried 'my companion' -- which, in Watson's own
        narration, is Holmes: Watson's portrait came back as six feet and
        hawk-nosed.  An alias by relation to the speaker is not a name."""
        watson = {"name": "John Watson", "aliases": ["my companion", "Dr. Watson", "his friend",
                                                     "the doctor"]}
        assert portrait.names_of(watson) == ["John Watson", "the doctor", "Dr. Watson", "Watson"]

    def test_the_surname_alone_is_a_name(self):
        """Stamford: 'Whatever have you been doing with yourself, Watson? You
        are as thin as a lath' -- the analysis listed 'Dr. Watson' and
        'Dr. John Watson', never 'Watson', and Watson had one candidate."""
        assert "Hope" in portrait.names_of({"name": "Jefferson Hope", "aliases": []})
        assert portrait.names_of({"name": "Stamford", "aliases": []}) == ["Stamford"]
        assert "Ann" not in portrait.names_of({"name": "Lucy Ann", "aliases": []})

    def test_a_paragraph_that_names_the_person_and_carries_a_look_word_is_a_candidate(self):
        found = portrait.candidates(CHAPTERS, portrait.names_of(HOLMES), first_chapter=1)
        assert Passage(chapter=2, n=1, text=NAMING) in found

    def test_the_paragraph_after_a_naming_one_is_a_candidate_too(self):
        """Doyle's portrait paragraph says 'he' throughout."""
        found = portrait.candidates(CHAPTERS, portrait.names_of(HOLMES), first_chapter=1)
        assert Passage(chapter=2, n=2, text=LOOK) in found

    def test_the_paragraph_before_a_naming_one_is_a_candidate_too(self):
        """Gregson: 'a tall, white-faced, flaxen-haired man' in one paragraph,
        named in the next when Holmes speaks to him."""
        met = "At the door we were met by a tall, white-faced, flaxen-haired man."
        named = "“No doubt you had drawn your own conclusions, Gregson,” my friend answered."
        found = portrait.candidates([chapter(3, PLAIN, met, named)], ["Gregson"], first_chapter=3)
        assert [p.n for p in found] == [2]

    def test_a_paragraph_without_a_look_word_is_not(self):
        found = portrait.candidates(CHAPTERS, portrait.names_of(HOLMES), first_chapter=1)
        assert all(p.text != PLAIN for p in found)

    def test_only_the_chapters_around_the_first_appearance_are_read(self):
        found = portrait.candidates(CHAPTERS, portrait.names_of(HOLMES), first_chapter=1)
        assert all(p.chapter < 1 + portrait.SPAN for p in found)

    def test_the_read_is_capped(self):
        many = [chapter(1, *([NAMING] * 40))]
        assert len(portrait.candidates(many, ["Holmes"], first_chapter=1)) == portrait.CAP

    def test_a_name_inside_another_word_is_not_a_mention(self):
        found = portrait.candidates([chapter(1, "The Holmesian method has hair-splitting rigour.")],
                                    ["Holmes"], first_chapter=1)
        assert found == []


class TestVerify:
    def test_a_quoted_sentence_must_be_verbatim_in_the_passages(self):
        passages = [Passage(chapter=2, n=2, text=LOOK)]
        good = Portrait(sentences=["In height he was rather over six feet, and so excessively "
                                   "lean that he seemed to be considerably taller."], build="lean")
        assert portrait.verify(good, passages) == good
        with pytest.raises(ValueError, match="not in the book"):
            portrait.verify(Portrait(sentences=["He had a full dark beard."]), passages)

    def test_curly_quotes_and_spacing_do_not_make_a_quote_foreign(self):
        passages = [Passage(chapter=2, n=1, text="“I’ve found it!” he  shouted.")]
        assert portrait.verify(Portrait(sentences=["\"I've found it!\" he shouted."]), passages)

    def test_a_slot_needs_a_sentence(self):
        """No slot without a sentence: a reading nobody can point at is invention."""
        with pytest.raises(ValidationError):
            Portrait(sentences=[], hair="black")


class FakeLLM:
    def __init__(self, *answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, tier, prompt, schema, **kw):
        self.prompts.append(prompt)
        return self.answers.pop(0)


class TestAsk:
    def test_the_model_reads_the_candidates_and_the_answer_is_verified(self, monkeypatch):
        answer = Portrait(sentences=["His eyes were sharp and piercing."], build="lean")
        fake = FakeLLM(answer)
        monkeypatch.setattr(portrait.llm, "structured", fake)
        got = portrait.ask(HOLMES, CHAPTERS)
        assert got == answer
        assert LOOK in fake.prompts[0] and "Sherlock Holmes" in fake.prompts[0]

    def test_a_foreign_quote_is_asked_again_then_the_book_stays_silent(self, monkeypatch):
        foreign = Portrait(sentences=["He had a full dark beard."], facial_hair="beard")
        fake = FakeLLM(foreign, foreign)
        monkeypatch.setattr(portrait.llm, "structured", fake)
        assert portrait.ask(HOLMES, CHAPTERS) == Portrait()
        assert len(fake.prompts) == 2 and "not in the book" in fake.prompts[1]

    def test_nothing_is_asked_when_no_paragraph_could_describe_the_person(self, monkeypatch):
        fake = FakeLLM()
        monkeypatch.setattr(portrait.llm, "structured", fake)
        assert portrait.ask({**HOLMES, "aliases": []}, [chapter(1, PLAIN)]) == Portrait()
        assert fake.prompts == []


class TestStated:
    def test_a_phrase_the_model_reads_whole_is_the_card(self):
        """'long chestnut hair' reads as brown AND long; the book's own words
        are the slot.  'white-faced' reads pale."""
        found = Portrait(sentences=["x"], hair="long chestnut hair", complexion="white-faced",
                         build="tall")
        assert portrait.stated(found) == {"hair": "long chestnut hair",
                                          "complexion": "white-faced", "build": "tall"}

    def test_a_phrase_read_in_part_snaps_onto_the_pool_phrase_that_reads_the_same(self):
        """Gregson is 'flaxen-haired' -- a colour, no length -- and a card that
        invents 'dark hair swept back' beside the quoted sentence tells the
        model two things (run 6).  The pool phrase that reads fair is the card."""
        got = portrait.stated(Portrait(sentences=["x"], hair="flaxen-haired", age="young"))
        assert got["hair"] in cast_card.POOLS["hair"] and coarse("hair", got["hair"]) == "fair"
        assert got["age"] in cast_card.POOLS["age"] and coarse("age", got["age"]) == "young"

    def test_a_list_of_phrases_states_the_first_one_that_reads(self):
        """Lucy: 'fair face; cheek more ruddy; pale-faced' -- three readings in
        one slot is no reading.  The first the model reads is the card;
        build has no reading and keeps the whole list."""
        found = Portrait(sentences=["x"], complexion="frightened; fair face; pale-faced",
                         build="rather over six feet; excessively lean")
        assert portrait.stated(found) == {"complexion": "fair face",
                                          "build": "rather over six feet, excessively lean"}

    def test_the_pool_phrase_nearest_the_books_words_is_preferred(self):
        """'about forty-three or forty-four' is middle-aged, and so is
        'about thirty-five'; 'about forty' shares the word."""
        got = portrait.stated(Portrait(sentences=["x"], age="about forty-three or forty-four"))
        assert got["age"] == "about forty"

    def test_an_age_is_always_the_pool_phrase(self):
        """The card reads 'A man {age}': 'A man young' is not a sentence."""
        got = portrait.stated(Portrait(sentences=["x"], age="about forty-three or forty-four"))
        assert got["age"] in cast_card.POOLS["age"] and coarse("age", got["age"]) == "middle-aged"

    def test_a_phrase_the_vocabulary_cannot_read_states_nothing(self):
        """'frightened face' is not a complexion; and a phrase the fidelity
        gate cannot read would raise in `expected`."""
        found = Portrait(sentences=["x"], hair="hair like a wire brush",
                         complexion="frightened face", build="little; lean")
        assert portrait.stated(found) == {"build": "little, lean"}

    def test_silence_states_nothing(self):
        assert portrait.stated(Portrait()) == {}


class TestPhysical:
    def test_the_book_sentences_come_before_the_dossier(self):
        found = Portrait(sentences=["His eyes were sharp and piercing."])
        assert portrait.physical_text(found, "Hands mottled with plaster.") == (
            "His eyes were sharp and piercing.")

    def test_a_silent_book_leaves_the_dossier(self):
        assert portrait.physical_text(Portrait(), "Hands mottled with plaster.") == (
            "Hands mottled with plaster.")
