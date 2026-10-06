"""G-GHOST (2026-10-05): H3 draws every person the text asserts, so a
possessive body part belonging to a cast member who is not in the shot's
faces ("over the brother's shoulder") is drawn as a second whole man.  The
gate reads the plan's own fields against a refs-derived unique-token table;
a face's own shoulder is legal, and an unresolvable possessive (the boat's
gunwale, the frame's height) is nobody's."""
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


def shot(episode, index):
    return SimpleNamespace(shots=[s for s in episode.shots if s.index == index])


def test_a_brothers_shoulder_with_no_brother_in_faces_is_one_ghost():
    episode, names = load()
    found = pg.ghost_limb_faults(shot(episode, 11), names)
    assert len(found) == 1
    assert "G-GHOST shot 11" in found[0]
    assert "frame" in found[0] and "brother" in found[0]


def test_a_trailing_curate_shoulder_clause_is_a_ghost():
    episode, names = load()
    found = pg.ghost_limb_faults(shot(episode, 15), names)
    assert len(found) == 1
    assert "at_rest" in found[0] and "curate" in found[0]


def test_a_faces_members_own_hand_is_clean():
    episode, names = load()
    assert pg.ghost_limb_faults(shot(episode, 0), names) == []


def test_an_unresolvable_possessive_is_nobodys():
    episode, names = load()
    assert pg.ghost_limb_faults(shot(episode, 2), names) == []


def test_a_cut_reads_its_own_faces_on_top_of_the_shots():
    cut = SimpleNamespace(at_s=2.0, faces=["curate"], frame="Close on the curate's hand at the latch.",
                          at_rest="", end="", motion="", camera="")
    s = SimpleNamespace(index=4, faces=["captain"], cuts=[cut], frame="Medium on the captain.",
                        at_rest="", end="", motion="", camera="")
    _, names = load()
    assert pg.ghost_limb_faults(SimpleNamespace(shots=[s]), names) == []


def test_names_from_refs_drops_a_token_two_entities_share():
    _, names = load()
    assert "dale" not in names                       # both Dale sisters claim it
    assert names.get("ann") == "ann_dale" and names.get("bess") == "bess_dale"
    assert names.get("curate") == "curate"


def test_ghost_hits_resolve_only_cast_owners():
    names = {"curate": "curate"}
    assert pg.ghost_hits("the boat's gunwale; the curate's shoulder", names) == \
        [("curate", "shoulder", "curate")]
    assert pg.ghost_hits("the curate’s shoulder", names) == [("curate", "shoulder", "curate")]
