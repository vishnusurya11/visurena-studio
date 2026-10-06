"""G-STAGE's mechanical cure (ep17 shot 14 hand fix, codified): 'a Martian
wading' becomes 'the Martian fighting-machine wading', the pid is staged, the
FIRST cured mention carries one short physical clause and every later mention
gets the name alone.  The cure measures like the checker: the cured doc passes
`stage_faults` (masking exempts 'Martian' inside the card name).  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures as pc
from studio import plan_gates as pg

VOCAB = {"machines": {"fighting_machine": {
             "name": "the Martian fighting-machine",
             "terms": ["tripod"],
             "physical": "A walking engine of glittering metal, higher than many houses."}},
         "creatures": {"martians": ["martian"]}}


def doc_of():
    return {"shots": [
        {"index": 0, "setup": "thames", "frame": "a Martian wading up the Thames",
         "motion": "The camera holds a locked-off frame", "at_rest": "", "end": "", "faces": []},
        {"index": 1, "setup": "thames", "frame": "a Martian stoops to the water",
         "motion": "", "at_rest": "", "end": "", "faces": []}],
        "setups": {"thames": {"described": "The river.", "props": ["fighting_machine"]}}}


def as_ep(doc):
    shots = [SimpleNamespace(cuts=[], **s) for s in doc["shots"]]
    setups = {k: SimpleNamespace(described=v.get("described", ""), crowd=v.get("crowd", ""),
                                 geometry=v.get("geometry", ""), props=v.get("props") or [],
                                 cast=v.get("cast") or []) for k, v in doc["setups"].items()}
    return SimpleNamespace(shots=shots, setups=setups)


def test_the_creature_word_becomes_the_card_name_and_the_gate_repasses():
    doc, unresolved = pc.stage_machines(doc_of(), VOCAB)
    assert unresolved == []
    first, second = doc["shots"][0]["frame"], doc["shots"][1]["frame"]
    assert first.startswith("the Martian fighting-machine, a walking engine")
    assert first.endswith("wading up the Thames")
    assert second == "the Martian fighting-machine stoops to the water"
    assert doc["setups"]["thames"]["props"] == ["fighting_machine"]
    assert pg.stage_faults(as_ep(doc), VOCAB) == []


def test_a_bare_machine_word_is_renamed_and_staged():
    doc = {"shots": [{"index": 0, "setup": "lane", "frame": "the tripod strides over the lane",
                      "motion": "", "at_rest": "", "end": "", "faces": []}],
           "setups": {"lane": {"described": "The lane.", "props": []}}}
    doc, unresolved = pc.stage_machines(doc, VOCAB)
    assert unresolved == []
    assert doc["shots"][0]["frame"].startswith("the Martian fighting-machine, a walking engine")
    assert doc["setups"]["lane"]["props"] == ["fighting_machine"]


def test_the_cure_is_idempotent_on_a_cured_doc():
    doc, _ = pc.stage_machines(doc_of(), VOCAB)
    again, unresolved = pc.stage_machines({k: v for k, v in doc.items()}, VOCAB)
    assert unresolved == []
    assert again["shots"][0]["frame"] == doc["shots"][0]["frame"]
    assert again["setups"]["thames"]["props"] == ["fighting_machine"]


def test_an_ambiguous_creature_word_comes_back_unresolved_and_the_pick_reruns():
    vocab = {"machines": {
        "fighting_machine": {"name": "the Martian fighting-machine", "terms": ["tripod"],
                             "physical": "A walker."},
        "handling_machine": {"name": "the Martian handling-machine", "terms": ["crab"],
                             "physical": "A digger."}},
        "creatures": {"martians": ["martian"]}}
    doc = {"shots": [{"index": 5, "setup": "pit", "frame": "a Martian digging the pit",
                      "motion": "", "at_rest": "", "end": "", "faces": []}],
           "setups": {"pit": {"described": "The pit.", "props": []}}}
    doc, unresolved = pc.stage_machines(doc, vocab)
    assert unresolved == [(5, "martian", ["fighting_machine", "handling_machine"])]
    assert doc["shots"][0]["frame"] == "a Martian digging the pit"   # nothing guessed
    doc = pc.rename_creature(doc, 5, "martian", "handling_machine", vocab)
    assert doc["shots"][0]["frame"].startswith("the Martian handling-machine")
    assert doc["setups"]["pit"]["props"] == ["handling_machine"]


def test_strip_creatures_drops_the_sentence_from_setup_text_only():
    doc = {"shots": [], "setups": {"pit": {
        "described": "The pit smokes under a grey sky. A Martian stands at its lip.",
        "geometry": "The rim runs LEFT to RIGHT.",
        "crowd": "", "props": []}}}
    out = pc.strip_creatures(doc, VOCAB)
    assert out["setups"]["pit"]["described"] == "The pit smokes under a grey sky."
    assert out["setups"]["pit"]["geometry"] == "The rim runs LEFT to RIGHT."


def test_strip_creatures_keeps_a_sentence_whose_creature_word_is_a_card_name():
    doc = {"shots": [], "setups": {"pit": {
        "described": "The Martian fighting-machine's shadow crosses the pit.",
        "geometry": "", "crowd": "", "props": ["fighting_machine"]}}}
    out = pc.strip_creatures(doc, VOCAB)
    assert "shadow crosses the pit" in out["setups"]["pit"]["described"]
