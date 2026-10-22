"""The grid draws the room a rise needs: a crane_up from a wide or full puts what the camera rises over in
the top third and the people in the lower half (shot framework A1 / B-5, 2026-10-21).

H3 obeys the first-frame cell and the camera verb, and an overrun invents contradictory content, so a rise
must open on a cell that already holds the place above the figures.  ep01 shot 18 (shipped, verdict 95;
prompt bench T18 rose 4 of 4) was drawn that way: "the two walkers in the BOTTOM half ... pale sky fills the
TOP quarter".  The follow clause (draw the walker side-on) waits for bench R2-7 and is not here."""
from __future__ import annotations

from studio import storyboard_grid as sg

BODY = "Wide down the broad Sunday street as the lawyer and the man about town walk east past the gas lamp."


def test_crane_up_panel_names_top_third():
    cut = sg.framing("wide", True, BODY, "crane_up")
    assert "top third" in cut and "lower half" in cut
    assert "top third" in sg.framing("full", True, BODY, "crane_up")


def test_a_locked_panel_is_unchanged():
    assert sg.framing("wide", True, BODY, "locked") == sg.framing("wide", True, BODY)
    assert sg.framing("wide", True, BODY) == sg.cut_clause("wide", True)


def test_the_grid_reads_each_shots_move_from_its_plan():
    from scripts.episode import grids
    import shot_framework_fixtures as sf
    shots = {s["index"]: s for s in sf.plan()["shots"]}
    as_shot = lambda i: type("S", (), {"motion": shots[i]["motion"], "camera": shots[i]["camera"]})()
    assert grids.move_of(as_shot(18)) == "crane_up" and grids.move_of(as_shot(10)) == "locked"


def test_an_insert_rise_keeps_its_thing_filling_the_frame():
    said = sg.framing("insert", False, "Insert of the gloved hands on the cane.", "crane_up")
    assert said.startswith("the frame is filled by the hands") and "top third" not in said
