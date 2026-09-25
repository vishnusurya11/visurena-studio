"""Step 11 never parks: no Escalation in the file, and a run ends with the
rubric in the judge's pen -- pass, or flagged with an audit row -- then the
dossier and the audit sheet.  The judge and the contact sheet are faked; qc.py,
dossier.py and sheet.py are launched with the argv the runner types."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.episode import step_11_qc
from studio import audit_rows, db, episode_home, learnings, registry, youtube_publish as yp
from studio.episode_run import EpisodeContext
from studio.judges.verdict import Fault, Verdict

CODEX = "20260901000001"


def test_the_step_module_names_no_escalation():
    text = (registry.ROOT / "scripts" / "episode" / "step_11_qc.py").read_text(encoding="utf-8")
    assert "Escalation" not in text and "escalate" not in text
    assert not hasattr(step_11_qc, "Escalation")


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    episode_home.make_rooms(book, 4)
    launched = []

    def launch(cmd):
        launched.append(cmd[1:])
        if cmd[1].endswith("qc.py"):
            master = episode_home.master_path(book, 4, "r2v")
            master.write_bytes(b"the cut")
            episode_home.write_json(book / "episodes" / "ep04" / "qc_r2v.json",
                                    {"passed": True, "sha8": yp.sha8(master), "seconds": 150.0})
        return 0
    context = EpisodeContext(conn, CODEX, book, "episode", unit="ep04", number=4, logs_root=tmp_path / "logs",
                             busy=lambda: False, hold=tmp_path / "RENDER_HOLD", launch=launch)
    context.home = episode_home.home(book, 4)
    context.extra = []
    context.launched = launched
    episode_home.write_json(context.home / "plan.json", {"setups": {}, "shots": [], "lines": []})
    episode_home.write_json(context.home / "placed.json", {"duration_s": 150.0, "shots": [], "lines": []})
    monkeypatch.setattr(step_11_qc, "contact_sheet", lambda home, master, sha8: Path(home) / "review" / f"contact_{sha8}.png")
    return context


def passing() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=True, confidence=1.0, reads=30)


def story_flagged() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                   faults=[Fault(kind="story", where="master", evidence={"matched": [], "listed": ["walking"]})])


def test_a_pass_signs_the_rubric_then_the_dossier_and_the_sheet_run(ctx, monkeypatch):
    monkeypatch.setattr(step_11_qc, "read_master", lambda home, master, plan, placed, tools_=None: (passing(), {}))
    step_11_qc.run(ctx)
    assert ctx.launched == [["scripts/episode/qc.py", CODEX, "4", "--engine=r2v"],
                            ["scripts/episode/dossier.py", CODEX, "4"],
                            ["scripts/audit/sheet.py", CODEX, "4"]]
    sha8 = yp.sha8(episode_home.master_path(ctx.book_dir, 4, "r2v"))
    doc = json.loads((ctx.home / "review" / f"eye_{sha8}.json").read_text(encoding="utf-8"))
    assert doc["reviewed_by"] == "judge:master_eye@1" and doc["contact"] == f"contact_{sha8}.png"
    assert all(cell["answer"] == "y" for cell in doc["rubric"].values())
    assert step_11_qc.done(ctx) and audit_rows.load(ctx.book_dir) == []


def test_a_story_fault_is_flagged_never_parked_and_leaves_an_audit_row(ctx, monkeypatch):
    monkeypatch.setattr(step_11_qc, "read_master", lambda home, master, plan, placed, tools_=None: (story_flagged(), {}))
    step_11_qc.run(ctx)
    assert [c[0] for c in ctx.launched] == ["scripts/episode/qc.py", "scripts/episode/dossier.py", "scripts/audit/sheet.py"]
    sha8 = yp.sha8(episode_home.master_path(ctx.book_dir, 4, "r2v"))
    doc = json.loads((ctx.home / "review" / f"eye_{sha8}.json").read_text(encoding="utf-8"))
    assert doc["rubric"]["story"]["answer"] == "n" and doc["rubric"]["story"]["flagged_by"] == "judge:master_eye@1"
    assert doc["rubric"]["story"]["waived_because"] == "" and doc["terminal"] == "flag"
    rows = audit_rows.load(ctx.book_dir)
    assert len(rows) == 1 and rows[0].gate == "MASTER" and rows[0].unit == "ep04" and rows[0].sha8 == sha8
    assert [l.action for l in learnings.load(ctx.learnings_path)] == ["flag"]
    assert step_11_qc.done(ctx)


def test_a_signed_rubric_is_not_judged_again(ctx, monkeypatch):
    monkeypatch.setattr(step_11_qc, "read_master", lambda home, master, plan, placed, tools_=None: (passing(), {}))
    step_11_qc.run(ctx)
    monkeypatch.setattr(step_11_qc, "read_master", lambda *a, **k: (_ for _ in ()).throw(AssertionError("judged twice")))
    step_11_qc.run(ctx)
    assert [c[0] for c in ctx.launched].count("scripts/episode/qc.py") == 2
