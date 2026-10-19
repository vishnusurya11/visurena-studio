"""P05 replay R6 ($0, CPU): Jekyll ep01's own plan.json, panel_dq.json, panel_content.json (copies under
tests/fixtures/ep01_replay/P05/) judged by the panel eye with fake readers.  A 2-panel rewind gives 2
reads and 26 cache hits; priced at ep01's measured seconds per cold read the step-08 projection is
under the 50 min cap.  The four whole-board passes ep01 ran were 1076, 554, 676 and 445 s
(timing.jsonl), 66 min for step 08 in all."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from studio.judges import panel_eye

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P05"
PASSES_S = (1076.2, 553.8, 676.4, 444.6)
STEP_08_S = 66 * 60
CAP_S = 50 * 60


def board_of(tmp_path):
    home = tmp_path / "book" / "episodes" / "ep01"
    board = home / "storyboard"
    board.mkdir(parents=True)
    plan = json.loads((FIX / "plan.json").read_text(encoding="utf-8"))
    for name in ("panel_dq.json", "panel_content.json"):
        shutil.copy(FIX / name, board / name)
    for shot in plan["shots"]:
        Image.new("RGB", (64, 64), (shot["index"] * 8, 40, 40)).save(board / f"shot_{shot['index']:02d}.png")
    return home, board, plan


def readers(seen):
    def run(workflow, values, timeout=0.0):
        return '{"size": "medium", "pictures": 1}' if workflow == panel_eye.CAPTION else "[]"

    def detect(rgb):
        seen["n"] += 1
        return []
    return dict(run=run, stage=lambda p: Path(p).stem, reader=lambda p: [], detect=detect, embed=lambda rgb, box: None)


def rewind(board, shots):
    for i in shots:
        Image.new("RGB", (64, 64), (250, i, 7)).save(board / f"shot_{i:02d}.png")


def test_a_two_panel_rewind_reads_two_panels_and_hits_the_cache_for_26(tmp_path):
    home, board, plan = board_of(tmp_path)
    assert len(plan["shots"]) == 28
    seen = {"n": 0}
    cold = panel_eye.judge(home, plan, **readers(seen))
    assert cold.evidence["reads"] == 28 and cold.evidence["cache_hits"] == 0
    rewind(board, (7, 21))
    again = panel_eye.judge(home, plan, **readers(seen))
    assert again.evidence["reads"] == 2 and again.evidence["cache_hits"] == 26
    assert again.reads == 28 and again.evidence["unread_for_time"] == []


def test_the_step_08_projection_is_under_the_50_minute_cap(tmp_path):
    cold_per_panel = PASSES_S[0] / 28
    eye_before = sum(PASSES_S)
    projected_eye = PASSES_S[0] + 3 * 2 * cold_per_panel        # one cold pass, then three 2-panel rewinds
    projected_step = STEP_08_S - eye_before + projected_eye
    assert projected_step < CAP_S
    assert round(projected_step / 60, 1) == 41.9 and STEP_08_S > CAP_S      # ep01 as run: 66 min, over the cap
