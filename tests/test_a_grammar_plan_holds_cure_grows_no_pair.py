"""A grammar plan is one shot per take (episode_takes.ONE_SHOT): the pair rulers of
ONE PER TAKE never judge it.  Jekyll Kawajiri ep01 (grammar anime_tv) still ran
`_grow_pairs` and the unsplit loop of `micro_targets`: pairs (4,5) and (24,25) were
reported unsplit and a micro-line was sought for each, and shot 4's hold grew.

Read-only measure on a copy of ep01 plan.json (rate 2.6): step 1 (_grow_pairs) moved
shot 4 by +0.03 s and reported (24, 25); steps 2-3 left seconds alone (projection above
the 120.5 floor; the setup cap shaved shot 27's coda).  So the +4.7 s padding is NOT
step 1's: only the pair rows and the micro-line hunt are cured here."""
import copy
import json
import sys
from pathlib import Path

from studio import plan_cures as pc

sys.path.insert(0, "scripts/episode")
PLAN = Path(__file__).parent / "fixtures" / "ep01_replay" / "P02" / "plan.json"
RATE = 2.6


def ep01(grammar: bool = True) -> dict:
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    if not grammar:
        doc.pop("grammar")
    return doc


def test_a_grammar_doc_gives_unsplit_empty():
    _, unsplit = pc.holds_and_unsplit(ep01(), RATE)
    assert unsplit == []


def test_the_legacy_pair_test_stays_green_without_a_grammar():
    _, unsplit = pc.holds_and_unsplit(ep01(grammar=False), RATE)
    assert unsplit == [(24, 25)]


def test_no_pair_hold_grows_under_a_grammar():
    out, _ = pc.holds_and_unsplit(ep01(), RATE)
    shot = lambda doc: next(s for s in doc["shots"] if s["index"] == 4)
    assert (shot(out)["beat_s"], shot(out)["coda_s"]) == (shot(ep01())["beat_s"], shot(ep01())["coda_s"])
    legacy, _ = pc.holds_and_unsplit(ep01(grammar=False), RATE)
    assert shot(legacy)["coda_s"] != shot(ep01())["coda_s"]            # the legacy path still grows it


def test_micro_targets_hunt_no_pair_insertion_under_a_grammar(monkeypatch):
    import plan_repair
    asked = []
    monkeypatch.setattr(pc, "pair_insertion_shot", lambda doc, pair, rate: asked.append(pair))
    plan_repair.micro_targets(ep01(), RATE)
    assert asked == []
    plan_repair.micro_targets(ep01(grammar=False), RATE)
    assert asked == [(24, 25)]                                          # the legacy path still hunts


def test_the_runtime_floor_and_hole_steps_still_run_under_a_grammar():
    doc = ep01()
    for s in doc["shots"]:
        s["coda_s"] = 0.0
    out, _ = pc.holds_and_unsplit(copy.deepcopy(doc), RATE)
    assert sum(pc._shot_secs(out, RATE).values()) > sum(pc._shot_secs(doc, RATE).values())
