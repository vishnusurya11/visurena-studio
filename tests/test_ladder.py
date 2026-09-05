"""The adapt ladder: a failed gate changes the FORM and keeps the FUNCTION.

Every step in the trailer stage is the same loop: try, gate, climb one rung,
and when the rungs or the time run out take the terminal rung -- which always
exists and never asks.  Each rung taken is a learning.
"""
from studio.ladder import Climb, Ladder, Rung, climb
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

    def test_every_learning_carries_what_its_attempt_cost(self):
        """Scarlet run 6: 31 learnings, every one `seconds: 0.0`.  A rung's
        cost is the number the budget rung reasons with (`cost_seconds` is a
        guess of 660 s) and the run never measured it."""
        learned = []
        b = budget(); b.start("s")
        clock = b.clock

        def attempt(rung, i):
            clock.t += 12.5 if i == 0 else 30.0
            return 0.5
        climb(ladder(), "s", attempt=attempt, gate=gate_above(0.75), budget=b,
              learn=learned.append)
        assert [l.seconds for l in learned] == [12.5, 30.0, 12.5, 0.0]
        assert learned[-1].terminal

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

    def test_every_learning_names_the_substep_it_was_climbed_for(self):
        """Run 6's two `unbound` learnings say `substep ""`: the retrospect
        cannot tell which character never bound."""
        learned = []
        b = budget(); b.start("s")
        climb(ladder(), "s", attempt=lambda rung, i: 0.1, gate=gate_above(0.75),
              budget=b, learn=learned.append, substep="g_lestrade")
        assert {l.substep for l in learned} == {"g_lestrade"}

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


class TestRounds:
    """The same ladder climbed ONE ATTEMPT PER ROUND, so many climbs share a
    round.  Step 07 renders every beat's next take back to back with the video
    model resident, reads the whole round in one vision session, and settles
    every climb from that round's verdicts."""

    def climbs(self, count=2):
        return [Climb(ladder(), "s", substep=f"B0{n}") for n in range(count)]

    def round_of(self, climbs, b, learn=lambda l: None):
        """What this round is asked for: one (climb, rung, try) per live climb."""
        asked = [(c, c.ask(b, learn)) for c in climbs if not c.done]
        return [(c, w[0], w[1]) for c, w in asked if w is not None]

    def test_each_round_asks_every_live_climb_for_one_attempt(self):
        b = budget(); b.start("s")
        climbs = self.climbs()
        verdicts = iter([0.9, 0.2, 0.8])
        rounds = []
        while True:
            asked = self.round_of(climbs, b)
            if not asked:
                break
            rounds.append([c.substep for c, _, _ in asked])
            for c, rung, _ in asked:
                value = next(verdicts)
                c.settle(rung, value, value >= 0.75, value, 0.75, 12.0, lambda l: None)
        assert rounds == [["B00", "B01"], ["B01"]]
        assert climbs[0].outcome.result == 0.9 and climbs[1].outcome.result == 0.8
        assert climbs[1].outcome.rungs == ["seed"]

    def test_a_climb_out_of_rungs_ends_terminal_when_it_is_next_asked(self):
        learned = []
        b = budget(); b.start("s")
        one = Climb(ladder(), "s", substep="B00")
        for _ in range(3):
            rung, i = one.ask(b, learned.append)
            one.settle(rung, 0.1, False, 0.1, 0.75, 5.0, learned.append)
        assert one.ask(b, learned.append) is None
        assert one.done and one.outcome.terminal and one.outcome.result is None
        assert learned[-1].action == "card" and learned[-1].terminal
        assert one.outcome.rungs == ["seed", "seed", "alternate"]

    def test_a_retry_no_budget_can_pay_for_ends_the_climb_on_the_terminal_rung(self):
        learned = []
        b = budget(seconds=5.0); b.start("s")
        one = Climb(ladder(), "s", substep="B00")
        rung, i = one.ask(b, learned.append)
        one.settle(rung, 0.1, False, 0.1, 0.75, 5.0, learned.append)
        assert one.ask(b, learned.append) is None
        assert one.outcome.terminal and learned[-1].gate == "budget"
        assert learned[-1].threshold == 10 and learned[-1].substep == "B00"

    def test_a_settled_pass_carries_the_rungs_it_took_getting_there(self):
        learned = []
        b = budget(); b.start("s")
        one = Climb(ladder(), "s", substep="B00", gate_name="identity")
        rung, _ = one.ask(b, learned.append)
        one.settle(rung, 0.1, False, 4.0, 3, 900.0, learned.append)
        rung, _ = one.ask(b, learned.append)
        one.settle(rung, 0.9, True, 1.0, 3, 900.0, learned.append)
        assert one.done and one.outcome.result == 0.9 and one.outcome.rungs == ["seed"]
        assert [(l.gate, l.action, l.seconds) for l in learned] == [("identity", "seed", 900.0)]
