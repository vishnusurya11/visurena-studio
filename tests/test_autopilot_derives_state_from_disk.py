"""The autopilot's state is a pure function of disk (decision 2026-10-06,
ops engineer §3): every row of the state table is one case here, and the
invariant that silence is never a state is run over a product of signals.

ep19 (2026-10-06) sat for hours between four launches because the layer
above drive.py was a Claude session that ended its turn.  Nothing here
reads a file; `Signals` is built by hand the way the supervisor builds it."""
from __future__ import annotations

import itertools
from dataclasses import replace

import pytest

from studio import autopilot as ap
from studio.autopilot import Derived, Signals, State
from studio.command_center.procs import ProcInfo
from studio.run_budget import EPISODE_CEILING_SECONDS

SHA = "2a50fc4f5a73943bf9211f999e66accade6260d3"
OVER_BUDGET_TAIL = (
    '  File "D:\\x\\studio\\llm.py", line 148, in guard_spend\n'
    '    raise OverBudget(f"episode {_SPEND[\'unit\']} has spent ${spent:.2f} of its ${cap:.2f} "\n'
    "studio.llm.OverBudget: episode ep19 has spent $3.10 of its $3.00 ceiling; "
    "this call would cross it, so it was not sent")


def rows(*events: tuple) -> list[dict]:
    """drive.jsonl rows from ('start',) / ('run', outcome) / ('end', code) tuples."""
    out = []
    for ev in events:
        if ev[0] == "start":
            out.append({"event": "start", "sha": SHA})
        elif ev[0] == "run":
            out.append({"event": "run", "n": 1, "sha": SHA, "outcome": ev[1]})
        else:
            out.append({"event": "end", "code": ev[1], "sha": SHA})
    return out


def signals(**kw) -> Signals:
    base = Signals(drive_rows=rows(("start",), ("run", "completed"), ("end", 0)), exit_code=None,
                   lock=None, proc_alive=False, uploads_rows=[], parked_rows=[],
                   home_files={"plan.json"}, log_tail="=== EPISODE completed | ep20 ===",
                   porcelain="", engine_up=True, clock_spent_s=0.0, brain_attempts=0,
                   brain_verdict=None, paused=False, head_sha=SHA, media_spent_usd=0.0)
    return replace(base, **kw)


PUBLIC = [{"episode": 20, "privacy": "public", "video_id": "x", "sha8": SHA[:8]}]
PARKED = [{"episode": 20, "reason": "over_budget"}]
TABLE = [
    ("published row", signals(uploads_rows=PUBLIC), State.PUBLISHED, "published"),
    ("parked row", signals(parked_rows=PARKED, uploads_rows=[]), State.PARKED, "parked: over_budget"),
    ("dirty tree before launch", signals(drive_rows=[], porcelain=" M studio/comfy.py\n"), State.WAIT_TREE, "tree_dirty"),
    ("clean tree, no lock, engine up", signals(drive_rows=[]), State.IDLE, "launch"),
    ("engine down", signals(drive_rows=[], engine_up=False), State.IDLE, "launch (engine down)"),
    ("pid alive", signals(proc_alive=True, drive_rows=rows(("start",))), State.RUNNING, "drive alive"),
    ("end 0 + public row", signals(uploads_rows=PUBLIC), State.PUBLISHED, "published"),
    ("end 0, no public row", signals(), State.NEEDS_BRAIN, "no_upload_row"),
    ("end 2 dirty tree", signals(drive_rows=rows(("start",), ("end", 2)),
                                 log_tail="ep20: REFUSED to start: the working tree is dirty; commit the code first (fix #2)"),
     State.WAIT_TREE, "tree_dirty"),
    ("end 2 title card", signals(drive_rows=rows(("start",), ("end", 2)),
                                 log_tail="ep20: REFUSED: ep20's title card could not be baked (titles_batch)"),
     State.NEEDS_BRAIN, "title_card"),
    ("end 1 refused + deferred file", signals(drive_rows=rows(("start",), ("run", "refused"), ("end", 1)),
                                              home_files={"plan.json", "plan.deferred.json"},
                                              log_tail="DEFERRED PLAN | ep20 | battery at plan: CONTRACT -> defer | aside: episodes/ep20/plan.deferred.json"),
     State.IDLE, "plan_deferred"),
    ("end 1 over budget, signed plan", signals(drive_rows=rows(("start",), ("run", "failed"), ("end", 1)),
                                               log_tail=OVER_BUDGET_TAIL),
     State.IDLE, "over_budget_signed_plan"),
    ("end 1 over budget, unsigned plan", signals(drive_rows=rows(("start",), ("run", "failed"), ("end", 1)),
                                                 home_files={"plan.json", "plan.deferred.json"},
                                                 log_tail=OVER_BUDGET_TAIL),
     State.PARKED, "over_budget"),
    ("end 1 dead clock", signals(drive_rows=rows(("start",), ("run", "refused"), ("end", 1)),
                                 clock_spent_s=EPISODE_CEILING_SECONDS, log_tail="REFUSED: qc FAIL"),
     State.PARKED, "clock_spent"),
    ("end 1 other traceback", signals(drive_rows=rows(("start",), ("run", "failed"), ("end", 1)),
                                      log_tail="Traceback (most recent call last):\n  ...\nKeyError: 0"),
     State.NEEDS_BRAIN, "failed: KeyError: 0"),
    ("end 1 refused, no deferred file", signals(drive_rows=rows(("start",), ("run", "refused"), ("end", 1)),
                                                log_tail="SystemExit: REFUSED: qc FAIL in qc_r2v.json for these exact bytes"),
     State.NEEDS_BRAIN, "qc_fail"),
    ("crash, no end row", signals(drive_rows=rows(("start",))), State.IDLE, "relaunch"),
    ("three crashes", signals(drive_rows=rows(("start",), ("start",), ("start",))), State.NEEDS_BRAIN, "crash_loop"),
    ("brain exhausted", signals(brain_attempts=3), State.PARKED, "brain_exhausted"),
    ("brain relaunch, clean, head matches", signals(brain_verdict={"verdict": "relaunch", "commit": SHA}),
     State.IDLE, "brain_relaunch"),
    ("brain park", signals(brain_verdict={"verdict": "park", "why": "a judge bug"}, brain_attempts=1),
     State.NEEDS_BRAIN, "brain: park"),
    ("paused", signals(paused=True), State.PAUSED, "paused"),
    ("held", signals(drive_rows=rows(("start",), ("run", "failed"), ("end", 1)),
                     log_tail="SystemExit: HELD: RENDER_HOLD is set; ep20 stops before step 09"),
     State.PAUSED, "held"),
    ("escalated to the owner", signals(drive_rows=rows(("start",), ("run", "failed"), ("end", 1)),
                                       log_tail="OWNER G-STANDING | ep20 | publish needs standing | sign: publish/standing.json"),
     State.PARKED, "escalated: G-STANDING"),
]


@pytest.mark.parametrize("label,sig,state,reason", TABLE, ids=[t[0] for t in TABLE])
def test_autopilot_derives_state_from_disk(label, sig, state, reason):
    got = ap.derive(sig, 20)
    assert isinstance(got, Derived)
    assert (got.state, got.reason) == (state, reason), label


def test_no_silent_stop():
    """The invariant: whatever the exit code, the outcome word and the files
    on disk, derive() names a state in the enum with a non-empty reason."""
    tails = ["=== EPISODE completed | x ===", "DEFERRED PLAN | x | y | aside: a", "REFUSED: qc FAIL",
             OVER_BUDGET_TAIL, "Traceback\nKeyError: 0", "", "HELD: x", "OWNER G-STANDING | x | y | sign: z",
             "REFUSED to start: the working tree is dirty", "title card could not be baked"]
    files = [set(), {"plan.json"}, {"plan.json", "plan.deferred.json"}, {"plan.json", "placed.json", "takes"}]
    for code, outcome, home, tail in itertools.product([0, 1, 2, None], ["completed", "refused", "failed"], files, tails):
        drive = rows(("start",), ("run", outcome)) + (rows(("end", code)) if code is not None else [])
        got = ap.derive(signals(drive_rows=drive, home_files=home, log_tail=tail), 20)
        assert got.state in State and got.reason, (code, outcome, home, tail)
        assert isinstance(got.packet, dict)


def test_a_stale_lock_is_recovered():
    """A lock whose pid is gone, or belongs to another command line, or to a
    process started after the lock, is stale (reboot: the lock survives, the
    drive does not)."""
    codex, lock = "20260827135508_the-war-of-the-worlds", {"drive_pid": 500, "started": 1000.0}
    live = [ProcInfo(500, 990.0, f'uv run python scripts/episode/drive.py {codex} 20')]
    other = [ProcInfo(500, 990.0, "python -m http.server")]
    reused = [ProcInfo(500, 5000.0, f'uv run python scripts/episode/drive.py {codex} 20')]
    assert ap.stale_lock(lock, [], codex, 20)
    assert ap.stale_lock(lock, other, codex, 20)
    assert ap.stale_lock(lock, reused, codex, 20)
    assert not ap.stale_lock(lock, live, codex, 20)
    assert not ap.stale_lock(None, [], codex, 20)


def test_a_crash_without_an_end_row_relaunches_then_asks_the_brain_after_three():
    one = rows(("start",), ("run", "refused"), ("end", 1), ("start",))
    assert ap.crashes(one) == 1
    assert ap.derive(signals(drive_rows=one), 20).state is State.IDLE
    three = rows(("start",), ("start",), ("end", 1), ("start",), ("start",))
    assert ap.crashes(three) == 3
    got = ap.derive(signals(drive_rows=three), 20)
    assert (got.state, got.reason) == (State.NEEDS_BRAIN, "crash_loop")
    assert ap.crashes([]) == 0


def test_over_budget_relaunches_a_signed_plan_once_and_parks_an_unsigned_one():
    """ep19: plan.json + plan.deferred.json (unsigned) and $3.10 of $3.00 ->
    PARKED on the first tick; a signed plan resumes once past step 02 since
    the rest of the chain is $0 local."""
    first = rows(("start",), ("run", "failed"), ("end", 1))
    got = ap.derive(signals(drive_rows=first, log_tail=OVER_BUDGET_TAIL, media_spent_usd=3.10), 19)
    assert (got.state, got.reason) == (State.IDLE, "over_budget_signed_plan")
    twice = first + first
    got = ap.derive(signals(drive_rows=twice, log_tail=OVER_BUDGET_TAIL), 19)
    assert (got.state, got.reason) == (State.PARKED, "over_budget")
    got = ap.derive(signals(drive_rows=first, log_tail=OVER_BUDGET_TAIL,
                            home_files={"plan.json", "plan.deferred.json"}), 19)
    assert (got.state, got.reason) == (State.PARKED, "over_budget")
    assert got.packet["episode"] == "ep19"


def test_a_dead_clock_parks_without_a_brain():
    """A brain cannot buy GPU hours: 18 000 s spent is PARKED, never NEEDS_BRAIN."""
    for tail in ["Traceback\nKeyError: 0", "DEFERRED PLAN | x | y | aside: a", ""]:
        for drive in [rows(("start",), ("run", "failed"), ("end", 1)), rows(("start",))]:
            got = ap.derive(signals(drive_rows=drive, log_tail=tail, clock_spent_s=EPISODE_CEILING_SECONDS + 1), 20)
            assert (got.state, got.reason) == (State.PARKED, "clock_spent"), tail
    got = ap.derive(signals(drive_rows=rows(("start",)), clock_spent_s=EPISODE_CEILING_SECONDS - 1), 20)
    assert got.state is State.IDLE


def test_the_brain_is_trusted_by_its_file_and_git_not_its_prose():
    """A verdict that says relaunch relaunches only when the tree is clean and
    HEAD is the commit it names; three attempts park the episode."""
    verdict = {"verdict": "relaunch", "commit": SHA, "why": "fixed, trust me"}
    assert ap.derive(signals(brain_verdict=verdict), 20).state is State.IDLE
    dirty = ap.derive(signals(brain_verdict=verdict, porcelain=" M studio/x.py\n"), 20)
    assert dirty.state is not State.IDLE and dirty.reason == "tree_dirty"
    moved = ap.derive(signals(brain_verdict=verdict, head_sha="deadbeef"), 20)
    assert (moved.state, moved.reason) == (State.NEEDS_BRAIN, "brain: head is not the verdict's commit")
    capped = ap.derive(signals(brain_verdict=verdict, head_sha="deadbeef", brain_attempts=3), 20)
    assert (capped.state, capped.reason) == (State.PARKED, "brain_exhausted")
    assert ap.derive(signals(brain_verdict={"verdict": "park"}, brain_attempts=3), 20).state is State.PARKED


def test_the_ledger_helpers_read_the_last_run_not_an_older_one():
    """ep19's fourth launch had three `end code 1` rows above it; a crashed
    fourth run has no exit code of its own, whatever the ledger says above."""
    crash_after_stops = rows(("start",), ("run", "refused"), ("end", 1), ("start",))
    assert ap.crashed(crash_after_stops) and not ap.crashed(rows(("start",), ("end", 1)))
    assert ap.exit_code(signals(drive_rows=crash_after_stops)) is None
    assert ap.exit_code(signals(drive_rows=crash_after_stops, exit_code=2)) == 2
    assert ap.exit_code(signals(drive_rows=rows(("start",), ("end", 1)))) == 1
    assert ap.last_row(crash_after_stops, "run")["outcome"] == "refused"
    assert ap.last_row([], "run") is None
    assert ap.published(PUBLIC, 20) and not ap.published(PUBLIC, 21)
    assert ap.parked(PARKED, 20)["reason"] == "over_budget" and ap.parked(PARKED, 21) is None
    pk = ap.packet(signals(drive_rows=crash_after_stops), 20, "x")
    assert pk["drive_row"] == {"n": 1, "sha": SHA, "outcome": "refused"} and pk["home"] == "episodes/ep20"


def test_caps_are_the_decision_numbers():
    assert (ap.RELAUNCH_CAP, ap.CURE_CAP, ap.BRAIN_ATTEMPTS, ap.ENGINE_RESTARTS, ap.CRASHES_BEFORE_BRAIN) == (2, 2, 3, 2, 3)


def test_a_retry_is_capped_then_handed_to_the_brain():
    """H3: a plan deferral retries twice ($0 cure on each relaunch), the third
    stop asks the brain (ep19: three refused runs before the wall)."""
    stop = rows(("start",), ("run", "refused"), ("end", 1))
    tail = "DEFERRED PLAN | ep19 | battery: CONTRACT -> defer | aside: episodes/ep19/plan.deferred.json"
    home = {"plan.json", "plan.deferred.json"}
    assert ap.derive(signals(drive_rows=stop * 2, log_tail=tail, home_files=home), 19).state is State.IDLE
    got = ap.derive(signals(drive_rows=stop * 3, log_tail=tail, home_files=home), 19)
    assert (got.state, got.reason) == (State.NEEDS_BRAIN, "retry_exhausted: plan_deferred")
    assert ap.stops(stop * 3) == 3


def test_a_cure_carries_its_work_order():
    tail = "SystemExit: REFUSED: the takes wait on the panels: eye_01.json older than panel 03"
    got = ap.derive(signals(drive_rows=rows(("start",), ("run", "refused"), ("end", 1)), log_tail=tail), 20)
    assert (got.state, got.reason, got.order) == (State.IDLE, "takes_wait_on_panels", ("redo", "08"))
