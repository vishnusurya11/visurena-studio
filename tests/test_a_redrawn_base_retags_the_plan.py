"""A redrawn base sheet re-tags the plans written before it (Jekyll ep05 repair, 2026-10-28).

Jekyll was redrawn (grey -> black hair, black -> bottle-green frock coat, G-ALIKE) and ep05's plan
still said "the doctor (thick iron-grey hair, long black frock coat)". `cast_alias.owner_of` binds
a tag by its fragments; none was in the new row, so "the doctor" bound nobody and step 06 refused
all ten Jekyll takes (P13 unstaged person: doctor; P4 Subject never cited).

Each stale fragment is replaced by the SAME clause of the SAME layer in the new look: the first
clause of the old hair layer becomes the first clause of the new one."""
from __future__ import annotations

from studio import relook

OLD = {"hair": "thick iron-grey hair, silver-grey at the temples and sides, brushed back from a high forehead",
       "top": "long black frock coat, black waistcoat, white shirt, black tie", "headwear": "tall black silk top hat"}
NEW = {"hair": "thick black hair, silver-grey only at the temples, brushed back from a high forehead",
       "top": "long deep bottle-green frock coat, dark green waistcoat, white shirt, black tie",
       "headwear": "tall black silk top hat"}


def HIS(frags):
    return any("iron-grey" in f or "frock coat" in f for f in frags)


def test_another_persons_tag_is_never_reworded():
    doc = {"shots": [{"frame": "the butler (black waistcoat, white shirt) at the door"}]}
    assert relook.retag(doc, OLD, NEW, HIS) == doc


def test_a_fragment_maps_to_the_same_clause_of_its_layer():
    assert relook.mapping(OLD, NEW) == {"thick iron-grey hair": "thick black hair",
                                        "silver-grey at the temples and sides": "silver-grey only at the temples",
                                        "long black frock coat": "long deep bottle-green frock coat",
                                        "black waistcoat": "dark green waistcoat"}


def test_the_plans_tags_take_the_new_words():
    doc = {"shots": [{"frame": "Medium over the doctor's shoulder (long black frock coat, thick iron-grey hair) "
                                "toward the lawyer (lank grey hair)."}],
           "setups": {"a": {"described": "the doctor (thick iron-grey hair, long black frock coat) by the fire"}}}
    got = relook.retag(doc, OLD, NEW, HIS)
    assert got["shots"][0]["frame"].startswith(
        "Medium over the doctor's shoulder (long deep bottle-green frock coat, thick black hair) toward")
    assert "(thick black hair, long deep bottle-green frock coat)" in got["setups"]["a"]["described"]
    assert "lank grey hair" in got["shots"][0]["frame"]


def test_words_outside_a_tag_are_left_alone():
    doc = {"lines": [{"text": "His iron-grey hair, Utterson thought."}]}
    assert relook.retag(doc, OLD, NEW, HIS) == doc
