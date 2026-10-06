"""ep19 (2026-10-06): the plan deferred on faults that all had cures.  Three
causes, one test each.  (A) the cylinder's alias "the shot" made the film word
"shot" a G-STAGE term, so every shot faulted; (B) the G-STAGE cure pasted the
card's first clause -- "the top turning slowly" -- into a shot, and the
contract refuses slow words; (C) plan_repair applied every cure as ONE round,
so that one bad cure threw away the light, crowd and move cures with it.  $0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))

import plan_repair  # noqa: E402
from studio import pack_refs, plan_cures  # noqa: E402


def test_a_film_word_is_never_a_prop_alias(tmp_path):
    props = tmp_path / "analysis" / "props"
    props.mkdir(parents=True)
    (props / "cyl.json").write_text(json.dumps({"aliases": ["the shot", "the cylinder", "a frame"]}),
                                    encoding="utf-8")
    assert pack_refs.prop_terms(tmp_path, "cyl") == ["cylinder"]


def test_a_card_clause_with_a_slow_word_is_not_pasted():
    assert plan_cures.physical_clause("the top turning slowly, grey clinker falling") == ""
    assert plan_cures.physical_clause("a brass hood on three jointed legs, tall") == \
        "a brass hood on three jointed legs"


def test_one_bad_cure_is_dropped_and_the_others_land(monkeypatch):
    def fake_apply(doc, rows, *a, **k):
        doc = json.loads(json.dumps(doc))
        for r in rows:
            doc["marks"].append(r)
        return doc, [], {r.split()[0] for r in rows}

    def valid(doc):
        if "BAD row" in doc["marks"]:
            raise ValueError("asks for a slow shot")

    monkeypatch.setattr(plan_repair, "apply", fake_apply)
    doc, uncured, names = plan_repair.apply_each({"marks": []}, ["LIGHT row", "BAD row", "CROWD row"],
                                                 None, 19, valid=valid)
    assert doc["marks"] == ["LIGHT row", "CROWD row"]
    assert uncured == ["BAD row"] and names == {"LIGHT", "CROWD"}
