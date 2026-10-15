"""Shot 6's panel drew the girl twice -- once on the cobbles, once still running in -- and both
panel gates passed it (casebook row, 2026-10-15).  The cure is the panel ladder's own
reprose rung for a `twin` fault (`panel_ladder.reprose` + `write_cured`: the frame led by
the cure phrase, timing untouched, the plan re-signed), applied for the owner's finding.
Usage: cure_shot06.py [kind ...]  (default: twin)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import episode_home, panel_ladder  # noqa: E402
from studio.judges.verdict import Fault  # noqa: E402

PLAN = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/plan.json"
INDEX = 6


def main(kinds: list[str]) -> None:
    faults = [Fault(kind=k, where=f"shot_{INDEX:02d}", note="owner 2026-10-15: the girl drawn twice / unreadable")
              for k in kinds]
    doc = panel_ladder.reprose(episode_home.read_json(PLAN), INDEX, faults)
    panel_ladder.write_cured(PLAN, doc)
    print(next(s for s in doc["shots"] if int(s["index"]) == INDEX)["frame"])


if __name__ == "__main__":
    main(sys.argv[1:] or ["twin"])
