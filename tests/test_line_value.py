"""What makes a line work with no scene around it.

The scorer ranked "No data yet." above "I knew of their guilt, and I determined
that I should be judge, jury, and executioner all rolled into one." -- because
it penalised >18 words and >4 seconds.  It was selecting for SHORTNESS, and
shortness is not the property.  A trailer line is a CLAIM that survives having
its context removed; how long it is only matters against the shot it sits on,
and assign_lines already refuses a line that outlasts its picture.

Every line below is real text from the two books in the library.
"""
from __future__ import annotations

from studio.trailer_dialogue import line_value

LEADS = ("sherlock_holmes", "jefferson_hope")


def score(text, speaker="sherlock_holmes", emotion="level"):
    return line_value(text, emotion, speaker, LEADS)


JUDGE = ("I knew of their guilt though, and I determined that I should be "
         "judge, jury, and executioner all rolled into one.")
AFGHAN = "You have been in Afghanistan, I perceive."
SUPPLIED = ("The face supplied the fear. The smell supplied the poison. "
            "The ring supplied the woman.")
REASON = "Most people reason forwards. I begin with the result."
NO_DATA = "No data yet."
WHAT_SORT = "What sort of a man was he?"
CAB = "You did not come here in a cab?"
ERRAND = "Just ask him to step up, Wiggins."


class TestAClaimBeatsAQuery:
    def test_a_question_loses_to_a_statement(self):
        """A question is dialogue from inside a conversation.  The answer never
        comes, because there is no next line in a trailer."""
        assert score(WHAT_SORT) < score(AFGHAN)

    def test_every_question_in_the_pool_loses_to_every_claim(self):
        for query in (WHAT_SORT, CAB):
            for claim in (JUDGE, AFGHAN, SUPPLIED, REASON):
                assert score(query) < score(claim), (query, claim)


class TestLengthIsNotTheProperty:
    def test_the_best_line_in_the_book_is_not_punished_for_being_long(self):
        assert score(JUDGE) > score(NO_DATA)

    def test_an_empty_short_line_ranks_below_every_real_one(self):
        for real in (JUDGE, AFGHAN, SUPPLIED, REASON):
            assert score(NO_DATA) < score(real), real

    def test_a_genuinely_unspeakable_line_is_still_refused(self):
        """Length stops being free somewhere.  Sixty words is a paragraph."""
        assert score(" ".join(["the murderer walked slowly through the fog"] * 9)) \
            < score(AFGHAN)


class TestStance:
    def test_a_first_person_declaration_outranks_an_errand(self):
        assert score(JUDGE) > score(ERRAND)

    def test_parallel_structure_is_rewarded(self):
        """'The face supplied... The smell supplied... The ring supplied...'
        is built to be quoted; that is what the repetition is FOR."""
        assert score(SUPPLIED) > score(ERRAND)

    def test_an_errand_with_a_proper_name_ranks_low(self):
        assert score(ERRAND) < score(REASON)


class TestTheSlateThisProduces:
    def test_the_top_four_are_all_claims(self):
        pool = [JUDGE, AFGHAN, SUPPLIED, REASON, NO_DATA, WHAT_SORT, CAB, ERRAND]
        top = sorted(pool, key=score, reverse=True)[:4]
        assert set(top) == {JUDGE, AFGHAN, SUPPLIED, REASON}, top
