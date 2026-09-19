"""The reference pack: every character, location and prop design becomes jobs."""
from studio.refs_pack import (STYLE_LEAD, T2I, Job, character_jobs, jobs_for,
                              location_jobs, pending, prop_jobs, relpath,
                              seed_for, styled, values_for)

CHARACTER = {
    "physical": "Man of 34, slender, dark brown hair parted on the left.",
    "wardrobe": {"day_suit": "Mid-grey herringbone suit, straw boater.",
                 "storm_soaked": "The grey suit soaked dark, hair plastered flat."},
    "design": {"sheet_prompt": "Man of 34 in a mid-grey suit. Character reference sheet."},
}
LOCATION = {"design": {"views": [
    {"id": "wide_establishing", "prompt": "A sandy heath with a raw pit."},
    {"id": "insert_sand", "prompt": "Yellow sand and grey clinker underfoot."}]}}
PROP = {"design": {"sheet_prompt": "A colossal cylinder on grey.",
                   "views": [{"id": "hero_open", "prompt": "The cylinder lid unscrewed."}]}}


def test_styled_leads_with_the_house_style():
    assert styled("a pit").startswith(STYLE_LEAD)
    assert styled("a pit").endswith("a pit")


def test_seed_is_stable_and_differs_by_key():
    assert seed_for("characters/narrator/sheet") == seed_for("characters/narrator/sheet")
    assert seed_for("characters/narrator/sheet") != seed_for("characters/curate/sheet")


def test_a_character_is_exactly_one_sheet_whatever_its_wardrobe_states():
    jobs = character_jobs("narrator", CHARACTER)
    assert [j.name for j in jobs] == ["sheet"]
    assert "Character reference sheet" in jobs[0].prompt


def test_character_without_design_yields_nothing():
    assert character_jobs("ghost", {"physical": "x"}) == []


def test_character_marked_not_drawn_yields_nothing():
    unseen = {"design": {"sheet_prompt": "x", "render": False}}
    assert character_jobs("god", unseen) == []


def test_a_location_picture_lives_under_its_place():
    jobs = location_jobs("horsell_pit", LOCATION)
    assert relpath(jobs[0]) == "refs/locations/horsell_pit/wide_establishing.png"


def test_a_prop_is_exactly_one_sheet_whatever_its_views():
    jobs = prop_jobs("cylinder", PROP)
    assert [j.name for j in jobs] == ["sheet"]


def test_jobs_for_dispatches_on_kind():
    assert jobs_for("props", "cylinder", PROP) == prop_jobs("cylinder", PROP)
    assert jobs_for("locations", "pit", LOCATION) == location_jobs("pit", LOCATION)


def test_pending_skips_pictures_already_on_disk():
    jobs = location_jobs("horsell_pit", LOCATION) + character_jobs("narrator", CHARACTER)
    done = {"refs/locations/horsell_pit/wide_establishing.png"}
    assert [j.name for j in pending(jobs, done.__contains__)] == ["sheet"]


def test_values_for_fill_the_manifest_names():
    job = Job("locations", "pit", "wide", "image_krea2_cinematic_2x", "a pit", 1536, 1024)
    values = values_for(job)
    assert set(values) == {"prompt", "width", "height", "seed", "filename_prefix"}
    assert values["prompt"].startswith(STYLE_LEAD)


ROOM = {"design": {"views": [
    {"id": "reverse", "prompt": "The door wall."},
    {"id": "wide_establishing", "prompt": "The whole round room."},
    {"id": "medium_table", "prompt": "The little table."}]}}


def test_a_location_is_exactly_one_picture_its_establishing_wide():
    jobs = location_jobs("observatory", ROOM)
    assert [(j.name, j.workflow) for j in jobs] == [("wide_establishing", T2I)]


def test_a_location_without_a_named_wide_uses_its_first_view():
    first_only = {"design": {"views": [{"id": "medium_bar", "prompt": "The bar."}]}}
    assert [j.name for j in location_jobs("inn", first_only)] == ["medium_bar"]
