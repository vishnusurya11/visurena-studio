"""The move cure never writes a slow word (ep19, 2026-10-05).

ep19's G-MOVES/G-AIM rows went to `rebalance_heads`, which changed the plan
and broke it: "shots.1 'motion' asks for a slow shot ('slowly')".  The catalog
phrasings for push_slow and crane_up carry the word ("The camera pushes in
slowly toward <subject>."), the templates copied it, and the gate replay never
asked the contract.  Now: no template says it, `head_faults` refuses any head
`slow_word` flags (so the llm escape is refused too), and every written head
must leave the full Episode contract no worse than it found it.  $0."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from studio import episode_spec, move_rebalance as mr

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "calibration" / "camera_catalog.md"
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"


def catalog_phrase(move: str) -> str:
    """The catalog's own H3 phrasing for `move`, its <subject> filled."""
    row = next(line for line in CATALOG.read_text(encoding="utf-8").splitlines()
               if line.startswith(f"| {move} |"))
    said = re.search(r'"([^"]+)"', row).group(1).rstrip(".")
    return re.sub(r"<[^>]+>", "the lamp", said) + ", travelling a forearm, across the whole shot"


def test_the_catalog_phrase_is_slow_and_head_faults_refuse_it():
    head = catalog_phrase("push_slow")
    assert episode_spec.slow_word(head) == "slowly"
    shot = mr.probe({"index": 0, "size": "medium", "frame": "The lamp.",
                     "at_rest": "THE FOCUS OF THE PICTURE IS the lamp",
                     "motion": "The camera holds a locked-off frame"})
    why = mr.head_faults(shot, head, "", "", mr.setup_ns({}))
    assert any("slow" in w for w in why)


def test_no_template_carries_a_slow_word():
    for move in mr.HEADS:
        assert episode_spec.slow_word(mr.render_head(move, ["lamp", "gate"], "a forearm")) is None


def test_a_head_that_breaks_the_contract_is_never_written(monkeypatch):
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    episode_spec.Episode(**doc)
    target = doc["shots"][0]["index"]
    slow, fine = catalog_phrase("push_slow"), "The camera holds a locked-off frame"
    monkeypatch.setattr(mr, "candidates", lambda *a, **k: [slow, fine])
    out, unfixed = mr.rebalance(copy.deepcopy(doc), [target])
    episode_spec.Episode(**out)
    assert all(episode_spec.slow_word(s["motion"]) is None for s in out["shots"])
    assert out["shots"][0]["motion"].startswith(fine) and target not in unfixed


def test_only_contract_breaking_heads_leave_the_shot_unfixed_and_untouched(monkeypatch):
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    target = doc["shots"][0]["index"]
    monkeypatch.setattr(mr, "candidates", lambda *a, **k: [catalog_phrase("crane_up")])
    out, unfixed = mr.rebalance(copy.deepcopy(doc), [target])
    assert target in unfixed and out["shots"][0]["motion"] == doc["shots"][0]["motion"]
