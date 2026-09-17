"""`plan_check` runs every free gate in one command, before anything renders.

MEASURED on episode 11 (2026-09-17): thirteen line runs, because each edit
(the dialogue dial, the turn ratio, the projection, the sync rule, a shot
longer than a take) was found by the NEXT gate on the road, after a GPU stage.
One command that says everything at once turns that loop into two passes.
"""
import inspect
import sys

sys.path.insert(0, "scripts/episode")


def test_the_check_names_every_gate_it_runs():
    import plan_check

    src = inspect.getsource(plan_check)
    for gate in ("house_style.faults", "plan_gates.faults", "plan_gates.advisories", "series_rate",
                 "still_motions", "plan_marks", "unbound_cast", "sheet_dq", "refuse_long_shots"):
        assert gate in src, gate


def test_a_shot_longer_than_a_take_is_reported_with_its_seconds():
    import plan_check

    class Shot:
        def __init__(self, index, beat, coda):
            self.index, self.beat_s, self.coda_s = index, beat, coda

    class Line:
        def __init__(self, shot, words):
            self.shot, self.text = shot, " ".join(["w"] * words)

    class Ep:
        shots = [Shot(0, 0.5, 0.0), Shot(1, 1.0, 0.5)]
        lines = [Line(0, 12), Line(1, 18), Line(1, 14)]

    long = plan_check.long_shots(Ep(), rate=2.68, budget=8.0)
    assert [i for i, _ in long] == [1]
    assert long[0][1] > 8.0
