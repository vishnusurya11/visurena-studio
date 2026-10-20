"""Deadline retro item 1 (2026-10-20, package A): every drive launch of a DELIVERED episode runs the dry check
itself and refuses -- exit non-zero, before any GPU second -- when a delivered take would be written without
a named owner order.  All three stopped repair launches of Jekyll HEL ep01 (2026-10-19 11:18, 12:29, 13:54
PDT) were found by launching; the dry check existed but read counters and nothing called it (RETRO.md RC2).

The check asks the real deciders, never a counter: the render pass (takes_r2v.wants_render over
take_currency.held_in), the early round (take_overlap.early_cures), the batched rung (take_ladder.route ->
batch_for), the terminal's best-draw swap (take_ladder.pick_best) and the freeze itself
(take_currency.frozen_in, the guard every writer of T<nn>.mp4 asks).

The two incidents are replayed by putting back the code each one ran on:
  - P03 (b83eac4) reworded the cheque sentence before the freeze existed (52e90bc): 28 renders, refused;
  - P08 (79b8049) made a round a change of bytes while the early round never read the freeze: T01, refused.
Today's code passes both launches.  Records: tests/fixtures/ep01_replay/repair_rerun/ (T00's delivered and
11:18 graphs, T01.dq.json, the delivered manifest.json, the 12:29 ladder/attempts/clock, and ep01's
repair.jsonl for the cap line).  Temp db and files; no GPU, no ComfyUI, no network."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.episode import repair_dry_check as dry
from studio import episode_home, repair_clock, take_ladder, work_orders
from studio import take_currency as tc
from tests.test_a_repair_freezes_its_delivered_takes import NEW_WORDS
from tests.test_an_owner_repair_runs_on_its_own_clock import ordered
from tests.test_episode_runner import CODEX, book, conn  # noqa: F401

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "repair_rerun"
TAKES = 28
T01_MTIME = 1_792_374_948


def manifest_sha8() -> dict[int, str]:
    """T<nn> -> the bytes step 12 delivered, off ep01's manifest.json."""
    rows = json.loads((FIX / "manifest.json").read_text(encoding="utf-8"))["inputs"]
    return {int(Path(r["path"]).stem[1:]): r["sha8"] for r in rows if "/takes/r2v/T" in r["path"]}


@pytest.fixture
def ep01(book, monkeypatch):  # noqa: F811
    """ep01 as delivered: 28 takes whose stand-in bytes hash to the manifest's sha8, each beside T00's
    delivered graph (the words with "cheque"); the delivered manifest."""
    home = episode_home.home(book, 1)
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    shutil.copy(FIX / "manifest.json", home / "manifest.json")
    (home / "plan.json").write_text(json.dumps({"shots": [], "lines": []}), encoding="utf-8")
    sha = manifest_sha8()
    for i in range(TAKES):
        (room / f"T{i:02d}.mp4").write_bytes(f"delivered T{i:02d}".encode())
        shutil.copy(FIX / "T00.graph.json", room / f"T{i:02d}.graph.json")
    by_bytes = {f"delivered T{i:02d}".encode(): s for i, s in sha.items()}
    monkeypatch.setattr(tc, "sha8_of", lambda p: by_bytes.get(Path(p).read_bytes(), "ffffffff"))
    canvas = tc.recorded_canvas(room / "T00.mp4")
    monkeypatch.setattr(dry, "render_rows", lambda codex, number, home, window: p03_rows(room, home, window, canvas))
    return SimpleNamespace(home=home, room=room)


def p03_rows(room: Path, home: Path, window, canvas) -> dict:
    """Every card as P03's code built it (NEW_WORDS: the cheque gone), asked of the render pass's decider."""
    return {i: dry.take_state({"index": i, "shots": [i], "prompt": NEW_WORDS}, room / f"T{i:02d}.mp4", home,
                              window, [], canvas, {i: {"index": i, "shots": [i]}}) for i in range(TAKES)}


def before_the_freeze(monkeypatch) -> None:
    """The code P03 landed on: no repair froze a delivered take (52e90bc came after 11:18)."""
    monkeypatch.setattr(tc, "frozen_in", lambda *a, **k: None)


# ---- P03: the reworded cheque ----------------------------------------------------------------

def test_p03s_reworded_cheque_lists_28_renders_and_refuses(conn, ep01, monkeypatch):
    ordered(conn, ep01.home)
    before_the_freeze(monkeypatch)
    said = dry.preflight(conn, CODEX, 1)
    assert said and said[0].startswith("REFUSED to start: the dry check")
    render = next(line for line in said if "render pass" in line)
    assert "28 take(s)" in render and all(f"T{i:02d}" in render for i in range(TAKES))


def test_todays_freeze_lets_the_same_repair_launch(conn, ep01):
    ordered(conn, ep01.home)
    assert dry.preflight(conn, CODEX, 1) == []


def test_without_an_owner_order_the_governing_repair_still_freezes(conn, ep01):
    shutil.copy(FIX / "repair.json", ep01.home / repair_clock.WINDOW)        # unbacked: drive start closes it
    assert dry.preflight(conn, CODEX, 1) == []


def test_a_never_repaired_delivered_episode_refuses_its_reworded_takes(conn, ep01):
    assert len(dry.unordered(dry.would_render(ep01.home, None, dry.render_rows(CODEX, 1, ep01.home, None)),
                             dry.delivered_takes(ep01.home), [])["render pass (takes_r2v.wants_render)"]) == TAKES


def test_an_undelivered_episode_is_never_refused(conn, ep01):
    (ep01.home / "manifest.json").unlink()
    assert dry.preflight(conn, CODEX, 1) == []


# ---- P08: the round rule and the early round -----------------------------------------------------

@pytest.fixture
def t01(book, monkeypatch):  # noqa: F811
    """ep01 at the 12:29 launch: T01 as delivered with its dq record (the gait row), the manifest, the
    killed run's window, ladder.json, attempts.json and clock."""
    home = episode_home.home(book, 1)
    room = home / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    (room / "T01.mp4").write_bytes(b"restored T01")
    os.utime(room / "T01.mp4", (T01_MTIME, T01_MTIME))
    shutil.copy(FIX / "T01.dq.json", room / "T01.dq.json")
    for src, dest in (("manifest.json", home / "manifest.json"), ("ladder_1229.json", room / take_ladder.LADDER_FILE),
                      ("attempts_1229.json", home / "attempts.json"), ("clock_1229.jsonl", home / "clock.jsonl"),
                      ("clock_1229.open.json", home / "clock.open.json")):
        shutil.copy(FIX / src, dest)
    (home / "plan.json").write_text(json.dumps({"shots": [], "lines": []}), encoding="utf-8")
    monkeypatch.setattr(tc, "sha8_of", lambda p: "a4b22b62" if Path(p).read_bytes() == b"restored T01" else "ffffffff")
    monkeypatch.setattr(dry, "render_rows", lambda codex, number, home, window: {
        1: dry.take_state({"index": 1, "shots": [1], "prompt": "x"}, room / "T01.mp4", home, window, [], (0, 0),
                          {1: {"index": 1, "shots": [1]}})})
    return SimpleNamespace(home=home, room=room)


def early_round_ignores_the_freeze(monkeypatch) -> None:
    """The code P08 landed on: the router never asked the freeze (d5d5587 came after 12:29)."""
    monkeypatch.setattr(take_ladder, "frozen_here", lambda *a, **k: None)


def test_p08s_round_rule_lists_t01_in_the_early_round_and_refuses(conn, t01, monkeypatch):
    ordered(conn, t01.home)
    early_round_ignores_the_freeze(monkeypatch)
    said = dry.preflight(conn, CODEX, 1)
    assert said and said[0].startswith("REFUSED to start")
    assert any("early round" in line and "T01" in line for line in said), said


def test_todays_router_keeps_frozen_t01_out_and_the_launch_goes(conn, t01):
    ordered(conn, t01.home)
    assert dry.preflight(conn, CODEX, 1) == []


def test_a_take_the_owners_order_names_is_no_refusal(conn, t01, monkeypatch):
    order_id = work_orders.order(conn, "redo", "unit", codex_id=CODEX, stage="episode", unit="ep01", step_id="09",
                                 note="retake T01: the feet slide", artefact="episodes/ep01/takes/r2v/T01.mp4")
    work_orders.note_taken(t01.home, "09", order_id)
    early_round_ignores_the_freeze(monkeypatch)
    assert dry.preflight(conn, CODEX, 1) == []


# ---- the owner's orders ---------------------------------------------------------------------

def test_an_owner_redo_before_09_orders_every_take():
    assert dry.unordered({"x": {1, 2}}, {1, 2}, [{"step_id": "02", "note": None}]) == {}
    assert dry.unordered({"x": {1, 2}}, {1, 2}, [{"step_id": "09", "note": "T02 hands"}]) == {"x": [1]}


def test_a_take_no_manifest_delivered_is_never_refused():
    assert dry.unordered({"x": {1, 30}}, {1}, []) == {"x": [1]}


def test_the_delivered_takes_are_the_manifests_take_rows(ep01):
    assert dry.delivered_takes(ep01.home) == set(range(TAKES))


def test_an_autopilot_cure_is_not_an_owner_order(conn, ep01):
    ordered(conn, ep01.home, by="autopilot")
    assert dry.owner_orders(conn, ep01.home, CODEX, 1) == []


def test_a_pending_owner_redo_is_an_order_and_opens_its_window(conn, ep01):
    work_orders.order(conn, "redo", "unit", codex_id=CODEX, stage="episode", unit="ep01", step_id="10")
    orders = dry.owner_orders(conn, ep01.home, CODEX, 1)
    assert [o["step_id"] for o in orders] == ["10"]
    assert dry.launch_window(conn, ep01.home, orders)["steps"] == ["10"]


def test_a_dry_check_that_cannot_run_refuses(conn, ep01, monkeypatch):
    monkeypatch.setattr(dry, "render_rows", lambda *a: (_ for _ in ()).throw(KeyError("plan")))
    said = dry.preflight(conn, CODEX, 1)
    assert said[0].startswith("REFUSED to start: the dry check could not run") and "KeyError" in said[0]


def test_a_render_road_that_raises_systemexit_refuses(conn, ep01, monkeypatch):
    """The real road (takes_r2v.opened/cards) refuses a plan with SystemExit -- G-LIGHT, chapter_faults --
    a BaseException; it is a dry check that could not run, never an escape past the launch's records."""
    def refuses(*a):
        raise SystemExit("G-LIGHT refuses the plan")
    monkeypatch.setattr(dry, "render_rows", refuses)
    said = dry.preflight(conn, CODEX, 1)
    assert said[0].startswith("REFUSED to start: the dry check could not run") and "G-LIGHT" in said[0]


def test_an_owner_redo_with_no_step_orders_no_take_its_note_does_not_name():
    """A whole-unit owner redo carries no step: counted as 09 or later, so only the takes its note names
    are ordered (errs to refusing; the owner names the takes or the step)."""
    assert dry.unordered({"x": {1, 2}}, {1, 2}, [{"step_id": None, "note": "redo T02"}]) == {"x": [1]}

def test_the_dry_checks_own_command_exits_non_zero_on_a_refusal(conn, ep01, monkeypatch, capsys):
    from studio import db
    ordered(conn, ep01.home)
    before_the_freeze(monkeypatch)
    monkeypatch.setattr(db, "get_connection", lambda *a, **k: conn)
    monkeypatch.setattr(dry, "report", lambda *a: ["the report"])
    assert dry.main(CODEX, 1, ["09"]) == 1
    assert "REFUSED to start: the dry check lists 28" in capsys.readouterr().out


# ---- the drive runs it ------------------------------------------------------------------------

def test_the_drive_refuses_the_launch_before_any_run(conn, ep01, monkeypatch):
    from scripts.episode import drive
    from studio import db
    ordered(conn, ep01.home)
    before_the_freeze(monkeypatch)
    monkeypatch.setattr(db, "get_connection", lambda *a, **k: conn)
    monkeypatch.setattr(drive, "git", lambda *a: "" if a[0] == "status" else "abc123\n")
    monkeypatch.setattr(drive, "run_once", lambda *a: pytest.fail("a refused launch runs nothing"))
    told = []
    monkeypatch.setattr(drive, "notify", told.append)
    assert drive.main(CODEX, 1) == 2
    assert "REFUSED to start: the dry check" in told[0]
    rows = [json.loads(line) for line in (ep01.home / "drive.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["event"] for r in rows] == ["start", "run", "end"] and rows[1]["outcome"] == "refused"
    assert rows[2]["code"] == 2 and rows[2]["refused"] == "dry_check"
    assert "T27" in (ep01.home / "drive_run01.log").read_text(encoding="utf-8")



def drive_rows(home: Path) -> list[dict]:
    return [json.loads(line) for line in (home / "drive.jsonl").read_text(encoding="utf-8").splitlines()]


def test_a_dry_check_that_raises_systemexit_is_a_recorded_refusal(conn, ep01, monkeypatch):
    from scripts.episode import drive
    from studio import db
    monkeypatch.setattr(db, "get_connection", lambda *a, **k: conn)
    monkeypatch.setattr(drive, "git", lambda *a: "" if a[0] == "status" else "abc123\n")
    monkeypatch.setattr(drive, "notify", lambda text: None)
    monkeypatch.setattr(dry, "render_rows", lambda *a: (_ for _ in ()).throw(SystemExit("G-LIGHT refuses the plan")))
    assert drive.main(CODEX, 1) == 2
    assert [r["event"] for r in drive_rows(ep01.home)] == ["start", "run", "end"]
    assert "could not run" in (ep01.home / "drive_run01.log").read_text(encoding="utf-8")


def test_a_database_that_will_not_open_is_a_recorded_refusal(ep01, monkeypatch):
    from scripts.episode import drive
    from studio import db
    def locked(*a, **k):
        raise RuntimeError("database is locked")
    monkeypatch.setattr(db, "get_connection", locked)
    monkeypatch.setattr(drive, "git", lambda *a: "" if a[0] == "status" else "abc123\n")
    monkeypatch.setattr(drive, "notify", lambda text: None)
    assert drive.main(CODEX, 1) == 2
    assert drive_rows(ep01.home)[-1]["refused"] == "dry_check"
    assert "database is locked" in (ep01.home / "drive_run01.log").read_text(encoding="utf-8")


# ---- the repair-cap display (drive_launch18.log: "repair 1.83 h of a 0.63 h cap") ------------------

def test_each_repair_is_shown_against_its_own_cap(tmp_path):
    shutil.copy(FIX / "repair_two_windows.jsonl", tmp_path / repair_clock.LOG)
    assert repair_clock.finish_part(tmp_path) == (" | repair 1.61 h of a 2.38 h cap (09), "
                                                  "0.22 h of a 0.63 h cap (10)")
