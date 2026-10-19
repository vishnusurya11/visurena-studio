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
    for gate in ("house_style.faults", "plan_gates.chapter_faults", "plan_gates.advisories", "series_rate",
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


def test_the_dead_packer_is_gone_and_the_one_per_take_row_reads_the_takes_own_budget():
    """`packed_shots` called the packer with the legacy 8 s budget (dead code since 5c23230
    pointed every caller at `episode_takes.budget_for`); the ONE PER TAKE row is the live one."""
    import plan_check

    src = inspect.getsource(plan_check)
    assert not hasattr(plan_check, "packed_shots")
    assert "tk.budget_for(ep)" in src and "ONE PER TAKE" in src


def test_the_take_lint_runs_on_the_dry_built_cards_not_on_raw_fields():
    """The old unpaced_shots advisory read raw plan fields the builder then
    rewrote ('the built prompt may differ') and is gone; the G-TAKELINT gate
    runs the REAL lint on dry-built cards (takes_r2v.dry_faults) and the ROW
    TEXT gate lints the injected row texts where they are stored."""
    import plan_check

    src = inspect.getsource(plan_check)
    assert "def unpaced_shots" not in src
    assert "dry_faults" in src and "take_lint_gate" in src
    assert "row_text_gate" in src and "row_lint" in src
