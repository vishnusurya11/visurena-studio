"""Choosing N distinct setups, spread across the book.

The rule this replaces allowed ONE element per scene and capped each location
at two, so twelve eligible scenes over six locations made NINE the arithmetic
maximum for A Study in Scarlet.  `SETUPS = 18` was unreachable by construction
and the build printed a success line anyway.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio.trailer_story import select_setups

BOOK = Path("library/20260822113400_a-study-in-scarlet")


@pytest.fixture(scope="module")
def scenes():
    return json.loads((BOOK / "screenplay/feature/screenplay.json")
                      .read_text(encoding="utf-8"))["scenes"]


@pytest.fixture(scope="module")
def refs():
    doc = json.loads((BOOK / "refs/refs.json").read_text(encoding="utf-8"))
    return {r["ref_id"] for r in doc["refs"]}


class TestSelectSetups:
    def test_it_returns_the_count_asked_for(self, scenes, refs):
        assert len(select_setups(scenes, refs, 24)) == 24

    def test_it_can_reach_counts_the_old_selector_could_not(self, scenes, refs):
        """Nine was the ceiling.  Thirty is now reachable."""
        assert len(select_setups(scenes, refs, 30)) == 30

    def test_every_setup_is_distinct(self, scenes, refs):
        chosen = select_setups(scenes, refs, 24)
        keys = {(c["scene"], c["index"]) for c in chosen}
        assert len(keys) == 24

    def test_it_spreads_across_many_scenes(self, scenes, refs):
        """The old selector reached six locations and twelve scenes at most."""
        chosen = select_setups(scenes, refs, 24)
        assert len({c["scene"] for c in chosen}) >= 10

    def test_no_single_location_dominates(self, scenes, refs):
        from collections import Counter
        chosen = select_setups(scenes, refs, 24)
        top = Counter(c["location_id"] for c in chosen).most_common(1)[0][1]
        assert top <= len(chosen) * 0.4

    def test_every_chosen_setup_has_a_location_plate(self, scenes, refs):
        for c in select_setups(scenes, refs, 24):
            assert f"loc-{c['location_id']}" in refs

    def test_it_finds_the_word_written_in_blood(self, scenes, refs):
        """RACHE is the single most remembered image in this book, and the old
        selector could not reach it: scene 5 was spent on wet grass, which won
        a tie broken by position in the JSON file."""
        chosen = select_setups(scenes, refs, 30)
        assert any("RACHE" in c["setup"] or "RACHE" in
                   " ".join(e.get("text", "") for e in c["covers"])
                   for c in chosen)

    def test_it_prefers_emphasised_setups(self, scenes, refs):
        """43 of 411 carry a camera move.  They should be over-represented."""
        chosen = select_setups(scenes, refs, 30)
        moved = sum(1 for c in chosen if c["term"] != "locked-off")
        assert moved / len(chosen) > 43 / 411

    def test_asking_for_more_than_exist_returns_what_exists(self, scenes, refs):
        chosen = select_setups(scenes, refs, 10_000)
        assert 0 < len(chosen) < 10_000
