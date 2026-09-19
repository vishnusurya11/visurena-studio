"""A series title card: one picture for the book, lettered per episode."""
from studio.series_title import (card_lines, chapter_name, letter_prompt,
                                 lines_read, missing_lines)


def test_chapter_name_drops_the_roman_numeral_and_full_stop():
    assert chapter_name("I. THE EVE OF THE WAR.") == "THE EVE OF THE WAR"
    assert chapter_name("XVII. THE “THUNDER CHILD”.") == "THE “THUNDER CHILD”"


def test_card_lines_are_series_episode_then_chapter():
    assert card_lines("The War of the Worlds", 1, "I. THE EVE OF THE WAR.") == [
        "THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"]


def test_letter_prompt_quotes_every_line_exactly():
    lines = ["THE WAR OF THE WORLDS", "EPISODE 12", "THE AVENGING ANGELS"]
    text = letter_prompt(lines)
    assert all(f'"{line}"' in text for line in lines)


def test_lines_read_is_forgiving_of_case_space_and_punctuation():
    ocr = "The War of the  Worlds\nEPISODE 1\nThe Eve of the War."
    assert lines_read(["THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"], ocr)


def test_a_misspelt_line_is_named():
    ocr = "THE WAR OF THE WORLOS\nEPISODE 1\nTHE EVE OF THE WAR"
    assert missing_lines(["THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"], ocr) == [
        "THE WAR OF THE WORLDS"]


def test_a_wrong_episode_number_is_caught():
    assert not lines_read(["EPISODE 1"], "EPISODE 11")
