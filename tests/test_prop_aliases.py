"""An alias is a claim about the PROSE, so it is tested against the prose.

MEASURED against episode 3's real panel text, 2026-09-13, with the aliases as
they shipped:

    walking_stick    named in 4 setups, matched 0 times
    pencilled_list   matched on sitting_room via `the sheet`
    fingerprint      matched on garden_path via `the print`

THE MISS.  Every alias was written article-first -- `the stick`, `the black
stick`, `his stick`, `the cane` -- and `props_in` matches whole phrases, so
`(?<![a-z])the stick(?![a-z])` cannot see "the black **walking stick**".  An
article-prefixed alias only fires when the writer uses no adjective, and a
writer with an adjective is the normal case.  The head-noun form `walking stick`
matches all four.  This is the ep02 failure verbatim -- "a silver-knobbed
walking stick came back drawn as an iron poker" -- still live a book later.

THE TWO FALSE HITS.  `the sheet` matched "the near edge of THE SHEET lifts",
which is Gregson's notepaper, so a chapter-2 prop stapled its picture and its
size contract onto five chapter-3 inserts.  `the print` matched "the camera
pushes straight in on THE PRINT", which is a square-toed BOOT print in clay --
so a photograph of a window pane arrived with "it is a thumbnail wide" over
panels drawing a boot mark.  Both are generic head nouns that belong to more
objects than the one that claimed them.
"""
import json
from pathlib import Path

import pytest

from studio import episode_home, episode_seq_board as sq, prop_refs

BOOK = "20260822113400_a-study-in-scarlet"


@pytest.fixture(scope="module")
def prose():
    """Episode 3's real panel text, per setup."""
    book = episode_home.book_dir(BOOK)
    episode = episode_home.load_plan(book, 3)
    return {name: " ".join(str(v) for cell in sq.segments(episode.shots, name) for v in cell.values())
            for name in episode.setups}


@pytest.fixture(scope="module")
def rows():
    book = episode_home.book_dir(BOOK)
    doc = json.loads((book / "refs" / "refs.json").read_text(encoding="utf-8"))
    return [r for r in doc["refs"] if r.get("kind") == "prop"]


def found(rows, text):
    return {r["entity_id"] for r in prop_refs.props_in(text, rows)}


def test_the_walking_stick_is_found_wherever_the_prose_names_it(prose, rows):
    named = [s for s, text in prose.items() if "walking stick" in text.lower()]
    assert named, "episode 3's prose names the walking stick"
    for setup in named:
        assert "walking_stick" in found(rows, prose[setup]), setup


def test_an_adjective_between_the_article_and_the_noun_no_longer_hides_it(rows):
    assert "walking_stick" in found(rows, "his right hand on the silver ball knob of the black walking stick")


def test_the_bare_head_noun_matches_on_its_own(rows):
    assert "walking_stick" in found(rows, "a walking stick stands against the chair")


def test_gregsons_notepaper_is_not_the_pencilled_list(prose, rows):
    """`the sheet` is a head noun that belongs to more objects than one."""
    assert "pencilled_list" not in found(rows, prose["sitting_room"])


def test_a_boot_print_in_the_clay_is_not_the_fingerprint(prose, rows):
    """`the print` likewise -- garden_path's insert is a square-toed boot mark."""
    assert "fingerprint" not in found(rows, prose["garden_path"])


def test_the_fingerprint_is_still_found_when_the_prose_means_it(rows):
    assert "fingerprint" in found(rows, "the fingerprint stands on the glass of the window pane")


def test_the_pencilled_list_is_still_found_when_the_prose_means_it(rows):
    assert "pencilled_list" in found(rows, "the list lies open on the breakfast table")


def test_the_lettered_props_still_match_where_they_should(prose, rows):
    assert "to_let_card" in found(rows, prose["garden_path"])
    assert "visiting_card" in found(rows, prose["front_room"])
    assert "rache_wall" in found(rows, prose["corner_wall"])


def test_no_prop_claims_a_setup_it_does_not_appear_in(prose, rows):
    """The whole-episode regression guard: this is the set the sheets stage."""
    got = {name: sorted(found(rows, text)) for name, text in prose.items()}
    assert got == {
        "sitting_room": ["blue_envelope", "walking_stick"],
        "cab": ["walking_stick"],
        "garden_path": ["to_let_card"],
        "hall": ["walking_stick"],
        "front_room": ["visiting_card", "walking_stick"],
        "corner_wall": ["rache_wall"],
    }
