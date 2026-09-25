"""The identity gate gets each segment's start as a SAMPLE INDEX.

ep12, 2026-09-25: take_verdict handed identity_dq its SegmentReport objects and
faces.segment_of compared them with the sample index k -- TypeError on T02,
the first take with a face through the armed identity gate. A segment starting
at start_s belongs from the first sample read at or after start_s / seconds.
"""
from studio import identity_gate
from studio.measure import faces


def test_one_segment_starts_at_sample_zero():
    assert identity_gate.sample_starts([0.0], 8.0) == [0]


def test_a_later_segment_starts_at_the_first_sample_after_it():
    shares = faces.sample_shares(8)
    starts = identity_gate.sample_starts([0.0, 4.0], 8.0)
    assert starts[0] == 0
    assert shares[starts[1]] >= 0.5 and (starts[1] == 0 or shares[starts[1] - 1] < 0.5)


def test_sample_frames_and_the_starts_read_the_same_shares():
    assert list(faces.sample_shares(len(faces.SAMPLE_AT))) == list(faces.SAMPLE_AT)


def test_no_cast_sheets_is_not_measured_rather_than_a_crash(monkeypatch):
    """ep12 T02: take_verdict calls identity_dq with no sheets; the empty bank left
    every face with no scores and Face.best raised on max() of nothing."""
    monkeypatch.setattr(identity_gate, "enabled", lambda: True)
    face = identity_gate.Face(k=0, h=0.3, scores={})
    monkeypatch.setattr(identity_gate, "observe", lambda *a, **kw: [face])
    report = identity_gate.identity_dq("take.mp4", [0], ["artilleryman"], ["char-artilleryman.png"])
    assert report["measured"] is False and report["ok"] is True
    assert "sheet" in report["note"]
