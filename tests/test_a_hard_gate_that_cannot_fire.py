""""It never fires" and "it cannot fire" are different claims.

Two of the take gate's HARD rungs have never fired. Measured over every judged
attempt on disk -- 97 of them, across episodes 1 to 5:

    frozen-at-start   wall 1.00 s    max ever observed 0.750   fired 0 of 97
    frozen-share      wall 0.40      max ever observed 0.340   fired 0 of 97

From which I concluded the walls protected nothing and made both advisory.
`tests/test_take_verdict.py::test_a_frozen_take_fails_hard_and_a_moving_one_passes`
refused it in the same run: iteration 4's T17 ran 14.75 of its 15.0 seconds
frozen -- a share of 0.98 -- and with the rungs advisory that take PASSES.

The inference was backwards. A hard gate that has not fired lately is not dead;
it may be a floor nobody has hit since the things upstream of it improved, and
the case it exists for is in the regression suite precisely because it once
happened. Only "it cannot fire" would justify moving a wall, and 0.98 > 0.40
says it can.

What survives is the narrower, true half: both walls were read on an instrument
the repo has since replaced, so they are UNVERIFIED on the current one rather
than wrong. `motion_gate` now uses block-max bins rather than the old 96x168
global-mean scan, and `frozen_gates` computes the share as
`sum(frozen_spans)/seconds` -- the fraction of runtime inside a >= 0.75 s still
run -- which is a strictly smaller quantity than the `still_share` the
"iteration 3 25 %, iteration 4 55 %" figures were taken from. Verifying them
needs the one thing nobody recorded: which takes a human actually called frozen.

This file exists so the next reader finds the distribution AND the refutation in
the same place, rather than re-deriving the demotion from the same numbers.
"""
from studio import take_verdict as tv


def gate(name, rows):
    return next(g for g in rows if g.name == name)


def a_verdict(leading: float, share: float):
    """The two frozen readings, with everything else clean.

    `lead` is read off the SEGMENTS (`max(s.lead_in_s ...)`), not off a
    take-level field, and `share` off `frozen_spans` over `seconds`."""
    seg = type("S", (), {"lead_in_s": leading})()
    spans = [(0.0, share * 6.0)] if share else []
    return tv.frozen_gates(type("V", (), {
        "seconds": 6.0, "frozen_spans": spans, "segments": [seg],
    })())


def test_the_catastrophic_share_is_above_the_wall():
    """T17 at 0.98 is why the wall is where it is, whatever the last 97 did."""
    assert 0.98 > tv.SHARE_HARD


def test_a_frozen_share_over_the_wall_is_hard():
    assert gate("frozen-share", a_verdict(0.0, 0.98)).hard is True


def test_a_frozen_start_over_the_wall_is_hard():
    assert gate("frozen-at-start", a_verdict(2.0, 0.0)).hard is True


def test_a_share_between_the_advisory_and_the_wall_is_advisory():
    row = gate("frozen-share", a_verdict(0.0, 0.30))
    assert row.ok is False and row.hard is False


def test_the_whole_observed_range_stays_under_the_walls():
    """The 97 attempts: max start 0.750, max share 0.340.  Both rungs report
    clean across all of it, which is the observation the demotion came from --
    kept here so it is not mistaken for evidence the walls are unreachable.

    Note the two rungs spell `hard` differently: `frozen-at-start` sets it
    statically (this rung CAN fail a take) while `frozen-share` sets it per
    reading (this reading DOES).  So the honest assertion for "inside the
    observed range" is `ok`, not `hard`."""
    assert gate("frozen-at-start", a_verdict(0.750, 0.0)).ok is True
    assert gate("frozen-share", a_verdict(0.0, 0.34)).ok is False      # over the 0.20 advisory
    assert gate("frozen-share", a_verdict(0.0, 0.34)).hard is False    # under the 0.40 wall


def test_a_clean_take_reports_clean():
    rows = a_verdict(0.0, 0.0)
    assert gate("frozen-at-start", rows).ok and gate("frozen-share", rows).ok


def test_a_frozen_start_still_costs_score():
    """The penalty is what has actually moved takes -- episode 4's T12 lost two
    rolls to it before its motion was rewritten."""
    assert gate("frozen-at-start", a_verdict(2.0, 0.0)).penalty > 0


def test_the_walls_are_unchanged():
    assert tv.SHARE_HARD == 0.40 and tv.SHARE_ADVISORY == 0.20


def test_the_refutation_is_written_down_beside_the_distribution():
    import inspect
    said = inspect.getsource(tv.frozen_gates)
    assert "0 of 97" in said and "backwards" in said
