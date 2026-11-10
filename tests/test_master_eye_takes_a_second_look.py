"""Jekyll ep07 retro S1, the master eye's half: a shot whose only people read is one frame gets
EXTRA_FRAMES more frames read in the same pass, so `ship_block.master_blocks` decides on a second
look -- another frame -- never on one 0.5 s read (shot_07 refused five runs on one frame)."""
from __future__ import annotations

from studio.judges import master_eye as me
from studio.judges.verdict import Fault

WHO = "who: 2 figures read as 'gabriel_john_utterson' by hair, facial hair and coat; the shot casts one"
PLACED = {"duration_s": 20.0, "shots": [{"index": 7, "t_start": 0.0, "t_end": 4.0, "seconds": 4.0},
                                        {"index": 8, "t_start": 4.0, "t_end": 20.0, "seconds": 16.0}]}
PLAN = {"shots": [{"index": 7}, {"index": 8}]}


def faulty_at(*times):
    return lambda read, spec, setup: [WHO] if read.at in times else []


def test_each_read_fault_carries_the_frames_its_shot_was_read_on(monkeypatch):
    monkeypatch.setattr(me, "content_faults", faulty_at(0.5))
    grouped = {7: [me.Read(at=0.5, shot=7), me.Read(at=1.5, shot=7), me.Read(at=2.5, shot=7)]}
    faults = me.read_faults({"grouped": grouped, "shots": {7: {}}}, {})
    assert [(f.where, f.evidence["at"], f.evidence["read_on"]) for f in faults] == [("shot_07", 0.5, 3)]


def test_second_times_are_new_frames_inside_the_lone_shot():
    lone = [Fault(kind="content", where="shot_07", evidence={"at": 0.5, "faults": [WHO], "read_on": 1})]
    more = me.second_times(lone, PLACED, [0.5, 10.0])
    assert len(more) == me.EXTRA_FRAMES and all(0.0 < t < 4.0 and t != 0.5 for t in more)


def test_no_lone_shot_means_no_second_look():
    two = [Fault(kind="content", where="shot_07", evidence={"at": a, "faults": [WHO], "read_on": 2})
           for a in (0.5, 2.0)]
    assert me.second_times(two, PLACED, [0.5, 2.0]) == []


def test_look_again_reads_the_new_frames_and_keeps_time_order(monkeypatch):
    monkeypatch.setattr(me, "content_faults", faulty_at(0.5))
    asked = []

    def frames(master, times):
        asked.append(list(times))
        return [f"pic{t}" for t in times]

    monkeypatch.setattr(me, "read_all", lambda pics, times, *a, **k: [me.Read(at=t, shot=me.shot_at(PLACED, t))
                                                                        for t in times])
    reads = [me.Read(at=0.5, shot=7), me.Read(at=10.0, shot=8)]
    times, pics, got = me.look_again("m.mp4", PLACED, PLAN, [0.5, 10.0], ["a", "b"], reads,
                                     frames=frames, reader=None, embed=None, cache=None)
    assert len(asked) == 1 and len(asked[0]) == me.EXTRA_FRAMES
    assert times == sorted(times) and [r.at for r in got] == times and len(pics) == len(times)
    assert sum(r.shot == 7 for r in got) == 1 + me.EXTRA_FRAMES


def test_look_again_reads_nothing_when_no_shot_is_lone(monkeypatch):
    monkeypatch.setattr(me, "content_faults", lambda *a: [])
    out = me.look_again("m.mp4", PLACED, PLAN, [0.5], ["a"], [me.Read(at=0.5, shot=7)],
                        frames=lambda *a: (_ for _ in ()).throw(AssertionError("read")), reader=None,
                        embed=None, cache=None)
    assert out[0] == [0.5]
