"""G-LOOK: a picture with no black in it reads as a print, not a projection.

MEASURED 2026-09-16 (`docs/analysis/ep08_ep09_why_worse.md`): global contrast is
the SAME across episodes 5-9; what changed is the floor. 5th-percentile luma on
cells 6.7 / 12.4 / 8.5 (ep05-07) against 36 (ep08) and 23.9 (ep09); near-black
share .43 / .25 / .28 against .03 / .06; and ep09 is one hue -- 71 % of its
pixels orange against 33 % in London. Nothing in DQ measured any of it.

Free: PIL and numpy over files on disk. No model, no GPU, no credit.
"""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from studio import look_gate as lg

BOOK = Path("library/20260822113400_a-study-in-scarlet")


def picture(tmp_path, name, rgb):
    path = tmp_path / name
    Image.fromarray(rgb.astype(np.uint8), "RGB").save(path)
    return path


def gradient_with_black_band(side=256):
    """A grey ramp with a true black band along the bottom: a projection."""
    ramp = np.tile(np.linspace(30, 220, side), (side, 1))
    ramp[-int(side * 0.15):] = 0.0
    return np.stack([ramp] * 3, axis=-1)


def lifted_grey(side=256):
    """A mid-grey field that never reaches the floor: a print."""
    rng = np.random.default_rng(1)
    field = 110.0 + rng.normal(0, 12.0, (side, side))
    return np.clip(np.stack([field] * 3, axis=-1), 40, 255)


def orange_field(side=256):
    """Every pixel orange, with a black band so only the hue is at fault."""
    rgb = np.zeros((side, side, 3))
    rgb[..., 0], rgb[..., 1], rgb[..., 2] = 210.0, 120.0, 30.0
    rgb[-int(side * 0.2):] = 0.0
    return rgb


def many_hues(side=256):
    """Six saturated hues in equal stripes over a black band."""
    rgb = np.zeros((side, side, 3))
    colours = [(220, 40, 40), (220, 160, 30), (40, 200, 40), (30, 200, 200),
               (40, 40, 220), (200, 40, 200)]
    width = side // len(colours)
    for i, colour in enumerate(colours):
        rgb[:, i * width:(i + 1) * width] = colour
    rgb[-int(side * 0.2):] = 0.0
    return rgb


class TestTheBlackFloor:
    def test_a_gradient_with_a_black_band_has_a_floor(self, tmp_path):
        got = lg.judge(picture(tmp_path, "a.png", gradient_with_black_band()))
        assert got["p5"] <= lg.P5_FLOOR and got["near_black"] >= lg.BLACK_SHARE
        assert "no black floor" not in " ".join(got["faults"])

    def test_a_lifted_mid_grey_field_has_none(self, tmp_path):
        got = lg.judge(picture(tmp_path, "b.png", lifted_grey()))
        assert got["p5"] > lg.P5_FLOOR and got["near_black"] < lg.BLACK_SHARE
        assert any(f.startswith("no black floor") for f in got["faults"])

    def test_luma_is_rec709(self):
        rgb = np.array([[[255.0, 0.0, 0.0], [0.0, 255.0, 0.0], [0.0, 0.0, 255.0]]])
        assert np.allclose(lg.luma(rgb)[0], [0.2126 * 255, 0.7152 * 255, 0.0722 * 255])

    def test_the_verdict_names_the_numbers(self, tmp_path):
        got = lg.judge(picture(tmp_path, "b.png", lifted_grey()))
        said = [f for f in got["faults"] if f.startswith("no black floor")][0]
        assert f"p5 {got['p5']:.1f}" in said and f"near-black {got['near_black']:.2f}" in said


class TestOneHue:
    def test_an_all_orange_field_is_one_hue(self, tmp_path):
        got = lg.judge(picture(tmp_path, "c.png", orange_field()))
        assert got["dominant_share"] > lg.ONE_HUE_SHARE
        assert got["hue_entropy"] < lg.HUE_ENTROPY_FLOOR
        assert any(f.startswith("one hue") for f in got["faults"])

    def test_six_hues_are_not_one(self, tmp_path):
        got = lg.judge(picture(tmp_path, "d.png", many_hues()))
        assert got["dominant_share"] < lg.ONE_HUE_SHARE
        assert got["hue_entropy"] > lg.HUE_ENTROPY_FLOOR
        assert not any(f.startswith("one hue") for f in got["faults"])

    def test_a_grey_picture_has_no_dominant_hue(self, tmp_path):
        got = lg.judge(picture(tmp_path, "e.png", gradient_with_black_band()))
        assert got["dominant_share"] == 0.0

    def test_the_orange_sector_is_named_in_degrees(self, tmp_path):
        got = lg.judge(picture(tmp_path, "c.png", orange_field()))
        assert 0 <= got["dominant_hue"] < 60


class TestTheEpisodeRollUp:
    def test_per_picture_faults_carry_the_file_name(self, tmp_path):
        paths = [picture(tmp_path, "Q00_0.png", lifted_grey()),
                 picture(tmp_path, "Q01_0.png", gradient_with_black_band())]
        said = lg.faults(paths)
        assert any(s.startswith("Q00_0.png: no black floor") for s in said)
        assert not any(s.startswith("Q01_0.png") for s in said)

    def test_an_episode_of_orange_cells_is_one_hue(self, tmp_path):
        paths = [picture(tmp_path, f"Q{i:02d}_0.png", orange_field()) for i in range(3)]
        assert any(s.startswith("episode: one hue") for s in lg.faults(paths))

    def test_an_episode_of_lifted_cells_has_no_black_floor(self, tmp_path):
        paths = [picture(tmp_path, f"Q{i:02d}_0.png", lifted_grey()) for i in range(3)]
        assert any(s.startswith("episode: no black floor") for s in lg.faults(paths))

    def test_a_varied_episode_with_a_floor_rolls_up_clean(self, tmp_path):
        paths = [picture(tmp_path, f"Q{i:02d}_0.png", many_hues()) for i in range(3)]
        assert lg.faults(paths) == []

    def test_no_pictures_is_no_verdict(self):
        assert lg.faults([]) == []


def cells_of(episode: str) -> list[Path]:
    room = BOOK / "episodes" / episode / "boards" / "cells"
    return sorted(p for p in room.glob("*.png") if "." not in p.stem)


@pytest.mark.skipif(not BOOK.exists(), reason="the library is not on this machine")
class TestCalibration:
    """The constants against the pictures they were set on."""

    def test_episode_7_cells_pass_the_roll_up(self):
        said = lg.faults(cells_of("ep07"))
        assert not any(s.startswith("episode:") for s in said), said

    def test_episode_9_cells_fail_the_roll_up_both_ways(self):
        said = [s for s in lg.faults(cells_of("ep09")) if s.startswith("episode:")]
        assert any("no black floor" in s for s in said), said
        assert any("one hue" in s for s in said), said

    def test_the_lamplit_parlour_cell_still_has_a_floor(self):
        """ep09's Q24_0A: luma 40, p5 near 0 -- the drawer does it when asked."""
        got = lg.judge(BOOK / "episodes" / "ep09" / "boards" / "cells" / "Q24_0A.png")
        assert not any(f.startswith("no black floor") for f in got["faults"])
