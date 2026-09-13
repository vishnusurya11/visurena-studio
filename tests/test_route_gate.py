from PIL import Image, ImageDraw

from studio import route_gate as rg


def corridor(door_px: int, extra_white_cuff: bool = False) -> Image.Image:
    im = Image.new("L", (768, 1344), 60)
    d = ImageDraw.Draw(im)
    cx, cy = 384, 500
    d.rectangle((cx - door_px // 3, cy - door_px // 2, cx + door_px // 3, cy + door_px // 2), fill=235)  # blown-out far window
    if extra_white_cuff:
        d.rectangle((100, 700, 160, 730), fill=195)  # a cuff: bright but not blown out
    return im


def test_door_height_finds_the_blown_out_far_window(tmp_path):
    p = tmp_path / "a.png"
    corridor(90, extra_white_cuff=True).save(p)
    assert abs(rg.door_height(p) - 90) <= 6


def test_a_panel_without_a_far_window_carries_no_geography(tmp_path):
    p = tmp_path / "b.png"
    Image.new("L", (768, 1344), 60).save(p)
    assert rg.door_height(p) is None


def test_regressions_flag_a_door_that_shrinks_more_than_a_quarter():
    assert rg.regressions([93, 82, 123, 122]) == []          # a 12 % dip is tolerated
    assert rg.regressions([93, None, 123, 82]) == [3]        # 33 % shrink after the doorway
    assert rg.regressions([None, None]) == []
