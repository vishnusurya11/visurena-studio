"""A take's twin check reads the SAMPLES frames its content read already
extracted -- zero extra frame extraction -- and fails the take when any frame
reads two figures as one person.

G-TWIN-TAKE: ep17 T12 (two identical Mrs. Elphinstones) and ep18 T11/T20 fall
to the dedicated same-face-AND-same-dress question; the one weak 'lookalikes'
count answered 0 on all three.  Frame reads are injected and the twin ask is
monkeypatched; a wide shot's recorder asserts zero calls.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from studio import panel_content as pc

from scripts.episode import take_content_check as tcc

WORK = Path("work")


def shot(size: str, faces=("a",)):
    return SimpleNamespace(size=size, faces=list(faces))


def test_a_twin_frame_fails_the_take_with_its_counts(monkeypatch):
    asked = []

    def ask(path, seed):
        asked.append((path.name, seed))
        return pc.Twins(2, 1, ["woman in a grey shawl x2"])

    monkeypatch.setattr(tcc, "read_twin_frame", ask)
    reads = [pc.Seen(people=1), pc.Seen(people=2), pc.Seen(people=1)]
    got = tcc.twin_faults_for(shot("medium_close"), reads, WORK, "T12")
    assert len(got) == 1 and got[0].startswith("twin:")
    assert "woman in a grey shawl x2" in got[0]
    assert asked == [("T12_1.png", 24)], "only the two-figure frame, on its own seed"


def test_all_distinct_frames_leave_the_take_unchanged(monkeypatch):
    monkeypatch.setattr(tcc, "read_twin_frame", lambda path, seed: pc.Twins(2, 2, []))
    reads = [pc.Seen(people=2), pc.Seen(people=2), pc.Seen(people=2)]
    assert tcc.twin_faults_for(shot("medium_close"), reads, WORK, "T12") == []


def test_a_wide_shot_is_never_asked(monkeypatch):
    asked = []

    def recorder(path, seed):
        asked.append(path)
        return pc.Twins(2, 1, [])

    monkeypatch.setattr(tcc, "read_twin_frame", recorder)
    reads = [pc.Seen(people=2), pc.Seen(people=2), pc.Seen(people=2)]
    assert tcc.twin_faults_for(shot("wide"), reads, WORK, "T12") == []
    assert asked == []


def test_an_unreadable_twin_frame_is_a_fault(monkeypatch):
    def unreadable(path, seed):
        raise pc.Unreadable("no figures")

    monkeypatch.setattr(tcc, "read_twin_frame", unreadable)
    got = tcc.twin_faults_for(shot("close"), [pc.Seen(people=2)], WORK, "T03")
    assert got and got[0].startswith("unread: twin")


def test_the_twin_faults_flip_the_verdict_row():
    row = {"passed": True, "faults": [], "people": 2}
    out = tcc.with_twins(row, ["twin: woman in a grey shawl x2 (2 figures, 1 distinct)"])
    assert not out["passed"] and out["faults"][0].startswith("twin:")
    assert tcc.with_twins(row, []) is row, "no twins leaves the row as judged"
