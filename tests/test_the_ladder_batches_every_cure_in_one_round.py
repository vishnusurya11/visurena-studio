"""Five-expert debate 2026-09-30: the rung-serial ladder spent one ROUND PER
RUNG (seed round, then move, then shorter, then replan), and the measured cure
rates were seed ~0% solo, shorter-on-lag 0/15, replan-content 3/21, while
move_type ran 89-100%.  The batched ladder restores the old F1 rule as code:
one router assigns every faulted take its own cure, free cures cost no round,
input-borne kinds take NO render, and a fault that survives its own cure goes
to the terminal, not around again."""
from __future__ import annotations

from pathlib import Path

from studio import take_ladder as tl
from studio.judges.verdict import Fault, Verdict


def fault(kind: str, take: int, **ev) -> Fault:
    return Fault(kind=kind, where=f"T{take:02d}", evidence=ev)


def room_of(tmp_path: Path) -> Path:
    room = tmp_path / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    return room


def test_the_router_assigns_the_measured_cures():
    assert tl.cure_of([fault("frozen-whole", 5)]) == "move_type"
    assert tl.cure_of([fault("held", 5)]) == "move_type"
    assert tl.cure_of([fault("last-vs-panel", 5)]) == "move_type"
    assert tl.cure_of([fault("lip-sync", 5)]) == "timeline_trim"      # free, never a render
    assert tl.cure_of([fault("lag", 5)]) == "timeline_trim"
    assert tl.cure_of([fault("leak", 5, covers=True)]) == "head_cut"  # free
    assert tl.cure_of([fault("content", 5)]) == ""                    # input-borne: terminal answers
    assert tl.cure_of([fault("letterbox", 5)]) == ""
    assert tl.cure_of([fault("look", 5)]) == ""
    assert tl.cure_of([fault("clones", 5)]) == ""
    assert tl.cure_of([fault("rotation", 5)]) == "seed"               # unknown-to-the-router kinds only


def test_a_mixed_take_takes_its_renderable_cure_and_content_alone_takes_none():
    assert tl.cure_of([fault("content", 5), fault("held", 5)]) == "move_type"
    assert tl.cure_of([fault("content", 5), fault("lettering", 5)]) == ""


def test_one_batched_round_renders_the_union_and_free_cures_cost_no_round(tmp_path):
    room = room_of(tmp_path)
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                faults=[fault("frozen-whole", 0), fault("held", 6), fault("content", 5),
                        fault("lip-sync", 19), fault("leak", 7, covers=True)])
    routed = tl.route(v, room)
    assert sorted(routed["move_type"]) == [0, 6]
    assert sorted(routed["timeline_trim"]) == [19]
    assert sorted(routed["head_cut"]) == [7]
    assert 5 not in {i for takes in routed.values() for i in takes}
    assert tl.renders_of(routed) == [0, 6]                             # only the renderable cures


def test_a_fault_that_survives_its_own_cure_goes_terminal_not_around_again(tmp_path):
    room = room_of(tmp_path)
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                faults=[fault("held", 6)])
    tl.count_round(room, "batch: move_type", tl.signatures(v))
    assert not tl.progressed(room, 6, ["held"])                        # identical signature
    assert tl.progressed(room, 6, ["drift"])                           # changed kind: re-routed
    assert tl.progressed(room, 3, ["held"])                            # a take with no history
    again = tl.route(v, room, try_i=2)
    assert again == {}                                                 # nothing progressed: terminal


def test_the_round_cap_is_two_batched_rounds(tmp_path):
    assert tl.ROUNDS_CAP == 2
    assert [r.name for r in tl.LADDER.rungs] == ["batched_cures"]
    assert tl.LADDER.rungs[0].tries == 2
