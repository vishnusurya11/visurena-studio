"""A timeline built before the plan changed must SAY SO, not crash.

MEASURED 2026-09-22 on ep08: the plan lost a line from shot 3 and gained one
on shot 17. `placed.json` still held the old placement, and the take builder
died inside a generator expression with a bare `StopIteration` -- no episode,
no take, no shot, no reason. The stale file is trivially detectable; what was
missing was anyone asking.
"""
import pytest

from studio.timeline_fresh import fingerprint, stale


class FakeLine:
    def __init__(self, index, shot, text):
        self.index, self.shot, self.text = index, shot, text


class FakeShot:
    def __init__(self, index, beat_s, coda_s):
        self.index, self.beat_s, self.coda_s = index, beat_s, coda_s


class FakeEpisode:
    def __init__(self, shots, lines):
        self.shots, self.lines = shots, lines


def episode(text="a line", beat=1.0):
    return FakeEpisode([FakeShot(0, beat, 1.0)], [FakeLine(0, 0, text)])


def test_fingerprint_of_the_same_plan_is_the_same():
    assert fingerprint(episode()) == fingerprint(episode())


def test_a_changed_line_changes_the_fingerprint():
    assert fingerprint(episode()) != fingerprint(episode(text="another line"))


def test_a_changed_beat_changes_the_fingerprint():
    assert fingerprint(episode()) != fingerprint(episode(beat=0.4))


def test_a_timeline_carrying_this_plans_fingerprint_is_fresh():
    ep = episode()
    assert stale(ep, {"plan": fingerprint(ep)}) == []


def test_a_timeline_carrying_another_fingerprint_names_the_rebuild():
    got = stale(episode(), {"plan": fingerprint(episode(text="older"))})
    assert len(got) == 1
    assert "timeline.py" in got[0]


def test_a_timeline_with_no_fingerprint_is_stale():
    assert stale(episode(), {}) != []


def test_a_missing_timeline_is_stale():
    assert stale(episode(), None) != []
