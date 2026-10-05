"""ep16 (2026-10-01): the grass-lane grid said only "a mrs. elphinstone" -- no
sheet staged, no wardrobe words -- and the drawer invented her in the dominant
purple, a Miss clone; and "three robbers" drew as brown-suit copies of the
brother because the attacker nouns were outside PEOPLE, so the working-city
strangers block never fired.  A face with no sheet now carries its row's worn
items in plain lower-case words, and robbers/attackers count as people."""
from __future__ import annotations

from studio.storyboard_grid import called
from studio.episode_seq_board import people


def test_an_unsheeted_face_carries_its_worn_items():
    cast = [{"name": "Mrs. Elphinstone", "ref": None,
             "wear": "Wearing: White muslin dress. Wide white straw hat. White kid gloves."},
            {"name": "the brother", "ref": 1, "wear": "Wearing: Brown Norfolk jacket."}]
    say = called(cast)
    assert say["the brother"] == "the person in <image1>"
    assert say["Mrs. Elphinstone"].startswith("a mrs. elphinstone (")
    assert "white muslin dress" in say["Mrs. Elphinstone"]
    assert say["Mrs. Elphinstone"] == say["Mrs. Elphinstone"].lower()   # the drawer letters capitals


def test_a_bare_unsheeted_face_stays_bare():
    assert called([{"name": "the gardener", "ref": None}])["the gardener"] == "a the gardener".replace("a the", "a the")  # no wear key: unchanged shape
    assert called([{"name": "gardener", "ref": None}])["gardener"] == "a gardener"


def test_attackers_are_people():
    assert people("three robbers press around the vehicle")
    assert people("two attackers grip the rail")
