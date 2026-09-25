"""Step 11 is done on a passed qc report for these bytes and a rubric that
clears: one the judge signed flagged (every `n` with its flag and evidence)
clears; one with a bare `n` does not; one about other bytes does not."""
from __future__ import annotations

import json

import pytest

from scripts.episode import eye_review as er, step_11_qc
from studio import db, episode_home, youtube_publish as yp
from studio.judges import master_eye as me
from studio.judges.verdict import Fault, Verdict
from studio.stage_run import StageContext

CODEX = "20260901000001"


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    episode_home.make_rooms(book, 4)
    context = StageContext(conn, CODEX, book, "episode", unit="ep04", number=4, logs_root=tmp_path / "logs",
                           busy=lambda: False, hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: 0)
    context.home = episode_home.home(book, 4)
    context.extra = []
    return context


def master_and_report(ctx) -> str:
    master = episode_home.master_path(ctx.book_dir, 4, "r2v")
    master.write_bytes(b"the cut")
    digest = yp.sha8(master)
    episode_home.write_json(ctx.home / "qc_r2v.json", {"passed": True, "sha8": digest, "seconds": 150.0})
    return digest


def story_flagged() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30, terminal="flag",
                   faults=[Fault(kind="story", where="master", severity="high",
                                 evidence={"turn_shot": 7, "verbs": ["catch"], "listed": ["walking"], "matched": []})])


def test_a_judge_flagged_rubric_clears_the_step(ctx):
    digest = master_and_report(ctx)
    assert not step_11_qc.done(ctx)
    me.write_rubric(ctx.home, digest, story_flagged())
    assert step_11_qc.rubric_signed(ctx.home, digest)
    assert step_11_qc.done(ctx)


def test_a_bare_n_does_not_clear_the_step(ctx):
    digest = master_and_report(ctx)
    doc = er.blank_rubric(digest, "master_r2v.mp4", "c.png", 5.0, 30)
    for field, _q in er.RUBRIC:
        doc["rubric"][field]["answer"] = "y"
    doc["rubric"]["story"]["answer"] = "n"
    doc["notes"] = "the turn is not on screen"
    er.review_dir(ctx.home).mkdir(parents=True, exist_ok=True)
    er.rubric_path(ctx.home, digest).write_text(json.dumps(doc), encoding="utf-8")
    assert not step_11_qc.done(ctx)


def test_a_rubric_about_other_bytes_does_not_clear(ctx):
    digest = master_and_report(ctx)
    me.write_rubric(ctx.home, digest, story_flagged())
    episode_home.master_path(ctx.book_dir, 4, "r2v").write_bytes(b"re-cut")
    assert not step_11_qc.done(ctx)
