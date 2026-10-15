"""T19 (narration, locked medium close on Enfield) fails frozen-whole on every kept attempt
(83 % static); G-DEAD refuses the master on a failed take and its neighbours (8.54 s + 4.96 s)
cannot cover 7.08 s at 1.5x.  The cures, in order, each written through the plan's own path
(`write_plan`, then re-signed by `panel_ladder.write_cured`, motion only, timing untouched):

    move_type [before.json]  the take ladder's move_type rung (`take_ladder.move_type`); with a
                             plan file, on the motion as it stood there (re-run after the aim fix)
    pull_reveal              the third move: push 86 %, follow 83 %, locked 83 % static -- the
                             same fault on three move types is the plan's; a pull-back changes the
                             whole frame's scale (G-MOVE: a pull has no wall), in the ladder's phrasing
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from studio import episode_home, panel_ladder, take_ladder  # noqa: E402
from studio.judges.verdict import Fault  # noqa: E402

PLAN = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/plan.json"
INDEX = 19


def move_type(before: str | None) -> dict:
    doc = episode_home.read_json(PLAN)
    if before:
        take_ladder.shot_doc(doc, INDEX)["motion"] = take_ladder.shot_doc(episode_home.read_json(Path(before)), INDEX)["motion"]
    return take_ladder.move_type(doc, INDEX, [Fault(kind="frozen-whole", where="T19", note="83% static")])


def pull_reveal() -> dict:
    doc = episode_home.read_json(PLAN)
    shot = take_ladder.shot_doc(doc, INDEX)
    rest = [c.strip() for c in shot["motion"].split(";")[1:]]
    shot["motion"] = "; ".join([take_ladder.PHRASING["pull_reveal"].format(aim="Mr. Enfield")] + rest)
    return doc


ORIGINAL = ("The camera pushes in a hand's breadth toward Mr. Enfield's face, across the whole shot; Mr. Enfield "
            "lowers his eyes and shakes his head at himself; he lifts his open hand toward the lawyer")
"""plan.py's own motion for shot 19: the move whose renders scored 100 and 87.6 before the
attempt-swap fault destroyed them (LESSONS, 2026-10-15)."""


def original() -> dict:
    doc = episode_home.read_json(PLAN)
    take_ladder.shot_doc(doc, INDEX)["motion"] = ORIGINAL
    return doc


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "move_type"
    doc = (pull_reveal() if mode == "pull_reveal" else original() if mode == "original"
           else move_type(sys.argv[2] if len(sys.argv) > 2 else None))
    panel_ladder.write_cured(PLAN, doc)
    print(take_ladder.shot_doc(doc, INDEX)["motion"])
