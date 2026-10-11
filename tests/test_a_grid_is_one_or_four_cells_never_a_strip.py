"""G-GRID-SHAPE: a grid holds 1 or 4 cells, never 2 or 3 (C1_verdict #3, 2026-10-11).

MEASURED over all 572 WotW h3 panels (C1_G §3.2): strip grids seamed 15/201
(2x1 8/60, 3x1 7/141), square-ish grids 0/198 (1x1 0/92, 2x2 0/100, 3x2 0/6),
Fisher p = 4.7e-5. Qwen draws its own grid count on a strip canvas: every 2x1
seam is a row at 50 % (a 2x2 drawn on 2:1), every 3x1 seam sits where a
4-column grid's gutters land. A seed bump never cured it (ep22 .99/.98/.98).
So n shots lay out as [4] * (n // 4) + [1] * (n % 4): 3 shots are three 1x1s,
the same 3 MP the 3x1 strip drew.
"""
from __future__ import annotations

from studio import grid_layout as gl


def shots(setup: str, n: int, size: str = "wide", start: int = 1) -> list[dict]:
    return [{"index": start + i, "setup": setup, "size": size} for i in range(n)]


def test_only_one_and_four_are_good():
    assert gl.GOOD == (1, 4)


def test_pieces_are_fours_then_ones():
    assert gl.pieces(6) == [4, 1, 1]
    assert gl.pieces(5) == [4, 1]
    assert gl.pieces(3) == [1, 1, 1]
    assert gl.pieces(2) == [1, 1]
    assert gl.pieces(8) == [4, 4]


def test_no_grid_is_ever_two_or_three_cells():
    for n in range(1, 13):
        assert all(p in (1, 4) for p in gl.pieces(n)), n
        for size in ("wide", "close", "medium"):
            for r in gl.rows_for("a", shots("a", n, size)):
                assert r["cols"] * r["rows"] not in (2, 3), (n, size, r)
                assert r["cols"] * r["rows"] == len(r["shots"])


def test_shots_left_over_are_laid_as_fours_then_tagged_ones():
    assert gl.laid("hall", [14, 15, 17]) == [gl.row("hall", 1, 1, [i], f"s{i}") for i in (14, 15, 17)]
    assert gl.laid("hall", [1, 2, 3, 4], tag="a") == [gl.row("hall", 2, 2, [1, 2, 3, 4], "a")]


def test_a_strip_shape_is_refused():
    for n in (2, 3):
        try:
            gl.shape(n)
        except ValueError:
            continue
        raise AssertionError(f"shape({n}) drew a strip")
