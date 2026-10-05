"""ep17 (owner 2026-10-04: "dont say martian .. always define the characters in
detail").  Grid steamer a said "In it: a martians wearing bare oily brown-grey
skin glistening like wet leather, saliva dripping from the v-shaped mouth" --
three fragments of a creature cut from its row -- and the drawer drew a naked
humanoid on the deck.  A face with no sheet staged is said by its WHOLE row
description, body first, in plain lower-case words.  $0: pure text."""
from __future__ import annotations

from studio.storyboard_grid import called

MARTIAN = ("A rounded grey-brown bulk the size of a bear and four feet across, whose whole body "
           "is one huge head. Oily grey-brown skin, fungoid, glistening like wet leather. "
           "Sixteen thin whip-like tentacles hang in two bunches beneath the mouth.")


def test_an_unsheeted_creature_carries_its_whole_body():
    say = called([{"name": "MARTIANS", "ref": None, "wear": MARTIAN}])["MARTIANS"]
    assert "the size of a bear" in say and "whole body is one huge head" in say
    assert "sixteen thin whip-like tentacles" in say
    assert say == say.lower()


def test_an_unsheeted_person_keeps_every_worn_item():
    wear = "Woman of 41. Wearing: White muslin dress. Wide white straw hat. White kid gloves. Grey parasol."
    say = called([{"name": "Mrs. Elphinstone", "ref": None, "wear": wear}])["Mrs. Elphinstone"]
    assert "grey parasol" in say and "woman of 41" in say
