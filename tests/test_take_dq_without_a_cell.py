"""THE TAKE WITH NO STORYBOARD CELL -- what the DQ may and may not say about it.

Episode 14 is rendered from the LOCATION PLATE and the CAST CARDS alone: the
paid API that draws the sheets has no credits, so `boards/cells/` is empty and
the takes carry no pins.  Four rows of the ladder are cosines to a cell --
`cut-landing`, `drift`, `coherence off-board`, `last-vs-cell` -- and one,
`foreign`, is a comparison to OTHER pictures that only means anything once the
take's own cells are in the bank.  Read against nothing, every one of them
returns the number that means "clean": 0 missed cuts, end_sim 1.0, 0 foreign
frames.  That is the episode-4 disease with a new cause -- a gate that says
nothing and is counted as a pass.

So: with no cell, those rows print `not measured (no cell)`, carry no value,
fire nothing and score nothing, and `take_dq.row` stops counting them among the
rows that can fire.  Every row that needs only the frames -- frozen, churn, the
unprompted cut, zoom, the picture rows, lip-sync, identity -- keeps working
exactly as it did.

Nothing here decodes a video, loads a model, touches the GPU or spends.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image

from studio import take_coherence as tc, take_verdict as tv

spec = importlib.util.spec_from_file_location(
    "take_dq", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "take_dq.py")
dq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dq)

CELL_ROWS = ["cut-landing", "drift", "coherence off-board", "last-vs-cell"]
CHURN_ONLY = {"frames": 144, "cells": False, "raw_diff": 8.0, "nonrigid": 10.7,
              "hard_cut": 45.0, "hard_cut_at": 33}


def cellless_segment(lead=0.0, share=0.0, seconds=6.0):
    """What `tv.cellless_segments` builds: the freeze numbers, and None for
    every field that is read against a cell."""
    return tv.SegmentReport("", "", 0.0, seconds, lead, share, "hold", None, None, None, 0)


def cellless_verdict(coherence=None, lead=0.0, share=0.0, seconds=6.0, spans=(), foreign=()):
    v = tv.TakeVerdict(14, 0, "T14.mp4", seconds, "narration", [], [cellless_segment(lead, share, seconds)],
                       list(spans), [], list(foreign), coherence if coherence is not None else dict(CHURN_ONLY))
    v.gates = tv.gates(v, None, "", [])
    v.score, v.passed = tv.score(v.gates)
    return v


# ---- which takes have no board ------------------------------------------------

def test_board_absent_is_true_with_no_pins_and_when_the_cells_are_gone(tmp_path):
    assert tv.board_absent(tmp_path, []) is True
    assert tv.board_absent(tmp_path, ["Q14_0.png", "Q14_1.png"]) is True
    assert tv.board_absent(tmp_path / "cells", ["Q14_0.png"]) is True       # the room itself is missing


def test_a_board_with_one_cell_still_on_disk_is_not_absent(tmp_path):
    """A HOLE IN A BOARD IS NOT THE SAME THING AS NO BOARD.  Some cells drawn
    and one missing is an inconsistency, and `cell_signatures` still raises on
    it -- the episode-4 guard is untouched.  Only a take with NOTHING to read
    takes the unmeasured road."""
    Image.new("RGB", (8, 8)).save(tmp_path / "Q14_0.png")
    assert tv.board_absent(tmp_path, ["Q14_0.png", "Q14_1.png"]) is False
    try:
        tv.cell_signatures(tmp_path, ["Q14_0.png", "Q14_1.png"])
        raise AssertionError("a named cell that is not there must raise")
    except FileNotFoundError as e:
        assert "Q14_1.png" in str(e)


# ---- the rows measured against the cell ----------------------------------------

def test_the_cell_rows_report_no_cell_and_fail_nothing():
    """AN ABSENT MEASUREMENT IS NOT A PASS: no value, so nothing can fire, and
    no penalty, so nothing is credited either."""
    rows = {g.name: g for g in cellless_verdict().gates}
    for name in CELL_ROWS:
        g = rows[name]
        assert g.value is None and g.ok and not g.hard and g.penalty == 0.0
        assert g.note == "not measured (no cell)"


def test_the_verdict_line_says_no_cell_on_every_cell_row():
    line = cellless_verdict().line()
    assert "coherence off-board not measured (no cell)" in line
    assert "cut-landing not measured (no cell)" in line and "drift not measured (no cell)" in line
    assert "last-vs-cell not measured (no cell)" in line


def test_foreign_is_not_measured_when_no_cell_was_classified():
    """`foreign` asks "is this frame someone else's picture rather than mine?".
    With no cell of the take's own in the bank `cut_landing.classify` is never
    run, the sample list is empty, and the old row read that as 0 foreign
    frames -- a pass off zero frames of comparison."""
    assert cellless_verdict().gates[2].name == "foreign"
    assert cellless_verdict().gates[2].value is None
    seen = {g.name: g for g in cellless_verdict(foreign=[{"foreign": True}, {"foreign": False}]).gates}
    assert seen["foreign"].value == 1 and not seen["foreign"].ok and seen["foreign"].hard


def test_the_cell_rows_are_unchanged_when_the_cells_were_read():
    """The other side of the wall: with a board, every row reads as before."""
    seg = tv.SegmentReport("Q02_0.png", "Q02_0E.png", 0.0, 5.0, 0.0, 0.0, "hold", 0.9, 0.40, False, 34)
    coh = {"offboard_share": 0.60, "last_vs_cell": 0.08, "hard_cut": 14.9, "nonrigid": 10.7}
    v = tv.TakeVerdict(2, 0, "T02.mp4", 5.0, "narration", [], [seg], [], [], [{"foreign": True}], coh)
    v.gates = tv.gates(v, None, "", [])
    rows = {g.name: g for g in v.gates}
    assert rows["drift"].hard and rows["cut-landing"].hard and rows["foreign"].hard
    assert rows["coherence off-board"].value == 0.60 and rows["last-vs-cell"].value == 0.08
    assert not tv.score(v.gates)[1]


# ---- the rows that need no cell ------------------------------------------------

def test_the_rows_that_need_no_cell_still_fire_without_one():
    """The freeze is read off the motion energy, the churn and the unprompted
    cut off the frame steps: none of the three has ever needed a picture to
    compare against, so none of them goes quiet here."""
    v = cellless_verdict(lead=2.75, share=0.84, spans=[(0.0, 5.0)])
    rows = {g.name: g for g in v.gates}
    assert rows["frozen-at-start"].hard and not rows["frozen-at-start"].ok    # ep05 T21, 2.75 s
    assert not rows["frozen-share"].ok and rows["frozen-share"].value == 0.83
    assert rows["cut"].value == 45.0 and rows["cut"].hard and not rows["cut"].ok
    assert rows["churn"].value == 10.7 and not rows["churn"].ok
    assert not v.passed


def test_a_wide_without_a_cell_keeps_its_hard_churn_wall():
    v = tv.TakeVerdict(14, 0, "T14.mp4", 6.0, "narration", [], [cellless_segment()], [], [], [], dict(CHURN_ONLY))
    wide = {g.name: g for g in tv.gates(v, None, "", [], size="wide")}["churn"]
    assert not wide.ok and wide.hard and "wide" in wide.note


def test_the_lanes_own_rows_are_untouched_by_a_missing_cell():
    """lip-sync, identity and the picture rows read the take, not the board."""
    rows = {g.name: g for g in cellless_verdict().gates}
    assert rows["lip-sync"].note == "n/a narration" and rows["identity"].note == "not measured"
    assert [rows[n].note for n in ("face-at-end", "look", "post-cut", "pulse")] == ["not measured"] * 4
    assert tv.lip_gate("dialogue", {"mux_lag_s": -0.5, "lag_measured": True}, "").hard


def test_the_row_order_is_the_same_with_and_without_a_board():
    """The ladder prints the same sixteen rows either way; four of them say
    they could not read anything."""
    assert [g.name for g in cellless_verdict().gates] == [
        "frozen-at-start", "frozen-share", "foreign", "cut-landing", "drift",
        "coherence off-board", "last-vs-cell", "cut", "churn", "zoom",
        "face-at-end", "look", "post-cut", "pulse", "lip-sync", "identity"]


# ---- the pieces ----------------------------------------------------------------

def test_cellless_segments_keep_the_freeze_numbers_and_measure_no_similarity():
    motion = {"segments": [{"cell": "Q00_0.png", "start_s": 0.0, "end_s": 6.0,
                            "leading_still_s": 1.25, "still_share": 0.3}]}
    segs = tv.cellless_segments([], motion, {})
    assert len(segs) == 1 and segs[0].lead_in_s == 1.25 and segs[0].still_share == 0.3
    assert segs[0].start_sim is None and segs[0].end_sim is None and segs[0].landed is None
    assert segs[0].cell == "" and segs[0].target == ""          # no pin: the gate invents no cell name


def test_cellless_segments_keep_the_pin_names_when_the_take_had_pins():
    """A take pinned to cells that were never drawn still has its segments."""
    motion = {"segments": [{"cell": "Q14_0.png", "start_s": 0.0, "end_s": 3.0,
                            "leading_still_s": 0.0, "still_share": 0.0},
                           {"cell": "Q14_1.png", "start_s": 3.0, "end_s": 6.0,
                            "leading_still_s": 0.5, "still_share": 0.1}]}
    segs = tv.cellless_segments([("Q14_0.png", 0), ("Q14_1.png", 72)], motion, {"Q14_0.png": "dialogue"})
    assert [s.cell for s in segs] == ["Q14_0.png", "Q14_1.png"] and segs[0].kind == "dialogue"
    assert all(s.end_sim is None and s.landed is None for s in segs)


def moving_frames(n: int = 4, size: int = 16) -> np.ndarray:
    """A small grey take: one bright block sliding one pixel a frame."""
    out = []
    for k in range(n):
        f = np.zeros((size, size), dtype=np.uint8)
        f[4:10, 2 + k:8 + k] = 200
        out.append(f)
    return np.stack(out)


def test_coherence_falls_back_to_the_frame_only_numbers_without_a_cell(monkeypatch, tmp_path):
    """No cell to load, so no `load_cells` call and no FileNotFoundError: the
    churn and the unprompted cut are still read, and the dict says `cells:
    False` so the two cosine rows know they have nothing."""
    monkeypatch.setattr(tc, "frames", lambda video, seconds=None: moving_frames())
    m = tv.coherence(tmp_path / "T14.mp4", {"anchors": []}, tmp_path / "cells", 6.0)
    assert m["cells"] is False and m["frames"] == 4
    assert "offboard_share" not in m and "last_vs_cell" not in m
    assert m["nonrigid"] >= 0.0 and m["hard_cut"] >= 0.0 and m["raw_diff"] > 0.0


def test_coherence_still_measures_the_board_when_the_cells_are_there(monkeypatch, tmp_path):
    cells = tmp_path / "cells"
    cells.mkdir()
    Image.fromarray(moving_frames()[0]).convert("RGB").save(cells / "Q14_0.png")
    monkeypatch.setattr(tc, "frames", lambda video, seconds=None: moving_frames())
    m = tv.coherence(tmp_path / "T14.mp4", {"anchors": [["Q14_0.png", 0]]}, cells, 6.0)
    assert "offboard_share" in m and "last_vs_cell" in m and m.get("cells", True) is True


def test_coherence_rows_blank_only_the_two_that_read_the_cell():
    rows = {g.name: g for g in tv.coherence_rows(dict(CHURN_ONLY))}
    assert rows["coherence off-board"].value is None and rows["last-vs-cell"].value is None
    assert rows["cut"].value == 45.0 and rows["churn"].value == 10.7
    assert [g.note for g in tv.coherence_rows({})] == ["not measured"] * 4      # no measurement at all


# ---- the strip and the record ---------------------------------------------------

def test_the_strip_draws_a_take_that_has_no_cell(monkeypatch, tmp_path):
    """`strip_row` used to `Image.open(cells / s.cell)` unconditionally; with no
    cell on disk the whole DQ run died on the report image, after the verdict."""
    monkeypatch.setattr(tv, "sample_frame", lambda video, at: None)
    v = cellless_verdict()
    out = tv.strip(v, tmp_path / "T14.mp4", tmp_path / "cells", tmp_path / "take_T14.png")
    assert out.is_file() and Image.open(out).size[0] > 0


def test_the_strip_labels_the_similarities_it_could_not_read():
    assert tv.sim_text(None) == "n/m" and tv.sim_text(0.873) == "0.87"
    assert tv.cut_text(None) == "not measured" and tv.cut_text(True) == "landed" and tv.cut_text(False) == "MISSED"


def fake_decode(monkeypatch, n: int = 8):
    """Every decode in `tv.measure` replaced by the same tiny synthetic take, and
    the two rows that would re-decode the file themselves switched off: no
    ffmpeg, no GPU, no model, no spend."""
    from studio import motion_gate

    take = np.zeros((n, 336, 192), dtype=np.float32)
    for k in range(n):
        take[k, 40:120, 20 + 4 * k:100 + 4 * k] = 200.0
    monkeypatch.setattr(motion_gate, "frames", lambda video, seconds=None: take)
    monkeypatch.setattr(tc, "frames", lambda video, seconds=None: take.astype(np.uint8))
    monkeypatch.setattr(tv, "zoom_of", lambda video, record, coherence_: {})
    monkeypatch.setattr(tv, "picture_rows", lambda video, record, seconds: tv.unmeasured(
        "face-at-end", "look", "post-cut", "pulse"))


def test_measure_judges_a_take_whose_cells_room_is_empty(monkeypatch, tmp_path):
    """The whole chain, end to end: an empty `boards/cells/` raises nothing, the
    four cell rows and foreign say `no cell`, and the frozen row still reads the
    take.  `cell_signatures`, `load_cells` and `foreign_pictures` are never
    reached -- there is no name for them to resolve."""
    fake_decode(monkeypatch)
    video = tmp_path / "T14.mp4"
    video.write_bytes(b"x")
    (tmp_path / "cells").mkdir()
    v = tv.measure(video, {"index": 14, "anchors": [], "lane": "narration", "refs": []},
                   tmp_path / "cells", 0.33)
    rows = {g.name: g for g in v.gates}
    assert [rows[n].note for n in CELL_ROWS + ["foreign"]] == ["not measured (no cell)"] * 5
    assert v.coherence["cells"] is False and rows["churn"].value is not None
    assert rows["frozen-at-start"].value is not None and len(v.segments) == 1
    assert v.segments[0].end_sim is None and v.bytes == 1


def test_measure_survives_a_cells_room_that_does_not_exist_at_all(monkeypatch, tmp_path):
    """Episode 14 will have no `boards/cells/` directory to glob."""
    fake_decode(monkeypatch)
    video = tmp_path / "T14.mp4"
    video.write_bytes(b"x")
    v = tv.measure(video, {"index": 14, "anchors": [["Q14_0.png", 0]], "lane": "narration", "refs": []},
                   tmp_path / "boards" / "cells", 0.33)
    assert {g.name for g in v.gates if g.note == "not measured (no cell)"} == set(CELL_ROWS + ["foreign"])
    assert v.segments[0].cell == "Q14_0.png" and v.segments[0].landed is None
    assert tv.to_json(v)["segments"][0]["end_sim"] is None            # the record says so too


def test_a_take_staged_with_cells_that_are_not_there_is_still_loud(monkeypatch, tmp_path):
    """THE EPISODE-4 GUARD IS NOT SPENT.  A take whose reference list names cells
    -- the build drew them and handed them to the render -- with none of them in
    the room it is judged against is the wrong-room fault, and raises as it did
    before.  Only a take that was NEVER given a cell is judged without one."""
    fake_decode(monkeypatch)
    video = tmp_path / "T02.mp4"
    video.write_bytes(b"x")
    rec = {"index": 2, "anchors": [["Q02_0.png", 0]], "lane": "narration",
           "refs": ["char-holmes.png", "Q02_0.png", "Q02_0E.png"]}
    try:
        tv.measure(video, rec, tmp_path / "boards", 0.33)
        raise AssertionError("a staged cell that is not in the room must raise")
    except FileNotFoundError as e:
        assert "Q02_0.png" in str(e) and str(tmp_path / "boards") in str(e)
    assert tv.staged_cells(rec) == ["Q02_0.png", "Q02_0E.png"]       # the cast card is not a cell
    assert tv.staged_cells({"refs": ["char-holmes.png", "plate_sofa.png"]}) == []


def test_the_record_counts_off_beat_only_where_the_landing_was_read():
    """`off_beat` is `not landed` over the segments, and `not None` is True:
    unread, every segment of a cell-less take would be counted off-beat."""
    v = tv.TakeVerdict(14, 0, "T14.mp4", 6.0, "narration", [], [cellless_segment(), cellless_segment()])
    assert dq.record(v, [v])["off_beat"] == 0
    missed = tv.SegmentReport("Q01_1.png", "Q01_1.png", 3.0, 6.0, 0.0, 0.0, "hold", 0.3, 1.0, False, 34)
    v.segments = [missed, cellless_segment()]
    assert dq.record(v, [v])["off_beat"] == 1


def test_only_the_rows_that_measured_something_count_as_live():
    """"PASS 100/100" on a take nobody could measure is the whole fault; the
    live count is what says how many rows the number speaks for."""
    v = cellless_verdict()                                # zoom and the picture rows not fed here
    live, total = dq.live_rows(v.gates)
    assert total == 16 and live == 4                      # frozen-at-start, frozen-share, cut, churn
    assert dq.row(14, v).startswith(f"T14 {'PASS' if v.passed else 'FAIL'} {v.score:g}/100 ({live} of 16 rows live)")
    assert "cut-landing not measured (no cell)" in dq.row(14, v)
