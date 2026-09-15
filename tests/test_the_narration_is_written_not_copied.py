r"""The 8-word quote ceiling has been in the spec since episode 1 and gated nothing.

MEASURED 2026-09-15 over all six published plans, longest run of consecutive
words appearing verbatim anywhere in the book:

    ep   lines  over 8  worst   narration  dialogue
    01     23      1     10w        1          0
    02     25      0      -         0          0
    03     25      0      -         0          0
    04     24      5     14w        2          3
    05     24      6     14w        4          2
    06     26      4     12w        1          3

THE TREND IS THE FINDING, NOT THE INCIDENTS. Episodes 2 and 3 quote nothing.
From episode 4 the narration starts transcribing, and episode 5 -- the most
faithful of the six -- carries the longest lift in the set:

    "If ever human features bespoke vice of the most malignant type, they were
     certainly his."

Fourteen words of Doyle. It is 1887 magazine prose, it is hard to say aloud, and
it plays over an insert of a restless hand, so it neither describes the picture
nor advances anything. Episodes 2 and 3, which quote nothing, are the two the
review rated highest as writing. The drift is from adaptation toward
audiobook-with-pictures.

NARRATION IS HARD, DIALOGUE IS ADVISORY, and the split is the whole judgement.
Narration is Watson's voice-over: it exists to carry what the picture cannot,
and a transcribed sentence spends that channel on what Doyle already wrote.
Dialogue is a character speaking, and Doyle's dialogue is better than anything
written to replace it -- the marine's "A sergeant, sir. Royal Marine Light
Infantry, sir." is episode 2's button and is very nearly verbatim. Its craft is
in the TRIM: Doyle's line runs on with "No answer? Right, sir." and cutting
those four words is the difference between a transcription and a button.

A QUERY, NOT A VALIDATOR -- `long_shots` records what happens otherwise. Four
published plans fail this; reading them is not endorsing them.
"""
import pytest

from studio.episode_spec import QUOTE_WALL, lifted_run, quoted_lines

BOOK = ("if ever human features bespoke vice of the most malignant type they were "
        "certainly those of enoch j drebber of cleveland and the brick fronts went "
        "past the open window at the horse's trot a sergeant sir royal marine light "
        "infantry sir no answer right sir")


def test_a_fresh_sentence_lifts_nothing():
    assert lifted_run("Nobody had said my name in weeks.", BOOK) == 0


def test_the_longest_lift_is_measured():
    said = "If ever human features bespoke vice of the most malignant type, they were certainly his."
    assert lifted_run(said, BOOK) == 14


def test_a_short_borrowing_is_under_the_wall():
    """Eight words is the ceiling and eight words is allowed."""
    assert lifted_run("the brick fronts went past the open window", BOOK) <= QUOTE_WALL


def test_the_trimmed_button_passes():
    """Doyle runs on with "No answer? Right, sir." Cutting those four words is
    the difference between a transcription and a button -- and the trimmed line
    is exactly at the wall, not over it."""
    assert lifted_run("A sergeant, sir. Royal Marine Light Infantry, sir.", BOOK) <= QUOTE_WALL


def test_the_untrimmed_one_does_not():
    said = "A sergeant, sir. Royal Marine Light Infantry, sir. No answer? Right, sir."
    assert lifted_run(said, BOOK) > QUOTE_WALL


def test_punctuation_and_case_do_not_hide_a_lift():
    said = "IF EVER human features -- bespoke vice of the most malignant type!"
    assert lifted_run(said, BOOK) >= 10


def test_an_empty_line_lifts_nothing():
    assert lifted_run("", BOOK) == 0
    assert lifted_run("Static.", "") == 0


# ---- narration is hard, dialogue advises ------------------------------------

LINES = [{"index": 0, "kind": "narration",
          "text": "If ever human features bespoke vice of the most malignant type, they were certainly his."},
         {"index": 1, "kind": "dialogue",
          "text": "A sergeant, sir. Royal Marine Light Infantry, sir. No answer? Right, sir."},
         {"index": 2, "kind": "narration", "text": "Nobody had said my name in weeks."}]


def test_a_transcribed_narration_line_is_refused():
    hard, _ = quoted_lines(LINES, BOOK)
    assert [l["index"] for l in hard] == [0]


def test_a_transcribed_dialogue_line_only_advises():
    _, soft = quoted_lines(LINES, BOOK)
    assert [l["index"] for l in soft] == [1]


def test_a_written_line_is_in_neither():
    hard, soft = quoted_lines(LINES, BOOK)
    assert 2 not in [l["index"] for l in hard + soft]


def test_the_report_names_the_run_length():
    hard, _ = quoted_lines(LINES, BOOK)
    assert hard[0]["lifted"] == 14


def test_a_plan_that_quotes_nothing_is_clean():
    hard, soft = quoted_lines([LINES[2]], BOOK)
    assert hard == [] and soft == []


def test_the_wall_is_the_one_the_spec_has_always_named():
    assert QUOTE_WALL == 8
