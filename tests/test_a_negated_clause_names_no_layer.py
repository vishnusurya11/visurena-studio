"""C3_verdict #8: a dossier says what it doesn't say.

117 of 281 dossier physicals across 29 books carry a negated list -- "The
dossier gives no height, build, hair, eye colour, age, or detailed clothing."
The clause splitter cut "hair" out of that list as its own clause and the
look table read it as the HAIR layer, so the row fallback (C2_verdict #6)
never fired for Watson, Lestrade, Utterson or Van Helsing.  A negation scopes
its sentence's comma list (until a ';'): the clauses under it name no head
layer.  Real colour in another clause or sentence stands."""
from __future__ import annotations

import pytest

from studio import look_table as lt, look_timeline

NEGATED = {
    "watson": "The dossier gives no height, build, hair, eye colour, age, or detailed clothing.",
    "lestrade": "The dossier provides no description of Lestrade's age, build, face, hair, clothing, "
                "or distinguishing physical features.",
    "utterson": "It gives no confirmed description of his height, build, age, hair, face, or clothing.",
    "van_helsing": "The dossier gives no direct description of Van Helsing's height, build, age, hair, face, "
                   "or ordinary clothing.",
}
ROW = "A man in his late twenties, thin, dark hair swept back, a thin waxed moustache, a tweed waistcoat."


@pytest.mark.parametrize("who", sorted(NEGATED))
def test_a_negated_list_names_no_head_layer(who):
    physical = "A professional man of the city. " + NEGATED[who]
    assert lt.layer_text(physical, "", "hair") == ""
    assert lt.layer_text(physical, "", "face") == ""
    markers = look_timeline.markers_from(look_timeline.Layers(), physical, fallback=ROW)
    assert markers.hair_colour == "dark"                       # the bound row's head now reaches the table


def test_a_real_colour_in_another_sentence_or_clause_stands():
    physical = "Grey hair cut short; a heavy walrus moustache. The text gives no eye colour or hair length."
    assert lt.first_of(lt.HAIR, lt.layer_text(physical, "", "hair")) == "grey"
    assert lt.first_of(lt.FACIAL, lt.layer_text(physical, "", "face")) == "moustache"


def test_a_semicolon_ends_the_negation():
    physical = "He wears no hat; thick black hair, worn long."
    assert lt.first_of(lt.HAIR, lt.layer_text(physical, "", "hair")) == "dark"
    assert lt.layer_text(physical, "", "headwear") == ""


def test_no_beard_is_not_a_beard():
    assert lt.first_of(lt.FACIAL, lt.layer_text("Brown hair, no beard.", "", "face")) == ""


def test_a_headless_dossier_is_still_refused():
    from studio.continuity_spec import CharacterLooks, Layers, Look, Markers
    look = Look(made_by="base", layers=Layers(top="Black frock coat."), markers=Markers(top="coat"))
    assert "head unauthored" in look_timeline.head_refusal(
        "henry_jekyll", CharacterLooks(base="frock", body=NEGATED["utterson"], looks={"frock": look}))
