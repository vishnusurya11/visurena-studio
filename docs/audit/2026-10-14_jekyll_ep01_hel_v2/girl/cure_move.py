"""The take ladder's move_type rung for one frozen take, written through the plan's own path
(`take_ladder.move_type` -> `panel_ladder.write_cured`: motion only, timing untouched, re-signed).
Usage: cure_move.py <shot index> "<why>"   (T06: frozen-whole 83 % on two seeds, 2026-10-15)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import episode_home, panel_ladder, take_ladder  # noqa: E402
from studio.judges.verdict import Fault  # noqa: E402

PLAN = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/plan.json"

if __name__ == "__main__":
    index, why = int(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else ""
    doc = take_ladder.move_type(episode_home.read_json(PLAN), index, [Fault(kind="frozen-whole", where=f"T{index:02d}", note=why)])
    panel_ladder.write_cured(PLAN, doc)
    print(take_ladder.shot_doc(doc, index)["motion"])
