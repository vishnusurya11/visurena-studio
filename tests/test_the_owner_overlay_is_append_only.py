"""The owner overlay only ever grows.

`owner.jsonl` is the casebook proper: every remark from now on is appended,
never rewritten, so a later row can never lose an earlier one.  An unverified
row has no place there -- the overlay is where a candidate goes once someone
has confirmed it.
"""
import pytest

from studio import casebook


def row(**over):
    base = dict(codex="00000000000000", unit="ep02", kind="take", path="episodes/ep02/takes/r2v/T05.mp4",
                sha8="0badcafe", verdict="fault", fault_class="anchored_slide", verdict_by="owner",
                verdict_at="2026-09-23", source="audit note")
    return casebook.Row(**(base | over))


def test_a_second_row_is_added_after_the_first(tmp_path):
    first = row()
    second = row(path="episodes/ep02/takes/r2v/T07.mp4", fault_class="lettering")
    casebook.append_owner(tmp_path, first)
    before = (tmp_path / casebook.OWNER).read_text(encoding="utf-8")
    casebook.append_owner(tmp_path, second)
    after = (tmp_path / casebook.OWNER).read_text(encoding="utf-8")
    assert after.startswith(before) and after.count("\n") == 2
    assert [r.path for r in casebook.read_rows(tmp_path / casebook.OWNER)] == [first.path, second.path]


def test_an_unverified_row_is_refused_from_the_overlay(tmp_path):
    with pytest.raises(ValueError):
        casebook.append_owner(tmp_path, row(verdict_by="unverified"))
    assert not (tmp_path / casebook.OWNER).exists()
