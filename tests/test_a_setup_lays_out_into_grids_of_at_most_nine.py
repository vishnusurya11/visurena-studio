"""The layout is a rule, not a signature: every setup's shots go into grids of
at most nine cells with cols x rows equal to the shots they hold (a blank
cell is a cell the drawer fills with its own invention), 5 -> 3 + 2, 7 -> 4 + 3,
and a face in a setup of wides gets a 1x1 of its own.  It supersedes the
2x2-minimum question of the 2026-09-22 audit (D3)."""
from __future__ import annotations

from studio import grid_layout as gl


def shots(setup: str, n: int, size: str = "wide", start: int = 1) -> list[dict]:
    return [{"index": start + i, "setup": setup, "size": size} for i in range(n)]


def test_five_is_three_and_two():
    rows = gl.layout({"a": {}}, shots("a", 5))
    assert [(r["cols"], r["rows"]) for r in rows] == [(3, 1), (2, 1)]
    assert [r["shots"] for r in rows] == [[1, 2, 3], [4, 5]]


def test_seven_is_four_and_three():
    rows = gl.layout({"a": {}}, shots("a", 7))
    assert [(r["cols"], r["rows"]) for r in rows] == [(2, 2), (3, 1)]
    assert [r["shots"] for r in rows] == [[1, 2, 3, 4], [5, 6, 7]]


def test_cols_times_rows_is_the_shot_count_and_never_more_than_nine():
    for n in range(1, 31):
        rows = gl.layout({"a": {}}, shots("a", n))
        assert sorted(i for r in rows for i in r["shots"]) == list(range(1, n + 1))
        for r in rows:
            assert r["cols"] * r["rows"] == len(r["shots"]) <= gl.MOST
            assert r["cols"] >= r["rows"]


def test_a_face_in_a_setup_of_wides_gets_its_own_one_by_one():
    mixed = shots("a", 2) + shots("a", 1, "close", 3) + shots("a", 1, "wide", 4)
    rows = gl.layout({"a": {}}, mixed)
    assert [(r["cols"], r["rows"], r["shots"]) for r in rows] == [(3, 1, [1, 2, 4]), (1, 1, [3])]
    assert rows[1]["tag"] == "s03" and not rows[0].get("tag")


def test_faces_together_are_not_split_into_ones():
    rows = gl.layout({"a": {}}, shots("a", 4, "close"))
    assert [(r["cols"], r["rows"]) for r in rows] == [(2, 2)]


def test_every_grid_of_a_setup_has_its_own_name():
    rows = gl.layout({"a": {}}, shots("a", 16))
    assert len({gl.name_of(4, r) for r in rows}) == len(rows) == 2
    assert [r["tag"] for r in rows] == ["a", "b"]


def test_setups_keep_plan_order_and_an_empty_setup_draws_nothing():
    rows = gl.layout({"b": {}, "a": {}, "c": {}}, shots("a", 2) + shots("b", 1, "wide", 3))
    assert [r["setup"] for r in rows] == ["b", "a"]


def test_the_layout_is_written_beside_the_grids(tmp_path):
    rows = gl.layout({"a": {}}, shots("a", 5))
    out = gl.write(tmp_path, rows)
    assert out == tmp_path / "storyboard" / "layout.json"
    assert gl.read(tmp_path) == rows


def test_the_rule_supersedes_the_audit_question_by_date():
    assert "D3" in gl.__doc__ and "2026-09-24" in gl.__doc__
