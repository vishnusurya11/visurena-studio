"""Jekyll ep03, 2026-10-27 11:32-11:54 PDT: the master eye sent T04 back for "faces at master" (the doctor's
face 0.093 of the frame height on a medium close, wall 0.12).  The retake rendered a fresh seed (84206, try 2)
from the same sheets and panel; the new draw scored 81.7, the old one 81.9, and take_dq --attempts put the old
draw back as T04.mp4 (T04_dq_kept.json: kept T04_fail2.mp4, 3158192 bytes, the bytes T04 held before).  The
take bytes were the same, but shots.json had been rewritten (seed, tries, render_s), so the master ladder's
fingerprint read "changed" and paid the recut, the 4x upscale, QC and a second master eye: ~14 minutes, and
the flag stayed.

Two rules now.  A changed record is not a changed take: the fingerprint is what the cut reads (the take,
its head, its still).  And a master retake must change an INPUT the measured fault lives in -- a seed cannot
grow a face the panel framed small (H3 obeys the cell and the camera verb) -- so each measured field routes
to the cure that can move it, or the retake is refused as a no-op before any render and the master flags at
once.  T04 is a spoken over-the-shoulder take on a locked grammar: its camera never travels, the panel owns
its framing, and the refusal says so and owes the panel a cure.

Replayed on ep03's own plan (tests/fixtures/ep03_master_retake/).  No GPU, no ComfyUI, no network."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import judged_gate, master_ladder as ml, step_attempts, take_ladder
from studio.judges.verdict import Fault, Verdict

FIX = Path(__file__).parent / "fixtures" / "ep03_master_retake"


@pytest.fixture
def ep03(tmp_path, monkeypatch):
    """ep03's home: its plan, T04 as the master judged it, its record before the retake."""
    home = tmp_path / "book" / "episodes" / "ep03"
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    shutil.copy(FIX / "plan.json", home / "plan.json")
    (room / "T04.mp4").write_bytes(b"T04 as judged, 3158192 bytes")
    record = json.loads((FIX / "T04_record_after_retake.json").read_text(encoding="utf-8"))
    (room / "shots.json").write_text(json.dumps([{**record, "seed": 84005, "tries": 1}]), encoding="utf-8")
    monkeypatch.setattr("scripts.episode.step_09_shoot.approved", lambda p: "--approved=render")
    monkeypatch.setattr("studio.gate_policy.of", lambda *a: None)
    return SimpleNamespace(home=home, room=room, record=record)


def ctx_of(home, said):
    return SimpleNamespace(home=home, stage="episode", log=lambda m, **k: said.append(m))


def faces_at(*shots) -> Verdict:
    """The master's faces field as ep03's rubric answered it, naming `shots`."""
    evidence = json.loads((FIX / "eye_faces.json").read_text(encoding="utf-8"))["faces"]
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                   faults=[Fault(kind="faces", where="master", evidence={**evidence, "under": list(shots)})])


def board_at(shot: int) -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                   faults=[Fault(kind="board", where="master", evidence={"off": {str(shot): 0.31}})])


def keep_best_put_the_old_draw_back(ep03, calls):
    """The ep03 render: the record rewritten with the new seed, the old bytes back as T04.mp4."""
    def retake(ctx, indices, why, flag, trims=None):
        calls.append((indices, why))
        (ep03.room / "shots.json").write_text(json.dumps([ep03.record]), encoding="utf-8")
    return retake


def test_a_rewritten_record_alone_is_not_a_changed_take(ep03):
    before = ml.fingerprint(ep03.home, 4)
    (ep03.room / "shots.json").write_text(json.dumps([ep03.record]), encoding="utf-8")
    assert ml.fingerprint(ep03.home, 4) == before
    (ep03.room / "T04.mp4").write_bytes(b"another draw")
    assert ml.fingerprint(ep03.home, 4) != before


def test_the_fixture_is_the_ep03_revert():
    kept = json.loads((FIX / "T04_dq_kept.json").read_text(encoding="utf-8"))
    new, old = kept["attempts"][0], kept["attempts"][2]
    assert kept["file"] == old["file"] and kept["bytes"] == old["bytes"] and new["score"] < old["score"]
    rows = [json.loads(l) for l in (FIX / "learnings_master.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["action"] for r in rows] == ["retake_shot", "flag"] and "faces at master" in rows[0]["note"]


def test_the_ep03_faces_retake_is_refused_before_any_render(ep03, monkeypatch, capsys):
    calls, said = [], []
    monkeypatch.setattr(take_ladder, "retake", keep_best_put_the_old_draw_back(ep03, calls))
    assert ml.retake_through_take_ladder(ctx_of(ep03.home, said), 4, faces_at(4, 17)) is False
    assert calls == [], "no render: nothing a render can change holds the face size"
    out = capsys.readouterr().out
    assert "NO-OP master: T04 faces" in out and "panel" in out
    assert step_attempts.count(ep03.home, "retakes") == 0


def test_the_refusal_owes_the_panel_its_cure(ep03, monkeypatch):
    monkeypatch.setattr(take_ladder, "retake", lambda *a, **k: pytest.fail("rendered"))
    ml.retake_through_take_ladder(ctx_of(ep03.home, []), 4, faces_at(4, 17))
    rows = [json.loads(l) for l in (ep03.home / take_ladder.OWED).read_text(encoding="utf-8").splitlines()]
    assert rows == [{"take": 4, "shot": 4, "field": "frame", "fault": "faces",
                     "row": "panel cure owed: shot 4 frame (master faces)"}]


def a_new_draw(ep03, calls):
    """A render whose cure's roll is kept: new bytes at T<nn>.mp4."""
    def retake(ctx, indices, why, flag, trims=None):
        calls.append((indices, why))
        (ep03.room / f"T{indices[0]:02d}.mp4").write_bytes(b"the cure's roll")
    return retake


def test_a_pulled_back_close_with_a_small_face_pushes_in_instead(ep03, monkeypatch):
    calls = []
    monkeypatch.setattr(take_ladder, "retake", a_new_draw(ep03, calls))
    ml.retake_through_take_ladder(ctx_of(ep03.home, []), 7, faces_at(7))
    plan = json.loads((ep03.home / "plan.json").read_text(encoding="utf-8"))
    motion = take_ladder.shot_doc(plan, 7)["motion"]
    assert motion.startswith("The camera pushes in toward") and calls == [([7], "retake_shot: faces -> push_slow")]


@pytest.mark.parametrize("shot, why", [(10, "already pushes"), (6, "locked grammar")])
def test_a_close_that_already_pushes_or_is_locked_by_its_grammar_has_no_cure(ep03, monkeypatch, capsys, shot, why):
    monkeypatch.setattr(take_ladder, "retake", lambda *a, **k: pytest.fail("rendered"))
    assert ml.retake_through_take_ladder(ctx_of(ep03.home, []), shot, faces_at(shot)) is False
    assert f"NO-OP master: T{shot:02d} faces" in capsys.readouterr().out


def test_a_board_fault_changes_the_move_type(ep03, monkeypatch):
    calls = []
    monkeypatch.setattr(take_ladder, "retake", a_new_draw(ep03, calls))
    before = take_ladder.shot_doc(json.loads((ep03.home / "plan.json").read_text(encoding="utf-8")), 4)["motion"]
    ml.retake_through_take_ladder(ctx_of(ep03.home, []), 4, board_at(4))
    after = take_ladder.shot_doc(json.loads((ep03.home / "plan.json").read_text(encoding="utf-8")), 4)["motion"]
    assert after != before and calls == [([4], "retake_shot: board -> move_type")]


def test_a_render_that_kept_the_old_draw_takes_no_recut_and_no_round(ep03, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(take_ladder, "retake", keep_best_put_the_old_draw_back(ep03, calls))
    assert ml.retake_through_take_ladder(ctx_of(ep03.home, []), 4, board_at(4)) is False
    assert calls and step_attempts.count(ep03.home, "retakes") == 0
    assert "NO-OP master: T04 kept its earlier draw" in capsys.readouterr().out


def test_a_render_that_kept_the_old_draw_puts_back_its_words_and_its_time(ep03, monkeypatch):
    """The kept draw was rendered from the old motion: the old plan goes back, and the swap's new mtime
    goes too, so step 10 does not read the same bytes as newer than the master."""
    import os
    take, plan = ep03.room / "T04.mp4", (ep03.home / "plan.json").read_text(encoding="utf-8")
    os.utime(take, (1_793_125_000, 1_793_125_000))
    render = keep_best_put_the_old_draw_back(ep03, [])

    def swapped_back(*a, **k):
        render(*a, **k)
        os.utime(take, (1_793_126_663, 1_793_126_663))     # 11:44:23, the swap's stamp
    monkeypatch.setattr(take_ladder, "retake", swapped_back)
    ml.retake_through_take_ladder(ctx_of(ep03.home, []), 4, board_at(4))
    assert (ep03.home / "plan.json").read_text(encoding="utf-8") == plan
    assert take.stat().st_mtime == 1_793_125_000


def test_a_repeats_fault_has_no_render_cure(ep03, monkeypatch, capsys):
    monkeypatch.setattr(take_ladder, "retake", lambda *a, **k: pytest.fail("rendered"))
    v = Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                faults=[Fault(kind="repeats", where="master", evidence={"pairs": [{"a": 3, "b": 9}]})])
    assert ml.retake_through_take_ladder(ctx_of(ep03.home, []), 3, v) is False
    assert "NO-OP master: T03 repeats" in capsys.readouterr().out


def test_a_refused_retake_is_no_round_and_no_learning_row(tmp_path):
    """The rung answers a RungResult: a no-op is judged_gate's NO ROUND, so only the terminal is booked."""
    learned = []
    ctx = SimpleNamespace(stage="episode", unit="ep03", book_dir=tmp_path, home=tmp_path / "episodes" / "ep03",
                          learn=learned.append)
    from studio.run_budget import EPISODE_SHARES, Budget
    ctx.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
    verdict, moved = faces_at(4), ml.Round()
    ladder = ml.rungs(verdict, recut=lambda: pytest.fail("recut"), retake=lambda s, v: False, moved=moved)
    got, taken = judged_gate.climbed(ctx, "MASTER", ml.once(verdict, lambda: pytest.fail("judged"), moved),
                                     ladder, ml.TERMINAL)
    assert taken == [] and learned == [] and got is verdict
