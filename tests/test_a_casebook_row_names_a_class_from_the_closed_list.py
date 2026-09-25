"""A casebook row names its fault from the closed class list, or it is no row.

The list is the contract every judge is benched against: a class nobody can
spell the same way twice cannot be counted.  A pass row carries no class; a
fault row must carry one from the list; a path is always relative to the book.
"""
import pytest
from pydantic import ValidationError

from studio import casebook


def fault(**over):
    base = dict(codex="00000000000000", unit="ep02", kind="take", path="episodes/ep02/takes/r2v/T05.mp4",
                sha8="0badcafe", verdict="fault", fault_class="anchored_slide", verdict_by="owner",
                verdict_at="2026-09-23", source="episodes/ep02/story.md#L4")
    return casebook.Row(**(base | over))


def test_a_class_from_the_list_is_accepted():
    assert fault().fault_class == "anchored_slide"


def test_a_class_off_the_list_is_refused():
    with pytest.raises(ValidationError):
        fault(fault_class="smudge")


def test_a_fault_row_must_name_its_class():
    with pytest.raises(ValidationError):
        fault(fault_class=None)


def test_a_pass_row_carries_no_class():
    assert fault(verdict="pass", fault_class=None).fault_class is None


def test_the_list_is_the_memo_list_plus_unknown():
    for name in ("frozen_start", "lettering", "stacked_pictures", "copies", "anchored_slide",
                 "orbit_repeat", "dead_body_moves", "wrong_letters", "plan_story", "line_unheard", "unknown"):
        assert name in casebook.CLASSES
    assert len(set(casebook.CLASSES)) == len(casebook.CLASSES)


def test_an_absolute_path_is_refused():
    with pytest.raises(ValidationError):
        fault(path="D:/somewhere/episodes/ep02/takes/r2v/T05.mp4")


def test_a_verdict_source_is_one_of_the_named_five():
    with pytest.raises(ValidationError):
        fault(verdict_by="reviewer")
    for who in casebook.BY:
        assert fault(verdict_by=who).verdict_by == who
