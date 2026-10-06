"""The mechanical G-MOVES/M2 cure (2026-10-05 self-curing pipeline, AREA 2):
`studio.move_rebalance` rewrites motion heads from the full camera catalog --
size-legal, G-AIM-safe, G-ANCHOR-safe -- and verifies every candidate by
replaying the REAL gate predicates before writing it (the G-CROWD-CLOSE
"cure measures like the checker" pattern).  The old `vary_heads` could only
produce PUSH and LOCKED, so ep18 drove push_slow to share 0.30 while distinct
moves stayed at 6 < MIN_MOVES 8, and M2 / G-ANCHOR rows bounced to the
writer as hand edits.  $0, deterministic, no llm import."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

from studio import cell_gates, episode_spec, move_rebalance as mr, plan_gates as pg

FIXTURES = Path(__file__).parent / "fixtures" / "episodes"

AT_REST = ("THE FOCUS OF THE PICTURE IS the lamp; the gate stands at the LEFT; "
           "the wall runs behind; the trough sits at the RIGHT")


def shot_of(**over) -> dict:
    base = {"index": 0, "setup": "yard", "size": "medium", "frame": "The yard.",
            "at_rest": AT_REST, "motion": "The camera holds a locked-off frame",
            "camera": "", "faces": [], "extras": 0}
    base.update(over)
    return base


def doc_of(shots: list[dict], lines: list[dict] | None = None, crowd: str = "",
           props: list[str] | None = None) -> dict:
    return {"shots": shots, "lines": lines or [],
            "setups": {"yard": {"described": "A stone yard.", "crowd": crowd,
                                "props": props or []}}}


def probe_episode(doc: dict) -> SimpleNamespace:
    return SimpleNamespace(
        shots=[mr.probe(s) for s in doc["shots"]],
        setups={name: mr.setup_ns(s) for name, s in doc["setups"].items()})


def orbit_doc() -> dict:
    """The fixture plan_gates' own docstring pins, dressed as a plan: sizes
    cycle wide/medium so the catalog's union offers exactly MIN_MOVES ids."""
    rows = json.loads((FIXTURES / "moves_orbit.json").read_text(encoding="utf-8"))
    sizes = ["wide", "medium", "medium", "wide", "medium"]
    return doc_of([shot_of(index=r["index"], motion=r["motion"], camera=r["camera"],
                           size=sizes[k % len(sizes)]) for k, r in enumerate(rows)])


def test_rebalance_reaches_the_moves_floor():
    doc, unfixed = mr.rebalance(orbit_doc(), [])
    ep = probe_episode(doc)
    ids = pg.move_ids(ep.shots)
    assert unfixed == []
    assert len(set(ids)) >= pg.MIN_MOVES
    assert max(ids.count(i) for i in set(ids)) / len(ids) <= pg.MAX_MOVE_SHARE
    assert pg.moves_faults(ep) == []


def test_m2_head_is_prepended_and_actions_survive():
    old = "his hand lifts the lid; the lid tips; steam rises"
    doc = doc_of([shot_of(size="medium_close", motion=old,
                          at_rest="THE FOCUS OF THE PICTURE IS the lid; "
                                  "the pot sits on the stove")])
    doc, unfixed = mr.rebalance(doc, [0])
    got = doc["shots"][0]["motion"]
    assert unfixed == []
    for clause in old.split("; "):
        assert clause in got
    assert got.split(";")[0].startswith("The camera ")
    assert "M2" not in {c for c, _ in episode_spec.motion_faults(got)}


def test_head_ok_refuses_an_aim_not_in_at_rest():
    shot = mr.probe(shot_of(at_rest="The gate stands at the LEFT; the wall runs behind"))
    setup = mr.setup_ns({})
    pan = ("The camera pans from the heliograph to the gate, travelling a forearm, "
           "across the whole shot")
    assert mr.head_ok(shot, pan, "", "", setup) is False
    good = ("The camera pans from the gate to the wall, travelling a forearm, "
            "across the whole shot")
    assert mr.head_ok(shot, good, "", "", setup) is True


def test_head_ok_refuses_sideways_on_an_anchored_medium_close():
    shot = mr.probe(shot_of(size="medium_close", frame="He leans on the fence.",
                            at_rest="THE FOCUS OF THE PICTURE IS the fence; "
                                    "he leans on the fence at the LEFT"))
    setup = mr.setup_ns({})
    truck = ("The camera tracks sideways to the right, past the fence, "
             "travelling a forearm, across the whole shot")
    assert mr.head_ok(shot, truck, "", "", setup) is False
    push = ("The camera pushes in slowly toward the fence, travelling a forearm, "
            "across the whole shot")
    assert mr.head_ok(shot, push, "", "", setup) is True


def test_ignored_moves_are_never_rendered():
    for banned in ("tilt_down", "crane_down", "rack_focus", "handheld", "orbit"):
        assert banned not in mr.HEADS
        assert all(banned not in legal for legal in mr.LEGAL.values())
    for move in mr.HEADS:       # the regex round-trip lock
        head = mr.render_head(move, ["lamp", "gate"], "a forearm")
        assert pg.move_id(head, "") == move, (move, head)


def test_amount_respects_size_and_crowd_caps():
    assert pg.amount(f"The camera pushes in, travelling {mr.amount_for(2.5, 5.0)}, "
                     "across the whole shot") <= 2.5
    assert pg.amount(f"The camera pushes in, travelling {mr.amount_for(pg.CROWD_CAP, 5.0)}, "
                     "across the whole shot") <= pg.CROWD_CAP
    truck = ("The camera tracks sideways to the right, past the lamp, "
             "travelling a stride, across the whole shot")
    doc = doc_of([shot_of(index=0, size="wide", motion=truck),
                  shot_of(index=1, size="close", motion=truck)],
                 crowd="seven men stand by the gate")
    doc, unfixed = mr.rebalance(doc, [0, 1])
    assert unfixed == []
    assert pg.move_faults(probe_episode(doc)) == []


def test_dialogue_shot_only_goes_locked():
    pan = ("The camera pans from the lamp to the gate, travelling a forearm, "
           "across the whole shot; his hand lifts")
    doc = doc_of([shot_of(index=0, motion=pan), shot_of(index=1, motion=pan),
                  shot_of(index=2, motion=pan)],
                 lines=[{"index": 0, "kind": "dialogue", "speaker": "man",
                         "text": "Words.", "shot": 1}])
    doc, _ = mr.rebalance(doc, [0, 1, 2])
    head = doc["shots"][1]["motion"].split(";")[0].strip()
    assert head in (mr.HEADS["locked"], pan.split(";")[0].strip())
    assert pg.amount(head) in (None, 0.0)


def test_rebalance_is_deterministic():
    one, _ = mr.rebalance(copy.deepcopy(orbit_doc()), [])
    two, _ = mr.rebalance(copy.deepcopy(orbit_doc()), [])
    assert json.dumps(one, sort_keys=True) == json.dumps(two, sort_keys=True)


def test_aim_never_names_an_unspanned_prop():
    shot = shot_of(at_rest="THE FOCUS OF THE PICTURE IS the heliograph; "
                           "the gate stands at the LEFT; the wall runs behind")
    aims = mr.cell_aims(shot, {"props": ["heliograph_tripod"]})
    assert aims and "heliograph" not in aims and "tripod" not in aims
    spoken = shot_of(frame="The heliograph on its stand.",
                     at_rest=shot["at_rest"])     # the shot's own prose names it
    assert "heliograph" in mr.cell_aims(spoken, {"props": ["heliograph_tripod"]})
