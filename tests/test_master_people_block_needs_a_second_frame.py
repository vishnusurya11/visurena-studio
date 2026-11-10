"""Jekyll ep07 retro S1 (brick 17): at the master a per-frame people read blocked shot_07 for five
runs (84 min) on ONE 0.5 s frame of Jekyll's hair; the owner watched and called it a misread.
A per-frame people line refuses only when a second frame of its shot agrees, and a shot read on
fewer than LOOK_FRAMES frames fails closed.  Scaffold words, a long leak and clones still stand on
one sighting (ep06 envelope, ep04 leaks).  The REFUSED line prints line, time and k of n."""
from __future__ import annotations

import pytest

from studio import master_ladder, ship_block
from studio.judges.verdict import Fault, Verdict

WHO = "who: 2 figures read as 'gabriel_john_utterson' by hair, facial hair and coat; the shot casts one"
CROWD = "3 figure(s) for 1 declared (1 cast + 0 extras), 0 of them copies of another"
SCAFFOLD = "scaffold: the prompt's words drawn in the picture (focus, picture)"


def people(at: float, read_on: int, line: str = WHO, where: str = "shot_07") -> Fault:
    return Fault(kind="content", where=where, evidence={"at": at, "faults": [line], "read_on": read_on})


def verdict(*faults: Fault) -> Verdict:
    return Verdict(judge="master_eye", version="t", passed=False, faults=list(faults), confidence=1.0)


def test_one_frame_of_a_shot_read_four_times_does_not_block():
    v = verdict(people(0.5, 4))
    assert ship_block.master_blocks(v.faults) == {}
    assert master_ladder.flag(v) is v


def test_two_frames_agreeing_block():
    assert list(ship_block.master_blocks([people(0.5, 4), people(2.0, 4)])) == ["shot_07"]


def test_a_shot_read_on_too_few_frames_fails_closed():
    assert list(ship_block.master_blocks([people(0.5, 1)])) == ["shot_07"]


def test_an_old_verdict_without_read_on_fails_closed():
    old = Fault(kind="content", where="shot_07", evidence={"at": 0.5, "faults": [WHO]})
    assert list(ship_block.master_blocks([old])) == ["shot_07"]


def test_scaffold_words_block_on_one_sighting():
    f = Fault(kind="content", where="shot_19", evidence={"at": 3.0, "faults": [SCAFFOLD], "read_on": 4})
    assert list(ship_block.master_blocks([f])) == ["shot_19"]


def test_clones_without_a_frame_block():
    f = Fault(kind="clones", where="shot_18", evidence={"cosine": 0.81})
    assert list(ship_block.master_blocks([f])) == ["shot_18"]


def test_the_ep05_strangers_shape_on_two_of_four_frames_blocks():
    faults = [people(1.0, 4, CROWD, "shot_18"), people(6.0, 4, CROWD, "shot_18")]
    assert list(ship_block.master_blocks(faults)) == ["shot_18"]


def test_a_non_blocking_fault_is_never_listed():
    f = Fault(kind="framing", where="shot_09", evidence={"at": 1.0, "faults": ["framing 'medium'"], "read_on": 4})
    assert ship_block.master_blocks([f]) == {}


def test_the_refusal_prints_line_time_and_count():
    with pytest.raises(SystemExit) as stop:
        master_ladder.flag(verdict(people(0.5, 4), people(2.0, 4)))
    said = str(stop.value)
    assert "stands at shot_07" in said and "at 0.5s" in said and "(2 of 4 frames)" in said and "who:" in said


def test_lone_people_shots_names_the_shots_a_second_look_must_read():
    assert ship_block.lone_people_shots([people(0.5, 1)]) == [7]
    assert ship_block.lone_people_shots([people(0.5, 1), people(2.0, 2)]) == []
    f = Fault(kind="content", where="shot_19", evidence={"at": 3.0, "faults": [SCAFFOLD], "read_on": 1})
    assert ship_block.lone_people_shots([f]) == []
