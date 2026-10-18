"""Jekyll 2026-10-18: Enfield wears black gloves on his signed Kawajiri sheet, and the
Sherlock-era wall on 'glove' refused every shot that said so.  The wall now reads the
cast: a glove is refused unless a person staged in that shot has a row bearing it.
$0: pure membership tests."""
from __future__ import annotations

from types import SimpleNamespace as NS

from studio.episode_spec import Shot, SubShot
from studio.plan_gates import banned_prop_faults

ENFIELD = {"entity_id": "enfield", "kind": "character", "physical": "black gloves, grey coat"}
UTTERSON = {"entity_id": "utterson", "kind": "character", "physical": "bare hands, black coat"}


def shot(faces, frame="a hand in a black glove on the rail", cuts=()):
    return Shot(index=3, section="friction", setup="lab", size="insert", frame=frame,
                motion="m", faces=faces, cuts=list(cuts))


def faults(s, refs):
    return banned_prop_faults(NS(shots=[s]), refs)


def test_a_staged_wearer_makes_the_glove_legal():
    assert faults(shot(["enfield"]), [ENFIELD, UTTERSON]) == []


def test_no_wearer_staged_keeps_the_ban():
    assert faults(shot(["utterson"]), [ENFIELD, UTTERSON])


def test_a_book_whose_rows_have_no_gloves_keeps_the_old_wall():
    assert faults(shot(["utterson"]), [UTTERSON])
    assert faults(shot([]), [])


def test_a_cut_is_checked_too():
    cut = SubShot(at_s=3.0, size="close", frame="a gloved hand", motion="m")
    s = shot(["utterson"], frame="f", cuts=[cut])
    assert faults(s, [ENFIELD, UTTERSON])
    assert faults(shot(["enfield"], frame="f", cuts=[cut]), [ENFIELD, UTTERSON]) == []
