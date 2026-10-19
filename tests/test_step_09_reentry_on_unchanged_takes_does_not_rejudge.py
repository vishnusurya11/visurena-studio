"""P08 item 8: step 09 entered again with every take's sha8 equal to the signed eye verdict's files
keeps the verdict: no eye read (ep01: 28 panels re-read for 2 changed), no duplicate audit row."""
from __future__ import annotations

from types import SimpleNamespace

from scripts.episode import step_09_shoot as s9
from studio import audit_rows, eye_verdict as ev
from studio.judges import take_eye
from studio.judges.verdict import Fault, Verdict


def ctx_with_verdict(tmp_path, monkeypatch):
    book = tmp_path / "book"
    home = book / "episodes" / "ep01"
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T00.mp4").write_bytes(b"take zero")
    flagged = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1, terminal="keep_best",
                      faults=[Fault(kind="warp", where="T00")])
    signed = ev.sign_verdict(room, [room / "T00.mp4"], flagged)
    monkeypatch.setattr(s9.episode_home, "load_plan", lambda b, n: None)
    ctx = SimpleNamespace(home=home, book_dir=book, number=1, unit="ep01", stage="episode")
    return ctx, room, signed


def test_unchanged_takes_keep_the_signed_verdict_and_read_nothing(tmp_path, monkeypatch):
    ctx, room, signed = ctx_with_verdict(tmp_path, monkeypatch)
    monkeypatch.setattr(take_eye, "judge", lambda *a, **k: (_ for _ in ()).throw(AssertionError("re-judged")))
    assert s9.judge_takes(ctx, "--approved=render") == signed
    assert audit_rows.load(ctx.book_dir) == []                    # no duplicate row


def test_a_changed_take_is_judged_again(tmp_path, monkeypatch):
    ctx, room, signed = ctx_with_verdict(tmp_path, monkeypatch)
    (room / "T00.mp4").write_bytes(b"a retaken take")
    reads = []
    monkeypatch.setattr(s9.judged_gate, "clear", lambda *a, **k: reads.append(1) or signed)
    s9.judge_takes(ctx, "--approved=render")
    assert reads == [1]


def test_a_retry_stamped_after_the_verdict_judges_again(tmp_path, monkeypatch):
    ctx, room, signed = ctx_with_verdict(tmp_path, monkeypatch)
    monkeypatch.setattr(s9, "reset_since_verdict", lambda c, takes: True)
    reads = []
    monkeypatch.setattr(s9.judged_gate, "clear", lambda *a, **k: reads.append(1) or signed)
    s9.judge_takes(ctx, "--approved=render")
    assert reads == [1]
