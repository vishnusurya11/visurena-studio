"""The ep18 delivered plan (2026-10-06 dry check) drew false faults from the
new vocabularies: the narrator's id 'unnamed_first_person_narrator' made
'first' a person token (G-PHANTOM), the cylinder's alias 'falling star' made
any star a machine (G-STAGE), and G-TWICE read adjectives as positions on ten
good shots -- so G-TWICE is advisory until calibrated, like panel_place.  $0."""
from __future__ import annotations

import json
from pathlib import Path

from studio import pack_refs, plan_gates


def test_id_filler_words_are_not_person_tokens():
    row = {"entity_id": "unnamed_first_person_narrator", "display": "the Narrator"}
    words = plan_gates.name_words(row)
    assert "narrator" in words and not words & {"unnamed", "first", "person"}


def test_a_star_is_not_a_machine(tmp_path):
    props = tmp_path / "analysis" / "props"
    props.mkdir(parents=True)
    (props / "cyl.json").write_text(json.dumps({"aliases": ["a falling star", "the cylinder"]}),
                                    encoding="utf-8")
    assert pack_refs.prop_terms(tmp_path, "cyl") == ["cylinder"]


def test_g_twice_is_advisory_in_the_battery():
    src = (Path(__file__).resolve().parents[1] / "scripts" / "episode" / "plan_check.py").read_text(
        encoding="utf-8")
    line = next(l for l in src.splitlines() if "double_position_faults" in l)
    after = src.split(line, 1)[1].split("\n")[1]
    assert "hard +=" not in after and "advisory" in src.split(line, 1)[1].split("EXPECTS")[0]


def test_a_card_name_masks_with_any_article():
    masked = pack_refs.mask_card_names("a hundred-foot Martian fighting-machine wades",
                                       ["the Martian fighting-machine"])
    assert "martian" not in masked.lower() and len(masked) == len("a hundred-foot Martian fighting-machine wades")
