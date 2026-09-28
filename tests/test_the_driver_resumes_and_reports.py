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
    runs, told = iter(["DEFERRED: budget", "DEFERRED: budget", "=== EPISODE completed | x ==="]), []
    code = drive.drive(run=lambda: next(runs), notify=told.append, max_runs=5)
    assert code == 0 and len(told) == 1 and "completed" in told[0]


def test_a_refusal_stops_and_tells_the_owner_its_last_lines():
    told = []
    code = drive.drive(run=lambda: "step 06\nSystemExit: REFUSED: the plan fails", notify=told.append, max_runs=5)
    assert code == 1 and "REFUSED" in told[0]


def test_resumes_are_capped():
    told = []
    code = drive.drive(run=lambda: "DEFERRED: budget", notify=told.append, max_runs=3)
    assert code == 1 and "3 runs" in told[-1]


def test_a_silent_log_is_reported_once():
    assert drive.silent(last_growth=0.0, now=1300.0, told=False)
    assert not drive.silent(last_growth=0.0, now=1300.0, told=True)
    assert not drive.silent(last_growth=0.0, now=600.0, told=False)
