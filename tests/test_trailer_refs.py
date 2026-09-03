

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
