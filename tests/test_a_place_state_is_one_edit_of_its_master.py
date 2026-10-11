"""Step 03_05: a setup's place STATE is one 2511 edit of the picture its view
names (never of another variant, never a fresh room); a first view of a
location is drawn once and recorded as its master; the variant is flagged,
never refused, when it leaves the same-place band (uncalibrated)."""
from __future__ import annotations

from types import SimpleNamespace

from studio.continuity_spec import PlaceBook
from tests import continuity_fixtures as fx
from tests.test_a_place_is_its_master import book

from scripts.refs import places


def setups(**kw):
    return {"front": SimpleNamespace(location="narrators_home", view="", place_state="forced door, dust",
                                     described="The villa.", **kw)}


def test_a_state_is_due_as_a_variant_of_the_setups_picture(tmp_path):
    b = book(tmp_path)
    due = places.states_due(b, setups())
    assert due == [("front", "narrators_home", "wide_establishing", "wide_establishing__forced_door_dust")]


def test_the_variant_edits_the_master_once_and_is_recorded_one_hop(tmp_path):
    b, calls = book(tmp_path), []

    def edit(prompt, source, target):
        calls.append((prompt, source.name))
        target.write_bytes(fx.PNG)
    made = places.derive_missing(b, setups(), edit, number=26)
    assert [p.name for p in made] == ["wide_establishing__forced_door_dust.png"]
    assert calls[0][1] == "wide_establishing.png" and "Change only: forced door, dust" in calls[0][0]
    book_ = PlaceBook.model_validate_json((b / "refs" / "places.json").read_text(encoding="utf-8"))
    place = book_.places[book_.place_of("narrators_home")]
    master = next(m for m in place.masters if m.location == "narrators_home")
    assert place.variants[0].parent_sha8 == master.sha8 != ""
    assert places.derive_missing(b, setups(), edit, number=26) == [] and len(calls) == 1


def test_the_plan_names_the_variant_once_it_is_drawn(tmp_path):
    b = book(tmp_path)
    (b / "refs" / "locations" / "narrators_home" / "wide_establishing__forced_door_dust.png").write_bytes(fx.PNG)
    doc = {"setups": {"front": {"location": "narrators_home", "view": "", "place_state": "forced door, dust"}}}
    cured, changed = places.resolve_states(doc, b)
    assert cured["setups"]["front"]["view"] == "wide_establishing__forced_door_dust" and changed == ["front"]


def test_a_first_draw_is_recorded_as_the_locations_master(tmp_path):
    b = book(tmp_path)
    room = b / "refs" / "locations" / "narrators_dining_room"
    room.mkdir(parents=True)
    for view in ("medium_french_window", "second_view"):
        (room / f"{view}.png").write_bytes(fx.PNG)
    places.record_master(b, "narrators_dining_room", "medium_french_window")
    places.record_master(b, "narrators_dining_room", "second_view")
    pb = PlaceBook.model_validate_json((b / "refs" / "places.json").read_text(encoding="utf-8"))
    masters = [m for p in pb.places.values() for m in p.masters if m.location == "narrators_dining_room"]
    assert [m.view for m in masters] == ["medium_french_window", "second_view"]


def test_a_variant_outside_the_same_place_band_is_flagged_not_refused(tmp_path):
    embed = {"m.png": [1.0, 0.0], "near.png": [0.95, 0.1], "far.png": [0.1, 1.0]}.get
    assert places.same_place_flag(tmp_path / "m.png", tmp_path / "near.png", lambda p: embed(p.name)) == ""
    assert "band" in places.same_place_flag(tmp_path / "m.png", tmp_path / "far.png", lambda p: embed(p.name))
