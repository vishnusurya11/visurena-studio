"""G-CROWD (five-expert debate 2026-09-30): a setup whose `crowd` prose stages
people under a shot that declares `extras=0` is born self-contradictory -- the
panel draws the crowd the prose asks for and the count judge then reads the
plan's zero.  Eleven ep14 shots carried this contradiction through three
picture stages; refused at plan time, the fix is one field.  The battery also
LISTS the shots that stage printed matter (the expects-text set), so the
writer and the lettering gate agree on where text belongs before anything is
drawn."""
from __future__ import annotations

from studio import plan_gates


def shot(index=0, extras=0, setup="street", size="wide", frame="", at_rest=""):
    class S:
        pass
    s = S()
    s.index, s.extras, s.setup, s.size, s.frame, s.at_rest = index, extras, setup, size, frame, at_rest
    return s


def ep(crowd="a dozen onlookers press in around the pit", extras=0, size="wide"):
    class Setup:
        pass
    st = Setup()
    st.crowd = crowd

    class E:
        pass
    e = E()
    e.shots, e.setups = [shot(extras=extras, size=size)], {"street": st}
    return e


def test_a_crowded_setup_under_a_shot_with_no_extras_is_refused():
    faults = plan_gates.crowd_faults(ep())
    assert len(faults) == 1 and faults[0].startswith("G-CROWD") and "shot 0" in faults[0]


def test_extras_declared_or_an_empty_crowd_is_clean():
    assert plan_gates.crowd_faults(ep(extras=4)) == []
    assert plan_gates.crowd_faults(ep(crowd="")) == []
    assert plan_gates.crowd_faults(ep(crowd="   ")) == []


def test_a_close_shot_keeps_the_crowd_out_of_frame_and_is_clean():
    assert plan_gates.crowd_faults(ep(size="cu")) == []
    assert plan_gates.crowd_faults(ep(size="mcu")) == []


def test_the_battery_lists_the_shots_that_stage_printed_matter():
    class E:
        pass
    e = E()
    e.shots = [shot(index=3, size="close", frame="a newspaper spread on the table"),
               shot(index=5, size="wide", frame="a newspaper blows down the street"),
               shot(index=8, size="medium", frame="he leans on the gate")]
    assert plan_gates.expects_text(e) == [3]      # the wide's print is unreadable at that size (ep07)
