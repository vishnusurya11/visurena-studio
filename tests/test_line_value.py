"""What makes a line work with no scene around it.

Two scorers have been wrong here.  The first ranked "No data yet." above the
best line in the book because it paid for SHORTNESS.  The second (MEASURED
against 38 real trailer lines, research 1.2) deleted half the corpus with
`< 5 words -> -3.0` and deleted every hook with `? -> -4.0`: "This is
Sparta!" scored -7.6 and an errand from the Ferrier subplot topped all 38.

A trailer line is a CLAIM that survives having its context removed.  Short is
the format, a question is a hook the next line answers, and length only
matters against the slot the line sits in.  The scorer is graded on a corpus
it was never tuned on (Cornell "You had me at hello" pairs, held out); the
38 lines are a smoke test.

Every Scarlet line below is real text from the book.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from studio.trailer_dialogue import line_value

FIXTURES = Path(__file__).parent / "fixtures"
LEADS = ("sherlock_holmes", "jefferson_hope")


def score(text, speaker="sherlock_holmes", emotion="level"):
    return line_value(text, emotion, speaker, LEADS)


JUDGE = ("I knew of their guilt though, and I determined that I should be "
         "judge, jury, and executioner all rolled into one.")
AFGHAN = "You have been in Afghanistan, I perceive."
SUPPLIED = ("The face supplied the fear. The smell supplied the poison. "
            "The ring supplied the woman.")
REASON = "Most people reason forwards. I begin with the result."
DEATH = "There is death in one and life in the other."
NO_DATA = "No data yet."
WHAT_SORT = "What sort of a man was he?"
CAB = "You did not come here in a cab?"
ERRAND = "Just ask him to step up, Wiggins."
FERRIER = ("I guess you are the daughter of John Ferrier. "
           "I saw you ride down from his house.")
SPARTA = "This is Sparta!"
BOOK = [JUDGE, AFGHAN, SUPPLIED, REASON, DEATH, NO_DATA, WHAT_SORT, CAB, ERRAND, FERRIER]


class TestShortIsTheFormat:
    def test_sparta_outscores_ferrier_errand(self):
        """Three words that take a side beat sixteen that run an errand."""
        assert score(SPARTA, "leonidas") > score(FERRIER, "jefferson_hope")

    def test_no_data_yet_does_not_top_the_book(self):
        assert max(BOOK, key=score) != NO_DATA

    def test_a_short_claim_is_not_punished_for_being_short(self):
        assert score(SPARTA, "leonidas") > score(ERRAND)

    def test_a_genuinely_unspeakable_line_is_still_refused(self):
        """Length stops being free somewhere.  Sixty words is a paragraph."""
        assert score(" ".join(["the murderer walked slowly through the fog"] * 9)) \
            < score(AFGHAN)


class TestAQuestionIsAHook:
    def test_a_question_is_no_longer_deleted(self):
        """18% of iconic trailer lines are questions, all as hook or threat."""
        assert score("What is the Matrix?", "neo") > score(FERRIER, "jefferson_hope")

    def test_a_question_and_its_statement_form_score_alike(self):
        assert abs(score("Is it safe?") - score("It is safe.")) < 0.01


class TestStance:
    def test_a_first_person_declaration_outranks_an_errand(self):
        assert score(JUDGE) > score(ERRAND)

    def test_parallel_structure_is_rewarded(self):
        """'The face supplied... The smell supplied... The ring supplied...'
        is built to be quoted; that is what the repetition is FOR."""
        assert score(SUPPLIED) > score(ERRAND)

    def test_two_first_person_sentences_are_not_anaphora(self):
        """'I guess... I saw...' is narration, not rhetoric; the Ferrier errand
        used to collect +1.5 for it."""
        from studio.trailer_dialogue import is_parallel
        assert not is_parallel(FERRIER)
        assert is_parallel(SUPPLIED)

    def test_an_errand_with_a_proper_name_ranks_low(self):
        assert score(ERRAND) < score(REASON)

    def test_the_errand_is_at_the_bottom_of_the_book(self):
        assert min(BOOK, key=score) == ERRAND


class TestGenerality:
    """Cornell (ACL 2012): memorable lines have fewer third-person pronouns,
    more indefinite articles, present tense."""

    def test_a_third_person_pronoun_costs(self):
        assert score("A man is suspected of a crime.") > score("He is suspected of his crime.")

    def test_present_beats_past(self):
        assert score("There is death in the room.") > score("There was death in the room.")

    def test_rarer_words_score_higher(self):
        assert score("A colourless skein of murder.") > score("A bad bit of it all.")


class TestHeldOut:
    def test_line_value_beats_chance_on_cornell_pairs(self):
        """Pairwise accuracy on the Cornell memorable / non-memorable pairs
        (same film, same speaker, same word count) with iconicity OFF.  The
        pairs are length-matched, so the length band is inert and this grades
        exactly the other terms.  Ties count half.  Chance is 0.50."""
        doc = json.loads((FIXTURES / "cornell_pairs.json").read_text(encoding="utf-8"))
        wins = ties = 0
        for pair in doc["pairs"]:
            a = line_value(pair["memorable"], None, "x", ())
            b = line_value(pair["non_memorable"], None, "x", ())
            wins += a > b
            ties += a == b
        accuracy = (wins + 0.5 * ties) / len(doc["pairs"])
        assert len(doc["pairs"]) >= 400
        assert accuracy >= 0.55, accuracy

    def test_corpus_median_words_under_seven(self):
        doc = json.loads((FIXTURES / "trailer_lines.json").read_text(encoding="utf-8"))
        assert len(doc["lines"]) == 38
        assert statistics.median(len(l["text"].split()) for l in doc["lines"]) <= 7

    def test_most_of_the_corpus_scores_above_the_controls(self):
        """The MEASURED failure was 26 of 38 iconic lines below zero and the
        Ferrier errand above all 38.  The smoke test: the median iconic line
        outscores the best control."""
        doc = json.loads((FIXTURES / "trailer_lines.json").read_text(encoding="utf-8"))
        iconic = sorted(line_value(l["text"], None, l["speaker"] or "", ()) for l in doc["lines"])
        best_control = max(line_value(c["text"], None, c["speaker"], ()) for c in doc["controls"])
        assert statistics.median(iconic) > best_control
