"""H3's grid, and what happens to values that miss it."""
import pytest

from studio.h3 import (MAX_PIXELS, NATIVE_H, NATIVE_W, check_canvas, frames_for,
                       legal_frames, seconds_for)


class TestFrameGrid:
    @pytest.mark.parametrize("n", [5, 22, 39, 56, 73, 90, 107, 124, 141, 243, 362])
    def test_known_legal_counts_are_unchanged(self, n):
        assert legal_frames(n) == n

    def test_an_off_grid_count_rounds_up_not_down(self):
        assert legal_frames(240) == 243

    def test_below_the_floor_clamps_to_the_floor(self):
        assert legal_frames(1) == 5

    def test_every_result_is_on_the_grid(self):
        assert all(legal_frames(n) % 17 == 5 for n in range(1, 400))

    def test_ten_seconds_is_the_243_frame_unit(self):
        assert frames_for(10.0) == 243
        assert round(seconds_for(243), 2) == 10.12

    def test_a_two_second_cut_gets_at_least_two_seconds(self):
        assert seconds_for(frames_for(2.0)) >= 2.0

    def test_frames_never_come_up_short_of_the_ask(self):
        """Rounding UP matters: a short clip leaves a hole in the cut."""
        for tenths in range(5, 150):
            want = tenths / 10
            assert seconds_for(frames_for(want)) >= want

    def test_zero_duration_is_rejected(self):
        with pytest.raises(ValueError, match="must be positive"):
            frames_for(0)


class TestCanvas:
    def test_native_canvas_passes(self):
        check_canvas(NATIVE_W, NATIVE_H)

    def test_native_canvas_sits_exactly_on_the_pixel_cap(self):
        assert NATIVE_W * NATIVE_H == MAX_PIXELS

    def test_off_grid_canvas_is_rejected(self):
        with pytest.raises(ValueError, match="not a multiple of 32"):
            check_canvas(1280, 704 + 8)

    def test_oversized_canvas_is_rejected_rather_than_silently_scaled(self):
        with pytest.raises(ValueError, match="exceeds"):
            check_canvas(1920, 1088)
