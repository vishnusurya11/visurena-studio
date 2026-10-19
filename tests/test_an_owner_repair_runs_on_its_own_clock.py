"""Owner ruling 2026-10-19, "Own repair clock": an owner-ordered repair of a DELIVERED episode runs
on its own capped clock, charged and logged apart; the 6 h rule stays as it is for every normal run.

ep01 (Jekyll HEL) had spent 21,673 s when the owner ordered its face repair, so every launch charged
the context's budget with that and cut the refine and the tiny-face rung (docs/audit/
2026-10-19_face_blur/RERUN.md section 0).  Now an owner redo order whose K12 receipt names a step of
an episode whose manifest exists opens a repair window: the budget is charged from the window's own
start, under a cap priced as the redone step's first and every first after it plus the judges'
pool (8,580 s for a redo of 09), the run rows are tagged `repair` so the episode's total and the
repair minutes are counted apart, and the window closes when its drive ends.  No GPU, no ComfyUI,
no network: the db is a temp file, the clock rows are written by hand."""
from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest

from studio import episode_home, episode_run, repair_clock, run_clock, step_runner, work_orders
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, OWNER_LIMIT_SECONDS
from tests.test_episode_runner import CODEX, _opts, book, conn, stub_step_02  # noqa: F401

EP01_SPENT = 21_673.0
"""run_budget.spent_before(ep01) on 2026-10-19 (RERUN.md section 0): past the owner's 6 h."""
REFINE = 2_236.0 + 550.0
"""What step 09's refine is priced against the reserve on ep01 (its 22 takes plus the 550 s margin)."""


def past_six_hours(home):
    """ep01's clock: one closed run row of 21,673 s, an hour ago."""
    home.mkdir(parents=True, exist_ok=True)
    ended = time.time() - 3600
    row = {"run_id": "ep01-old", "pid": 1, "started": ended - EP01_SPENT, "ended": ended,
           "seconds": EP01_SPENT, "how": "closed"}
    (home / run_clock.CLOCK).write_text(json.dumps(row) + "\n", encoding="utf-8")


def ordered(connection, home, by="owner", step="09"):
    """An order row as studio_cli redo writes it (by the owner unless named), taken and receipted."""
    order_id = work_orders.order(connection, "redo", "unit", codex_id=CODEX, stage="episode", unit="ep01",
                                 step_id=step, by=by)
    work_orders.note_taken(home, step, order_id)
    return order_id


def delivered(home):
    (home / "manifest.json").write_text("{}", encoding="utf-8")


def ctx_for(connection, tmp_path):
    """ep01's context on a clock past 6 h, its run's live file open as episode.run_unit opens it."""
    past_six_hours(episode_home.home(tmp_path / "book", 1))
    ctx = episode_run.context(connection, CODEX, 1, **_opts(tmp_path))
    run_clock.open_run(ctx.home, ctx.tracker.run_id)
    return ctx


# ---- the cap ------------------------------------------------------------------------------

def test_a_redo_of_09_is_capped_at_its_priced_firsts_and_the_judges_pool():
    owed = sum(EPISODE_SHARES[s] for s in ("09", "10", "11", "12", "13")) * EPISODE_CEILING_SECONDS
    assert repair_clock.cap_for(["09"]) == pytest.approx(owed + EPISODE_SHARES["judges"] * EPISODE_CEILING_SECONDS)
    assert repair_clock.cap_for(["09"]) == pytest.approx(8_580.0)
    assert repair_clock.cap_for(["11", "09"]) == repair_clock.cap_for(["09"])      # the earliest step rules


def test_the_cap_is_never_unlimited():
    assert repair_clock.cap_for(["01"]) <= OWNER_LIMIT_SECONDS
    assert repair_clock.cap_for(["13"]) == pytest.approx((EPISODE_SHARES["13"] + EPISODE_SHARES["judges"])
                                                         * EPISODE_CEILING_SECONDS)


# ---- who opens a window -------------------------------------------------------------------

def test_no_receipt_opens_no_window(conn, book, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    delivered(home)
    assert repair_clock.window_for(conn, home, None) is None


def test_an_undelivered_episode_opens_no_window(conn, book, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    ordered(conn, home)
    assert repair_clock.window_for(conn, home, None) is None


def test_an_autopilot_cure_is_no_owner_order(conn, book, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    delivered(home)
    ordered(conn, home, by="autopilot")
    assert repair_clock.window_for(conn, home, None) is None


def test_an_owner_redo_of_a_delivered_episode_opens_its_window(conn, book, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    delivered(home)
    order_id = ordered(conn, home)
    window = repair_clock.window_for(conn, home, 1_000.0)
    assert window == {"opened_at": 1_000.0, "cap_s": repair_clock.cap_for(["09"]), "steps": ["09"],
                      "orders": {"09": order_id}}
    assert repair_clock.read(home) == window


def test_an_open_window_holds_for_a_relaunch_inside_its_drive(conn, book, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    delivered(home)
    ordered(conn, home)
    window = repair_clock.window_for(conn, home, 1_000.0)
    work_orders.clear_taken(home, "09")                  # 09 completed in the first run of the drive
    assert repair_clock.window_for(conn, home, 2_000.0) == window


# ---- the clock rows -----------------------------------------------------------------------

def test_a_repair_run_is_tagged_and_counted_apart_from_the_episode(tmp_path):
    past_six_hours(tmp_path)
    run_clock.open_run(tmp_path, "fix", now=lambda: 5_000.0)
    run_clock.tag_repair(tmp_path, "fix")
    run_clock.close_run(tmp_path, now=lambda: 5_900.0)
    assert run_clock.rows(tmp_path)[-1]["repair"] is True
    assert run_clock.spent(tmp_path) == pytest.approx(EP01_SPENT)
    assert run_clock.repair_spent(tmp_path) == pytest.approx(900.0)
    assert run_clock.repair_spent(tmp_path, since=5_600.0) == pytest.approx(300.0)


def test_another_runs_live_file_is_never_tagged(tmp_path):
    run_clock.open_run(tmp_path, "mine", now=lambda: 5_000.0)
    run_clock.tag_repair(tmp_path, "theirs")
    assert "repair" not in run_clock.read_open(tmp_path)


# ---- the budget a drive runs on -----------------------------------------------------------

def test_a_normal_launch_past_six_hours_still_cuts_the_refine(conn, book, tmp_path):
    ctx = ctx_for(conn, tmp_path)
    ctx.after_orders()
    assert ctx.repair_window is None and ctx.budget.limit == OWNER_LIMIT_SECONDS
    assert not ctx.budget.leaves_reserve("09", REFINE)


def test_an_owner_redo_of_an_undelivered_episode_still_cuts_it(conn, book, tmp_path):
    ctx = ctx_for(conn, tmp_path)
    ordered(conn, ctx.home)
    ctx.after_orders()
    assert ctx.repair_window is None and not ctx.budget.leaves_reserve("09", REFINE)


def test_an_owner_repair_of_a_delivered_episode_runs_on_its_own_clock(conn, book, tmp_path, capsys):
    ctx = ctx_for(conn, tmp_path)
    delivered(ctx.home)
    ordered(conn, ctx.home)
    ctx.after_orders()
    assert ctx.repair_window["cap_s"] == pytest.approx(8_580.0)
    assert ctx.budget.limit == pytest.approx(8_580.0) and ctx.budget.leaves_reserve("09", REFINE)
    assert run_clock.read_open(ctx.home)["repair"] is True
    assert "REPAIR CLOCK" in capsys.readouterr().out


def test_the_window_charges_what_it_already_spent(conn, book, tmp_path):
    ctx = ctx_for(conn, tmp_path)
    delivered(ctx.home)
    ordered(conn, ctx.home)
    now = time.time()
    repair_clock.open_window(ctx.home, {"09": 1}, now - 8_000.0)
    rows = [{"run_id": "fix1", "started": now - 8_000.0, "ended": now - 1_000.0, "seconds": 7_000.0,
             "how": "killed", "repair": True}]
    with (ctx.home / run_clock.CLOCK).open("a", encoding="utf-8") as f:
        f.write("".join(json.dumps(r) + "\n" for r in rows))
    ctx.after_orders()
    assert not ctx.budget.leaves_reserve("09", REFINE)       # 7,000 s of 8,580 s spent
    assert ctx.budget.leaves_reserve("12", 60.0 + 1.0)


def test_a_spent_repair_clock_says_cap_once(conn, book, tmp_path, capsys):
    ctx = ctx_for(conn, tmp_path)
    delivered(ctx.home)
    ordered(conn, ctx.home)
    now = time.time()
    repair_clock.open_window(ctx.home, {"09": 1}, now - 9_000.0)
    row = {"run_id": "fix1", "started": now - 9_000.0, "ended": now - 10.0, "seconds": 8_990.0,
           "how": "killed", "repair": True}
    with (ctx.home / run_clock.CLOCK).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    ctx.after_orders()
    ctx.before_step("10")
    ctx.before_step("11")
    out = capsys.readouterr().out
    assert out.count("CAP repair") == 1


def test_the_step_runner_tells_the_context_its_orders_were_taken(conn):
    seen = []
    tracker = SimpleNamespace(run_id="r", event=lambda *a, **k: None)
    ctx = SimpleNamespace(conn=conn, codex_id=CODEX, stage="episode", unit="ep01", home=None, tracker=tracker,
                          held=lambda: False, after_orders=lambda: seen.append("orders"))
    step = SimpleNamespace(STEP_ID="01", NAME="bind", GPU=False, done=lambda ctx: True)
    assert step_runner.run_steps(ctx, [step]) == "completed"
    assert seen == ["orders"]


# ---- the window's end and the finish line -------------------------------------------------

def test_the_drive_end_closes_the_window_and_logs_it(tmp_path):
    past_six_hours(tmp_path)
    repair_clock.open_window(tmp_path, {"09": 7}, 5_000.0)
    run_clock.open_run(tmp_path, "fix", now=lambda: 5_000.0)
    run_clock.tag_repair(tmp_path, "fix")
    run_clock.close_run(tmp_path, now=lambda: 6_200.0)
    closed = repair_clock.close(tmp_path, now=lambda: 6_210.0)
    assert closed["spent_s"] == pytest.approx(1_200.0) and closed["closed_at"] == 6_210.0
    assert repair_clock.read(tmp_path) is None and repair_clock.history(tmp_path)[-1] == closed
    assert repair_clock.close(tmp_path) is None


def test_the_drive_end_row_carries_the_repair_and_its_own_spent_clock(tmp_path):
    from scripts.episode import drive
    past_six_hours(tmp_path)
    assert drive.end_row(tmp_path, 1, "abc")["clock_spent"] is True               # the 6 h, as today
    repair_clock.open_window(tmp_path, {"09": 7}, time.time())
    row = drive.end_row(tmp_path, 2, "abc")
    assert row["clock_spent"] is False and row["repair"]["cap_s"] == pytest.approx(8_580.0)
    assert repair_clock.read(tmp_path) is None


def test_the_finish_line_prints_the_episode_total_and_the_repair_apart(tmp_path):
    from tests.test_gpu_ledger import load
    past_six_hours(tmp_path)
    assert "repair" not in load().finish_line(tmp_path)
    repair_clock.open_window(tmp_path, {"09": 7}, 5_000.0)
    run_clock.open_run(tmp_path, "fix", now=lambda: 5_000.0)
    run_clock.tag_repair(tmp_path, "fix")
    run_clock.close_run(tmp_path, now=lambda: 8_600.0)
    repair_clock.close(tmp_path, now=lambda: 8_600.0)
    line = load().finish_line(tmp_path)
    assert line.startswith("charged 6.02 h | wall ") and line.endswith(" | repair 1.00 h of a 2.38 h cap")
