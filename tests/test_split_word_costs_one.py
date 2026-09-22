"""A word the transcriber split costs ONE error, even when it respelt the seam.

MEASURED 2026-09-22 on ep08 line 9: "the carriages rocked on" came back as
"the carriage is rocked on". The audio was right -- say_lines transcribed the
same recording at WER 0.00 -- and the two forms are the same sound. `distance`
already charges one for a clean split ("under lines" for "underlines"), but
"carriage" + "is" is not "carriages" letter for letter, so it charged two, and
0.222 of a nine-word line failed a 0.2 wall on a line nobody misread.
"""
from studio.voice_qc import distance, error_rate, letters_apart


def words(s):
    return s.split()


def test_a_clean_split_still_costs_one():
    assert distance(words("under lines here"), words("underlines here")) == 1


def test_a_split_that_respelt_the_seam_costs_one():
    assert distance(words("the carriage is rocked on"),
                    words("the carriages rocked on")) == 1


def test_a_clean_join_still_costs_one():
    assert distance(words("underlines here"), words("under lines here")) == 1


def test_a_join_that_respelt_the_seam_costs_one():
    assert distance(words("the carriages rocked on"),
                    words("the carriage is rocked on")) == 1


def test_a_genuinely_wrong_word_still_costs_one_each():
    assert distance(words("the carriage is locked on"),
                    words("the carriages rocked on")) == 2


def test_two_short_words_are_not_joined_on_a_letter_of_slack():
    # "a" + "to" is "ato", one letter from "at" -- far too short to be a seam
    assert distance(words("a to"), words("at")) == 2


def test_the_ep08_line_now_passes_its_wall():
    assert error_rate("Londonwards. Four to a compartment. The carriage is rocked on.",
                      "Londonwards, four to a compartment, the carriages rocked on.") < 0.2


def test_letters_apart_counts_single_character_edits():
    assert letters_apart("carriageis", "carriages") == 1
    assert letters_apart("carriage", "carriage") == 0
    assert letters_apart("locked", "rocked") == 1
    assert letters_apart("abc", "xyz") == 3
