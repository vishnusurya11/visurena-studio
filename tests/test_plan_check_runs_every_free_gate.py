"""`plan_check` runs every free gate in one command, before anything renders.

MEASURED on episode 11 (2026-09-17): thirteen line runs, because each edit
(the dialogue dial, the turn ratio, the projection, the sync rule, a shot
longer than a take) was found by the NEXT gate on the road, after a GPU stage.
One command that says everything at once turns that loop into two passes.

ep12 (2026-09-17): the QUOTE gate lived only in seq_boards, so a nine-word lift
was found after the lines, respot, timeline and plates had run.  It is here now.
"""
import inspect
import sys

sys.path.insert(0, "scripts/episode")


def test_the_check_names_every_gate_it_runs():
    import plan_check

    src = inspect.getsource(plan_check)
    for gate in ("house_style.faults", "plan_gates.faults", "plan_gates.advisories", "series_rate",
                 "still_motions", "plan_marks", "unbound_cast", "sheet_dq", "refuse_long_shots",
                 "quoted_lines", "book_words"):
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


def test_a_short_shot_that_packs_into_its_neighbours_take_is_named():
    """ep12 shot 21: a 1.7 s silent reaction packed into T20 with shot 20 (5.5 s),
    so one take carried an internal cut the model had to place -- the thing
    one-shot-per-take was written to avoid. The plan check names it first."""
    import plan_check

    class Shot:
        def __init__(self, index, setup, beat, coda):
            self.index, self.setup, self.beat_s, self.coda_s, self.cuts = index, setup, beat, coda, []

    class Line:
        def __init__(self, shot, words):
            self.shot, self.text = shot, " ".join(["w"] * words)

    class Ep:
        shots = [Shot(20, "canyon", 0.6, 0.0), Shot(21, "canyon", 1.2, 0.0), Shot(22, "canyon", 1.0, 0.3)]
        lines = [Line(20, 10), Line(22, 12)]

    packed = plan_check.packed_shots(Ep(), rate=2.86)
    assert packed == [(20, 21)]


def test_a_walk_with_no_pace_is_named_before_the_dry_build():
    """ep12 shot 1: 'leading a horse up the trail' failed L8 NO PACE in the dry
    build, after the sheets were paid for. The plan check reads the same lint."""
    import plan_check

    class Shot:
        def __init__(self, index, frame, motion):
            self.index, self.frame, self.motion = index, frame, motion

    class Ep:
        shots = [Shot(1, "Medium of the trail at dawn.", "Jefferson Hope walks up the trail; his hand tightens."),
                 Shot(2, "Medium of Jefferson Hope walking up the trail at a walking pace.", "his hand tightens.")]

    assert plan_check.unpaced_shots(Ep()) == [(1, "walks")]
