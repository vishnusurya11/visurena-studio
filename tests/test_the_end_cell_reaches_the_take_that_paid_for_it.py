r"""A travelling shot's END cell must reach the take, not just the sheet.

`end_pair_verdict` learned on 2026-09-15 that the 0.45 re-staging floor is a
question about a camera that was TOLD TO STAY, and must not judge a shot whose
camera travels. That fixed the DRAWING side. It did not reach the SPENDING side:

    scripts/episode/takes_r2v.py:287   sq.reaches(start, end, size)
    studio/take_verdict.py:313         sq.reaches(cells / n, cells / end_name, size)

Both omit the new `motion` argument, so `camera_end("")` is `""`, `travels` is
False, and the floor is re-applied at exactly the two places that decide whether
a take is GIVEN its END cell and whether `drift` AIMS at it.

MEASURED on episode 7's six drawn END cells, with and without the motion:

    cell       no motion   with motion   attached to its take
    Q10_0E        True        True             yes
    Q11_0E       False        True             NO
    Q14_0E       False        True             NO
    Q21_0E        True        True             yes
    Q23_0E        True        True             yes
    Q24_0E       False        True             NO

Three of six. Each was drawn on a paid sheet, survived the sheet gate, was
looked at by eye and found correct -- and was then withheld from the take it
was drawn for, in silence. The half of the fix that cost money is the half that
did not land.

This is the second time in one day that this fix appeared to work and did not:
first because the test built its own seg dict, then because the sheet cache was
keyed on the filename. Both times the artefact was the only witness. So this
test asserts on the REAL cells and the REAL plan, not on constructed inputs.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_home, episode_seq_board as sq

BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"
CELLS = BOOK / "episodes/ep07/boards/cells"


def ep07():
    if not (BOOK / "episodes/ep07/plan.json").exists():
        pytest.skip("episode 7 is not on this disk")
    return episode_home.load_plan(BOOK, 7)


def test_reaches_takes_the_motion_and_uses_it():
    """The signature, and that the argument is not merely accepted and ignored."""
    if not CELLS.exists():
        pytest.skip("episode 7 cells are not on this disk")
    shots = {s.index: s for s in ep07().shots}
    start, end = CELLS / "Q11_0.png", CELLS / "Q11_0E.png"
    if not end.exists():
        pytest.skip("Q11_0E is not on disk")
    said = shots[11].motion
    assert sq.camera_end(said), "shot 11's camera travels; the fixture is wrong"
    assert sq.reaches(start, end, shots[11].size, said) is True


def test_every_drawn_end_cell_of_episode_7_reaches_its_take():
    """The measurement that found this. Each of these was drawn, paid for, and
    judged correct by eye; three were withheld."""
    if not CELLS.exists():
        pytest.skip("episode 7 cells are not on this disk")
    shots = {s.index: s for s in ep07().shots}
    withheld = []
    for end in sorted(CELLS.glob("Q*_0E.png")):
        n = int(end.name[1:3])
        shot = shots.get(n)
        if shot is None:
            continue
        if not sq.reaches(CELLS / f"Q{n:02d}_0.png", end, shot.size, shot.motion):
            withheld.append(end.name)
    assert withheld == [], f"drawn END cells that cannot reach their take: {withheld}"


def test_the_built_cards_actually_carry_them():
    """Not the verdict but the ARTEFACT: does the take card the renderer is given
    list the END cell among its reference images?

    This asserts on the cards as `takes_r2v --prompts` builds them, which is the
    path a render takes. It does NOT assert on episode 7's shipped shots.json:
    that episode went out with Q11_0E, Q14_0E and Q24_0E withheld, and it is
    published. The defect is recorded in the module docstring; the guarantee is
    for episode 8 onward."""
    made = BOOK / "episodes/ep07/takes/r2v/prompts.json"
    if not made.exists():
        pytest.skip("run takes_r2v --prompts first; it is free")
    cards = json.loads(made.read_text(encoding="utf-8"))
    cards = cards if isinstance(cards, list) else cards.get("cards", [])
    carried = {r for c in cards for r in c.get("refs", []) if r.endswith("E.png")}
    drawn = {p.name for p in CELLS.glob("Q*_0E.png")} if CELLS.exists() else set()
    if not drawn:
        pytest.skip("no END cells on disk")
    assert drawn - carried == set(), f"drawn END cells not given to any take: {sorted(drawn - carried)}"


def test_a_locked_shot_still_loses_a_restaged_end():
    """The floor is not gone, only scoped. Episode 2's fault must still be caught."""
    said = "The camera is static across the whole shot; Holmes raises the glass."
    assert sq.end_pair_verdict(0.072, motion=said) == "restaged"
