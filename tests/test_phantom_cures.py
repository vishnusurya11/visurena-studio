"""G-PHANTOM's mechanical cure (ep18, 2026-10-05): delete the offending sentence
exactly as the hand repair did, measured by the gate's own `phantom_hits` -- the
cure MEASURES LIKE THE CHECKER -- and guarded so the field never drops under its
G-FIRSTFRAME per-setup floor (90/60 words).  A deletion that would breach the
floor is left to the llm cure as residue.  $0: arithmetic."""
from __future__ import annotations

from studio import plan_cures as pc
from studio import plan_gates as pg

NAMES = {"curate": "curate", "narrator": "unnamed_first_person_narrator"}
FILL = "The roadway runs toward the gate between low brick walls under a flat grey sky."
BAD = "The narrator and the curate approach along the dusted roadway."


def doc_of(described: str, geometry: str = "") -> dict:
    return {"setups": {"roadway": {"described": described, "geometry": geometry}}}


def test_strip_deletes_exactly_the_offending_sentence_and_repasses_the_gate():
    described = " ".join([BAD] + [FILL] * 7)          # 7 x 14 = 98 clean words
    doc, residue = pc.strip_phantoms(doc_of(described), NAMES, set())
    kept = doc["setups"]["roadway"]["described"]
    assert residue == []
    assert "curate" not in kept and kept.count(FILL) == 7
    assert pg.phantom_hits(kept, NAMES, set()) == []  # the cure measures like the checker
    assert len(kept.split()) >= pg.DESCRIBED_WORDS


def test_a_deletion_that_breaches_the_floor_is_left_untouched_as_residue():
    described = " ".join([BAD] + [FILL] * 2)          # 28 clean words < the 90 floor
    doc, residue = pc.strip_phantoms(doc_of(described), NAMES, set())
    assert doc["setups"]["roadway"]["described"] == described
    assert residue == ["roadway"]


def test_the_geometry_floor_is_sixty_words():
    geometry = " ".join([BAD] + [FILL] * 5)           # 70 clean words >= the 60 floor
    doc, residue = pc.strip_phantoms(doc_of(" ".join([FILL] * 7), geometry), NAMES, set())
    assert residue == []
    assert "curate" not in doc["setups"]["roadway"]["geometry"]


def test_strip_is_idempotent_on_a_clean_doc():
    described = " ".join([FILL] * 7)
    doc, residue = pc.strip_phantoms(doc_of(described), NAMES, set())
    assert residue == [] and doc["setups"]["roadway"]["described"] == described


def test_the_dispatch_row_routes_a_phantom_fault_to_the_strip():
    row = ("G-PHANTOM setup 'roadway' (described): sentence 'The narrator and the curate "
           "approach' names 'curate'; a place description is the empty stage and this "
           "sentence prints a phantom into every take of the setup, measured 1 against 0")
    assert pc.cure_for(row) == "strip_phantoms"


def test_split_sentences_and_floor_for():
    assert pc.split_sentences("One here. Two there! Three?") == ["One here.", "Two there!", "Three?"]
    assert pc.floor_for("described") == pg.DESCRIBED_WORDS
    assert pc.floor_for("geometry") == pg.GEOMETRY_WORDS
