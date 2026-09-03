"""Every beat carried the same camera sentence, twenty-three times over.

`motivated_move` existed and was never called.  What was missing was not the
sentence builder but the two things it needs from the book: what starts the
move, and what it arrives at.
"""
from __future__ import annotations

from studio.shot_grammar import camera_for, cause_of, destination_of

STOOP = "Holmes stoops over the body and lifts a small glass phial."
DOOR = "The door swings open on a dark hallway."
BARE = "Some time passes uneventfully."


class TestDestinationOf:
    def test_it_finds_the_thing_the_sentence_lands_on(self):
        assert "phial" in destination_of(STOOP)

    def test_it_keeps_the_words_that_make_the_noun_specific(self):
        """'the phial' and 'a small glass phial' are different pictures."""
        assert destination_of(STOOP) == "a small glass phial"

    def test_it_takes_the_last_concrete_noun_not_the_first(self):
        """The sentence lands on the phial; the body is where it started."""
        assert "body" not in destination_of(STOOP)

    def test_a_line_with_no_photographable_noun_has_no_destination(self):
        assert destination_of(BARE) == ""

    def test_a_single_noun_line_still_yields_one(self):
        assert "door" in destination_of(DOOR)


class TestCauseOf:
    def test_it_takes_the_action_that_starts_the_move(self):
        assert cause_of(STOOP) == "Holmes stoops over the body"

    def test_it_drops_the_trailing_clause_that_holds_the_destination(self):
        assert "phial" not in cause_of(STOOP)

    def test_a_single_clause_line_is_its_own_cause(self):
        assert cause_of(DOOR) == "The door swings open on a dark hallway"


class TestCameraFor:
    def test_a_move_names_its_cause_and_its_destination(self):
        sentence = camera_for(STOOP, "insert", 0.4)
        assert "Holmes stoops" in sentence and "phial" in sentence

    def test_a_line_with_no_destination_locks_the_camera_off(self):
        """A move with no target is drift by definition, and three flavours of
        drift is still drift.  Refusing to move is the honest output."""
        assert "static" in camera_for(BARE, "medium", 0.4)

    def test_the_sentence_is_a_sentence(self):
        assert camera_for(STOOP, "close", 0.4).endswith(".")

    def test_different_beats_do_not_share_one_sentence(self):
        """23 of 23 beats read 'The camera pushes in with small amplitude at
        slow speed.'  That is the defect, stated."""
        sentences = {camera_for(t, s, p) for t, s, p in
                     [(STOOP, "insert", 0.1), (DOOR, "wide", 0.5),
                      (STOOP, "close", 0.9), (DOOR, "medium", 0.2)]}
        assert len(sentences) == 4

    def test_a_wide_early_shot_does_not_push_in(self):
        assert "pushes in" not in camera_for(DOOR, "extreme_wide", 0.05)
