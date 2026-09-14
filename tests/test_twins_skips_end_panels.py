"""An END panel is SUPPOSED to describe its start panel's picture.

`twins` compares panel TEXT for near-duplication, which is right for two
different shots and exactly backwards for an END cell: `end_text` builds an END
panel as "the same place, the same camera and the same light as panel N, drawn
afresh with ..." plus its one change.  High overlap with panel N is the rule
being OBEYED, not broken.

MEASURED on episode 3, 2026-09-13, running the gate over all six setups: 9 hard
findings would have refused 5 of 6 setups, and 6 of the 9 are an END panel
flagged against the panel it closes -- Q01_0E vs panel 5, Q06_0E vs panel 7,
Q07_1E vs panel 3, Q19_0E vs panel 3.

The picture side already judges this pair properly, and in a BAND rather than
under a ceiling: `episode_seq_board.END_FLOOR/END_CEILING` (0.45-0.80) exists
precisely because an END cell that is too DIFFERENT is a re-stage and an END cell
that is too SIMILAR is a copy.  A one-sided text ceiling cannot express that, so
it should not try -- it should leave the pair to the gate that can.

Two panels that are genuinely the same picture are still caught, and an END
panel against an unrelated panel is still caught.  Only the pair an END cell is
defined by is exempt.
"""
from studio.sheet_gate import twins


def panel(shot: int, sub: int, text: str, end: bool = False) -> dict:
    return {"shot": shot, "sub": sub, "end": end, "frame": text, "at_rest": "", "changed": ""}


SAME = ("Medium close on Holmes at the hall's far end with his overcoat buttoned, his head a "
        "quarter of the frame's height, the loose-papered wall at the RIGHT.")


def checks(found):
    return [(f.panel, f.hard) for f in found]


def test_an_end_panel_may_repeat_the_panel_it_closes():
    """Q19_0E against panel 3 -- the shape that refused four ep03 setups."""
    segs = [panel(19, 0, SAME), panel(19, 0, SAME, end=True)]
    assert twins(segs) == []


def test_two_ordinary_panels_that_are_one_picture_are_still_refused():
    segs = [panel(22, 0, SAME), panel(24, 0, SAME)]
    found = twins(segs)
    assert found and any(f.hard for f in found)


def test_an_end_panel_is_still_measured_against_a_panel_it_does_not_close():
    """It is exempt from ITS OWN start panel, not from the whole sheet."""
    segs = [panel(19, 0, "Insert on the yellow plaster, the word in blood-red."),
            panel(22, 0, SAME), panel(22, 0, SAME, end=True)]
    found = twins(segs)
    assert not found or all(f.panel != "22.0E" or "19" not in (f.note or "") for f in found)


def test_the_start_panel_is_not_blamed_for_its_own_end_panel():
    segs = [panel(19, 0, SAME), panel(19, 0, SAME, end=True)]
    assert not [f for f in twins(segs) if f.panel.startswith("19.0") and f.hard]


def test_two_end_panels_are_not_compared_to_each_other():
    """Their text is a TEMPLATE -- `end_text` opens every END cell with "the same
    place, the same camera and the same light as panel N" -- so comparing two of
    them measures the boilerplate, not the pictures. Episode 4's parlour was
    refused for Q10_0E against Q09_0E at 0.772, two different shots' arrivals.

    It is also redundant. If the two START panels differ (this gate checks that)
    and each END is within `END_FLOOR..END_CEILING` of its own start (the picture
    gate checks that), the two ENDs cannot be one picture."""
    segs = [panel(9, 0, "Medium on Holmes at the table."),
            panel(9, 0, SAME, end=True),
            panel(10, 0, "Close on Rance on the sofa."),
            panel(10, 0, SAME, end=True)]
    assert not [f for f in twins(segs) if f.panel.endswith("E") and f.hard]


def test_two_start_panels_that_are_one_picture_are_still_refused_alongside():
    """The exemption is for END-vs-END only; the starts are still judged."""
    segs = [panel(9, 0, SAME), panel(9, 0, SAME, end=True),
            panel(10, 0, SAME), panel(10, 0, SAME, end=True)]
    assert [f for f in twins(segs) if f.hard]
