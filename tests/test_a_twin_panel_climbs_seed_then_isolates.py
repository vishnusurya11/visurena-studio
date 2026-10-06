"""On the second rung a twin-faulted shot is ISOLATED into its own tagged 1x1
grid instead of only reprosed: the shared grid loses the shot, both new rows
are drawn, both names are remembered so the cap and resumes hold, and the
shot's frame prose is led by the twin cure.

G-TWIN cure ladder, rung 2.  The tagged-1x1 form is the exact one `rows_for`
already emits for faces, so grids.py and panels.py need nothing new.  A shot
already alone in a 1x1 is left as laid out -- the terminal's business.  A
recording fake ctx captures run_script; no GPU, no model, no spend.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from studio import grid_layout, panel_ladder
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Rung
from studio.run_budget import EPISODE_SHARES, Budget

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit, self.number, self.book_id = "episode", "ep05", 5, "book"
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep05"
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.launched = []

    def learn(self, learning):
        pass

    def run_script(self, script, *extra, gpu=False, clock=None):
        """The fake render: grids.py leaves its grid on disk, as the real one does."""
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
        Image.new("RGB", (64 * row["cols"], 64 * row["rows"]), "grey").save(
            grids / f"{grid_layout.name_of(5, row)}.png")
    return ctx.home / "storyboard"


def twin_verdict(where: str) -> Verdict:
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=25,
                   faults=[Fault(kind="twin", where=where,
                                 note="twin: figure in a long coat x2 (3 figures, 2 distinct)")])


def test_the_reprose_rung_isolates_the_twin_shot_into_a_tagged_1x1(tmp_path):
    ctx = Ctx(tmp_path)
    shared = grid_layout.row("doorway_night", 2, 2, [14, 15, 16, 17])
    board = board_of(ctx, [shared])
    rebuilt = []
    climb = panel_ladder.climb(ctx, rebuild=lambda only=None: rebuilt.append(only))

    climb.take(Rung("reprose", panel_ladder.RUNG_SECONDS), 0, twin_verdict("shot_16"))

    rest = grid_layout.row("doorway_night", 3, 1, [14, 15, 17])
    alone = grid_layout.row("doorway_night", 1, 1, [16], tag="s16")
    assert grid_layout.read(ctx.home) == [rest, alone]
    assert ctx.launched == [
        ["scripts/episode/grids.py", *grid_layout.argv(rest), "--seed-bump=1"],
        ["scripts/episode/grids.py", *grid_layout.argv(alone), "--seed-bump=1"]]
    superseded = sorted(p.name for p in (board / "superseded").iterdir())
    assert superseded == sorted(f"ep05_grid_doorway_night_2x2_v1.{ext}" for ext in ("png", "json", "txt"))
    assert set(panel_ladder.load_climbed(ctx.home)) >= {
        grid_layout.name_of(5, rest), grid_layout.name_of(5, alone)}
    assert rebuilt == [[14, 15, 16, 17]]
    frame = next(s["frame"] for s in json.loads((ctx.home / "plan.json").read_text(encoding="utf-8"))["shots"]
                 if s["index"] == 16)
    assert frame.startswith(panel_ladder.CURES["twin"])


def test_a_shot_already_alone_is_left_as_laid_out(tmp_path):
    ctx = Ctx(tmp_path)
    alone = grid_layout.row("doorway_night", 1, 1, [16], tag="s16")
    board_of(ctx, [alone])
    climb = panel_ladder.climb(ctx, rebuild=lambda only=None: None)
    assert climb.isolate(16) is False
    assert grid_layout.read(ctx.home) == [alone]
    assert ctx.launched == []


def test_the_seed_rung_never_isolates(tmp_path):
    ctx = Ctx(tmp_path)
    shared = grid_layout.row("doorway_night", 2, 2, [14, 15, 16, 17])
    board_of(ctx, [shared])
    climb = panel_ladder.climb(ctx, rebuild=lambda only=None: None)
    climb.take(Rung("redraw_grid_seed", panel_ladder.RUNG_SECONDS), 0, twin_verdict("shot_16"))
    assert grid_layout.read(ctx.home) == [shared], "the first rung is the plain seed redraw"


def test_the_twin_cure_phrase_is_affirmative_and_leads():
    assert panel_ladder.cure("twin", {}) == panel_ladder.CURES["twin"]
    assert "exactly once" in panel_ladder.CURES["twin"]
