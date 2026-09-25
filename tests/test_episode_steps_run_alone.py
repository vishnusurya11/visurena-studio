"""Each episode step on its own: `done` reads its output off disk, `run` launches
the wrapped scripts with exactly the argv scripts/episode/run.py used to type.

The launch is a fake that records argv and returns 0 (or writes the one file the
step reads back); the queue is idle; the brake is off.  No GPU, no library.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

from scripts.episode import (step_01_bind, step_03_places, step_04_record, step_05_timeline,
                             step_06_prompts, step_07_board, step_08_panels, step_09_shoot,
                             step_10_edit, step_11_qc, step_12_deliver)
from studio import db, episode_home, eye_verdict, youtube_publish as yp
from studio.escalate import Escalation
from studio.stage_run import StageContext

CODEX = "20260901000001"
PY = sys.executable
PLAN = {"setups": {"yard": {"location": "yard", "view": "wide_establishing", "described": "a yard"},
                   "room": {"location": "", "view": "", "described": "a room"}},
        "shots": [{"index": 1, "setup": "yard"}, {"index": 2, "setup": "yard"}],
        "lines": [{"index": 1, "text": "one"}, {"index": 2, "text": "two"}]}


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    episode_home.make_rooms(book, 4)
    launched = []
    context = StageContext(conn, CODEX, book, "episode", unit="ep04", number=4,
                           logs_root=tmp_path / "logs", busy=lambda: False,
                           hold=tmp_path / "RENDER_HOLD",
                           launch=lambda cmd: launched.append(cmd[1:]) or 0)
    context.home = episode_home.home(book, 4)
    context.extra = []
    context.launched = launched
    (context.home / "plan.json").write_text(json.dumps(PLAN), encoding="utf-8")
    return context


def _png(path: Path, shade: int = 10) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), (shade, shade, shade)).save(path)
    return path


def _json(path: Path, doc) -> Path:
    return episode_home.write_json(path, doc)


# ---- 01 bind ------------------------------------------------------------------

def test_bind_reads_the_cast_flag():
    assert step_01_bind.cast_of(["--cast=a,b=Bee:f"]) == ["a", "b=Bee:f"]
    assert step_01_bind.cast_of([]) == []


def test_bind_is_done_when_refs_are_stamped_for_this_unit(ctx):
    assert not step_01_bind.done(ctx)
    _json(ctx.book_dir / "refs" / "refs.json", {"chapter": 4, "refs": []})
    assert step_01_bind.done(ctx)
    _json(ctx.book_dir / "refs" / "refs.json", {"chapter": 3, "refs": []})
    assert not step_01_bind.done(ctx)


def test_bind_refuses_without_a_cast_and_launches_cast_rows_with_one(ctx):
    with pytest.raises(SystemExit, match="usage"):
        step_01_bind.run(ctx)
    ctx.extra = ["--cast=a,b=Bee:f"]
    assert not step_01_bind.done(ctx)
    step_01_bind.run(ctx)
    assert ctx.launched == [["scripts/refs/cast_rows.py", CODEX, "4", "a", "b=Bee:f"]]


# ---- 03 places ----------------------------------------------------------------

def test_places_names_one_picture_per_located_setup(ctx):
    pics = step_03_places.pictures(ctx.book_dir, PLAN)
    assert pics == [ctx.book_dir / "refs" / "locations" / "yard" / "wide_establishing.png"]


def test_places_is_done_when_every_picture_exists(ctx):
    assert not step_03_places.done(ctx)
    _png(ctx.book_dir / "refs" / "locations" / "yard" / "wide_establishing.png")
    assert step_03_places.done(ctx)


def test_places_launches_the_drawer_with_the_flags(ctx):
    ctx.extra = ['--new=yard="The yard"']
    step_03_places.run(ctx)
    assert ctx.launched == [["scripts/refs/places.py", CODEX, "4", "--draw", '--new=yard="The yard"']]


# ---- 04 record ----------------------------------------------------------------

def test_record_is_done_when_every_line_is_measured_and_spread_checked(ctx):
    assert not step_04_record.done(ctx)
    _json(ctx.home / "audio" / "lines" / "lines.json", [{"index": 1, "seconds": 1.0}])
    _json(ctx.home / "review" / "speaker_check.json", {})
    assert not step_04_record.done(ctx)
    _json(ctx.home / "audio" / "lines" / "lines.json", [{"index": 1}, {"index": 2}])
    assert step_04_record.done(ctx)


def test_record_launches_say_lines_then_speaker_check(ctx):
    ctx.extra = ["--redo=2"]
    step_04_record.run(ctx)
    assert ctx.launched == [["scripts/episode/say_lines.py", CODEX, "4", "--redo=2"],
                            ["scripts/episode/speaker_check.py", CODEX, "4"]]


# ---- 05 timeline --------------------------------------------------------------

def test_timeline_is_done_only_with_a_fresh_timeline(ctx, monkeypatch):
    assert not step_05_timeline.done(ctx)        # no plan the contract accepts, no timeline
    monkeypatch.setattr(step_05_timeline.episode_home, "load_plan", lambda b, n: object())

    def stale(b, n, ep):
        raise SystemExit("stale")
    monkeypatch.setattr(step_05_timeline.episode_home, "load_placed", stale)
    assert not step_05_timeline.done(ctx)
    monkeypatch.setattr(step_05_timeline.episode_home, "load_placed", lambda b, n, ep: {})
    assert step_05_timeline.done(ctx)


def test_timeline_launches_respot_then_timeline(ctx):
    step_05_timeline.run(ctx)
    assert ctx.launched == [["scripts/episode/respot.py", CODEX, "4"],
                            ["scripts/episode/timeline.py", CODEX, "4"]]


# ---- 06 prompts ---------------------------------------------------------------

def test_prompts_are_done_when_newer_than_the_plan_and_the_measured_lines(ctx):
    assert not step_06_prompts.done(ctx)
    lines = _json(ctx.home / "audio" / "lines" / "lines.json", [])
    prompts = _json(ctx.home / "takes" / "r2v" / "prompts.json", [])
    assert step_06_prompts.done(ctx)
    import os
    os.utime(prompts, (0, 0))
    assert not step_06_prompts.done(ctx) and lines.exists()


def test_prompts_launch_the_lint_then_the_last_frame_check(ctx):
    step_06_prompts.run(ctx)
    assert ctx.launched == [["scripts/episode/takes_r2v.py", CODEX, "4", "--from-refs", "--prompts"],
                            ["scripts/episode/no_last_frame.py", CODEX, "4"]]


# ---- 07 board -----------------------------------------------------------------

def test_board_parks_the_unit_without_a_layout(ctx):
    assert not step_07_board.done(ctx)
    with pytest.raises(Escalation) as got:
        step_07_board.run(ctx)
    assert got.value.gate == "PLAN" and got.value.verdict == "storyboard/layout.json"
    assert ctx.launched == []


def test_board_draws_every_laid_out_grid_and_is_done_when_they_exist(ctx):
    _json(ctx.home / "storyboard" / "layout.json",
          [{"setup": "yard", "cols": 2, "rows": 1}, {"setup": "room", "cols": 1, "rows": 1, "tag": "b"}])
    step_07_board.run(ctx)
    assert ctx.launched == [["scripts/episode/grids.py", CODEX, "4", "yard", "2", "1"],
                            ["scripts/episode/grids.py", CODEX, "4", "room", "1", "1", "b"]]
    assert not step_07_board.done(ctx)
    _png(ctx.home / "storyboard" / "grids" / "ep04_grid_yard_2x1.png")
    _png(ctx.home / "storyboard" / "grids" / "ep04_grid_room_1x1_b.png")
    assert step_07_board.done(ctx)


def test_board_redraws_an_existing_grid_only_when_a_flag_asks(ctx):
    _json(ctx.home / "storyboard" / "layout.json", [{"setup": "yard", "cols": 2, "rows": 1}])
    _png(ctx.home / "storyboard" / "grids" / "ep04_grid_yard_2x1.png")
    step_07_board.run(ctx)
    assert ctx.launched == []
    ctx.extra = ["--seed-bump=1"]
    step_07_board.run(ctx)
    assert ctx.launched == [["scripts/episode/grids.py", CODEX, "4", "yard", "2", "1", "--seed-bump=1"]]


# ---- 08 panels ----------------------------------------------------------------

def _panels(ctx) -> list[Path]:
    return [_png(ctx.home / "storyboard" / f"shot_{i:02d}.png", i * 20) for i in (1, 2)]


def _verdicts(ctx) -> None:
    rows = [{"shot": 1, "passed": True}, {"shot": 2, "passed": True}]
    _json(ctx.home / "storyboard" / "panel_dq.json", rows)
    _json(ctx.home / "storyboard" / "panel_content.json", rows)


def test_panels_runs_the_cutter_and_both_gates_then_asks_for_the_eye(ctx):
    panels = _panels(ctx)
    with pytest.raises(Escalation) as got:
        step_08_panels.run(ctx)
    assert ctx.launched == [["scripts/episode/panels.py", CODEX, "4"],
                            ["scripts/episode/panel_check.py", CODEX, "4"],
                            ["scripts/episode/panel_content_check.py", CODEX, "4"]]
    assert got.value.gate == "EYE"
    assert got.value.verdict == f"storyboard/eye_{eye_verdict.fingerprint(panels)}.json"
    assert (ctx.home / "storyboard" / "contact.png").exists()


def test_panels_skips_the_vision_gate_when_its_verdict_is_current(ctx):
    _panels(ctx)
    _verdicts(ctx)
    with pytest.raises(Escalation):
        step_08_panels.run(ctx)
    assert [c[0] for c in ctx.launched] == ["scripts/episode/panels.py", "scripts/episode/panel_check.py"]


def test_panels_is_done_with_both_verdicts_the_sheet_and_a_signed_eye(ctx):
    panels = _panels(ctx)
    assert not step_08_panels.done(ctx)
    _verdicts(ctx)
    _png(ctx.home / "storyboard" / "contact.png")
    assert not step_08_panels.done(ctx)
    eye_verdict.sign(ctx.home / "storyboard", panels, "pass", "clean")
    assert step_08_panels.done(ctx)
    assert step_08_panels.panel_refusals(ctx.home) == []


def test_panels_refuses_when_the_cutter_left_nothing(ctx):
    with pytest.raises(SystemExit, match="no panels"):
        step_08_panels.run(ctx)


# ---- 09 shoot -----------------------------------------------------------------

def test_shoot_launches_the_chain_with_the_exact_argv_then_asks_for_the_eye(ctx):
    panels = _panels(ctx)
    _verdicts(ctx)
    eye_verdict.sign(ctx.home / "storyboard", panels, "pass", "clean")
    take = ctx.home / "takes" / "r2v" / "T01.mp4"
    take.parent.mkdir(parents=True)
    take.write_bytes(b"take")
    ctx.extra = ["--retake=1", "--why=froze"]
    with pytest.raises(Escalation) as got:
        step_09_shoot.run(ctx)
    assert ctx.launched == [
        ["scripts/episode/takes_r2v.py", CODEX, "4", "--from-refs", "--no-ends", "--approved=render",
         "--retake=1", "--why=froze"],
        ["scripts/episode/take_dq.py", CODEX, "4"],
        ["scripts/episode/take_content_check.py", CODEX, "4"],
        ["scripts/episode/take_strip.py", CODEX, "4"]]
    assert got.value.verdict == f"takes/r2v/eye_{eye_verdict.fingerprint([take])}.json"


def test_shoot_is_done_when_every_kept_take_is_judged_twice_and_signed(ctx):
    room = ctx.home / "takes" / "r2v"
    room.mkdir(parents=True)
    take = room / "T01.mp4"
    take.write_bytes(b"take")
    (room / "T01_fail1.mp4").write_bytes(b"lost")
    assert step_09_shoot.takes_of(room) == [take]
    assert not step_09_shoot.done(ctx)
    _json(room / "T01.dq.json", {})
    _json(room / "T01.content.json", {})
    assert not step_09_shoot.done(ctx)
    eye_verdict.sign(room, [take], "pass", "moves")
    assert step_09_shoot.done(ctx)


# ---- 10 edit ------------------------------------------------------------------

def test_edit_reads_the_engine_flag_and_defaults_to_the_house_engine():
    assert step_10_edit.engine_of([]) == "r2v"
    assert step_10_edit.engine_flags(["--bed=x", "--engine=i2v"]) == ["--engine=i2v", "--bed=x"]


def test_edit_launches_the_title_then_assemble_with_the_engine(ctx):
    step_10_edit.run(ctx)
    assert ctx.launched == [["scripts/episode/series_title.py", CODEX, "4"],
                            ["scripts/episode/assemble.py", CODEX, "4", "--engine=r2v"]]


def test_edit_skips_a_title_card_already_animated_and_is_done_with_a_master(ctx):
    _png(ctx.book_dir / "title" / "ep04.png")
    (ctx.book_dir / "title" / "ep04.mp4").write_bytes(b"card")
    step_10_edit.run(ctx)
    assert ctx.launched == [["scripts/episode/assemble.py", CODEX, "4", "--engine=r2v"]]
    assert not step_10_edit.done(ctx)
    episode_home.master_path(ctx.book_dir, 4, "r2v").write_bytes(b"cut")
    assert step_10_edit.done(ctx)


# ---- 11 qc --------------------------------------------------------------------

def _master(ctx, passed=True):
    master = episode_home.master_path(ctx.book_dir, 4, "r2v")
    master.write_bytes(b"the cut")
    _json(ctx.home / "qc_r2v.json", {"passed": passed, "sha8": yp.sha8(master), "seconds": 150.0})
    return master


def test_qc_names_the_pair_the_publish_ladder_reads(ctx):
    master, qc = step_11_qc.pair(ctx.home, "r2v")
    assert master == ctx.home / "cut" / "master_r2v.mp4" and qc == ctx.home / "qc_r2v.json"


def test_qc_launches_qc_then_parks_on_the_master_eye(ctx):
    ctx.launch = lambda cmd: ctx.launched.append(cmd[1:]) or _master(ctx) and 0
    with pytest.raises(Escalation) as got:
        step_11_qc.run(ctx)
    assert ctx.launched == [["scripts/episode/qc.py", CODEX, "4", "--engine=r2v"]]
    sha8 = yp.sha8(episode_home.master_path(ctx.book_dir, 4, "r2v"))
    assert got.value.gate == "MASTER" and got.value.verdict == f"review/eye_{sha8}.json"


def test_qc_refuses_a_failed_report(ctx):
    ctx.launch = lambda cmd: _master(ctx, passed=False) and 0
    with pytest.raises(SystemExit, match="FAIL"):
        step_11_qc.run(ctx)


def test_qc_is_done_with_a_passed_report_on_these_bytes_and_a_filled_rubric(ctx):
    from scripts.episode import eye_review as er
    master = _master(ctx)
    assert not step_11_qc.done(ctx)
    sha8 = yp.sha8(master)
    rubric = er.blank_rubric(sha8, master.name, "c.png", 5.0, 30)
    _json(er.rubric_path(ctx.home, sha8), rubric)
    assert not step_11_qc.done(ctx)          # blank: unanswered
    for field, _q in er.RUBRIC:
        rubric["rubric"][field]["answer"] = "y"
    rubric["notes"] = "watched"
    _json(er.rubric_path(ctx.home, sha8), rubric)
    assert step_11_qc.done(ctx)
    master.write_bytes(b"re-cut")
    assert not step_11_qc.done(ctx)          # the report is about other bytes


# ---- 12 deliver ---------------------------------------------------------------

def test_deliver_writes_the_manifest_and_prints_the_master_first(ctx, capsys, monkeypatch):
    monkeypatch.setattr(episode_home, "LIBRARY", ctx.book_dir.parent)
    master = _master(ctx)
    ctx.tracker.event("11", "completed")
    step_12_deliver.run(ctx)
    out = capsys.readouterr().out.splitlines()
    assert out[0] == str(master.resolve())
    doc = episode_home.read_json(ctx.home / "manifest.json")
    assert doc["master"] == "book/episodes/ep04/cut/master_r2v.mp4"
    assert doc["qc"]["sha8"] == yp.sha8(master) and doc["qc"]["passed"] is True
    assert doc["steps"] == {"11": "completed"}
    assert doc["timing"] == {"total_seconds": 0, "runs": 0, "by_stage": {}}
    assert step_12_deliver.done(ctx)


def test_deliver_is_not_done_before_a_passed_qc(ctx):
    assert not step_12_deliver.done(ctx)
    with pytest.raises(SystemExit):
        step_12_deliver.run(ctx)


def test_timing_sums_the_clock_rows(ctx):
    from studio import episode_clock
    episode_clock.stamp(ctx.book_dir, 4, "takes", 0, 10)
    episode_clock.stamp(ctx.book_dir, 4, "takes", 20, 25)
    episode_clock.stamp(ctx.book_dir, 4, "qc", 30, 31)
    assert step_12_deliver.timing(ctx.book_dir, 4) == {"total_seconds": 16.0, "runs": 3,
                                                       "by_stage": {"takes": 15.0, "qc": 1.0}}
