"""The grid driver draws with v1 or v2 by name, and says which in the manifest.

v2 stays beside v1 until a same-seed render of ep09's grids decides between
them (audit 2026-09-22, Tier 3 item 19); the manifest records the version so
the panels a grid was cut into can be traced back to the words that drew it.
"""
import pytest

from scripts.episode.grids import PROMPTS, compose, prompt_version
from studio.storyboard_grid import grid_prompt_v2

PLACE = ([2], "the walled lawn on the crest of Maybury Hill")
CAST = [{"ref": 1, "name": "NARRATOR", "entity": "n", "wear": "a grey suit", "against": "a"}]
BLOCKS = [{"size": "MEDIUM", "body": "THE HUSSAR SHOUTS", "cut": "at the waist",
           "who": ["NARRATOR"], "extras": 1}]


def test_v2_is_grid_prompt_v2_word_for_word():
    assert compose("v2", BLOCKS, 1, 1, PLACE, CAST, 2) == grid_prompt_v2(BLOCKS, 1, 1, PLACE, CAST, 2)


def test_v1_keeps_its_old_words_and_its_no_duplicates_line():
    text = compose("v1", BLOCKS, 1, 1, PLACE, CAST, 2)
    assert "THE HUSSAR SHOUTS" in text and "DRAWN IN EXACTLY THE ART STYLE OF <image2>" in text


def test_an_unknown_version_is_refused():
    with pytest.raises(SystemExit):
        compose("v3", BLOCKS, 1, 1, PLACE, CAST, 2)


def test_the_version_comes_from_the_command_line_and_defaults_to_v1():
    assert prompt_version(["grids.py", "wotw", "9", "--prompt=v2"]) == "v2"
    assert prompt_version(["grids.py", "wotw", "9"]) == "v1"
    assert set(PROMPTS) == {"v1", "v2"}
