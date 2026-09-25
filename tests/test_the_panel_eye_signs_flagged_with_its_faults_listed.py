"""The real judge over a board with a calibrated fault in a stored row, no
rung affordable: the eye file is signed `flagged` by judge:panel_eye@1 with
the fault listed by kind and panel, and the note names it.  A clean board is
signed `pass` the same way."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from studio import episode_home, eye_verdict, judged_gate
from studio.gate_policy import Policy
from studio.judges import panel_eye
from studio.ladder import Ladder
from studio.run_budget import EPISODE_SHARES, Budget

AUTO = Policy(state="auto", judge="panel_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best")


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned = []

    def learn(self, learning):
        self.learned.append(learning)


def board_of(tmp_path, flags: list[str]) -> tuple[Path, dict]:
    home = tmp_path / "book" / "episodes" / "ep01"
    board = home / "storyboard"
    board.mkdir(parents=True)
    Image.new("RGB", (64, 64), (50, 50, 50)).save(board / "shot_01.png")
    episode_home.write_json(board / "panel_dq.json", [{"shot": 1, "passed": not flags, "flags": flags}])
    episode_home.write_json(board / "panel_content.json", [{"shot": 1, "passed": True, "faults": []}])
    plan = {"setups": {"s": {"described": "a yard"}},
            "shots": [{"index": 1, "setup": "s", "size": "wide", "faces": [], "frame": "a yard"}]}
    return board, plan


def tools():
    def run(workflow, values, timeout=0.0):
        return '{"size": "wide", "pictures": 1}' if workflow == panel_eye.CAPTION else "[]"
    return dict(run=run, stage=lambda p: Path(p).stem, reader=lambda p: [],
                detect=lambda rgb: [], embed=lambda rgb, box: None)


def clear(ctx, board, plan):
    return judged_gate.clear(
        ctx, "EYE_PANELS", judge=lambda: panel_eye.judge(board.parent, plan, **tools()),
        sign=lambda v: eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), v),
        ladder=judged_gate.Rungs(Ladder([], "keep_best"), take=lambda *a: None),
        terminal=lambda v: v, policy=AUTO)


def test_a_calibrated_row_ends_flagged_with_the_fault_listed(tmp_path):
    ctx = Ctx(tmp_path)
    board, plan = board_of(tmp_path, ["stacked"])
    signed = clear(ctx, board, plan)
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "flagged" and doc["signed_by"] == "judge:panel_eye@1"
    assert doc["terminal"] == "keep_best"
    assert [(f["kind"], f["where"]) for f in doc["faults"]] == [("stacked", "shot_01")]
    assert doc["faults"][0]["evidence"]["calibrated"] is True
    assert "stacked at shot_01" in doc["note"] and doc["note"].endswith("-> keep_best")
    assert eye_verdict.passed(board, [board / "shot_01.png"])
    assert ctx.learned[-1].terminal and ctx.learned[-1].gate == "EYE_PANELS"


def test_a_clean_board_is_signed_pass_by_the_judge(tmp_path):
    ctx = Ctx(tmp_path)
    board, plan = board_of(tmp_path, [])
    doc = json.loads(clear(ctx, board, plan).read_text(encoding="utf-8"))
    assert doc["verdict"] == "pass" and doc["signed_by"] == "judge:panel_eye@1"
    assert doc["faults"] == [] and "1 read" in doc["note"] and ctx.learned == []


def test_the_judge_names_itself_and_counts_its_reads(tmp_path):
    board, plan = board_of(tmp_path, [])
    verdict = panel_eye.judge(board.parent, plan, **tools())
    assert verdict.judge == "panel_eye" and verdict.version == "1"
    assert verdict.signer == "judge:panel_eye@1" and verdict.reads == 1 and verdict.confidence == 1.0
