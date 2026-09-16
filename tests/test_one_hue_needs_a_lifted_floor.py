"""A candlelit room is one warm hue over black. That is cinema, not a print.

MEASURED building episode 10. Every sheet drew clean and no cell failed the
black floor -- the episode's median 5th-percentile luma is 4.1 with half of
every frame near black, deeper than London's -- and the look gate refused the
whole episode as "one hue" on hue entropy alone (0.81 against 1.10).

    episode     p5 luma   near-black   hue entropy   dominant share
    ep07 good     8.4        0.27          1.41           0.26
    ep09 bad     22.2        0.07          0.85           0.69
    ep10          4.1        0.49          0.81           0.39

Hue entropy is measured over SATURATED pixels only, so a room lit by one lamp
with half the frame black has nothing saturated that is not lamp-coloured, and
scores as ep09 does. What separated ep09 from ep07 was never entropy alone: it
was the dominant share (0.69 against 0.26 -- "94 % of the colour in one orange
band") TOGETHER with a floor that had lifted off black. Reviewer 8 said it in
one line: the loss was "no direction and no floor", not "one hue".

So the wall is the dominant share, and low entropy counts only against a picture
that has also lost its floor. ep07 passes, ep09 fails, ep10 passes -- on the
numbers above, which are pinned here.
"""
from studio import look_gate as lg


def test_a_warm_single_source_scene_over_black_is_not_one_hue():
    """ep10's parlour_evening: share 0.45, entropy 0.64, p5 4.1, near-black 0.56."""
    assert not lg.one_hue(0.45, 0.64, p5=4.1, near_black=0.56)


def test_a_flat_orange_daylight_with_no_floor_is_one_hue():
    """ep09: share 0.69, entropy 0.85, p5 22.2, near-black 0.07."""
    assert lg.one_hue(0.69, 0.85, p5=22.2, near_black=0.07)


def test_low_variety_with_no_floor_is_one_hue_even_under_the_share_wall():
    """The print case: lifted mid-grey with one tint and nothing black in it."""
    assert lg.one_hue(0.40, 0.70, p5=25.0, near_black=0.02)


def test_the_share_wall_alone_is_enough_whatever_the_floor():
    """One hue filling two thirds of the frame is one hue, black or not."""
    assert lg.one_hue(0.70, 1.30, p5=3.0, near_black=0.50)


def test_gaslit_london_passes():
    """ep07: share 0.26, entropy 1.41, p5 8.4, near-black 0.27."""
    assert not lg.one_hue(0.26, 1.41, p5=8.4, near_black=0.27)


def test_the_roll_up_reads_the_floor_before_it_calls_a_hue():
    warm_over_black = [{"p5": 4.0, "near_black": 0.5, "dominant_share": 0.45, "hue_entropy": 0.6}] * 5
    assert lg.roll_up(warm_over_black) == []
    lifted_orange = [{"p5": 22.0, "near_black": 0.07, "dominant_share": 0.69, "hue_entropy": 0.85}] * 5
    assert any("one hue" in f for f in lg.roll_up(lifted_orange))
