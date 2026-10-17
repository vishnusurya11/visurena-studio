"""The face refine rides step 09's two lanes (studio/take_schedule.py, take_overlap.py):
a take that passes its dq and is owed a refine gets a REFINE job on the GPU queue --
behind every first render and every retake, ahead of the GPU checks -- so the GPU
never waits on a CPU check.  Refines ordered while one waits join it (one process,
warm weights).  When the clock's reserve needs the time the refine is cut FIRST,
logged and recorded, never a measuring check.  Fakes only: no GPU, no ComfyUI."""
from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

from studio import episode_home, take_overlap as to
from studio.run_budget import EPISODE_SHARES, Budget
from studio.take_schedule import CHECKS, FIRST, REFINE, RETAKE, Job, enqueue

CODE = "c0dec0de"


# ---- the queue's policy ------------------------------------------------------------------

def test_a_refine_waits_behind_renders_and_retakes():
    q = enqueue([Job(FIRST), Job(CHECKS)], Job(REFINE, (0,)))
    q = enqueue(q, Job(RETAKE, (2,), "seed"))
    assert [j.kind for j in q] == [FIRST, RETAKE, REFINE, CHECKS]


def test_refines_ordered_while_one_waits_join_it():
    q = enqueue([Job(FIRST), Job(REFINE, (0,), "face refine")], Job(REFINE, (3,), "face refine"))
    assert [(j.kind, j.takes) for j in q] == [(FIRST, ()), (REFINE, (0, 3))]


# ---- the lanes -----------------------------------------------------------------------------

class Proc:
    def __init__(self, steps, rc=0):
        self.steps, self.rc, self.returncode = list(steps), rc, None

    def poll(self):
        if self.steps:
            self.steps.pop(0)()
            return None
        self.returncode = self.rc
        return self.rc


class Refines:
    """The refine's bookkeeping, faked: which takes are owed one and at what price."""

    def __init__(self, owed: dict[int, float]):
        self.owed_by, self.cuts = owed, []

    def owed(self, indices):
        return {i: p for i, p in self.owed_by.items() if i in indices}

    def cut(self, indices, price):
        self.cuts.append((sorted(indices), price))


class World:
    def __init__(self, tmp_path: Path, takes=3, faults=None):
        self.book = tmp_path / "book"
        self.home = episode_home.home(self.book, 1)
        self.room = self.home / "takes" / "r2v"
        self.room.mkdir(parents=True)
        self.takes, self.faults, self.spawned, self.logged = takes, faults or {}, [], []

    def land(self, i):
        def step():
            (self.room / f"T{i:02d}.mp4").write_bytes(f"take {i} {time.time()}".encode())
            time.sleep(0.002)
            sheet = self.room / "shots.json"
            rows = json.loads(sheet.read_text()) if sheet.exists() else []
            rows = [r for r in rows if r["index"] != i] + [{"index": i}]
            sheet.write_text(json.dumps(sorted(rows, key=lambda r: r["index"])))
        return step

    def verdict(self, i):
        def step():
            gates = [{"name": k, "ok": False, "hard": True} for k in self.faults.get(i, [])]
            (self.room / f"T{i:02d}.dq.json").write_text(json.dumps({"measures_sha8": CODE, "gates": gates}))
        return step

    def spawn(self, cmd):
        script, args = cmd[0], [str(a) for a in cmd[1:]]
        self.spawned.append((script, args))
        if script == to.RENDER:
            named = next((a.split("=", 1)[1] for a in args if a.startswith("--retake=")), None)
            takes = [int(v) for v in named.split(",")] if named else list(range(self.takes))
            return Proc([self.land(i) for i in takes])
        if script == to.REFINE_SCRIPT:
            return Proc([lambda: None])
        return Proc([lambda: None] + [self.verdict(int(a)) for a in args if a.isdigit()])

    def ctx(self, spent=0.0):
        now = [0.0]
        budget = Budget(5 * 3600, EPISODE_SHARES, clock=lambda: now[0], limit=6 * 3600)
        budget.start("09")
        now[0] = spent
        return SimpleNamespace(home=self.home, book_dir=self.book, number=1, budget=budget, busy=lambda: False,
                               command=lambda script, extra=(): [script, *extra],
                               log=lambda msg, **k: self.logged.append(msg))

    def shoot(self, refines, ctx=None, **kw):
        shop = to.Shop(ctx or self.ctx(), ["--from-refs", "--no-ends", "--approved=render"], spawn=self.spawn,
                       sleep=lambda s: None, code=CODE, refine=refines, **kw)
        shop.run()
        return shop

    def refines(self):
        return [args for script, args in self.spawned if script == to.REFINE_SCRIPT]


def test_a_take_that_passed_its_dq_is_refined_on_the_gpu_after_the_renders(tmp_path):
    w = World(tmp_path)
    w.shoot(Refines({0: 110.0, 2: 220.0}), early=True)
    scripts = [s for s, _ in w.spawned]
    assert scripts.index(to.REFINE_SCRIPT) > scripts.index(to.RENDER)
    got = sorted(int(a) for args in w.refines() for a in args if a.isdigit())
    assert got == [0, 2] and all("--within=takes" in args for args in w.refines())


def test_a_take_with_a_dq_cure_is_retaken_not_refined(tmp_path):
    w = World(tmp_path, faults={0: ["gait"]})
    w.shoot(Refines({0: 110.0, 1: 110.0}), early=True)
    refined = {int(a) for args in w.refines() for a in args if a.isdigit()}
    assert 0 not in refined and 1 in refined


def test_nothing_owed_spawns_no_refine(tmp_path):
    w = World(tmp_path)
    w.shoot(Refines({}), early=True)
    assert w.refines() == []


def test_no_refine_bookkeeping_is_the_lanes_as_they_were(tmp_path):
    w = World(tmp_path)
    w.shoot(None, early=True)
    assert w.refines() == []


def test_the_reserve_cuts_the_refine_first_and_says_so(tmp_path):
    w = World(tmp_path)
    owed_after = Budget(5 * 3600, EPISODE_SHARES).owed_after("09")
    refines = Refines({0: 220.0})
    w.shoot(refines, ctx=w.ctx(spent=6 * 3600 - owed_after - 600.0), early=True)
    assert w.refines() == [] and refines.cuts == [([0], 220.0)]
    assert any("REFINE CUT" in m for m in w.logged)
    assert all("--ceiling-spent" not in args for s, args in w.spawned if s == to.CHECK), "no check was cut"


def test_a_take_is_refined_once_per_pass(tmp_path):
    w = World(tmp_path)
    w.shoot(Refines({1: 110.0}), early=True)
    assert sum(args.count("1") for args in w.refines()) == 1
