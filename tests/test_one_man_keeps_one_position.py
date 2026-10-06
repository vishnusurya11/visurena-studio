"""G-TWICE (2026-10-05): one faces member given two different world anchors
inside ONE drawn surface is drawn twice.  A surface is frame+at_rest, or end
alone, or one cut's pair; at_rest is NEVER compared against end, because
motion legitimately moves a person between those two drawn pictures."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from studio import plan_gates as pg

FIXTURE = Path(__file__).parent / "fixtures" / "episodes" / "ghost_twice_shots.json"


def load():
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    shots = [SimpleNamespace(**{**s, "cuts": [SimpleNamespace(**c) for c in s.get("cuts", [])]})
             for s in doc["shots"]]
    return SimpleNamespace(shots=shots), pg.names_from_refs(doc["refs"])


def one(index, **over):
    base = dict(index=index, faces=["captain", "curate"], cuts=[], frame="", at_rest="",
                end="", motion="", camera="")
    base.update(over)
    return SimpleNamespace(shots=[SimpleNamespace(**base)])


def test_scullery_and_kitchen_door_in_one_surface_is_one_fault():
    episode, names = load()
    probe = SimpleNamespace(shots=[s for s in episode.shots if s.index == 20])
    found = pg.double_position_faults(probe, names)
    assert len(found) == 1
    assert "G-TWICE shot 20" in found[0]
    assert "'scullery'" in found[0] and "'kitchen'" in found[0] and "curate" in found[0]


def test_at_rest_against_end_is_never_compared():
    _, names = load()
    probe = one(1, faces=["captain"], at_rest="The captain stands at the window.",
                end="The captain waits at the door.")
    assert pg.double_position_faults(probe, names) == []


def test_a_screen_space_anchor_places_nobody():
    _, names = load()
    probe = one(2, faces=["captain"],
                at_rest="The captain stands at the LEFT frame edge; the captain turns at the kitchen door.")
    assert pg.double_position_faults(probe, names) == []


def test_door_and_doorway_never_conflict():
    _, names = load()
    probe = one(3, faces=["captain"],
                at_rest="The captain stands at the door; the captain leans by the doorway.")
    assert pg.double_position_faults(probe, names) == []


def test_a_cut_surface_fires_independently_of_its_parent():
    _, names = load()
    cut = SimpleNamespace(at_s=2.0, faces=[],
                          frame="The curate kneels at the hearth.",
                          at_rest="The curate leans against the window.", end="")
    probe = one(4, frame="Medium on the captain at the gate.", at_rest="", cuts=[cut])
    found = pg.double_position_faults(probe, names)
    assert len(found) == 1
    assert "cut@2.0" in found[0] and "'hearth'" in found[0] and "'window'" in found[0]


def test_the_whole_fixture_yields_exactly_the_one_twice_fault():
    episode, names = load()
    found = pg.double_position_faults(episode, names)
    assert len(found) == 1 and "shot 20" in found[0]


def test_anchors_of_skips_cast_pronoun_and_body_words():
    names = {"captain": "captain", "curate": "curate"}
    assert pg.anchors_of("he waits behind the captain near the gate", names) == "gate"
    assert pg.anchors_of("one step behind his LEFT side", names) == ""
    assert pg.anchors_of("a hand on the curate's shoulder", names) == ""
