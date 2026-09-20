"""A setup-level prop reaches only the takes whose own prose names it.

MEASURED on WotW ep05 (2026-09-20).  `Setup.props` names the props of a PLACE,
and the take builder staged every one of them -- sheet and definition sentence
-- on every take of that setup.  Chapter 5's one prop card carries the Martian
mast AND the humped dome that rises at the killing, so the dome was in the
words from shot zero and H3 drew it sitting at the mast's foot in the sunset
shots, twenty shots early.  Every one of those takes scored PASS.

The same shape reaches every later episode: the cylinder, the fighting-machine
and the heat-ray are all setup props of places the story visits before those
things arrive.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import pack_refs

CARD = {
    "id": "pit_mast_mirror",
    "name": "the mast and wobbling mirror over the Horsell pit",
    "aliases": ["thin mast", "restless mirror", "thin rod with a disk", "humped shape", "black dome"],
    "profile": {"physical": "A thin jointed metal rod rising out of the sand-pit.",
                "scale": "The mast stands about three times a man's height above the pit rim."},
}


class Shot:
    def __init__(self, frame="", motion="", at_rest=""):
        self.frame, self.motion, self.at_rest = frame, motion, at_rest


def book_with_prop(tmp_path: Path) -> Path:
    (tmp_path / "analysis" / "props").mkdir(parents=True)
    (tmp_path / "analysis" / "props" / "pit_mast_mirror.json").write_text(
        json.dumps(CARD), encoding="utf-8")
    sheet = tmp_path / "refs" / "props" / "pit_mast_mirror"
    sheet.mkdir(parents=True)
    (sheet / "sheet.png").write_bytes(b"png")
    return tmp_path


def test_the_head_noun_of_each_alias_is_the_term(tmp_path):
    """The card says "thin mast" and the plan says "the thin jointed mast", so
    the whole alias matches nothing and the head noun matches what is meant."""
    assert pack_refs.prop_terms(book_with_prop(tmp_path), "pit_mast_mirror") == \
        ["disk", "dome", "mast", "mirror"]


def test_a_generic_alias_head_identifies_nothing(tmp_path):
    """"humped shape" contributes no term: a take that says "the shape of the
    heather" is not naming a Martian machine."""
    assert "shape" not in pack_refs.prop_terms(book_with_prop(tmp_path), "pit_mast_mirror")


def test_a_shot_that_never_names_the_prop_does_not_stage_it(tmp_path):
    """ep05 shot 0, the hook: a man standing knee-deep in the heather at sunset,
    three shots before the mast comes up."""
    book = book_with_prop(tmp_path)
    shots = [Shot(frame="Wide of Horsell Common with the sun going down: the Narrator standing "
                        "knee-deep in the purple-brown heather",
                  motion="The camera tracks sideways to the right past a black furze bush",
                  at_rest="The low raw ring of flung yellow sand crosses the CENTRE RIGHT")]
    assert pack_refs.props_named(book, ["pit_mast_mirror"], pack_refs.shot_prose(shots)) == []


def test_a_shot_that_names_the_prop_stages_it(tmp_path):
    """ep05 shot 3: the rod comes up, joint by joint, and the mirror turns."""
    book = book_with_prop(tmp_path)
    shots = [Shot(frame="Medium on the raw yellow sand heaps: the first joint of the thin jointed "
                        "mast standing a hand's height clear of the rim",
                  motion="The camera tilts up to the top of the mast",
                  at_rest="the folded disk against it")]
    got = pack_refs.props_named(book, ["pit_mast_mirror"], pack_refs.shot_prose(shots))
    assert [name for _, (name, _) in got] == ["the mast and wobbling mirror over the Horsell pit"]


def test_the_declared_list_still_gates(tmp_path):
    """The filter can only ever REMOVE: a prop the setup does not declare is
    never staged, however loudly the prose names it."""
    book = book_with_prop(tmp_path)
    shots = [Shot(frame="the thin jointed mast and its mirror and the black dome")]
    assert pack_refs.props_named(book, [], pack_refs.shot_prose(shots)) == []


def test_the_plural_is_the_same_noun(tmp_path):
    book = book_with_prop(tmp_path)
    shots = [Shot(frame="two thin masts stand over the sand")]
    assert len(pack_refs.props_named(book, ["pit_mast_mirror"], pack_refs.shot_prose(shots))) == 1
