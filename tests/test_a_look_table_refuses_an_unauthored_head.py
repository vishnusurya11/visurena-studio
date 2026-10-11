"""The look table refuses a bound character whose head is unauthored (C1_verdict #9).

MEASURED on Jekyll and Hyde (C1_L §3): their dossiers' `physical` names no hair,
beard, age or hat, so every head layer of every look is empty and every marker is
blank -- and LOOK-STATE, comparing blank markers, passes anything: a judge that
reads nothing (the 'unread' lesson again). A NEWLY written table refuses such a
character with a 'head unauthored' reason; existing looks.json files are never
re-judged. The replay over every WotW and Scarlet character with a look table
must refuse nobody, or this would park the series.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.refs import looks_table
from studio import look_timeline
from studio.continuity_spec import CharacterLooks, Layers, Look, Markers

ROOT = Path(__file__).resolve().parents[1]
BOOKS = [ROOT / "library" / "20260827135508_the-war-of-the-worlds", ROOT / "library" / "20260822113400_a-study-in-scarlet"]


def looks(**head) -> CharacterLooks:
    base = Look(made_by="base", layers=Layers(top="Black frock coat.", **head), markers=Markers(top="coat"))
    return CharacterLooks(base="frock", body="A man of fifty.", looks={"frock": base})


def test_a_jekyll_shaped_dossier_is_refused_head_unauthored():
    why = look_timeline.head_refusal("henry_jekyll", looks())
    assert why and "head unauthored" in why and "henry_jekyll" in why


def test_any_head_layer_authors_the_head():
    assert look_timeline.head_refusal("utterson", looks(hair="Iron-grey hair.")) is None
    assert look_timeline.head_refusal("utterson", looks(headwear="Black top hat.")) is None


def test_build_refuses_before_it_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(looks_table, "table_for", lambda book, who, _agent=None: looks())
    with pytest.raises(SystemExit, match="head unauthored"):
        looks_table.build(tmp_path, ["henry_jekyll"])
    assert not look_timeline.path_of(tmp_path).exists()


@pytest.mark.skipif(not all(b.exists() for b in BOOKS), reason="the library is not on disk")
def test_no_wotw_or_scarlet_character_with_a_look_table_is_refused():
    from scripts.refs.continuity_replay import table_of
    refused = [why for book in BOOKS for who, card in table_of(book).characters.items()
               if (why := look_timeline.head_refusal(who, card))]
    assert refused == []
