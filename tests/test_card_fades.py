"""The title card fades up and fades down; it never hard-cuts."""
from studio.card_fade import IN_S, OUT_S, card_fades


def test_a_four_second_card_fades_up_then_down_inside_its_own_length():
    fades = card_fades(4.46)
    assert fades["in_d"] == IN_S
    assert fades["out_start"] == round(4.46 - OUT_S, 3)
    assert fades["out_d"] == OUT_S
    assert fades["out_start"] > fades["in_d"]


def test_a_card_shorter_than_its_fades_still_starts_at_zero():
    fades = card_fades(0.5)
    assert fades["out_start"] == 0.0 and fades["in_d"] <= 0.5


def test_the_filter_strings_carry_both_fades():
    v, a = card_fades(4.46)["video"], card_fades(4.46)["audio"]
    assert "fade=t=in" in v and "fade=t=out" in v
    assert "afade=t=in" in a and "afade=t=out" in a
