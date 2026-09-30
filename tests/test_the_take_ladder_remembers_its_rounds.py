"""The take ladder's memory (2026-09-29, three-agent debate on ep14's 14 rounds):
the old process allowed ONE batched retake round per master, chosen by a person
(ep10 synthesis F1); the automated ladder had no round cap, no per-take attempt
cap and no memory across resumes -- T19 was retaken 8 times, T05 7, and every
resume restarted the climb with a fresh budget.  Now: rounds are counted in
takes/r2v/ladder.json (it survives a resume), the episode stops at ROUNDS_CAP,
and a take with MAX_TAKE_ATTEMPTS archived attempts is never retaken again."""
from pathlib import Path

from studio import take_ladder as tl
from studio.judges.verdict import Fault, Verdict


def room_of(tmp_path: Path) -> Path:
    room = tmp_path / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    return room


def test_rounds_are_counted_on_disk_and_survive_a_new_reader(tmp_path):
    room = room_of(tmp_path)
    assert tl.rounds_of(room) == 0
    tl.count_round(room, "seed: content")
    tl.count_round(room, "move_type: last-vs-panel")
    assert tl.rounds_of(room) == 2                       # a fresh process reads the same file
    assert tl.ROUNDS_CAP == 4 and tl.MAX_TAKE_ATTEMPTS == 3


def test_a_take_with_three_archived_attempts_is_out(tmp_path):
    room = room_of(tmp_path)
    for k in (1, 2, 3):
        (room / "attempts" / f"T19_fail{k}.mp4").write_bytes(b"x")
    (room / "attempts" / f"T05_fail1.mp4").write_bytes(b"x")
    assert tl.attempts_of(room, 19) == 3 and tl.attempts_of(room, 5) == 1
    wanted = {19: [Fault(kind="content", where="T19")], 5: [Fault(kind="content", where="T05")]}
    assert sorted(tl.under_cap(room, wanted)) == [5]


def test_the_climb_is_incurable_at_the_round_cap_or_when_every_take_is_out(tmp_path):
    room = room_of(tmp_path)
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                faults=[Fault(kind="content", where="T19")])
    assert tl.still_curable(room, v)
    for k in range(tl.MAX_TAKE_ATTEMPTS):
        (room / "attempts" / f"T19_fail{k}.mp4").write_bytes(b"x")
    assert not tl.still_curable(room, v)                 # its one take is out of attempts
    v2 = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                 faults=[Fault(kind="content", where="T05")])
    for n in range(tl.ROUNDS_CAP):
        tl.count_round(room, f"round {n}")
    assert not tl.still_curable(room, v2)                # the episode is out of rounds
