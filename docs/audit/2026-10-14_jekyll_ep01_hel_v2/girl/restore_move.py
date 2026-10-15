"""Put one shot's motion back to what it was in a saved plan (the move its kept take was
rendered with), through `panel_ladder.write_cured` (motion only, re-signed).

T06 (2026-10-15): the push toward the kerb cured the frozen crane but both of its renders
walked the little man on the spot (G-GAIT shuffle 0.041 / 0.04 heights a step, seen by eye:
his legs step while he crosses ~10 px in two seconds); `take_dq --attempts` kept the crane
render that passed 95, so the plan says the crane again.
Usage: restore_move.py <shot index> <saved plan.json>"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import episode_home, panel_ladder, take_ladder  # noqa: E402

PLAN = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/plan.json"

if __name__ == "__main__":
    index, saved = int(sys.argv[1]), episode_home.read_json(Path(sys.argv[2]))
    doc = episode_home.read_json(PLAN)
    take_ladder.shot_doc(doc, index)["motion"] = take_ladder.shot_doc(saved, index)["motion"]
    panel_ladder.write_cured(PLAN, doc)
    print(take_ladder.shot_doc(doc, index)["motion"])
