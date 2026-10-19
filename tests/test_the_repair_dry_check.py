"""The repair rerun's dry check (incident 2026-10-19 11:18 PDT: RERUN.md said "every take is current"
without reading the files, and the launch queued all 28 of ep01's takes).  Before an owner's repair
launches, `scripts/episode/repair_dry_check.py <book> <n>` reports what step 09 would render, take by
take (current / frozen / render, and why), whether the refine and the tiny-face rung are priced inside
the repair cap, whether the owner's redo order still stands, and what steps 10-13 would do -- with no
GPU and no write to the episode (it says so, from a before/after listing).

Replayed on ep01's real T00 graph pair, dq record, manifest and leftover window
(tests/fixtures/ep01_replay/repair_rerun/).  Temp db and files; no GPU, no ComfyUI, no network."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from scripts.episode import repair_dry_check as dry
from studio import repair_clock, run_clock
from studio import take_currency as tc
from tests.test_a_repair_freezes_its_delivered_takes import NEW_WORDS, ep01, graph_prompt, in_repair  # noqa: F401
from tests.test_an_owner_repair_runs_on_its_own_clock import EP01_SPENT, delivered, ordered, past_six_hours
from tests.test_episode_runner import CODEX, book, conn  # noqa: F401

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "repair_rerun"
REFINE_S, RUNG_S = 2_236.0, 984.0
"""ep01's refine (its 22 owed takes) and one two-face tiny-face draw, as priced (RERUN.md section 0)."""


def card() -> dict:
    return {"index": 0, "shots": [0], "prompt": NEW_WORDS}


RECORDS = {0: {"index": 0, "shots": [0]}}


# ---- per take -----------------------------------------------------------------------------

def test_a_normal_run_would_render_t00_for_its_words(ep01):
    state, why = dry.take_state(card(), ep01.take, ep01.home, None, [], ep01.canvas, RECORDS)
    assert state == "render" and "prompt" in why


def test_the_repair_freezes_t00_on_its_delivered_bytes(ep01):
    window = repair_clock.open_window(ep01.home, {"09": 38}, 1_000.0)
    state, why = dry.take_state(card(), ep01.take, ep01.home, window, [], ep01.canvas, RECORDS)
    assert state == "frozen" and "delivered" in why and "56da138b" in why and "prompt" in why


def test_the_cards_own_words_read_current(ep01):
    own = {**card(), "prompt": graph_prompt("T00.graph.json")}
    assert dry.take_state(own, ep01.take, ep01.home, None, [], ep01.canvas, RECORDS)[0] == "current"


def test_a_missing_take_or_record_renders(ep01):
    assert dry.take_state(card(), ep01.take, ep01.home, None, [], ep01.canvas, {})[0] == "render"
    ep01.take.unlink()
    assert dry.take_state(card(), ep01.take, ep01.home, None, [], ep01.canvas, RECORDS)[1] == "no take on disk"


def test_the_stale_reason_names_the_first_input_that_moved(ep01):
    assert dry.stale_why(NEW_WORDS, ep01.take, [], ep01.canvas) == "prompt"
    assert dry.stale_why(graph_prompt("T00.graph.json"), ep01.take, [], (576, 1024)) == "canvas"
    assert dry.stale_why(graph_prompt("T00.graph.json"), ep01.take, [], ep01.canvas) is None


# ---- the window and the order -------------------------------------------------------------

def test_a_backed_leftover_window_is_the_one_the_drive_continues(conn, book, tmp_path):
    delivered(tmp_path)
    window = repair_clock.open_window(tmp_path, {"09": ordered(conn, tmp_path)}, 1_000.0)
    got, said = dry.window_now(conn, tmp_path, ["09"])
    assert got == window and "continues" in said


def test_an_unbacked_leftover_is_said_closed_and_the_order_assumed(conn, book, tmp_path):
    delivered(tmp_path)
    shutil.copy(FIX / "repair.json", tmp_path / repair_clock.WINDOW)
    got, said = dry.window_now(conn, tmp_path, ["09"])
    assert "closes it" in said and got["steps"] == ["09"] and got["cap_s"] == pytest.approx(8_580.0)
    assert repair_clock.read(tmp_path)["orders"] == {"09": 38}          # the dry check closed nothing


def test_an_undelivered_episode_has_no_window(conn, book, tmp_path):
    assert dry.window_now(conn, tmp_path, ["09"])[0] is None


def test_a_taken_owner_order_still_owed_needs_no_new_order(conn, book, tmp_path):
    order_id = ordered(conn, tmp_path)
    redo = {"09"}
    assert dry.order_needed(conn, tmp_path, ["09"], redo, pending=[]) is None
    assert f"#{order_id}" in dry.order_line(conn, tmp_path, ["09"], redo, pending=[])


def test_no_receipt_and_no_redo_needs_a_new_order(conn, book, tmp_path):
    assert "redo" in dry.order_needed(conn, tmp_path, ["09"], set(), pending=[])


# ---- the prices -------------------------------------------------------------------------

def test_inside_the_repair_cap_the_refine_and_the_rung_both_run(tmp_path):
    past_six_hours(tmp_path)
    window = repair_clock.open_window(tmp_path, {"09": 38}, time.time())
    got = dry.priced(tmp_path, window, REFINE_S, RUNG_S)
    assert got["refine"] and got["rung"]
    assert got["after_rung_s"] == pytest.approx(REFINE_S + RUNG_S + 550.0 + got["owed_after_s"])


def test_on_the_episodes_own_clock_the_refine_is_cut(tmp_path):
    past_six_hours(tmp_path)
    got = dry.priced(tmp_path, None, REFINE_S, RUNG_S)
    assert not got["refine"] and got["spent_s"] == pytest.approx(EP01_SPENT)


def test_what_a_killed_repair_run_spent_is_charged_to_its_window(tmp_path):
    window = repair_clock.open_window(tmp_path, {"09": 38}, 5_000.0)
    run_clock.open_run(tmp_path, "killed", now=lambda: 5_000.0)
    run_clock.tag_repair(tmp_path, "killed")
    run_clock.close_run(tmp_path, now=lambda: 5_060.0)
    assert dry.priced(tmp_path, window, REFINE_S, RUNG_S)["spent_s"] == pytest.approx(60.0)


# ---- no writes ----------------------------------------------------------------------------

def test_the_listing_sees_a_write_and_an_untouched_episode(ep01):
    before = dry.snapshot(ep01.home)
    assert dry.changed(before, dry.snapshot(ep01.home)) == []
    (ep01.home / "takes" / "r2v" / "T00.graph.json").write_text("{}", encoding="utf-8")
    (ep01.home / "repair.json").write_text("{}", encoding="utf-8")
    assert dry.changed(before, dry.snapshot(ep01.home)) == ["repair.json", "takes/r2v/T00.graph.json"]


def test_a_count_line_sums_the_states():
    rows = {0: ("frozen", "x"), 1: ("current", "y"), 2: ("frozen", "z"), 3: ("render", "w")}
    assert dry.count_line(rows) == "step 09 renders 1 take(s) (T03): 1 current, 2 frozen, 1 render"
    assert tc.FREEZE_FROM == "09"
