"""The tiny-face rung keeps a draw that is NO WORSE than the take it replaces (ship review, skeptic
minor 1, 2026-10-19).  ep01 T01 already fails a hard row -- gait, 'the feet slide' -- so a 1024 draw
of it that fails the same row and draws the faces would have been thrown away by 'kept only when it
passes everything'.  The bar now: the draw's hard faults are a subset of the old take's failing hard
rows (its dq and content verdicts, and the take eye's last record of it), and it adds none.
Replayed on ep01 T01's real records (tests/fixtures/ep01_replay/tiny_face/: T01.dq.json,
T01.content.json and eye_b368ae93.json, copies of the files under takes/r2v/ at 2bfb178).
Nothing renders here: the render, the checks and the judge are fakes."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.episode import tiny_face as tf
from studio.judges import take_eye
from studio.judges.verdict import Fault, Verdict
from tests.test_the_tiny_face_rung import ctx_at, room_at

FIX = Path(__file__).resolve().parent / "fixtures" / "ep01_replay" / "tiny_face"
DQ = json.loads((FIX / "T01.dq.json").read_text(encoding="utf-8"))


def real_room(tmp_path):
    """room_at's T01, carrying ep01 T01's own dq and content verdicts and the take eye's record."""
    book, home, room = room_at(tmp_path)
    for name in ("T01.dq.json", "T01.content.json", "eye_b368ae93.json"):
        shutil.copy(FIX / name, room / name)
    return book, home, room


def draw_verdict(*extra: Fault) -> Verdict:
    """The take eye's verdict on a draw that fails what ep01 T01 fails, plus `extra`."""
    faults = take_eye.dq_faults(1, DQ) + list(extra)
    return Verdict(judge="take_eye", version="1", passed=not faults, faults=faults, confidence=1.0, reads=1)


WARP = Fault(kind="warp", where="T01", severity="normal", note="fail: S 2.9 HARD: the face is redrawn")
FRAMING = Fault(kind="framing", where="T01", severity="low", evidence={"second_vote": True})


def test_ep01_t01s_old_take_already_fails_gait_and_only_gait():
    texts = {s: (FIX / f"T01{s}").read_text(encoding="utf-8") for s in (".dq.json", ".content.json")}
    assert tf.old_hard(FIX, 1, texts) == {"gait"}


def test_the_eye_records_hard_faults_at_the_take_count_too(tmp_path):
    shutil.copy(FIX / "eye_b368ae93.json", tmp_path / "eye_b368ae93.json")
    assert tf.eye_hard(tmp_path, 1) == {"gait"}
    assert tf.eye_hard(tmp_path, 8) == {"clones"}
    assert tf.eye_hard(tmp_path / "none", 1) == set()


def test_a_draw_failing_only_the_rows_the_old_take_failed_is_kept(tmp_path):
    book, home, room = real_room(tmp_path)
    ctx = ctx_at(home, renders=[1])
    assert tf.rung(ctx, "--approved=render", judge=lambda take: draw_verdict()) == [1]
    assert (room / "T01.mp4").read_bytes() == b"1024 draw"
    assert any("no worse" in m and "gait" in m for m in ctx.logged)


def test_an_advisory_the_draw_adds_is_not_a_new_hard_fault(tmp_path):
    book, home, room = real_room(tmp_path)
    ctx = ctx_at(home, renders=[1])
    assert tf.rung(ctx, "--approved=render", judge=lambda take: draw_verdict(FRAMING)) == [1]


def test_a_draw_adding_a_hard_fault_gives_the_old_take_back(tmp_path):
    book, home, room = real_room(tmp_path)
    ctx = ctx_at(home, renders=[1])
    assert tf.rung(ctx, "--approved=render", judge=lambda take: draw_verdict(WARP)) == []
    assert (room / "T01.mp4").read_bytes() == b"old take"
    assert json.loads((room / "T01.dq.json").read_text(encoding="utf-8"))["take_sha8"] == DQ["take_sha8"]
    assert any("warp" in m and "old take stays" in m for m in ctx.logged)


def test_a_take_with_no_failing_row_keeps_only_a_clean_draw():
    assert tf.no_worse(draw_verdict(), {"gait"}) and not tf.no_worse(draw_verdict(), set())
    assert tf.no_worse(Verdict(judge="take_eye", version="1", passed=True, confidence=1.0), set())
