"""Step 03 drew a place master from the setup's own words and nothing else, so a setup that
names lettering bait drew lettering into the master: Jekyll ep05's by-street "newspaper bills"
came out as posters, and every grid cell and take of that place inherits the picture.  A take
already carries `unlettered_for` (Jekyll ep01 iter4 "FILED" on the cheque); the master did not.

The master's prompt now carries the same affirmative sentence whenever its words hold a bait
noun (prompt_lint.BAIT), and is unchanged otherwise -- no master already on disk is redrawn."""
from __future__ import annotations

from scripts.refs import places

STREET = "A narrow London by-street at night; a hoarding pasted with newspaper bills by the door."
ROOM = "A surgical theatre under a dusty skylight, benches in a ring."


def test_a_master_naming_a_newspaper_is_told_it_is_unlettered():
    got = places.master_prompt(STREET, "")
    assert got.startswith(STREET)
    assert got.endswith("Every sign, plate, newspaper and paper in the picture is plain and unlettered.")


def test_a_master_with_no_bait_is_drawn_from_its_words_alone():
    assert places.master_prompt(ROOM, "") == ROOM


def test_the_look_still_follows_the_words():
    got = places.master_prompt(STREET, "gothic anime")
    assert got.index("gothic anime") < got.index("unlettered")


def test_draw_missing_draws_the_master_prompt(tmp_path, monkeypatch):
    from types import SimpleNamespace
    drawn = []
    monkeypatch.setattr(places, "status", lambda book, setups: [("street", "lane", "wide", "missing")])
    monkeypatch.setattr(places, "record_master", lambda book, loc, view: None)
    places.draw_missing(tmp_path, {"street": SimpleNamespace(described=STREET)}, lambda p, t: drawn.append(p))
    assert drawn == [places.master_prompt(STREET, "")]
