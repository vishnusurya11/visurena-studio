"""A sheet is filled, or the cells nobody asked for are paid for anyway.

`chunks` split greedily: ten panels became NINE and ONE.  The one then picked up
whatever END cells were going and landed at two panels in a 2x2 grid -- so the
drawer was told "a 2 by 2 grid of 4 equal panels", drew four, and `attempt`
enumerated the two the packer sent and discarded the rest.

MEASURED on episode 4's parlour: 10 start cells -> 9 + 1, a second sheet of two
panels costing a full $0.13 for half a picture, and the GRID gate refusing the
whole setup.

Balanced, the same ten become 5 + 5, and each half fills its 3x3 with the END
cells `end_choices` already ranks -- two full sheets, nothing discarded.
"""
from studio.episode_seq_board import chunks


def test_a_full_sheet_is_left_alone():
    assert [len(c) for c in chunks(list(range(9)), 9)] == [9]


def test_ten_panels_split_evenly_rather_than_nine_and_one():
    assert [len(c) for c in chunks(list(range(10)), 9)] == [5, 5]


def test_eleven_panels_split_six_and_five():
    assert [len(c) for c in chunks(list(range(11)), 9)] == [6, 5]


def test_nineteen_panels_take_three_sheets_of_seven_six_six():
    assert [len(c) for c in chunks(list(range(19)), 9)] == [7, 6, 6]


def test_every_panel_survives_and_keeps_its_order():
    got = [x for c in chunks(list(range(11)), 9) for x in c]
    assert got == list(range(11))


def test_a_short_setup_is_one_chunk():
    assert [len(c) for c in chunks(list(range(4)), 9)] == [4]
