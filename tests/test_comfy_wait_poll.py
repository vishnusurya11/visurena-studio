"""comfy.wait polls at wait_record's 0.5 s, not 5 s (efficiency debate 2026-11-09, e3_io_poll_ab: the 5 s lattice
cost a paired mean of 1.693 s per job, n=10 pairs, identical outputs)."""
from studio import comfy


def test_wait_polls_at_half_a_second(monkeypatch):
    seen = {}
    monkeypatch.setattr(comfy, "wait_record", lambda pid, timeout, poll: seen.setdefault("poll", poll) and {})
    monkeypatch.setattr(comfy, "outputs_of", lambda record: [])
    comfy.wait("job-1")
    assert seen["poll"] == 0.5


def test_wait_keeps_an_explicit_poll(monkeypatch):
    seen = {}
    monkeypatch.setattr(comfy, "wait_record", lambda pid, timeout, poll: seen.setdefault("poll", poll) and {})
    monkeypatch.setattr(comfy, "outputs_of", lambda record: [])
    comfy.wait("job-1", poll=5.0)
    assert seen["poll"] == 5.0
