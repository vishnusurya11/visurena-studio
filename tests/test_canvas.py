"""The delivery canvas is ONE declaration, and every stage derives from it.

Before this module the aspect was written down seven times -- in frames.py,
storyboard.py, shots.py, takes_r2v.py, assemble.py, title.py and the sheet
prompt -- and the owner's "1:1 this time" (2026-09-12) had to be applied
seven times or the pipeline would cut a square take into a vertical master
and never say so.
"""
import pytest

from studio import canvas, h3


def test_the_vertical_canvas_is_what_we_have_always_rendered():
    assert canvas.size("9:16") == (768, 1344)


def test_the_square_canvas_keeps_h3s_short_edge():
    assert canvas.size("1:1") == (768, 768)


@pytest.mark.parametrize("aspect", canvas.ASPECTS)
def test_every_canvas_is_a_fixed_point_of_h3s_own_transform(aspect):
    """H3 rewrites a canvas it dislikes and says nothing, so the only safe
    canvas is one its own `adapt_canvas` leaves alone."""
    width, height = canvas.size(aspect)
    h3.check_canvas(width, height)


@pytest.mark.parametrize("aspect", canvas.ASPECTS)
def test_the_canvas_is_the_nearest_legal_shape_to_the_declared_ratio(aspect):
    """H3 rounds both edges to a multiple of 32 with the short edge at 768, so
    "9:16" renders 768x1344 -- 4:7, 1.6 % wider than 9:16.  The canvas is the
    NEAREST legal shape, and 2 % is the whole slack the rounding can produce."""
    want_w, want_h = canvas.ratio(aspect)
    width, height = canvas.size(aspect)
    assert abs((width / height) / (want_w / want_h) - 1.0) < 0.02


def test_an_unknown_aspect_is_refused_rather_than_guessed():
    with pytest.raises(KeyError):
        canvas.size("4:3")


def test_the_comfy_label_is_the_resolution_selectors_own_wording():
    assert canvas.comfy_ratio("9:16") == "9:16 (Portrait Widescreen)"
    assert canvas.comfy_ratio("1:1") == "1:1 (Square)"


def test_the_drawer_is_told_the_shape_in_words():
    assert canvas.words("9:16") == "vertical 9:16"
    assert canvas.words("1:1") == "square 1:1"


def test_the_smallest_sheet_that_holds_the_panels_is_chosen():
    assert canvas.grid(4, "1:1") == (2, 2, (2048, 2048))
    assert canvas.grid(9, "1:1") == (3, 3, (2048, 2048))
    assert canvas.grid(3, "9:16") == (3, 1, (1536, 1024))
    assert canvas.grid(9, "9:16") == (3, 3, (2048, 3072))


def test_more_panels_than_any_sheet_holds_is_refused():
    with pytest.raises(ValueError):
        canvas.grid(99, "1:1")


@pytest.mark.parametrize("aspect", canvas.ASPECTS)
def test_every_grids_cell_survives_the_crop_to_the_canvas(aspect):
    """A cell is centre-cropped to the delivery aspect and upscaled to the
    render canvas.  Two things have to hold or a face stops reading: the crop
    keeps most of the drawn cell, and its short edge stays over 512 px (at
    341x512 -- a 1024x1536 sheet -- a face did not survive)."""
    for cols, rows, (sheet_w, sheet_h) in canvas.grids(aspect):
        cell_w, cell_h = sheet_w / cols, sheet_h / rows
        kept_w, kept_h = canvas.crop_to(cell_w, cell_h, aspect)
        assert (kept_w * kept_h) / (cell_w * cell_h) >= 0.80
        assert min(kept_w, kept_h) >= 512


def test_the_crop_keeps_the_whole_cell_when_it_already_matches():
    assert canvas.crop_to(1024, 1024, "1:1") == (1024, 1024)


def test_the_crop_takes_the_narrower_dimension():
    """A 682x1024 cell cropped to 9:16 loses width, keeping its full height."""
    assert canvas.crop_to(682, 1024, "9:16") == (576, 1024)
