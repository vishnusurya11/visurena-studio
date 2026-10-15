"""studio/take_overlap.py runs step 09's two lanes for real: the takes_r2v
process on the GPU and a take_dq --cpu-only process beside it, measuring each
take the moment it lands.  A dq-borne cure (a move or a seed) is queued as a
retake right behind the first renders, as ONE early round of the take ladder.

Every process here is a fake: a render "lands" one take per poll, a check
writes its verdict when it ends.  No GPU, no ComfyUI, no clock."""
from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import episode_home, take_ladder, take_overlap as to
from studio.run_budget import EPISODE_SHARES, Budget

CODE = "c0dec0de"


class Proc:
    """A process that ends after `ticks` polls, running `effect` once per poll."""

    def __init__(self, steps: list, rc: int = 0):
        self.steps, self.rc, self.returncode = list(steps), rc, None

    def poll(self):
        if self.steps:
            self.steps.pop(0)()
            return None
        self.returncode = self.rc
        return self.rc


class World:
    """The take room and the processes the shop spawns into it."""

    def __init__(self, tmp_path: Path, takes: int = 3, faults: dict | None = None, render_rc: int = 0):
        self.book = tmp_path / "book"
        self.home = episode_home.home(self.book, 1)
        self.room = self.home / "takes" / "r2v"
        self.room.mkdir(parents=True)
        self.takes, self.faults, self.render_rc = takes, faults or {}, render_rc
        self.spawned: list[tuple[str, list[str]]] = []
        self.dying_checks = 0

    def land(self, i: int):
        def step():
            (self.room / f"T{i:02d}.mp4").write_bytes(f"take {i} {time.time()}".encode())
            time.sleep(0.002)
            sheet = self.room / "shots.json"
            rows = json.loads(sheet.read_text()) if sheet.exists() else []
            rows = [r for r in rows if r["index"] != i] + [{"index": i}]
            sheet.write_text(json.dumps(sorted(rows, key=lambda r: r["index"])))
        return step

    def verdict(self, i: int):
        def step():
            gates = [{"name": k, "ok": False, "hard": True} for k in self.faults.get(i, [])]
            (self.room / f"T{i:02d}.dq.json").write_text(json.dumps({"measures_sha8": CODE, "gates": gates}))
        return step

    def spawn(self, cmd: list[str]) -> Proc:
        script, args = cmd[0], [str(a) for a in cmd[1:]]
        self.spawned.append((script, args))
        if script == to.RENDER:
            named = next((a.split("=", 1)[1] for a in args if a.startswith("--retake=")), None)
            takes = [int(v) for v in named.split(",")] if named else list(range(self.takes))
            return Proc([self.land(i) for i in takes], self.render_rc)
        if self.dying_checks:
            self.dying_checks -= 1
            return Proc([lambda: None], rc=1)
        takes = [int(a) for a in args if a.isdigit()]
        return Proc([lambda: None] + [self.verdict(i) for i in takes])

    def ctx(self, **kw):
        budget = Budget(5 * 3600, EPISODE_SHARES, limit=6 * 3600)
        budget.start("09")
        base = dict(home=self.home, book_dir=self.book, number=1, budget=budget, busy=lambda: False,
                    command=lambda script, extra=(): [script, *extra], log=lambda *a, **k: None)
        return SimpleNamespace(**(base | kw))

    def shoot(self, ctx=None, **kw):
        ctx = ctx or self.ctx()
        shop = to.Shop(ctx, ["--from-refs", "--no-ends", "--approved=render"], spawn=self.spawn,
                       sleep=lambda s: None, code=CODE, **kw)
        shop.run()
        return shop

    def checks(self) -> list[list[str]]:
        return [args for script, args in self.spawned if script == to.CHECK]

    def renders(self) -> list[list[str]]:
        return [args for script, args in self.spawned if script == to.RENDER]


def test_each_take_is_checked_while_the_next_one_renders(tmp_path):
    w = World(tmp_path)
    order = []
    spawn = w.spawn
    w.spawn = lambda cmd: order.append((cmd[0], len(list(w.room.glob("T??.mp4"))))) or spawn(cmd)
    w.shoot(early=True)
    first_check = next(n for script, n in order if script == to.CHECK)
    assert first_check < w.takes                     # the first check began before the last take landed
    assert sorted(int(a) for args in w.checks() for a in args if a.isdigit()) == [0, 1, 2]


def test_every_check_beside_a_render_is_cpu_only(tmp_path):
    w = World(tmp_path)
    w.shoot(early=True)
    assert w.checks() and all("--cpu-only" in args for args in w.checks())


def test_a_dq_fault_queues_its_retake_right_behind_the_first_renders(tmp_path):
    w = World(tmp_path, faults={1: ["gait"]})
    w.shoot(early=True)
    first, retake = w.renders()
    assert not any(a.startswith("--retake") for a in first)
    assert "--retake=1" in retake and any(a.startswith("--why=batched_cures: gait") for a in retake)
    rounds = json.loads((w.room / take_ladder.LADDER_FILE).read_text())["rounds"]
    assert len(rounds) == 1 and rounds[0]["early"] and rounds[0]["faults"] == {"1": ["gait"]}


def test_the_early_round_leaves_its_learning_like_any_rung(tmp_path):
    w = World(tmp_path, faults={1: ["gait"]})
    learned = []
    w.shoot(w.ctx(learn=learned.append), early=True)
    assert [(l.gate, l.action, l.measured) for l in learned] == [("EYE_TAKES", "early_cures", 1)]
    assert "gait" in learned[0].note


def test_a_retaken_take_is_checked_with_its_attempts(tmp_path):
    w = World(tmp_path, faults={1: ["gait"]})
    w.shoot(early=True)
    again = [args for args in w.checks() if "1" in args and "--attempts" in args]
    assert again, w.checks()


def test_the_early_round_is_one_round_however_many_jobs_carry_it(tmp_path):
    w = World(tmp_path, faults={0: ["gait"], 2: ["gait"]})
    w.shoot(early=True)
    retaken = sorted(int(v) for args in w.renders()[1:] for a in args if a.startswith("--retake=")
                     for v in a.split("=", 1)[1].split(","))
    assert retaken == [0, 2]
    assert take_ladder.rounds_of(w.room) == 1


def test_no_early_retake_once_the_episode_has_taken_a_ladder_round(tmp_path):
    w = World(tmp_path, faults={1: ["gait"]})
    take_ladder.count_round(w.room, "batched_cures: content")
    w.shoot(early=True)
    assert len(w.renders()) == 1


def test_the_ladders_own_round_overlaps_its_checks_without_ordering_more(tmp_path):
    w = World(tmp_path, faults={1: ["gait"]})
    shop = w.shoot(retake=([1], "batched_cures: gait"), attempts=True)
    assert len(w.renders()) == 1 and "--retake=1" in w.renders()[0]
    assert [a for a in w.checks()[0] if a.isdigit()] == ["1"] and "--attempts" in w.checks()[0]
    assert not shop.queue


def test_no_budget_means_no_early_rung(tmp_path):
    w = World(tmp_path, faults={1: ["gait"]})
    w.shoot(w.ctx(budget=None), early=True)
    assert len(w.renders()) == 1


def test_a_refused_render_stops_new_jobs_and_refuses_the_step(tmp_path):
    w = World(tmp_path, faults={1: ["gait"]}, render_rc=1)
    with pytest.raises(SystemExit, match="REFUSED"):
        w.shoot(early=True)
    assert len(w.renders()) == 1


def test_a_check_that_dies_is_tried_again_then_left_to_the_catch_all(tmp_path):
    w = World(tmp_path, takes=1)
    w.dying_checks = 1
    w.shoot(early=True)
    assert len(w.checks()) == 2
    w2 = World(tmp_path / "again", takes=1)
    w2.dying_checks = 5
    w2.shoot(early=True)
    assert len(w2.checks()) == to.CPU_TRIES


def test_the_overlapped_checks_are_stamped_inside_the_takes_row(tmp_path):
    w = World(tmp_path)
    w.shoot(early=True)
    rows = [json.loads(l) for l in (w.home / "timing.jsonl").read_text().splitlines()]
    assert [r["stage"] for r in rows][-1] == "takes"
    assert all(r.get("within") == "takes" for r in rows if r["stage"] == "take_dq")


def test_a_take_still_being_written_has_not_landed(tmp_path):
    w = World(tmp_path)
    w.land(0)()
    assert to.landed(w.room, CODE) == [0]
    time.sleep(0.01)
    (w.room / "T00.mp4").write_bytes(b"half a retake")       # newer than shots.json: still writing
    assert to.landed(w.room, CODE) == []


def test_a_verdict_by_older_measuring_code_is_measured_again(tmp_path):
    w = World(tmp_path)
    w.land(0)()
    w.verdict(0)()
    assert to.landed(w.room, CODE) == []
    assert to.landed(w.room, "newcode1") == [0]
    assert to.landed(w.room, "newcode1", any_code=True) == []


def test_a_boundary_pause_launches_no_early_retake(tmp_path):
    from studio import boundary
    w = World(tmp_path, faults={1: ["gait"]})
    spawn = w.spawn

    def spawn_then_pause(cmd):
        proc = spawn(cmd)
        if cmd[0] == to.CHECK:
            boundary.request(w.home, "pause --at-boundary")
        return proc

    w.spawn = spawn_then_pause
    with pytest.raises(boundary.PausedAtBoundary):
        w.shoot(early=True)
    assert len(w.renders()) == 1
    assert not (w.room / take_ladder.LADDER_FILE).exists()      # nothing ordered was recorded as a round


def test_a_busy_engine_holds_the_render_and_refuses_past_the_cap(tmp_path):
    w = World(tmp_path)
    with pytest.raises(SystemExit, match="stayed busy"):
        w.shoot(w.ctx(busy=lambda: True, wait_cap=10.0), early=True)
    assert w.renders() == []


def test_the_takes_row_names_the_retakes_its_round_was_launched_for(tmp_path):
    w = World(tmp_path, takes=2)
    w.shoot(retake=([0, 1], "batched_cures: gait"), attempts=True)
    rows = [json.loads(l) for l in (w.home / "timing.jsonl").read_text().splitlines()]
    assert "--retake=0,1" in rows[-1]["note"] and rows[-1]["stage"] == "takes"
