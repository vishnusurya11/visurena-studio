"""A place is its masters.  A state variant is ONE edit of a master (never of
another variant); a derived side names a fresh master of the same place; a
location id belongs to exactly one place (WotW: one dining room under two ids
was two rooms)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio.continuity_spec import Place, PlaceBook


def villa(**over) -> dict:
    doc = {"name": "The narrator's villa",
           "members": ["narrators_home", "narrators_study", "narrators_dining_room"],
           "masters": [{"master_id": "front", "location": "narrators_home", "view": "wide_establishing",
                        "sha8": "7972962f"},
                       {"master_id": "study", "location": "narrators_study", "view": "wide_establishing",
                        "sha8": "13c8eea6"}],
           "states": [{"state_id": "abandoned", "start": {"chapter": 26}, "until": {"chapter": 26},
                       "deltas": ["the front door stands forced open on its hinge"]}],
           "variants": [{"master_id": "front", "state_id": "abandoned",
                         "view": "wide_establishing__abandoned", "parent_sha8": "7972962f"}]}
    doc.update(over)
    return doc


def test_a_variant_of_its_master_is_accepted():
    assert Place.model_validate(villa()).variants[0].parent_sha8 == "7972962f"


def test_a_variant_of_a_variant_is_refused():
    bad = villa()
    bad["variants"][0]["parent_sha8"] = "deadbeef"
    with pytest.raises(ValidationError, match="one hop"):
        Place.model_validate(bad)


def test_a_master_outside_the_members_is_refused():
    bad = villa()
    bad["masters"][0]["location"] = "maybury_hill"
    with pytest.raises(ValidationError, match="member"):
        Place.model_validate(bad)


def test_a_derived_side_must_name_a_fresh_master_of_the_place():
    bad = villa()
    bad["masters"].append({"master_id": "rev", "location": "narrators_study", "view": "reverse",
                           "derived_from": "study_rev2", "made_by": "edit"})
    with pytest.raises(ValidationError, match="derived"):
        Place.model_validate(bad)


def test_a_side_derived_from_a_derived_side_is_refused():
    bad = villa()
    bad["masters"] += [{"master_id": "rev", "location": "narrators_study", "view": "reverse",
                        "derived_from": "study", "made_by": "edit"},
                       {"master_id": "rev2", "location": "narrators_study", "view": "reverse2",
                        "derived_from": "rev", "made_by": "edit"}]
    with pytest.raises(ValidationError, match="chain"):
        Place.model_validate(bad)


def test_a_variant_naming_an_unknown_state_is_refused():
    bad = villa()
    bad["variants"][0]["state_id"] = "on_fire"
    with pytest.raises(ValidationError, match="state"):
        Place.model_validate(bad)


def test_a_location_in_two_places_is_refused():
    other = {"name": "Maybury", "members": ["maybury_hill", "narrators_home"], "masters": []}
    with pytest.raises(ValidationError, match="one place"):
        PlaceBook.model_validate({"places": {"villa": villa(), "hill": other}})


def test_the_book_finds_a_locations_place_and_its_state():
    book = PlaceBook.model_validate({"places": {"villa": villa()}})
    assert book.place_of("narrators_dining_room") == "villa"
    assert book.place_of("horsell_common") == ""
    assert book.places["villa"].state_at(26) == "abandoned"
    assert book.places["villa"].state_at(25) == ""
