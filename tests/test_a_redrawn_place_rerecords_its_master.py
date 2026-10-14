"""A redrawn place master re-records its sha8, and a re-derived state replaces its variant row.

Jekyll's switch to Hellsing (owner 2026-10-13): the photoreal masters ep01 uses are
superseded and drawn again through `places.py --draw`.  `record_master` kept the old
sha8 of a master id it already held, so every variant edited from the new picture
would name a parent that no longer exists, and `record_variant` appended a second
row for the same view.
"""
from __future__ import annotations

from types import SimpleNamespace

from PIL import Image

from scripts.refs import places
from studio.continuity_spec import PlaceBook
from tests.test_a_place_is_its_master import book


def png(path, shade):
    Image.new("RGB", (8, 8), (shade, shade, shade)).save(path)


def masters_and_variants(b):
    pb = PlaceBook.model_validate_json((b / "refs" / "places.json").read_text(encoding="utf-8"))
    place = pb.places[pb.place_of("narrators_home")]
    return place.masters, place.variants


def test_a_redrawn_master_takes_its_new_sha8(tmp_path):
    b = book(tmp_path)
    pic = places.picture(b, "narrators_home", "wide_establishing")
    png(pic, 10)
    places.record_master(b, "narrators_home", "wide_establishing")
    png(pic, 200)
    places.record_master(b, "narrators_home", "wide_establishing")
    masters, _ = masters_and_variants(b)
    mine = [m for m in masters if m.master_id == "narrators_home/wide_establishing"]
    assert len(mine) == 1 and mine[0].sha8 == places.sha8(pic)


def test_a_rederived_state_replaces_its_variant_row(tmp_path):
    b = book(tmp_path)
    setups = {"front": SimpleNamespace(location="narrators_home", view="", place_state="forced door, dust",
                                       described="The villa.")}
    edit = lambda prompt, source, target: png(target, 50)
    places.derive_missing(b, setups, edit, number=1)
    places.picture(b, "narrators_home", "wide_establishing__forced_door_dust").unlink()
    png(places.picture(b, "narrators_home", "wide_establishing"), 120)
    places.derive_missing(b, setups, edit, number=1)
    masters, variants = masters_and_variants(b)
    master = next(m for m in masters if m.master_id == "narrators_home/wide_establishing")
    assert len(variants) == 1 and variants[0].parent_sha8 == master.sha8
