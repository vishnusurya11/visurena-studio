"""The panel ladder redraws at most `max_grids` DISTINCT grids per episode
(gates.yaml: 2).  When faults sit in three grids, the first two climb both
rungs and the third is never drawn again: its panel is kept as it stands and
the terminal verdict lists its fault, flagged."""
from __future__ import annotations

import json
from pathlib import Path

from studio import episode_home, eye_verdict, grid_layout, judged_gate, panel_ladder
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.run_budget import EPISODE_SHARES, Budget

CODEX = "20260901000001"
AUTO = Policy(state="auto", judge="panel_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best", max_grids=2)
PLAN = {"setups": {"a": {"described": "a"}, "b": {"described": "b"}, "c": {"described": "c"}},
        "shots": [{"index": i, "setup": s, "size": "wide", "frame": "a place"} for i, s in enumerate("abc", 1)]}


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit, self.number, self.book_id = "episode", "ep03", 3, CODEX
        self.book_dir = tmp_path / "book"
        self.home = episode_home.home(self.book_dir, 3)
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned, self.launched = [], []

    def learn(self, learning):
        self.learned.append(learning)

    def run_script(self, script, *extra, gpu=False, clock=None):
        """The fake render: grids.py leaves its grid on disk, as the real one does."""
        self.launched.append([script, *extra])
        plain = [a for a in extra if not a.startswith("--")]
        row = {"setup": plain[0], "cols": int(plain[1]), "rows": int(plain[2]), "tag": plain[3] if len(plain) > 3 else ""}
        (self.home / "storyboard" / "grids" / f"{grid_layout.name_of(self.number, row)}.png").write_bytes(b"drawn")
        return 0


def board_of(ctx) -> Path:
    ctx.home.mkdir(parents=True)
    (ctx.home / "plan.json").write_text(json.dumps(PLAN), encoding="utf-8")
    rows = grid_layout.layout(PLAN["setups"], PLAN["shots"])
    grid_layout.write(ctx.home, rows)
    grids = ctx.home / "storyboard" / "grids"
    grids.mkdir(parents=True)
    for row in rows:
        (grids / f"{grid_layout.name_of(3, row)}.png").write_bytes(b"grid")
    for i in (1, 2, 3):
        (ctx.home / "storyboard" / f"shot_{i:02d}.png").write_bytes(bytes([i]) * 8)
    return ctx.home / "storyboard"


def failing() -> Verdict:
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=3,
                   faults=[Fault(kind="stacked", where=f"shot_{i:02d}") for i in (1, 2, 3)])


def test_only_two_grids_climb_and_the_third_is_flagged(tmp_path, monkeypatch):
    ctx = Ctx(tmp_path)
    board = board_of(ctx)
    monkeypatch.setattr(episode_home, "write_plan", lambda out, doc: episode_home.write_json(out, doc))
    climb = panel_ladder.climb(ctx, lambda: None, cap=AUTO.max_grids)
    signed = judged_gate.clear(
        ctx, "EYE_PANELS", judge=failing,
        sign=lambda v: eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), v),
        ladder=climb.rungs, terminal=climb.keep_best, policy=AUTO)
    drawn = [cmd[1] for cmd in ctx.launched]                      # the setup argument of grids.py
    assert drawn == ["a", "b", "a", "b"]
    assert sorted(p.name for p in (board / "superseded").iterdir()) == sorted(
        f"ep03_grid_{s}_1x1_v{k}.png" for s in "ab" for k in (1, 2))
    assert (board / "grids" / "ep03_grid_c_1x1.png").exists()
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "flagged" and doc["terminal"] == "keep_best"
    assert [f["where"] for f in doc["faults"]] == ["shot_01", "shot_02", "shot_03"]
    assert [f["evidence"]["climbed"] for f in doc["faults"]] == [True, True, False]


def test_the_cap_counts_distinct_grids_not_renders():
    climb = panel_ladder.Climb(None, Path("."), lambda: None, cap=2)
    rows = [{"setup": s, "cols": 1, "rows": 1, "shots": [i]} for i, s in enumerate("abc", 1)]
    first = climb.climbing(rows, [1, 2, 3])
    assert [r["setup"] for r in first] == ["a", "b"]
    again = climb.climbing(rows, [1, 2, 3])
    assert [r["setup"] for r in again] == ["a", "b"]
    assert [r["setup"] for r in climb.kept(rows, [1, 2, 3])] == ["c"]
