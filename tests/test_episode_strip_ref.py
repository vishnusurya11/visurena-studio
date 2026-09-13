"""A take's own storyboard strip: the panels before, of, and after the take,
side by side with gutters -- continuity without the sheet's other faces."""
from PIL import Image

from studio import episode_strip_ref as sr


def panel(colour):
    return Image.new("RGB", (768, 1344), colour)


def test_the_strip_holds_the_panels_in_order_with_white_gutters():
    strip = sr.compose([panel("red"), panel("green"), panel("blue")], height=672)
    assert strip.height == 672
    assert strip.width == 3 * 384 + 2 * sr.GUTTER
    assert strip.getpixel((0, 0)) == (255, 0, 0)
    assert strip.getpixel((384 + sr.GUTTER // 2, 10)) == (255, 255, 255)
    assert strip.getpixel((strip.width - 1, 10)) == (0, 0, 255)


def test_neighbours_are_the_panel_before_and_after_the_run():
    assert sr.neighbours([3, 4], first=0, last=25) == [2, 3, 4, 5]
    assert sr.neighbours([0], first=0, last=25) == [0, 1]
    assert sr.neighbours([25], first=0, last=25) == [24, 25]
