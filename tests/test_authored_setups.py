"""Selecting from the framings the screenplay already wrote.

`scene["shots"]` holds 411 authored camera setups for A Study in Scarlet -- each
one a framing with an element span -- and no trailer code has ever read it.  The
selector instead ranked raw action lines and could return at most NINE setups
for this book, by arithmetic: one element per scene, twelve eligible scenes, a
flat two-per-location cap.  Thirty-one shots were then cut from those nine.
"""
from __future__ import annotations

import pytest

from studio.trailer_story import (action_text, authored_setups, covered_elements,
                                  invented_density, is_emphasised, named_things,
                                  setup_value, verbatim_density)

SCENE = {
    "number": 5, "duration_s": 90.0,
    "slug": {"location_id": "number_3_lauriston_gardens"},
    "cast": ["sherlock_holmes", "g_lestrade"],
    "elements": [
        {"kind": "action", "text": "Lestrade strikes a match.", "provenance": "verbatim"},
        {"kind": "action", "text": "The flame reveals RACHE across the plaster.",
         "provenance": "verbatim"},
        {"kind": "dialogue", "character": "g_lestrade", "text": "Rache, revenge.",
         "provenance": "adapted"},
        {"kind": "action", "text": "Holmes studies the wet grass.", "provenance": "invented"},
    ],
    "shots": [
        {"index": 0, "setup": "Locked-off medium frame on Lestrade at the plaster wall.",
         "term": "locked-off", "covers_start": 0, "covers_end": 2},
        {"index": 1, "setup": "Dolly in toward the writing on the wall.",
         "term": "dolly in", "covers_start": 1, "covers_end": 1},
        {"index": 2, "setup": "Locked-off close on the grass beside the path.",
         "term": "locked-off", "covers_start": 3, "covers_end": 3},
    ],
}


class TestAuthoredSetups:
    def test_it_yields_one_candidate_per_authored_framing(self):
        assert len(list(authored_setups([SCENE]))) == 3

    def test_a_candidate_knows_its_scene_and_place(self):
        first = next(iter(authored_setups([SCENE])))
        assert first["scene"] == 5
        assert first["location_id"] == "number_3_lauriston_gardens"

    def test_a_candidate_names_the_people_in_its_own_frame(self):
        """Not the scene's cast: the shot's.  The Lestrade framing is Lestrade,
        the grass insert is Holmes, the wall is nobody."""
        found = list(authored_setups([SCENE]))
        assert [c["subjects"] for c in found] == [["g_lestrade"], [], ["sherlock_holmes"]]
        assert all(c["cast"] == {"sherlock_holmes", "g_lestrade"} for c in found)

    def test_a_scene_with_no_authored_shots_yields_nothing(self):
        assert list(authored_setups([{**SCENE, "shots": []}])) == []

    def test_the_real_book_has_far_more_setups_than_action_lines(self):
        import json
        from pathlib import Path
        book = Path("library/20260822113400_a-study-in-scarlet")
        scenes = json.loads((book / "screenplay/feature/screenplay.json")
                            .read_text(encoding="utf-8"))["scenes"]
        assert len(list(authored_setups(scenes))) == 411


class TestCoveredElements:
    def test_a_setup_covers_the_span_it_names(self):
        covered = covered_elements(SCENE, SCENE["shots"][0])
        assert len(covered) == 3

    def test_the_span_reaches_dialogue_as_well_as_action(self):
        """`action_elements` filtered kind == 'action', so 'You have been in
        Afghanistan, I perceive.' could never be selected as an image."""
        covered = covered_elements(SCENE, SCENE["shots"][0])
        assert any(e["kind"] == "dialogue" for e in covered)

    def test_action_text_joins_the_setup_to_its_action(self):
        text = action_text({"setup": SCENE["shots"][0]["setup"],
                            "covers": covered_elements(SCENE, SCENE["shots"][0])})
        assert "plaster wall" in text and "RACHE" in text


class TestSignals:
    def test_a_camera_move_marks_emphasis(self):
        """43 of 411 setups carry a move.  The adapter spent one only where it
        meant something."""
        assert is_emphasised({"term": "dolly in"})
        assert not is_emphasised({"term": "locked-off"})

    def test_verbatim_density_is_a_ratio_not_a_count(self):
        covered = covered_elements(SCENE, SCENE["shots"][0])
        assert verbatim_density({"covers": covered}) == pytest.approx(2 / 3)

    def test_an_invented_moment_cannot_be_one_a_reader_remembers(self):
        covered = covered_elements(SCENE, SCENE["shots"][2])
        assert invented_density({"covers": covered}) == 1.0

    def test_named_things_finds_the_icon(self):
        assert named_things("The flame reveals RACHE across the plaster") >= 1

    def test_named_things_is_capped_so_length_cannot_win(self):
        names = "Drebber Stangerson Ferrier Lucy Gregson Lestrade Jefferson Hope"
        assert named_things(names, cap=3) == 3

    def test_camera_vocabulary_is_not_a_named_thing(self):
        assert named_things("Locked-off Dolly Handheld") == 0


class TestSetupValue:
    def test_the_rache_setup_outranks_the_wet_grass_setup(self):
        """The defect, stated.  Both are in scene 5; the old ranker tied 75 of
        268 lines at the IDF ceiling and broke the tie by document order, so
        wet grass won because it appears earlier in the JSON."""
        rache = dict(next(c for c in authored_setups([SCENE]) if c["index"] == 0))
        grass = dict(next(c for c in authored_setups([SCENE]) if c["index"] == 2))
        args = ({}, {}, {"char-sherlock_holmes", "char-g_lestrade"}, {})
        assert setup_value(rache, *args) > setup_value(grass, *args)

    def test_the_emphasised_setup_ranks_highest_of_all(self):
        cands = [dict(c) for c in authored_setups([SCENE])]
        args = ({}, {}, {"char-sherlock_holmes", "char-g_lestrade"}, {})
        best = max(cands, key=lambda c: setup_value(c, *args))
        assert best["term"] == "dolly in"


class TestShoutedThings:
    """Screenplay convention capitalises what the audience must notice.

    Across A Study in Scarlet's 268 action lines there are exactly thirteen
    such tokens, and they are a list of the book's beats: RACHE, RING, CLICK
    (the handcuffs), THROBBING (the aneurism), MURDER, HOPE.  Rare, deliberate,
    and the score had no term for it -- so the single most remembered image in
    the book ranked 25th and was never selected.
    """

    def test_a_shouted_word_is_found(self):
        from studio.trailer_story import shouted_things
        assert shouted_things("The flame reveals RACHE across the plaster") == 1

    def test_ordinary_capitalisation_is_not_shouting(self):
        from studio.trailer_story import shouted_things
        assert shouted_things("Holmes and Watson enter Baker Street") == 0

    def test_it_is_capped_so_a_long_line_cannot_win_on_volume(self):
        from studio.trailer_story import shouted_things
        assert shouted_things("RACHE RING CLICK MURDER HOPE THROBBING", cap=2) == 2

    def test_the_word_written_in_blood_is_selected(self):
        """The end-to-end claim, on the real book."""
        import json
        from pathlib import Path
        from studio.trailer_story import action_text, select_setups
        book = Path("library/20260822113400_a-study-in-scarlet")
        scenes = json.loads((book / "screenplay/feature/screenplay.json")
                            .read_text(encoding="utf-8"))["scenes"]
        refs = {r["ref_id"] for r in json.loads(
            (book / "refs/refs.json").read_text(encoding="utf-8"))["refs"]}
        chosen = select_setups(scenes, refs, 30)
        assert any("RACHE" in action_text(c) for c in chosen)
