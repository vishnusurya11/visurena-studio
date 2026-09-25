"""A panel fault climbs: redraw_grid_seed (the old grid moved to superseded/,
grids.py on a bumped seed, the panels and both machine gates rebuilt), then
reprose (the cell prose cured through write_plan, the grid redrawn), then the
terminal keep_best signs flagged with the faults listed, learns, and leaves an
audit row.  No verdict file exists while the ladder climbs."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from studio import audit_rows, episode_home, eye_verdict, grid_layout, judged_gate, panel_ladder
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.run_budget import EPISODE_SHARES, Budget

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"
CODEX = "20260901000001"
AUTO = Policy(state="auto", judge="panel_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best", max_grids=2)


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit, self.number, self.book_id = "episode", "ep05", 5, CODEX
        self.book_dir = tmp_path / "book"
        self.home = episode_home.home(self.book_dir, 5)
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned, self.launched = [], []

    def learn(self, learning):
        self.learned.append(learning)

    def run_script(self, script, *extra, gpu=False, clock=None):
        """The fake render: grids.py leaves its grid on disk, as the real one does."""
        self.launched.append([script, *extra])
        plain = [a for a in extra if not a.startswith("--")]
        row = {"setup": plain[0], "cols": int(plain[1]), "rows": int(plain[2]), "tag": plain[3] if len(plain) > 3 else ""}
        for ext in ("png", "json", "txt"):
            (self.home / "storyboard" / "grids" / f"{grid_layout.name_of(self.number, row)}.{ext}").write_bytes(b"drawn")
        return 0


def board_of(ctx) -> tuple[Path, list[dict]]:
    """A plan the contract accepts, its layout, one grid file per row, one panel per shot."""
    ctx.home.mkdir(parents=True)
    shutil.copy(PLAN, ctx.home / "plan.json")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    rows = grid_layout.layout(plan["setups"], plan["shots"])
    grid_layout.write(ctx.home, rows)
    grids = ctx.home / "storyboard" / "grids"
    grids.mkdir(parents=True)
    for row in rows:
        for ext in ("png", "json", "txt"):
            (grids / f"{grid_layout.name_of(5, row)}.{ext}").write_text(ext, encoding="utf-8")
    for shot in plan["shots"]:
        (ctx.home / "storyboard" / f"shot_{shot['index']:02d}.png").write_bytes(bytes([shot["index"]]) * 8)
    return ctx.home / "storyboard", rows


def failing(*wheres: str) -> Verdict:
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=25,
                   faults=[Fault(kind="clones", where=w, evidence={"cosine": 0.8}) for w in wheres])


def test_seed_then_reprose_then_flagged(tmp_path):
    ctx = Ctx(tmp_path)
    board, rows = board_of(ctx)
    grid = next(r for r in rows if 9 in r["shots"])
    name = grid_layout.name_of(5, grid)
    rebuilt, files_while_climbing = [], []
    reads = iter([failing("shot_09"), failing("shot_09"), failing("shot_09")])

    def rebuild():
        rebuilt.append(len(ctx.launched))
        files_while_climbing.append(sorted(p.name for p in board.glob("eye_*")))

    signed = judged_gate.clear(
        ctx, "EYE_PANELS", judge=lambda: next(reads),
        sign=lambda v: eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), v),
        ladder=panel_ladder.rungs(ctx, rebuild, cap=AUTO.max_grids),
        terminal=panel_ladder.keep_best, policy=AUTO)

    argv = grid_layout.argv(grid)
    assert ctx.launched == [["scripts/episode/grids.py", *argv, "--seed-bump=1"],
                            ["scripts/episode/grids.py", *argv, "--seed-bump=2"]]
    assert rebuilt == [1, 2] and files_while_climbing == [[], []]
    superseded = sorted(p.name for p in (board / "superseded").iterdir())
    assert superseded == sorted(f"{name}_v{k}.{ext}" for k in (1, 2) for ext in ("png", "json", "txt"))
    assert (board / "grids" / f"{name}.png").read_bytes() == b"drawn"       # the fresh render stands

    plan = json.loads((ctx.home / "plan.json").read_text(encoding="utf-8"))
    frame = next(s["frame"] for s in plan["shots"] if s["index"] == 9)
    assert frame.startswith(panel_ladder.cure("clones", {}))

    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "flagged" and doc["terminal"] == "keep_best"
    assert doc["signed_by"] == "judge:panel_eye@1" and doc["faults"][0]["where"] == "shot_09"
    assert [(l.action, l.terminal) for l in ctx.learned] == [
        ("redraw_grid_seed", False), ("reprose", False), ("keep_best", True)]
    assert audit_rows.load(ctx.book_dir)[0].gate == "EYE_PANELS"


def test_a_pass_after_the_seed_rung_never_reproses(tmp_path):
    ctx = Ctx(tmp_path)
    board, rows = board_of(ctx)
    before = (ctx.home / "plan.json").read_text(encoding="utf-8")
    reads = iter([failing("shot_09"), Verdict(judge="panel_eye", version="1", passed=True, confidence=1.0, reads=25)])
    signed = judged_gate.clear(
        ctx, "EYE_PANELS", judge=lambda: next(reads),
        sign=lambda v: eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), v),
        ladder=panel_ladder.rungs(ctx, lambda: None, cap=2), terminal=panel_ladder.keep_best, policy=AUTO)
    assert len(ctx.launched) == 1 and ctx.launched[0][-1] == "--seed-bump=1"
    assert (ctx.home / "plan.json").read_text(encoding="utf-8") == before
    assert json.loads(signed.read_text(encoding="utf-8"))["verdict"] == "pass"
    assert audit_rows.load(ctx.book_dir) == []


def test_the_rungs_are_priced_at_a_grid_each_under_keep_best():
    ladder = panel_ladder.rungs(Ctx(Path(".")), lambda: None).ladder
    assert [(r.name, r.tries) for r in ladder.rungs] == [("redraw_grid_seed", 1), ("reprose", 1)]
    assert all(r.cost_seconds == panel_ladder.GRID_SECONDS for r in ladder.rungs)
    assert ladder.terminal == "keep_best"
