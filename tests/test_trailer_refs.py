

class TestEveryPlaceTheBookGoes:
    """Locations were drawn from a SAMPLE of twelve scenes and capped at eight.

    A Study in Scarlet has thirteen locations and got six plates.  Selection
    then deleted every setup in the other seven -- 141 of 411, including all of
    Utah: Lucy, the farm, the Danite riders, the alkali plain.  The one
    geographic contrast the book offers was unreachable, and no score could
    rescue it, because a place with no plate cannot be bound.

    The same sampling bug already cost this pipeline its Jekyll sheet.  A book
    has a finite number of places; plate all of them.
    """

    def test_it_returns_every_location_in_the_screenplay(self):
        from studio.trailer_refs import all_locations
        scenes = [{"slug": {"location_id": "a"}}, {"slug": {"location_id": "b"}},
                  {"slug": {"location_id": "a"}}, {"slug": {"location_id": "c"}}]
        assert set(all_locations(scenes)) == {"a", "b", "c"}

    def test_it_keeps_first_appearance_order(self):
        from studio.trailer_refs import all_locations
        scenes = [{"slug": {"location_id": "z"}}, {"slug": {"location_id": "a"}}]
        assert all_locations(scenes) == ["z", "a"]

    def test_a_scene_with_no_location_is_skipped_not_crashed_on(self):
        from studio.trailer_refs import all_locations
        assert all_locations([{"slug": {}}, {"slug": {"location_id": "a"}}]) == ["a"]

    def test_the_real_book_needs_thirteen_plates_not_eight(self):
        import json
        from pathlib import Path
        from studio.trailer_refs import all_locations
        scenes = json.loads(
            (Path("library/20260822113400_a-study-in-scarlet")
             / "screenplay/feature/screenplay.json").read_text(encoding="utf-8"))["scenes"]
        assert len(all_locations(scenes)) == 13


class TestPaletteFor:
    def test_every_register_has_a_grade_line(self):
        from studio.trailer_refs import PALETTES, palette_for
        from studio.trailer_stage_spec import Register
        assert set(Register.__args__) == set(PALETTES)
        assert palette_for("gothic", "1890 Transylvania").endswith("light sources.")

    def test_the_setting_rides_inside_the_line(self):
        from studio.trailer_refs import palette_for
        assert "1881 London" in palette_for("detective", "1881 London")
        assert palette_for("nonsense") == palette_for("procedural")


def test_a_contract_is_never_silently_cut_short():
    """MEASURED 2026-09-11: Watson's description ran 607 characters and the 220-char
    limit kept its first sentence and dropped the rest WITHOUT SAYING SO, so the
    walking stick's length never reached any drawer and 23 panels each invented one.
    A contract is complete or it is a lie, so `contract_description` has no limit."""
    from studio.trailer_refs import contract_description, dropped_by_limit
    long = ("A man in his late twenties, as thin as a lath, dark hair swept back, a brown tweed "
            "overcoat over a tweed waistcoat with a watch chain and a white cravat pinned with a "
            "stud, both hands bare and sunburnt. The stick stands hip high and its shaft is as "
            "thick as one finger. His boots are black and square-toed.")
    whole = contract_description(long)
    assert "hip high" in whole and "square-toed" in whole
    assert dropped_by_limit(long) and not dropped_by_limit("A short man in a grey coat.")
