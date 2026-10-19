"""Skeptic round on d5d5587 (incident 2, 2026-10-19).  take_ladder.landed counted a ladder.json round when
ANY draw of a take it names was written after it launched -- it never asked which render wrote the draw.  So
a later write of the same take brought a dead round back: a stale round of T05 followed by one real round
of T05 read as two rounds (ROUNDS_CAP after one), and on ep01 the tiny-face rung's one draw of T01 (the
dry check names T01 its worst single draw) would have revived the killed 12:29 round.

The rule now: a round's draws land only inside its own window -- from its launch to the end of the run that
launched it (run_clock's span: a kill loses at most one beat) or the launch of the next round that names
the same take, whichever comes first.  A round launched by this very process is in flight and counts; a
dead process whose pid Windows hands to a later one does not (BORN: the round predates this process).

Also here: the dry check prints the router's own batch even when the climb is closed by a counter (it
names both), and takes_r2v refuses a named retake of a frozen take where the bytes would change -- a
backstop under every caller; the tiny-face rung's one draw is the repair's own work and still renders.

Replayed on ep01's records (tests/fixtures/ep01_replay/repair_rerun/): ladder.json, attempts.json,
clock.jsonl and clock.open.json as the 12:29 kill left them.  No GPU, no ComfyUI, no network."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from studio import take_ladder
from tests.test_a_freeze_holds_at_every_render_site import (  # noqa: F401
    FIX, RETRY_STAMP, dry_text, ep01, in_repair, killed_run)


def book(room: Path, rounds: list[dict]) -> None:
    (room / take_ladder.LADDER_FILE).write_text(json.dumps({"rounds": rounds}), encoding="utf-8")


def take_at(room: Path, name: str, when: float) -> None:
    (room / name).parent.mkdir(parents=True, exist_ok=True)
    (room / name).write_bytes(name.encode())
    os.utime(room / name, (when, when))


# ---- a later render of the same take never revives a dead round -----------------------------------

def test_a_stale_round_then_one_real_round_of_the_same_take_is_one_round(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    book(room, [{"why": "batched_cures: warp", "at": 100.0, "faults": {"5": ["warp"]}},
                {"why": "batched_cures: warp", "at": 200.0, "pid": 1, "takes": [5], "faults": {"5": ["warp"]}}])
    take_at(room, "attempts/T05_fail1.mp4", 50.0)               # the take as both rounds found it
    take_at(room, "T05.mp4", 250.0)                             # the real round's render
    assert take_ladder.rounds_of(room) == 1
    assert [r["at"] for r in take_ladder.counted(room)] == [200.0]


def test_the_tiny_face_draw_of_t01_does_not_revive_the_1229_round(ep01):
    killed_run(ep01)
    (ep01.room / "T01.mp4").rename(ep01.room / "attempts" / "T01_fail1.mp4")   # displaced, mtime kept
    (ep01.room / "T01.mp4").write_bytes(b"the tiny-face rung's 1024 draw")      # lands now
    assert take_ladder.rounds_of(ep01.room, RETRY_STAMP) == 0
    assert take_ladder.rounds_of(ep01.room) == 1                                # the 20:14 round, as before


def test_the_1229_round_sits_in_the_killed_run_and_its_window_closed_a_beat_after(ep01):
    killed_run(ep01)
    stale = take_ladder.rounds_on_file(ep01.room)[1]
    assert take_ladder.window_end(ep01.room, stale, 1, []) == 1_792_438_171.196265 + 60.0


def closed_run(home: Path, started: float, ended: float) -> None:
    row = {"run_id": "x", "pid": 7, "started": started, "ended": ended, "seconds": ended - started, "how": "killed"}
    (home / "clock.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")


def test_a_draw_inside_the_launching_run_lands_and_one_after_it_does_not(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    closed_run(tmp_path, 1_000.0, 2_000.0)
    book(room, [{"why": "batched_cures: seed", "at": 1_500.0, "pid": 7, "takes": [3]}])
    take_at(room, "T03.mp4", 2_030.0)                           # inside the one lost beat
    assert take_ladder.rounds_of(room) == 1
    take_at(room, "T03.mp4", 5_000.0)                           # a later run's render of T03
    assert take_ladder.rounds_of(room) == 0


# ---- in flight is THIS process, not a dead one whose pid came back ----------------------------------

def test_a_dead_process_with_this_pid_does_not_put_its_round_in_flight(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    book(room, [{"why": "batched_cures: seed", "at": take_ladder.BORN - 100.0, "pid": os.getpid(), "takes": [3]}])
    assert take_ladder.rounds_of(room) == 0


def test_a_round_this_process_launched_counts_before_a_byte_lands(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    take_ladder.count_round(room, "batched_cures: seed", {"3": ["seed"]}, takes=[3])
    assert take_ladder.rounds_of(room) == 1 and take_ladder.BORN <= time.time()


# ---- the dry check prints the router's batch even when a counter closed the climb -----------------

def test_the_dry_check_shows_the_freeze_empties_the_batch_not_only_the_counter(ep01):
    killed_run(ep01)                                            # attempts.json retakes 2/2: the climb is closed
    window = json.loads((FIX / "repair.json").read_text(encoding="utf-8"))
    line = next(x for x in dry_text(ep01.home, window).splitlines() if x.startswith("take ladder"))
    assert "the climb is closed: attempts.json retakes 2/2" in line, line
    assert "route -> batch_for alone: none" in line, line


def test_outside_a_repair_the_closed_climb_still_names_what_the_router_would_batch(ep01):
    killed_run(ep01)
    line = next(x for x in dry_text(ep01.home, None).splitlines() if x.startswith("take ladder"))
    assert line.split(": ", 1)[1].startswith("batch none"), line
    assert "route -> batch_for alone: T01" in line, line


# ---- the backstop where the bytes change: takes_r2v ---------------------------------------------------

def named_retake(ep01, monkeypatch, tiny: bool = False) -> bool:
    from scripts.episode import takes_r2v
    monkeypatch.setattr(takes_r2v, "TINY_FACE", tiny)
    card = {"index": 1, "shots": [1], "prompt": "x"}
    return takes_r2v.wants_render(card, ep01.room / "T01.mp4", {}, [1], lambda: True)


def test_outside_a_repair_a_named_retake_of_t01_renders(ep01, monkeypatch):
    assert named_retake(ep01, monkeypatch)


def test_inside_the_repair_takes_r2v_refuses_a_named_retake_of_frozen_t01(ep01, monkeypatch, capsys):
    in_repair(ep01.home)
    assert not named_retake(ep01, monkeypatch)
    assert "KEPT T01" in capsys.readouterr().out


def test_the_tiny_face_rungs_one_draw_still_renders_inside_the_repair(ep01, monkeypatch):
    in_repair(ep01.home)
    assert named_retake(ep01, monkeypatch, tiny=True)
