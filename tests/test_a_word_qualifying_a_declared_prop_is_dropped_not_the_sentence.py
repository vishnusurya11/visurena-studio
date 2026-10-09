"""ep25 (2026-10-09 04:58Z): the plan deferred on G-PHANTOM -- the Regent's Park
setup DECLARES the prop `fighting_machine` and its description says 'the brazen
cowled Martian fighting-machine' twice, once in the light sentence.  'Martian'
names the creature row, and the place text is pasted into every take: the word
is a real risk.  The sentence is not -- it stages the declared machine and the
setup's only sunset light.  The cure drops the cast word that qualifies a
declared prop and keeps the sentence."""
from __future__ import annotations

from studio import plan_cures as pc
from studio import plan_gates

NAMES = {"martian": "martians", "curate": "curate"}
DESCRIBED = ("The top of Baker Street where it meets Regent's Park. Beyond the railings, lawns stretch out "
             "to a dark mass of plane and elm trees. Far away above the treetops stands the fighting-machine, "
             "a brazen cowled Martian fighting-machine on tall jointed brass legs. The last clear sunset light "
             "falls from the left, gilding the brass Martian fighting-machine above the trees.")


def _doc(described: str, props=("fighting_machine",)):
    return {"setups": {"regents_park_corner": {"described": described, "geometry": "", "props": list(props)}}}


def test_the_qualifying_word_goes_and_both_sentences_stay(monkeypatch):
    monkeypatch.setattr(pc, "floor_for", lambda field: 0)
    doc, residue = pc.strip_phantoms(_doc(DESCRIBED), NAMES, set())
    text = doc["setups"]["regents_park_corner"]["described"]
    assert "Martian" not in text
    assert "The last clear sunset light falls from the left" in text
    assert "brazen cowled fighting-machine" in text
    assert not plan_gates.phantom_hits(text, NAMES, set())


def test_an_undeclared_machine_still_loses_its_sentence(monkeypatch):
    monkeypatch.setattr(pc, "floor_for", lambda field: 0)
    doc, _ = pc.strip_phantoms(_doc(DESCRIBED, props=()), NAMES, set())
    assert "sunset light" not in doc["setups"]["regents_park_corner"]["described"]


def test_a_person_word_that_qualifies_nothing_is_still_a_phantom(monkeypatch):
    monkeypatch.setattr(pc, "floor_for", lambda field: 0)
    text = "The curate kneels by the copper. The room is grey and cold with light from the left."
    doc, _ = pc.strip_phantoms(_doc(text), NAMES, set())
    assert "curate" not in doc["setups"]["regents_park_corner"]["described"]
