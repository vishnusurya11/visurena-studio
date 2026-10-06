"""one_position, the G-TWICE llm cure: a canned rewrite is accepted only when
the CODE-SIDE probe passes (both detectors re-run, the word budget, the style
lints); a failing answer is re-asked with the probe's lines; three failures
keep the original fields; OverBudget keeps the doc and never raises.  No test
here calls a paid API."""
from __future__ import annotations

import copy

from studio import llm, plan_llm_cures as plc
from tests.test_episode_writer import FakeModel

NAMES = {"captain": "captain", "curate": "curate"}
ROWS = ["G-TWICE shot 20: frame+at_rest places curate at both 'scullery' and 'kitchen'; "
        "one person holds one position per picture, measured 2 against 1"]

FRAME = "Medium on the captain leading the curate into the scullery, the doorway framing them both."
AT_REST = "The curate follows at the kitchen door, his lantern raised to shoulder height."
END = "Both men stand inside the scullery, the lantern light on the stone sink."

GOOD = {"frame": "Medium on the captain and the curate crossing the kitchen, the scullery doorway ahead.",
        "at_rest": "The curate stands at the kitchen door, his lantern raised, the captain a pace ahead.",
        "end": END}
BAD = {"frame": FRAME, "at_rest": AT_REST, "end": END}


def doc_of():
    return {"shots": [{"index": 20, "faces": ["captain", "curate"], "cuts": [],
                       "frame": FRAME, "at_rest": AT_REST, "end": END,
                       "motion": "They walk at a normal walking pace.", "camera": "at the far wall"}]}


def test_a_good_rewrite_lands_in_the_shot():
    doc = doc_of()
    fake = FakeModel(GOOD)
    out = plc.one_position(doc, ROWS, NAMES, caller=fake)
    assert out["shots"][0]["frame"] == GOOD["frame"]
    assert out["shots"][0]["at_rest"] == GOOD["at_rest"]
    assert len(fake.prompts) == 1


def test_a_rewrite_still_doubled_is_probed_and_re_asked():
    doc = doc_of()
    fake = FakeModel(BAD, GOOD)
    out = plc.one_position(doc, ROWS, NAMES, caller=fake)
    assert out["shots"][0]["at_rest"] == GOOD["at_rest"]
    assert len(fake.prompts) == 2
    assert llm.REFUSED in fake.prompts[1]
    assert "places curate at both" in fake.prompts[1]      # the probe's own fault line


def test_three_refused_asks_keep_the_original_fields():
    doc = doc_of()
    fake = FakeModel(BAD)
    out = plc.one_position(doc, ROWS, NAMES, caller=fake)
    assert out["shots"][0]["frame"] == FRAME and out["shots"][0]["at_rest"] == AT_REST
    assert len(fake.prompts) == plc.ASKS


def test_overbudget_keeps_the_doc_and_does_not_raise():
    doc = doc_of()
    frozen = copy.deepcopy(doc)
    out = plc.one_position(doc, ROWS, NAMES, caller=FakeModel(llm.OverBudget("the ceiling")))
    assert out == frozen


def test_the_rewriter_closure_rewrites_one_shot_through_the_same_probe():
    doc = doc_of()
    plc.rewriter(doc, NAMES, caller=FakeModel(GOOD))(20, "at_rest")
    assert doc["shots"][0]["at_rest"] == GOOD["at_rest"]


def test_the_probe_is_code_not_the_models_own_judgement():
    shot = doc_of()["shots"][0]
    assert plc.probe(shot, plc.ShotPositions(**BAD), NAMES)          # two anchors refuse
    assert plc.probe(shot, plc.ShotPositions(**GOOD), NAMES) == []
    slow = {**GOOD, "end": "The lantern light slowly crosses the stone sink and the men inside."}
    assert any("slow" in why for why in plc.probe(shot, plc.ShotPositions(**slow), NAMES))
    short = {**GOOD, "end": "The sink."}
    assert any("words" in why for why in plc.probe(shot, plc.ShotPositions(**short), NAMES))
