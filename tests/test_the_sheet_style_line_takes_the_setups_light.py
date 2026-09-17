"""The sheet's style line names the setup's own source, as the take's does.

ep10's night sheets were drawn under "low side sun, deep black shadow", the
episode line; they came out candlelit only because every `described` names
its source. That is the ep08 configuration (28/28 takes under a London line
over a Utah desert). `house_style.light_for(setup)` exists for the take
prompt (implementer C); the sheet's `style_line` now takes the setup too, and
`plan_gates` carries the picture gates on the same two roads.
"""
from studio import episode_seq_board as sq, house_style, plan_gates
from studio.episode_spec import Setup


def lamp_setup() -> Setup:
    return Setup(described=("Interior, inside a log sitting-room at night with squared log walls closed on "
                            "all four sides: the one oil lamp burning low on the pine table is the only light "
                            "and it comes from the lamp alone, low and yellow, on the faces at the table, and "
                            "everything past an arm's length from the lamp is black"),
                 cast=[], landmark="the oil lamp on the pine table", landmark_at="start",
                 landmark_size="is the height of a hand", route="from the lamp to the dark window",
                 geometry="The lamp stands at the CENTRE of the frame and the room is black at the TOP edge.",
                 crowd="", outdoors=False, props=[])


def test_the_sheet_style_line_names_the_lamp_not_the_sun():
    house_style.adopt("Ferrier's farm, Utah, 1860", "low sidelong light, deep black shadow")
    line = sq.style_line(lamp_setup())
    assert "lamp" in line.lower() and "sun" not in line.lower()


def test_the_sheet_style_line_falls_back_to_the_episode_light_without_a_setup():
    house_style.adopt("Ferrier's farm, Utah, 1860", "low sidelong light, deep black shadow")
    assert "low sidelong light" in sq.style_line()


def test_plan_gates_carry_the_picture_gates():
    import inspect

    assert "picture_gates.faults" in inspect.getsource(plan_gates.faults)
    assert "picture_gates.advisories" in inspect.getsource(plan_gates.advisories)
