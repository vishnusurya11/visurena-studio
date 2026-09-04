"""The adapt ladder: a failed gate changes the FORM and keeps the FUNCTION.

Every step in the trailer stage is the same loop: try, gate, climb one rung,
and when the rungs or the time run out take the terminal rung -- which always
exists and never asks.  Each rung taken is a learning.
"""
from studio.ladder import Ladder, Rung, climb
from studio.run_budget import Budget


class Clock:
    t = 0.0

    def __call__(self):
        return self.t


def budget(seconds=1000.0):
    return Budget(ceiling_seconds=seconds, shares={"s": 1.0}, clock=Clock())


def ladder():
    return Ladder(rungs=[Rung("seed", cost_seconds=10, tries=2),
                         Rung("alternate", cost_seconds=10, tries=1)],
                  terminal="card")


def gate_above(threshold):
    def gate(value):
        return value >= threshold, value, threshold
    return gate


class TestPasses:
    def test_first_try_passing_takes_no_rung_and_learns_nothing(self):
        learned = []
        b = budget(); b.start("s")
        out = climb(ladder(), "s", attempt=lambda rung, i: 0.9,
                    gate=gate_above(0.75), budget=b, learn=learned.append)
        assert out.result == 0.9 and out.rungs == [] and learned == []

    def test_second_seed_passing_records_one_learning(self):
        values = iter([0.5, 0.8])
        learned = []
        b = budget(); b.start("s")
        out = climb(ladder(), "s", attempt=lambda rung, i: next(values),
                    gate=gate_above(0.75), budget=b, learn=learned.append)
        assert out.result == 0.8
        assert out.rungs == ["seed"]
        assert learned[0].action == "seed" and learned[0].measured == 0.5

    def test_rungs_are_climbed_in_order_with_their_tries(self):
        seen = []
        b = budget(); b.start("s")
        climb(ladder(), "s", attempt=lambda rung, i: seen.append((rung.name, i)) or 0.0,
              gate=gate_above(0.75), budget=b, learn=lambda l: None)
        assert seen == [("seed", 0), ("seed", 1), ("alternate", 0)]


class TestTerminal:
    def test_all_rungs_failing_ends_on_the_terminal_rung(self):
        learned = []
        b = budget(); b.start("s")
        out = climb(ladder(), "s", attempt=lambda rung, i: 0.1,
                    gate=gate_above(0.75), budget=b, learn=learned.append)
        assert out.terminal and out.result is None
        assert learned[-1].action == "card" and learned[-1].terminal

    def test_no_time_left_goes_terminal_before_retrying(self):
        calls = []
        learned = []
        b = budget(seconds=5.0); b.start("s")
        out = climb(ladder(), "s", attempt=lambda rung, i: calls.append(1) or 0.1,
                    gate=gate_above(0.75), budget=b, learn=learned.append)
        assert calls == [1] and out.terminal
        assert learned[-1].gate == "budget"

    def test_the_first_try_still_runs_with_no_budget_for_a_retry(self):
        """The normal path is not a rung; only RETRIES are budget-gated."""
        b = budget(seconds=15.0); b.start("s")
        out = climb(ladder(), "s", attempt=lambda rung, i: 0.9,
                    gate=gate_above(0.75), budget=b, learn=lambda l: None)
        assert out.result == 0.9
