"""G-PHANTOM (ep18, 2026-10-05): a setup's `described`/`geometry` text is pasted
verbatim into every grid cell and every take prompt of the setup, so a person or
creature named there is DRAWN into every take as a phantom extra.  'The narrator
and the curate approach along the dusted roadway' put both men into frames the
shots never staged them in.  Pure functions, no I/O, no API, $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_gates as pg

ROWS = [
    {"kind": "character", "entity_id": "unnamed_first_person_narrator",
     "name": "Unnamed first-person narrator", "display": "the Narrator", "gender": "male"},
    {"kind": "character", "entity_id": "curate", "name": "the curate",
     "display": "the curate", "gender": "male"},
    {"kind": "character", "entity_id": "martians", "name": "the Martians",
     "display": "A Martian", "gender": "creature"},
    {"kind": "prop", "entity_id": "walking_machine", "name": "the walking machine"},
]

CLEAN = ("The dusted roadway runs toward the gate between low brick walls. "
         "Grey daylight comes in low from the LEFT, deep shadow past the wall.")


def names() -> dict[str, str]:
    return pg.person_tokens(ROWS)


def setup_of(described: str = "", geometry: str = "", crowd: str = ""):
    return SimpleNamespace(described=described, geometry=geometry, crowd=crowd)


def ep(**setups):
    return SimpleNamespace(setups=setups)


def test_person_tokens_covers_creatures_and_skips_articles_and_props():
    got = names()
    assert got["curate"] == "curate"
    assert got["martian"] == "martians"          # gender=='creature' row, display 'A Martian'
    assert got["narrator"] == "unnamed_first_person_narrator"
    assert "the" not in got                      # an article names nobody
    assert "machine" not in got                  # a prop row is not a person


def test_person_tokens_drops_a_word_two_rows_claim():
    rows = [{"kind": "character", "entity_id": "john_ferrier", "display": "John Ferrier"},
            {"kind": "character", "entity_id": "john_rance", "display": "John Rance"}]
    got = pg.person_tokens(rows)
    assert "john" not in got and got["ferrier"] == "john_ferrier"


def test_name_words_reads_id_display_and_name():
    got = pg.name_words(ROWS[0])
    assert {"narrator", "unnamed", "first", "person"} <= got
    assert "the" not in got


def test_phantom_faults_fire_on_the_ep18_evidence_sentences():
    episode = ep(roadway=setup_of(
        described=CLEAN + " The narrator and the curate approach along the dusted roadway.",
        geometry="A Martian stands beyond the aperture."))
    found = pg.phantom_faults(episode, names(), set())
    assert len(found) == 2
    assert "setup 'roadway' (described)" in found[0] and "'curate'" in found[0]
    assert "setup 'roadway' (geometry)" in found[1] and "'martian'" in found[1]


def test_a_possessive_form_fires():
    episode = ep(stair=setup_of(described="The curate's shoulders block the stair."))
    found = pg.phantom_faults(episode, names(), set())
    assert len(found) == 1 and "'curate'" in found[0]


def test_a_generic_person_noun_fires_without_any_cast_token():
    episode = ep(bridge=setup_of(geometry="A figure waits on the far bank."))
    found = pg.phantom_faults(episode, names(), set())
    assert len(found) == 1 and "'figure'" in found[0]


def test_the_crowd_field_never_fires():
    episode = ep(bridge=setup_of(described=CLEAN, geometry="",
                                 crowd="Forty onlookers and a woman crowd the parapet."))
    assert pg.phantom_faults(episode, names(), set()) == []


def test_a_clean_described_passes():
    episode = ep(roadway=setup_of(described=CLEAN, geometry="The gate sits at the RIGHT edge."))
    assert pg.phantom_faults(episode, names(), set()) == []


def test_a_place_name_collision_does_not_fire():
    rows = [{"kind": "character", "entity_id": "john_ferrier", "display": "John Ferrier"}]
    place_words = {"st", "john", "wood"}
    episode = ep(lane=setup_of(described="The lane bends at St John's Wood."))
    assert pg.phantom_faults(episode, pg.person_tokens(rows), place_words) == []
