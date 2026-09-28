"""G-STORY's first-dialogue wall holds only when the chapter itself speaks early.

ep13 (2026-09-27): chapter 13 has no quoted speech until about halfway; every
writer draft failed the 25 % wall (0.57, 0.28, 0.53, 0.53), and the plan was
patched with an unmarked flash-forward to pass it -- the owner's "why is he the
first shot".  Where the chapter's first quote falls past the wall, the wall is
no refusal: enter the chapter later and compress, never reorder (G-ORDER).
"""
from studio import plan_gates as pg

LATE = ["The Martians fell back.", "Guns were dug in.", "I found a boat.", "I woke by a hedge.",
        '"What does it mean?" he asked.']
EARLY = ['"Hush," she said.', "The door closed.", "Night fell.", "He slept."]


def test_the_chapter_quote_share_is_where_its_first_speech_falls():
    assert pg.quote_share(EARLY) == 0.0
    assert 0.6 < pg.quote_share(LATE) < 1.0


def test_a_late_speaking_chapter_is_not_held_to_the_wall():
    assert pg.dialogue_wall_holds(pg.quote_share(LATE)) is False
    assert pg.dialogue_wall_holds(pg.quote_share(EARLY)) is True
    assert pg.dialogue_wall_holds(None) is True
