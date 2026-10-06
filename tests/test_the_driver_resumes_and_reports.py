"""The episode driver: one launcher that resumes, reports, and freezes the code.

Ten-agent debate 2026-09-27 (plan fixes #1 and #2): ep13 took 29 launches and
8 kills; a DEFERRED run sat dead ~90 min until the owner asked "why did you
stop??"; five commits landed between masters of a live episode.  The driver
runs episode.py, resumes a DEFERRED run, tells the owner on a stop or a long
silence, and refuses to start on a dirty tree, recording the SHA it ran.
"""
from studio import episode_drive as drive


def test_a_run_is_read_by_how_it_ended():
    assert drive.outcome("... === EPISODE completed | x ===") == "completed"
    assert drive.outcome("RuntimeError: DEFERRED: EYE_TAKES needs 528 s") == "deferred"
    assert drive.outcome("SystemExit: REFUSED: qc FAIL in qc_r2v.json") == "refused"
    assert drive.outcome("Traceback ... KeyError: 0") == "failed"


def test_a_dirty_tree_is_refused_and_library_is_not_the_tree():
    assert drive.dirty(" M studio/comfy.py\n")
    assert not drive.dirty("")
    assert not drive.dirty("?? library/x/ep14/plan.json\n")


def test_a_deferred_run_is_resumed_until_it_completes():
    runs, told = iter(["DEFERRED: EYE_TAKES needs 528 s", "DEFERRED: EYE_TAKES needs 528 s", "=== EPISODE completed | x ==="]), []
    code = drive.drive(run=lambda: next(runs), notify=told.append, max_runs=5)
    assert code == 0 and len(told) == 1 and "completed" in told[0]


def test_a_refusal_stops_and_tells_the_owner_its_last_lines():
    told = []
    code = drive.drive(run=lambda: "step 06\nSystemExit: REFUSED: the plan fails", notify=told.append, max_runs=5)
    assert code == 1 and "REFUSED" in told[0]


def test_resumes_are_capped():
    told = []
    code = drive.drive(run=lambda: "DEFERRED: EYE_TAKES needs 528 s", notify=told.append, max_runs=3)
    assert code == 1 and "3 runs" in told[-1]


def test_a_silent_log_is_reported_once():
    assert drive.silent(last_growth=0.0, now=1300.0, told=False)
    assert not drive.silent(last_growth=0.0, now=1300.0, told=True)
    assert not drive.silent(last_growth=0.0, now=600.0, told=False)


def test_a_plan_deferral_is_not_resumed():
    """ep14 (2026-09-28): the driver resumed six 'DEFERRED PLAN' runs (~2.5 h);
    a plan deferral waits on a plan fix, not on budget, so a rerun repeats it."""
    assert drive.outcome("DEFERRED PLAN | x | battery at plan: CONTRACT : ... -> defer") == "refused"
    assert drive.outcome("RuntimeError: DEFERRED: EYE_TAKES needs 528 s for its rung") == "deferred"


# ---- the autopilot's words (decision 2026-10-06): the ep19 tail -------------------------

EP19_TAIL = ('  File "D:\\x\\studio\\llm.py", line 148, in guard_spend\n'
             '    raise OverBudget(f"episode {_SPEND[\'unit\']} has spent ${spent:.2f} of its ${cap:.2f} "\n'
             "studio.llm.OverBudget: episode ep19 has spent $3.10 of its $3.00 ceiling; "
             "this call would cross it, so it was not sent")
OWNER_LINE = "OWNER G-STANDING | book ep19 | the book has no standing | sign: publish/standing.json"


def test_the_money_wall_and_an_owner_gate_are_read_by_name():
    """ep19 (2026-10-06, launch04): the $3 wall's stop read as `failed`, the
    same word as a crash, and the only evidence was the traceback's prose."""
    assert drive.outcome(EP19_TAIL) == "overbudget"
    assert drive.outcome("step 13\n" + OWNER_LINE) == "escalated"
    # the caught form (plan_ladder): the wall's own line AND the deferral it caused; money is the cause
    assert drive.outcome("studio.llm.OverBudget: episode ep19 has spent $3.10\n"
                         "DEFERRED PLAN | x | MONEY: ... -> defer") == "overbudget"
    assert drive.outcome("Traceback ... KeyError: 0") == "failed"


def test_the_wall_and_an_owner_gate_stop_and_tell_like_a_refusal():
    for log, word in ((EP19_TAIL, "OverBudget"), (OWNER_LINE, "OWNER G-STANDING")):
        told = []
        assert drive.drive(run=lambda: log, notify=told.append, max_runs=5) == 1
        assert len(told) == 1 and word in told[0]


def test_the_error_class_is_read_off_the_last_class_line_never_the_prose():
    assert drive.error_class(EP19_TAIL) == "studio.llm.OverBudget"
    assert drive.error_class("Traceback (most recent call last):\n  File x\nKeyError: 0") == "KeyError"
    assert drive.error_class("x\nSystemExit: REFUSED: qc FAIL in qc_r2v.json") == "SystemExit"
    assert drive.error_class("ValueError: a\nlater\nRuntimeError: DEFERRED: x") == "RuntimeError"
    assert drive.error_class("=== EPISODE completed | x ===") is None
    assert drive.error_class("a note: with a colon\nwarning: skipped") is None


def test_the_run_row_carries_the_error_class_only_when_there_is_one():
    from scripts.episode import drive as launcher
    row = launcher.run_row(2, "abc123", EP19_TAIL)
    assert row == {"event": "run", "n": 2, "sha": "abc123", "outcome": "overbudget",
                   "error": "studio.llm.OverBudget"}
    assert "error" not in launcher.run_row(1, "abc123", "=== EPISODE completed | x ===")


def test_drive_quiet_keeps_telegram_for_the_supervisor(monkeypatch, capsys):
    """DRIVE_QUIET=1 (autopilot 2026-10-06): the drive prints, the supervisor
    owns the owner's channel -- PUBLISHED, PARKED, SERIES_COMPLETE, once each."""
    from scripts.episode import drive as launcher
    sent = []
    monkeypatch.setattr(launcher.subprocess, "run", lambda *a, **k: sent.append(a[0]))
    monkeypatch.setenv("DRIVE_QUIET", "1")
    launcher.notify("ep20 PUBLISHED")
    assert sent == [] and "[drive] ep20 PUBLISHED" in capsys.readouterr().out
    monkeypatch.delenv("DRIVE_QUIET")
    launcher.notify("ep20 PUBLISHED")
    assert len(sent) == 1 and "notify_bench.py" in " ".join(map(str, sent[0]))
    assert launcher.quiet({"DRIVE_QUIET": "1"}) and not launcher.quiet({}) and not launcher.quiet({"DRIVE_QUIET": "0"})
