"""A 'twin: ...' row line reaches both judges AS KIND 'twin'.

G-TWIN-JUDGES: panel_eye classifies the panel_content line (and CALIBRATED
makes it refuse, not flag-as-thin); take_eye marks it HARD_CONTENT so the
take ladder and the terminal see the kind.  Risk pinned here: if take_eye
collapsed the line to kind 'content' (INPUT_BORNE), the one-retake cure would
be silently skipped.
"""
from studio.judges import panel_eye, take_eye

LINE = "twin: woman in a grey shawl x2 (2 figures, 1 distinct)"


def test_the_panel_eye_classifies_the_twin_line():
    assert panel_eye.content_kind(LINE, {}) == "twin"


def test_the_twin_kind_is_calibrated_so_it_refuses():
    assert "twin" in panel_eye.CALIBRATED


def test_the_panel_content_row_becomes_a_twin_fault():
    rows = [{"shot": 16, "passed": False, "faults": [LINE], "lookalikes": 0}]
    faults = panel_eye.content_faults(rows)
    assert [(f.kind, f.where) for f in faults] == [("twin", "shot_16")]
    assert faults[0].evidence["calibrated"]


def test_the_panel_dq_twin_flag_arrives_by_its_own_name():
    rows = [{"shot": 16, "passed": False, "flags": ["twin"], "cast_faces": 3, "planned": 2}]
    faults = panel_eye.dq_faults(rows)
    assert [(f.kind, f.where) for f in faults] == [("twin", "shot_16")]


def test_the_take_eye_emits_the_twin_kind_hard():
    faults = take_eye.content_faults(5, {"faults": [LINE]})
    assert [(f.kind, f.where) for f in faults] == [("twin", "T05")]
    assert faults[0].evidence["hard"]
    assert "twin" in take_eye.HARD_CONTENT


def test_an_unread_twin_line_stays_unread():
    faults = take_eye.content_faults(5, {"faults": ["unread: twin no distinct"]})
    assert faults[0].kind == "unread"
