"""F5 (ep10 synthesis): a norm is a function of the run's own conditions.

A constant norm of 1200 s for take_dq hid a 1095 s run that was five times its
warm time (it shared the queue with a retake); a constant 900 s for lines hid
an 806 s FAIL. A norm that knows the count and the frames does not.
"""
import pytest

from studio import episode_clock as ck


def test_a_takes_norm_scales_with_the_frames():
    assert ck.norm_for("takes", frames=[141]) == pytest.approx(300 + 60 + 1.2 * 141)
    assert ck.norm_for("takes", frames=[141, 209]) == pytest.approx(300 + 2 * 60 + 1.2 * 350)


def test_the_takes_norm_without_frames_is_thirty_takes_of_141():
    assert ck.norm_for("takes") == pytest.approx(300 + 30 * (60 + 1.2 * 141))


def test_a_take_dq_norm_scales_with_the_count():
    assert ck.norm_for("take_dq", count=1) == 38
    assert ck.norm_for("take_dq", count=30) == 270


def test_qc_and_lines_scale_with_the_line_count_and_title_is_fixed():
    assert ck.norm_for("qc", count=30) == 210
    assert ck.norm_for("lines", count=30) == 600
    assert ck.norm_for("title") == 140


def test_a_stage_with_no_condition_falls_back_to_the_table():
    assert ck.norm_for("respot") == ck.NORMS["respot"]
    assert ck.norm_for("qc") == ck.NORMS["qc"]
    assert ck.norm_for("plan") == 0


def test_a_failed_row_is_slow_whatever_its_seconds():
    assert ck.slow({"stage": "lines", "seconds": 0.2, "ok": False})
    assert not ck.slow({"stage": "lines", "seconds": 0.2, "ok": True})


def test_slow_takes_the_condition_scaled_norm():
    row = {"stage": "take_dq", "seconds": 1095, "ok": True}
    assert not ck.slow(row), "the constant 1200 hid it"
    assert ck.slow(row, norm=ck.norm_for("take_dq", count=30))


def test_the_note_names_the_takes_a_run_covered():
    assert ck.indices_in("--retake=3,4,15 --approved") == [3, 4, 15]
    assert ck.indices_in("3 4 5 15 20 29") == [3, 4, 5, 15, 20, 29]
    assert ck.indices_in("2 --attempts") == [2]
    assert ck.indices_in("--engine=r2v") == []


def test_a_row_norm_is_for_the_takes_the_row_ran():
    """Takes are keyed by their first SHOT index (ep10 has no T19, T23, T30,
    T32), so a retake is looked up by index, never by position."""
    cond = {"frames": {0: 141, 1: 209, 21: 192}, "lines": 30}
    full = {"stage": "takes", "note": "--approved", "seconds": 1}
    two = {"stage": "takes", "note": "--retake=1,21 --approved", "seconds": 1}
    assert ck.row_norm(full, cond) == pytest.approx(300 + 3 * 60 + 1.2 * 542)
    assert ck.row_norm(two, cond) == pytest.approx(300 + 2 * 60 + 1.2 * 401)
    assert ck.row_norm({"stage": "take_dq", "note": "15", "seconds": 1}, cond) == 38
    assert ck.row_norm({"stage": "qc", "note": "", "seconds": 1}, cond) == 210


def _row(stage, started, ended, ok=True, note=""):
    return {"stage": stage, "started": f"2026-09-16T{started}", "ended": f"2026-09-16T{ended}",
            "seconds": 1.0, "ok": ok, "note": note}


def test_an_overlapping_pair_is_contended():
    dq = _row("take_dq", "20:20:47", "20:39:02")
    takes = _row("takes", "20:23:43", "20:37:56")
    after = _row("assemble", "20:42:20", "20:43:46")
    assert ck.contended(dq, [dq, takes, after])
    assert ck.contended(takes, [dq, takes, after])
    assert not ck.contended(after, [dq, takes, after])


def test_a_stage_that_starts_the_second_another_ends_is_not_contended():
    title = _row("title", "18:55:29", "19:01:57")
    assemble = _row("assemble", "19:01:57", "19:07:00")
    assert not ck.contended(assemble, [title, assemble])


def test_a_refusal_row_is_not_a_contention():
    takes = _row("takes", "20:23:43", "20:37:56")
    refused = _row("take_dq", "20:25:00", "20:25:00", ok=False, note="refused: queue busy")
    refused["seconds"] = 0.0
    assert not ck.contended(refused, [takes, refused])
    assert not ck.contended(takes, [takes, refused])


@pytest.fixture
def book(tmp_path, monkeypatch):
    monkeypatch.setattr(ck.episode_home, "home", lambda b, n: tmp_path / f"ep{n:02d}")
    return tmp_path


def test_the_report_prints_the_scaled_norm_and_marks_contended_rows(book):
    home = book / "ep10"
    home.mkdir()
    (home / "placed.json").write_text('{"lines": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}', encoding="utf-8")
    ck.stamp(book, 10, "take_dq", 1000.0, 1000.0 + 1095, note="")
    ck.stamp(book, 10, "takes", 1180.0, 1180.0 + 853, note="--retake=2,3 --approved")
    ck.stamp(book, 10, "qc", 3000.0, 3200.0)
    said = ck.report(book, 10)
    assert "CONTENDED" in said
    assert "110" in said, "qc norm for ten lines is 60 + 5*10"
    lines = {l.split()[0]: l for l in said.splitlines()}
    assert "SLOW" in lines["take_dq"] and "CONTENDED" in lines["take_dq"]
    assert "CONTENDED" not in lines["qc"]


def test_conditions_are_read_off_the_episodes_own_files(book, monkeypatch):
    home = book / "ep10"
    (home / "takes" / "r2v").mkdir(parents=True)
    (home / "placed.json").write_text('{"lines": [1, 2]}', encoding="utf-8")
    (home / "takes" / "r2v" / "shots.json").write_text(
        '[{"index": 0, "frames": 141}, {"index": 2, "frames": 209}]', encoding="utf-8")
    assert ck.conditions(book, 10) == {"frames": {0: 141, 2: 209}, "lines": 2}
    assert ck.conditions(book, 11) == {}
