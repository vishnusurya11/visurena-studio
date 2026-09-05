"""The story SPINE: three movements, in order, with the answer withheld.

Run 10 had no spine.  Setups were score-ranked and scattered on the music
grid, so the killer's face arrived at 8.75 s and the handcuffs at 17 s -- the
whodunit was over before the trailer was.  A trailer is not a playlist of
good frames; it is world -> problem -> threat, and that order is the product.

The fixture is run 10's own screenplay, trimmed to three authored setups a
scene (tests/fixtures/scarlet_scenes.json).  Nothing here reads `library/`.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from studio.trailer_story import (MOVEMENTS, PLACE_SHARE, PRINCIPAL_SHARE, face_of,
                                  identity_scenes, late_floor, movement_bounds, movement_of,
                                  movement_quota, select_by_movement, select_setups, turn_of)

HOLMES, WATSON, HOPE = "sherlock_holmes", "john_watson", "jefferson_hope"
FIXTURE = Path(__file__).parent / "fixtures" / "scarlet_scenes.json"


def scarlet() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["scenes"]


def sheets(scenes: list[dict]) -> set[str]:
    """Every location plated and the three characters run 10 had sheets for."""
    places = {f"loc-{sc['slug']['location_id']}" for sc in scenes}
    return places | {f"char-{c}" for c in (HOLMES, WATSON, HOPE)}


def kendall_tau(order: list, key: list) -> float:
    """Rank agreement between the play order and the story order, -1..1."""
    pairs = [(a, b) for a in range(len(order)) for b in range(a + 1, len(order))]
    live = [(a, b) for a, b in pairs if key[a] != key[b]]
    if not live:
        return 1.0
    agree = sum(1 for a, b in live if (key[a] < key[b]))
    return (2 * agree - len(live)) / len(live)


class TestMovementBounds:
    """Two marks cut the story in three.  The second is the story's own break
    (`turn_of`); the first is where the lead's world stops being the whole
    cast list."""

    def test_the_turn_closes_the_second_movement(self):
        scenes = scarlet()
        assert turn_of(scenes, HOLMES)["number"] == 11
        assert movement_bounds(scenes, HOLMES)[1] == 11

    def test_the_first_movement_is_the_leads_introduction(self):
        """Scarlet: the bar and the hospital, before Lestrade knocks."""
        assert movement_bounds(scarlet(), HOLMES)[0] == 2

    def test_every_scene_lands_in_exactly_one_movement(self):
        bounds = movement_bounds(scarlet(), HOLMES)
        found = {sc["number"]: movement_of(sc["number"], bounds) for sc in scarlet()}
        assert set(found.values()) == set(MOVEMENTS)
        assert found[1] == "M1" and found[5] == "M2" and found[11] == "M2"
        assert found[12] == "M3" and found[18] == "M3"

    def test_a_story_with_no_room_still_leaves_a_middle(self):
        """Two marks that would collide are pulled apart: a movement with no
        scene in it cannot be ordered."""
        scenes = [{"number": n, "cast": [HOLMES] if n == 1 else [HOPE], "speaking": [],
                   "slug": {"location_id": "room"}, "elements": []} for n in (1, 2, 3)]
        m1, m2 = movement_bounds(scenes, HOLMES)
        assert m1 < m2


class TestQuota:
    def test_the_quotas_scale_with_the_shot_count(self):
        for count in (8, 12, 20, 41):
            quota = movement_quota(count)
            assert sum(quota.values()) == count
            assert quota["M1"] / count == pytest.approx(0.25, abs=0.09)
            assert quota["M2"] / count == pytest.approx(0.45, abs=0.09)
            assert quota["M3"] / count == pytest.approx(0.30, abs=0.09)

    def test_every_movement_gets_a_shot_once_there_are_three(self):
        assert all(n >= 1 for n in movement_quota(3).values())
        assert sum(movement_quota(1).values()) == 1


class TestIdentityScenes:
    """R4.  The trailer sells the question of who; the answer is the killer
    photographed in the room the detective is searching."""

    def test_the_figure_where_the_lead_stands_is_the_answer(self):
        found = identity_scenes(scarlet(), HOLMES, HOPE)
        assert {11, 18, 19, 20} <= found

    def test_the_figures_own_country_is_not_the_answer(self):
        """Utah is Hope before anyone is looking for him -- it gives nothing
        away and it is most of the second half."""
        found = identity_scenes(scarlet(), HOLMES, HOPE)
        assert found.isdisjoint({12, 13, 14, 15, 16, 17})

    def test_late_floor_is_three_quarters_of_the_shots(self):
        assert late_floor(12) == 9 and late_floor(41) == 30


class TestSelectByMovement:
    """The order IS the list order (`trailer_order.one_each`), so the spine
    lives here or nowhere."""

    @pytest.fixture()
    def chosen(self):
        scenes = scarlet()
        return select_by_movement(scenes, sheets(scenes), 12, {}, HOLMES, HOPE,
                                  banned={20, 21, 22})

    def test_it_returns_what_it_was_asked_for(self, chosen):
        assert len(chosen) == 12

    def test_the_movements_play_in_order(self, chosen):
        bounds = movement_bounds(scarlet(), HOLMES)
        played = [movement_of(c["scene"], bounds) for c in chosen]
        assert played == sorted(played, key=MOVEMENTS.index)
        assert set(played) == set(MOVEMENTS)

    def test_the_story_order_survives_the_cut(self, chosen):
        """R7: run 10's order was a score ranking scattered on the beat grid.
        Kendall tau against (movement, scene) measured 0.4 as the floor."""
        bounds = movement_bounds(scarlet(), HOLMES)
        key = [(MOVEMENTS.index(movement_of(c["scene"], bounds)), c["scene"]) for c in chosen]
        assert kendall_tau(chosen, key) >= 0.4

    def test_the_answer_never_plays_before_three_quarters(self, chosen):
        """Hope handcuffed and Hope writing RACHE are the answer; run 10 put
        them at 8.75 s and 17 s."""
        reveal = identity_scenes(scarlet(), HOLMES, HOPE)
        early = [c["scene"] for c in chosen[:late_floor(len(chosen))]]
        assert not (set(early) & reveal)

    def test_the_climax_still_reaches_the_screen(self, chosen):
        reveal = identity_scenes(scarlet(), HOLMES, HOPE)
        assert set(c["scene"] for c in chosen) & reveal

    def test_a_banned_scene_is_never_photographed(self, chosen):
        """R4's other half: the resolution gives the story away in one frame."""
        assert all(c["scene"] not in {20, 21, 22} for c in chosen)

    def test_the_ranked_selector_would_have_shipped_the_resolution(self):
        """The regression, stated: run 10's B04 and B11 are scene 21, which
        story.json had already listed as restricted."""
        scenes = scarlet()
        ranked = select_setups(scenes, sheets(scenes), 25, {})
        assert any(c["scene"] in {20, 21, 22} for c in ranked)


class TestNoOneOwnsTheTrailer:
    """R10/R6.  Run 10 gave Holmes 26 of 51 shots -- nine of his twelve
    setups the same three-quarter deerstalker face with an orange lamp
    behind -- and spent 39% of its seconds in 221B Baker Street, while Lucy,
    Drebber and Stangerson had ref sheets and were never cast."""

    def chosen(self, count=12):
        scenes = scarlet()
        plates = sheets(scenes) | {f"char-{c}" for c in ("john_ferrier", "g_lestrade",
                                                         "tobias_gregson")}
        return scenes, plates, select_by_movement(scenes, plates, count, {}, HOLMES, HOPE,
                                                  banned={20, 21, 22})

    def test_no_principal_owns_more_than_45_percent_of_the_shots(self):
        scenes, plates, chosen = self.chosen()
        faces = Counter(face_of(c, plates, HOLMES, HOPE) for c in chosen)
        worst = max(n for who, n in faces.items() if who)
        assert worst / len(chosen) <= PRINCIPAL_SHARE

    def test_more_than_one_face_reaches_the_screen(self):
        scenes, plates, chosen = self.chosen()
        faces = {face_of(c, plates, HOLMES, HOPE) for c in chosen}
        assert len(faces - {None}) >= 3

    def test_the_cap_never_reorders_the_movements(self):
        scenes, plates, chosen = self.chosen()
        bounds = movement_bounds(scenes, HOLMES)
        played = [movement_of(c["scene"], bounds) for c in chosen]
        assert played == sorted(played, key=MOVEMENTS.index)

    def test_the_cap_never_moves_the_answer_earlier(self):
        scenes, plates, chosen = self.chosen()
        reveal = identity_scenes(scenes, HOLMES, HOPE)
        early = [c["scene"] for c in chosen[:late_floor(len(chosen))]]
        assert not set(early) & reveal

    def test_at_least_four_places_and_none_owns_the_trailer(self):
        scenes, plates, chosen = self.chosen()
        places = Counter(c["location_id"] for c in chosen)
        assert len(places) >= 4
        assert max(places.values()) / len(chosen) <= PLACE_SHARE + 0.05
