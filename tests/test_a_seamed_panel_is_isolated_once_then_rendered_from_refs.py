"""The seam rung (C1_verdict #4) and the owner's seam fallback (2026-10-11).

MEASURED (C1_G §3): 16 of 18 seamed WotW panels shipped on keep_best. The
seed bump never cured a seam (ep22 pantry_empty .99/.98/.98, ep14 nine
redraws) and the reprose rung moved nothing on ep22, but a 1x1 grid carried
0/92 seams. So a `seam` or `stacked` fault isolates its shot into its own 1x1
ONCE -- outside the 2-grid cap, which exists for open-ended seed and reprose
climbs -- and writes no reprose. A shot already alone cannot be isolated
again, so the rung is finite by construction.

OWNER RULING 2026-10-11: a shot whose panel is still seamed or stacked after
its isolate renders its take from the reference sheets only (its doubled
panel is never staged: a staged doubled cell is a duplicate-figure source),
ships unattended, and is FLAGGED in the audit sheet.
A recording fake ctx captures run_script; no GPU, no model, no spend.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from studio import audit_rows, eye_verdict, grid_layout, judged_gate, panel_ladder, refs_only
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Rung
from studio.run_budget import EPISODE_SHARES, Budget

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"
AUTO = Policy(state="auto", judge="panel_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best", max_grids=2)


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit, self.number, self.book_id = "episode", "ep05", 5, "20260901000001"
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep05"
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.launched, self.learned = [], []

    def learn(self, learning):
        self.learned.append(learning)

    def run_script(self, script, *extra, gpu=False, clock=None):
        self.launched.append([script, *extra])
        plain = [a for a in extra if not a.startswith("--")]
        row = {"setup": plain[0], "cols": int(plain[1]), "rows": int(plain[2]),
               "tag": plain[3] if len(plain) > 3 else ""}
        name = grid_layout.name_of(self.number, row)
        for ext in ("json", "txt"):
            (self.home / "storyboard" / "grids" / f"{name}.{ext}").write_text(ext, encoding="utf-8")
        Image.new("RGB", (64 * row["cols"], 64 * row["rows"]), "white").save(
            self.home / "storyboard" / "grids" / f"{name}.png")
        return 0


def board_of(ctx, rows: list[dict]) -> Path:
    ctx.home.mkdir(parents=True)
    shutil.copy(PLAN, ctx.home / "plan.json")
    grid_layout.write(ctx.home, rows)
    grids = ctx.home / "storyboard" / "grids"
    grids.mkdir(parents=True)
    for row in rows:
        for ext in ("json", "txt"):
            (grids / f"{grid_layout.name_of(5, row)}.{ext}").write_text(ext, encoding="utf-8")
        Image.new("RGB", (64 * row["cols"], 64 * row["rows"]), "grey").save(grids / f"{grid_layout.name_of(5, row)}.png")
    for i in (14, 15, 16, 17):
        Image.new("RGB", (8, 8), (i, i, i)).save(ctx.home / "storyboard" / f"shot_{i:02d}.png")
    return ctx.home / "storyboard"


def seamed(kind: str = "stacked", where: str = "shot_16") -> Verdict:
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=25,
                   faults=[Fault(kind=kind, where=where, note=f"{kind}: two pictures in one cell")])


SHARED = grid_layout.row("doorway_night", 2, 2, [14, 15, 16, 17])


def test_a_stacked_fault_isolates_its_shot_once_outside_the_cap(tmp_path):
    ctx = Ctx(tmp_path)
    board_of(ctx, [SHARED])
    climb = panel_ladder.climb(ctx, rebuild=lambda only=None: None)
    calls = []
    real = climb.isolate
    climb.isolate = lambda i, *a, **k: calls.append(i) or real(i, *a, **k)
    climb.take(Rung("redraw_grid_seed", panel_ladder.RUNG_SECONDS), 0, seamed())
    assert calls == [16]
    assert climb.redrawn == [] and panel_ladder.load_climbed(ctx.home) == []
    assert grid_layout.read(ctx.home)[-1] == grid_layout.row("doorway_night", 1, 1, [16], tag="s16")
    assert len(ctx.launched) == 4                  # three 1x1s for the rest, one for the shot


def test_a_seam_fault_on_a_shot_already_alone_is_not_curable(tmp_path):
    ctx = Ctx(tmp_path)
    board_of(ctx, [grid_layout.row("doorway_night", 1, 1, [16], tag="s16")])
    climb = panel_ladder.climb(ctx, rebuild=lambda only=None: None)
    assert climb.isolate(16) is False
    assert climb.curable(seamed("seam")) is False


def test_no_reprose_is_written_for_a_stacked_only_verdict(tmp_path):
    ctx = Ctx(tmp_path)
    board_of(ctx, [SHARED])
    before = (ctx.home / "plan.json").read_bytes()
    climb = panel_ladder.climb(ctx, rebuild=lambda only=None: None)
    climb.take(Rung("reprose", panel_ladder.RUNG_SECONDS), 0, seamed())
    assert (ctx.home / "plan.json").read_bytes() == before
    assert "stacked" not in panel_ladder.CURES and "seam" not in panel_ladder.CURES


def test_isolate_then_still_stacked_ends_refs_only_flagged_and_audited(tmp_path):
    ctx = Ctx(tmp_path)
    board = board_of(ctx, [SHARED])
    reads = iter([seamed(), seamed(), seamed()])
    climb = panel_ladder.climb(ctx, rebuild=lambda only=None: None, cap=2)
    signed = judged_gate.clear(
        ctx, "EYE_PANELS", judge=lambda: next(reads),
        sign=lambda v: eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), v),
        ladder=climb.rungs, terminal=climb.keep_best, policy=AUTO)
    assert [l.action for l in ctx.learned] == ["redraw_grid_seed", "keep_best"]
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "flagged" and doc["faults"][0]["evidence"]["refs_only"] is True
    assert refs_only.read(ctx.home) == {16}
    assert audit_rows.load(ctx.book_dir)[0].faults[0]["evidence"]["refs_only"] is True


def test_a_refs_only_shot_stages_no_panel_and_is_never_held_on_it(tmp_path):
    from scripts.episode import takes_r2v
    from studio import episode_home, take_coherence, take_ladder
    from studio.judges import take_eye
    home = episode_home.home(tmp_path, 5)
    (home / "storyboard" / "h3").mkdir(parents=True)
    for i in (3, 4):
        Image.new("RGB", (8, 8)).save(home / "storyboard" / "h3" / f"shot_{i:02d}.png")
        Image.new("RGB", (8, 8)).save(home / "storyboard" / f"shot_{i:02d}.png")
    refs_only.add(home, [4], "stacked after its isolate")
    assert takes_r2v.storyboard_panel(tmp_path, 5, 3) is not None
    assert takes_r2v.storyboard_panel(tmp_path, 5, 4) is None
    assert list(take_coherence.panels(home, [3, 4])) == ["shot_03.png"]
    hard = [Fault(kind=sorted(take_eye.HARD_CONTENT)[0], where="T04")]
    assert take_ladder.still_for(home, 3, hard) is not None
    assert take_ladder.still_for(home, 4, hard) is None
