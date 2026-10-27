"""Steps 10 and 11 under "upscale last, once" (Jekyll ep03 retro #2, 2026-10-27).

Step 10 makes the judged cut (assemble --at-cut -> cut/cut_r2v.mp4).  Step 11 measures THAT file
(qc.py --at-cut -> qc_r2v_cut.json), the master eye reads it and signs eye_<cut sha8>.json, the
master ladder recuts at cut scale, and only then is the judged cut upscaled once (assemble --upscale),
its QC report and rubric carried to the master's sha8 for step 12 and the upload -- with the face strip
cut from the upscaled master (log only).  A carried verdict holds only while cut/upscaled.json traces
the master's bytes to the judged cut on disk: another file at the master's name, or a new cut, is not
done, and the next run upscales the judged cut again (or judges the new cut first).

The launcher is a fake that writes what each script would; the judge and the face strip are faked.
No GPU, no ffmpeg, no ComfyUI."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.episode import step_10_edit, step_11_qc
from studio import db, episode_home, master_upscale as mu, youtube_publish as yp
from studio.episode_run import EpisodeContext
from studio.judges import master_eye
from studio.judges.verdict import Fault, Verdict

CODEX = "20260901000001"


def passing() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=True, confidence=1.0, reads=30)


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    episode_home.make_rooms(book, 4)
    home = episode_home.home(book, 4)
    master = episode_home.master_path(book, 4, "r2v")
    cut = mu.cut_of(master)
    launched, judged = [], []

    def launch(cmd):
        args = cmd[1:]
        launched.append(args)
        if args[0].endswith("qc.py"):
            target, report = (cut, home / "qc_r2v_cut.json") if "--at-cut" in args else (master, home / "qc_r2v.json")
            episode_home.write_json(report, {"passed": True, "sha8": yp.sha8(target), "seconds": 150.0,
                                             "measures_sha8": step_11_qc.qc_measures_sha8(), "at_cut": "--at-cut" in args})
        if args[0].endswith("assemble.py") and "--upscale" in args:
            master.write_bytes(b"4x of " + cut.read_bytes())
            mu.record_made(master, cut, "av3", 3444, 3444)
        if args[0].endswith("assemble.py") and "--at-cut" in args:
            cut.write_bytes(b"a recut")
        return 0
    context = EpisodeContext(conn, CODEX, book, "episode", unit="ep04", number=4, logs_root=tmp_path / "logs",
                             busy=lambda: False, hold=tmp_path / "RENDER_HOLD", launch=launch)
    context.home, context.extra, context.launched, context.judged = home, [], launched, judged
    cut.write_bytes(b"the judged cut")
    episode_home.write_json(home / "plan.json", {"setups": {}, "shots": [], "lines": []})
    episode_home.write_json(home / "placed.json", {"duration_s": 150.0, "shots": [], "lines": []})
    monkeypatch.setattr(step_11_qc, "contact_sheet", lambda home, master, sha8: Path(home) / "review" / f"contact_{sha8}.png")
    monkeypatch.setattr(step_11_qc, "read_master",
                        lambda home, master, plan, placed, tools_=None: judged.append(Path(master).name) or (passing(), {}))
    monkeypatch.setattr(step_11_qc, "strip_on_master",
                        lambda ctx, master: {"crops": [{"take": "T01", "eye": "sharp"}], "note": "log only"})
    return context


def master_of(ctx) -> Path:
    return episode_home.master_path(ctx.book_dir, 4, "r2v")


def test_qc_and_the_eye_read_the_cut_then_it_is_upscaled_once(ctx):
    step_11_qc.run(ctx)
    assert ctx.launched == [["scripts/episode/qc.py", CODEX, "4", "--engine=r2v", "--at-cut"],
                            ["scripts/episode/assemble.py", CODEX, "4", "--engine=r2v", "--upscale"],
                            ["scripts/episode/dossier.py", CODEX, "4"],
                            ["scripts/audit/sheet.py", CODEX, "4"]]
    assert ctx.judged == ["cut_r2v.mp4"] and step_11_qc.done(ctx)


def test_the_upload_reads_the_upscaled_master_with_the_cuts_verdicts_on_its_bytes(ctx):
    from scripts.episode import eye_review
    step_11_qc.run(ctx)
    engine, master, qc = yp.deliverable(ctx.home, "")
    assert master == master_of(ctx) and master.read_bytes().startswith(b"4x of")
    report, cut_sha = episode_home.read_json(qc), yp.sha8(mu.cut_of(master))
    assert report["sha8"] == yp.sha8(master) and report["cut_sha8"] == cut_sha and report["passed"]
    rubric = episode_home.read_json(eye_review.rubric_path(ctx.home, yp.sha8(master)))
    assert eye_review.refusals(rubric, yp.sha8(master), Path("eye.json")) == []
    assert rubric["judged_on"] == {"file": "cut_r2v.mp4", "sha8": cut_sha}
    assert rubric["face_strip"]["crops"][0]["take"] == "T01", "the strip is the master's, beside the fields"


def test_another_file_at_the_masters_name_is_not_done_and_is_upscaled_again(ctx):
    step_11_qc.run(ctx)
    master_of(ctx).write_bytes(b"a master from somewhere else")
    assert not step_11_qc.done(ctx)
    ctx.launched.clear()
    ctx.judged.clear()
    step_11_qc.run(ctx)
    assert [a[0] for a in ctx.launched][:1] == ["scripts/episode/assemble.py"] and ctx.judged == []
    assert step_11_qc.done(ctx)


def test_a_carried_report_copied_onto_a_foreign_master_is_not_done(ctx):
    import shutil
    from scripts.episode import eye_review
    step_11_qc.run(ctx)
    old = yp.sha8(master_of(ctx))
    master_of(ctx).write_bytes(b"forged")
    new = yp.sha8(master_of(ctx))
    report = episode_home.read_json(ctx.home / "qc_r2v.json") | {"sha8": new}
    episode_home.write_json(ctx.home / "qc_r2v.json", report)
    doc = episode_home.read_json(eye_review.rubric_path(ctx.home, old)) | {"sha8": new}
    episode_home.write_json(eye_review.rubric_path(ctx.home, new), doc)
    assert not step_11_qc.done(ctx), "upscaled.json never made these bytes from the judged cut"


def test_a_new_cut_is_judged_before_any_upscale(ctx):
    step_11_qc.run(ctx)
    mu.cut_of(master_of(ctx)).write_bytes(b"a recut after the upscale")
    assert not step_11_qc.done(ctx)
    ctx.launched.clear()
    step_11_qc.run(ctx)
    assert [a[0] for a in ctx.launched][:2] == ["scripts/episode/qc.py", "scripts/episode/assemble.py"]
    assert ctx.judged == ["cut_r2v.mp4", "cut_r2v.mp4"] and step_11_qc.done(ctx)


def test_the_carry_refuses_a_master_not_made_from_the_judged_cut(ctx, monkeypatch):
    ctx.launch = lambda cmd: ctx.launched.append(cmd[1:]) or 0      # the upscale ran and made nothing
    episode_home.write_json(ctx.home / "qc_r2v_cut.json", {"passed": True, "sha8": yp.sha8(mu.cut_of(master_of(ctx))),
                                                           "measures_sha8": step_11_qc.qc_measures_sha8()})
    master_of(ctx).write_bytes(b"stale master")
    with pytest.raises(SystemExit, match="not made from the judged cut"):
        step_11_qc.run(ctx)
    assert not (ctx.home / "qc_r2v.json").exists()


def test_the_master_ladder_recuts_at_cut_scale(ctx):
    step_11_qc.recut(ctx, [])
    assert ctx.launched[0] == ["scripts/episode/assemble.py", CODEX, "4", "--engine=r2v", "--at-cut"]
    assert ctx.launched[1] == ["scripts/episode/qc.py", CODEX, "4", "--engine=r2v", "--at-cut"]


def test_the_cut_is_read_without_a_face_strip(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(step_11_qc, "face_strip", lambda *a: pytest.fail("a strip from the 768 cut"))
    monkeypatch.setattr(step_11_qc.master_eye, "read", lambda home, m, plan, placed, **kit: seen.update(kit) or ("v", {}))
    step_11_qc.read_master(tmp_path, tmp_path / "cut" / "cut_r2v.mp4", {}, {}, {"frames": None, "detect": None})
    assert seen["strip"] == []


# ---- step 10 -------------------------------------------------------------------------------------

def test_edit_assembles_the_judged_cut(ctx):
    (ctx.book_dir / "title").mkdir(exist_ok=True)
    (ctx.book_dir / "title" / "ep04.mp4").write_bytes(b"card")
    ctx.launched.clear()
    step_10_edit.run(ctx)
    assert ctx.launched == [["scripts/episode/assemble.py", CODEX, "4", "--engine=r2v", "--at-cut"]]


def test_edit_is_done_on_a_current_cut_and_not_on_one_qc_refused(ctx):
    import os
    import time
    title = ctx.book_dir / "title" / "ep04.mp4"
    title.parent.mkdir(exist_ok=True)
    title.write_bytes(b"card")
    take = ctx.home / "takes" / "r2v" / "T01.mp4"
    take.parent.mkdir(parents=True, exist_ok=True)
    take.write_bytes(b"take")
    cut = mu.cut_of(master_of(ctx))
    now = time.time()
    os.utime(title, (now - 100, now - 100))
    os.utime(take, (now - 50, now - 50))
    os.utime(cut, (now + 10, now + 10))                 # cut after the takes, the timeline and the card
    assert step_10_edit.done(ctx)
    os.utime(take, (now + 50, now + 50))
    assert not step_10_edit.done(ctx), "a take newer than the cut"
    os.utime(cut, (now + 60, now + 60))
    episode_home.write_json(ctx.home / "qc_r2v_cut.json", {"sha8": yp.sha8(cut), "passed": False, "lufs_ok": False})
    assert not step_10_edit.done(ctx), "QC refused these cut bytes on a cut-side row: recut"


def test_the_carry_refuses_an_unsigned_or_unmeasured_cut(ctx):
    master, cut = master_of(ctx), mu.cut_of(master_of(ctx))
    master.write_bytes(b"4x")
    mu.record_made(master, cut, "av3", 3444, 3444)
    cut_qc = ctx.home / "qc_r2v_cut.json"
    assert "measure the cut first" in step_11_qc.carry_refusal(ctx.home, master, cut, cut_qc)
    episode_home.write_json(cut_qc, {"passed": True, "sha8": yp.sha8(cut)})
    assert "judges the cut first" in step_11_qc.carry_refusal(ctx.home, master, cut, cut_qc)
    master_eye.write_rubric(ctx.home, yp.sha8(cut), passing())
    assert step_11_qc.carry_refusal(ctx.home, master, cut, cut_qc) == ""
