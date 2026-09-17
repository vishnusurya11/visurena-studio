"""G4 -- one consolidated, numeric verdict per rendered take attempt.

Nothing here decodes a video, loads a model, touches the GPU or spends: every
gate is fed the numbers it reads.  The penalties are calibrated so every take
the owner named on 2026-09-11 15:15 fails and every take the reviewers called
clean scores 94-100.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from studio import take_verdict as tv


def seg(cell="Q01_0.png", target=None, a=0.0, b=5.0, lead=0.0, share=0.0, start=1.0, end=1.0,
        landed=True, offset=0, kind="hold"):
    return tv.SegmentReport(cell, target or cell, a, b, lead, share, kind, start, end, landed, offset)


def verdict(segments, seconds=5.0, lane="narration", spans=None, foreign=None, audio=None,
            line_text="", unplanned=()):
    v = tv.TakeVerdict(1, 0, "T01.mp4", seconds, lane, [], segments, spans or [], [], foreign or [])
    v.gates = tv.gates(v, audio, line_text, list(unplanned))
    v.score, v.passed = tv.score(v.gates)
    return v


def test_the_budget_and_the_tolerances_are_the_calibrated_ones():
    """RETAKE_BUDGET: a take is 9 min of GPU at the median and 37 min at the worst,
    so three renders is the ceiling.  LAG_TOL is one frame at 24 fps; WER_CEIL is
    voice_qc.MAX_ERROR_RATE -- iteration 2's T11/T18/T21 measured 1.00-1.06 and were
    recorded passed:true because the WER was never scored."""
    assert tv.RETAKE_BUDGET == 2
    assert tv.LAG_TOL == 0.042 and tv.WER_CEIL == 0.20
    assert (tv.DRIFT_HARD, tv.DRIFT_ADVISORY) == (0.50, 0.75)
    assert (tv.SHARE_HARD, tv.SHARE_ADVISORY) == (0.40, 0.20)


def test_score_is_a_hundred_less_the_penalties_and_never_negative():
    assert tv.score([tv.Gate("a", 0, True, True, "", 0.0)]) == (100.0, True)
    assert tv.score([tv.Gate("a", 0, False, True, "", 30.0)]) == (70.0, False)
    assert tv.score([tv.Gate("a", 0, False, False, "", 250.0)]) == (0.0, True)   # advisory: fails nothing


def test_a_frozen_take_fails_hard_and_a_moving_one_passes():
    """T17 iteration 4: 14.75 of 15.0 s frozen, and the old gate passed it."""
    frozen = verdict([seg(lead=4.9, share=0.98, b=15.0)], seconds=15.0, spans=[(0.0, 14.75)])
    assert not frozen.passed and frozen.score < 30
    moving = verdict([seg(target="Q03_0E.png", end=0.9, b=7.0)], seconds=7.0)
    assert moving.passed and moving.score >= 95


def test_a_segment_that_opens_on_the_wrong_picture_fails_cut_landing():
    """Iteration 4 T01: the cut stepped on time but the picture after it was the
    neighbour cell (0.31)."""
    v = verdict([seg("Q01_0.png", a=0.0, b=3.2),
                 seg("Q01_1.png", a=3.2, b=6.8, start=0.31, landed=False, offset=-3)], seconds=6.8)
    g = {x.name: x for x in v.gates}
    assert not g["cut-landing"].ok and g["cut-landing"].hard and g["cut-landing"].note == "1/2 on pin"
    assert not v.passed


def test_an_unplanned_cut_is_penalised_and_named():
    v = verdict([seg()], unplanned=[2.5, 4.0])
    g = {x.name: x for x in v.gates}
    assert not g["cut-landing"].ok and "2 unplanned" in g["cut-landing"].note
    assert g["cut-landing"].penalty == 30.0


def test_drift_is_hard_only_when_an_end_cell_was_drawn():
    hold = verdict([seg(end=0.27)])                          # a cab crossing a static frame
    end_drawn = verdict([seg(target="Q03_0E.png", end=0.27)])
    assert not {x.name: x for x in hold.gates}["drift"].hard
    assert {x.name: x for x in end_drawn.gates}["drift"].hard
    assert hold.passed and not end_drawn.passed


def test_a_drift_in_the_advisory_band_is_flagged_but_does_not_fail():
    """review7/holds11: a held segment reads 0.93-1.00 and a drifted one 0.28-0.60.
    Below 0.50 with an END cell drawn is hard; 0.50-0.75 is advisory.  A hold
    with no END cell is aimed at nothing and reads 0.25-0.29 against its own
    start cell by right: it is not flagged (analyst H, ep10)."""
    v = verdict([seg(target="Q03_0E.png", end=0.62)])
    g = {x.name: x for x in v.gates}["drift"]
    assert not g.ok and not g.hard and v.passed and v.score < 100
    hold = {x.name: x for x in verdict([seg(end=0.62)]).gates}["drift"]
    assert hold.ok and not hold.hard


def test_the_drift_advisory_is_scoped_to_aimed_segments_like_the_hard_half():
    """MEASURED ep05-10 (analyst H): the advisory fired on 125 of 137 takes with
    no END target and on 0 of 25 with one -- 19 false alarms on ep10 alone,
    Spearman against the reviewer -0.03.  A push-in's last frame compared to
    its own START cell is a stillness meter, not a drift."""
    unaimed = {x.name: x for x in verdict([seg(end=0.29)]).gates}["drift"]
    assert unaimed.ok and not unaimed.hard and unaimed.penalty == 0.0 and unaimed.note == "0.29"
    adv = {x.name: x for x in verdict([seg(target="Q03_0E.png", end=0.60)]).gates}["drift"]
    assert not adv.ok and not adv.hard
    hard = {x.name: x for x in verdict([seg(target="Q03_0E.png", end=0.40)]).gates}["drift"]
    assert not hard.ok and hard.hard
    mixed = {x.name: x for x in verdict([seg(target="Q03_0E.png", end=0.95), seg("Q03_1.png", end=0.29)]).gates}["drift"]
    assert mixed.ok and mixed.note == "0.95"                  # no "worst hold" blame on a clean row


def test_foreign_frames_are_hard_and_capped():
    v = verdict([seg()], foreign=[{"foreign": True}, {"foreign": True}, {"foreign": False}])
    g = {x.name: x for x in v.gates}["foreign"]
    assert not g.ok and g.hard and g.penalty == 60.0
    assert not v.passed


def test_the_frozen_share_is_advisory_below_the_hard_ceiling():
    mid = {x.name: x for x in verdict([seg(share=0.30)], spans=[(0.0, 1.5)]).gates}["frozen-share"]
    assert not mid.ok and not mid.hard
    bad = verdict([seg(share=0.60)], spans=[(0.0, 3.0)])
    assert not {x.name: x for x in bad.gates}["frozen-share"].ok and not bad.passed


def test_lip_gate_reads_lag_and_wer_on_dialogue_only():
    assert tv.lip_gate("narration", None, "").ok
    assert tv.lip_gate("dialogue", {"mux_lag_s": 0.01, "lag_measured": True, "heard": "the room suits you"},
                       "the room suits you").ok
    assert not tv.lip_gate("dialogue", {"mux_lag_s": -0.5, "lag_measured": True}, "").ok
    assert tv.lip_gate("dialogue", {"mux_lag_s": 0.0, "lag_measured": False}, "").note == "not measured"


def test_the_word_error_rate_is_actually_scored():
    """Iteration 2's T11/T18/T21 measured WER 1.00-1.06 and were recorded passed:true:
    the docstring promised the check, the code never ran it."""
    heard = {"mux_lag_s": 0.0, "lag_measured": True, "heard": "nothing at all like the line"}
    g = tv.lip_gate("dialogue", heard, "the room suits you very well indeed")
    assert not g.ok and "wer" in g.note and g.penalty > 0


def test_identity_is_not_measured_without_the_face_model():
    g = {x.name: x for x in verdict([seg()]).gates}["identity"]
    assert g.note == "not measured" and g.ok and not g.hard


def test_a_measured_identity_stranger_is_hard():
    g = tv.identity_gate_row({"measured": True, "ok": False, "hard": ["STRANGER frame 2: best x 0.43 < 0.45"],
                              "flags": ["STRANGER frame 2: best x 0.43 < 0.45"], "present": {}})
    assert g.hard and not g.ok and g.penalty == 0.0            # hard gates fail; they do not also score


def test_a_pass_outranks_a_higher_scoring_fail():
    good, bad = verdict([seg()]), verdict([seg(lead=4.0)])
    assert tv.best_of([bad, good]) is good
    assert tv.rank_key(good) > tv.rank_key(bad)


def test_among_fails_the_better_score_is_kept_when_a_freeze_and_a_foreign_frame_compete():
    """T01 iteration 4: the hand-renaming demoted the better file.  A 1.5 s freeze
    (penalty 25) outscores four foreign frames (penalty 60)."""
    freeze = verdict([seg(lead=1.5)])
    intruded = verdict([seg()], foreign=[{"foreign": True}] * 4)
    assert not freeze.passed and not intruded.passed
    assert tv.best_of([intruded, freeze]) is freeze


def test_retake_stops_at_the_budget_or_at_the_first_pass():
    fail = lambda: verdict([seg(lead=4.0)])                    # noqa: E731
    assert tv.needs_retake([fail()])
    assert tv.needs_retake([fail(), fail()])
    assert not tv.needs_retake([fail(), fail(), fail()])       # RETAKE_BUDGET = 2 spent
    assert not tv.needs_retake([fail(), verdict([seg()])])


def test_segments_fold_end_pins_and_pick_the_end_cell_as_target(tmp_path):
    """The END cell is the target only when ONE CAMERA MOVE REACHES IT.

    `segments_of` used to target any `Q..E.png` on disk. It now applies the
    same `sq.reaches` rule the BUILDER applies when staging references, so a
    take is never failed for missing a picture it was never given. The pair
    here is therefore drawn one push apart (measured 0.66, inside the
    0.45-0.80 band); a flat fill measures as a re-stage and is not a target.
    """
    import numpy as np
    y, x = np.mgrid[0:64, 0:64]
    a = (128 + 110 * np.sin(x / 11.0) * np.cos(y / 13.0)).astype("uint8")
    start = Image.fromarray(a)
    start.save(tmp_path / "Q02_0.png")
    start.crop((16, 16, 48, 48)).resize((64, 64)).save(tmp_path / "Q02_0E.png")
    Image.fromarray(np.roll(a, 31, axis=1)).save(tmp_path / "Q02_1.png")
    anchors = [["Q02_0.png", 0], ["Q02_1.png", 97], ["Q02_0E.png", 93], ["Q02_1.png", 205]]
    segs = tv.segments_of(anchors, tmp_path, 8.25)
    assert [(s[0], s[1], s[4]) for s in segs] == [("Q02_0.png", "Q02_0E.png", 0), ("Q02_1.png", "Q02_1.png", 97)]
    assert segs[0][3] == round(97 / 24, 3) and segs[1][3] == round(int(8.25 * 24) / 24, 3)


ROW_ORDER = ["frozen-at-start", "frozen-share", "foreign", "cut-landing", "drift",
             "coherence off-board", "last-vs-cell", "cut", "churn", "zoom",
             "face-at-end", "look", "post-cut", "pulse", "lip-sync", "identity"]


def test_the_verdict_line_names_every_gate_in_order():
    """The `wardrobe` placeholder is gone (analyst H, change 6): a row that has
    never measured anything is not a wall, and printing it as one made
    "30/30 pass" a statement about rows that cannot fire."""
    v = verdict([seg()])
    assert [g.name for g in v.gates] == ROW_ORDER
    assert v.line().startswith("T01 a0 PASS 100/100")


def test_the_picture_rows_are_not_measured_while_their_modules_are_absent(monkeypatch):
    """face-at-end, look, post-cut and pulse are wired by interface to modules
    another implementer builds.  Absent at import time, each is a `not
    measured` row -- a gate may say it could not read something; it may not
    be silent and be taken for a pass."""
    import sys
    for name in ("studio.face_end", "studio.take_look", "studio.take_edit"):
        monkeypatch.setitem(sys.modules, name, None)          # `from studio import x` raises ImportError
    rows = {g.name: g for g in tv.picture_rows(Path("T01.mp4"), {"placed_seconds": 5.0}, 5.0)}
    assert list(rows) == ["face-at-end", "look", "post-cut", "pulse"]
    assert all(g.value is None and g.ok and not g.hard and g.note == "not measured" for g in rows.values())


def test_the_picture_rows_are_wired_by_interface_when_the_modules_exist(monkeypatch):
    """The interface: face_end.row(video, record), take_look.row(video, seconds),
    take_edit.rows(video, seconds, placed_seconds) -> the named Gates."""
    import sys
    from types import ModuleType
    seen = {}
    face_end, take_look, take_edit = ModuleType("studio.face_end"), ModuleType("studio.take_look"), ModuleType("studio.take_edit")
    face_end.row = lambda video, record: seen.setdefault("face", (video, record)) and tv.Gate("face-at-end", 0.86, False, True, "0.86 clipped")
    take_look.row = lambda video, seconds: seen.setdefault("look", seconds) and tv.Gate("look", 0.02, True, True, "floor 0.02")
    take_edit.rows = lambda video, seconds, placed: seen.setdefault("edit", (seconds, placed)) and [
        tv.Gate("post-cut", 8.6, False, False, "8.6", 5.0), tv.Gate("pulse", 0.1, True, False, "0.1")]
    for name, mod in (("studio.face_end", face_end), ("studio.take_look", take_look), ("studio.take_edit", take_edit)):
        monkeypatch.setitem(sys.modules, name, mod)
    record = {"placed_seconds": 5.0, "seconds": 5.3}
    rows = tv.picture_rows(Path("T01.mp4"), record, 5.0)
    assert [g.name for g in rows] == ["face-at-end", "look", "post-cut", "pulse"]
    assert rows[0].hard and not rows[0].ok and rows[2].penalty == 5.0
    assert seen == {"face": (Path("T01.mp4"), record), "look": 5.0, "edit": (5.3, 5.0)}
    v = tv.TakeVerdict(1, 0, "T01.mp4", 5.0, "narration", [], [seg()])
    v.gates = tv.gates(v, None, "", [], picture=rows)
    assert [g.name for g in v.gates] == ROW_ORDER and not tv.score(v.gates)[1]


def test_the_plan_size_reaches_the_churn_row():
    """A wide's churn wall is 6.0 and HARD (take_coherence.NONRIGID_WIDE); the
    size travels through `gates` the way `motion` reaches the zoom row."""
    coh = {"offboard_share": 0.0, "last_vs_cell": 0.7, "hard_cut": 12.6, "nonrigid": 6.4}
    v = tv.TakeVerdict(3, 0, "T03.mp4", 6.3, "narration", [], [seg("Q03_0.png")], coherence=coh)
    wide = {g.name: g for g in tv.gates(v, None, "", [], size="wide")}["churn"]
    assert not wide.ok and wide.hard and "wide" in wide.note
    medium = {g.name: g for g in tv.gates(v, None, "", [], size="medium")}["churn"]
    assert medium.ok and not medium.hard


T17 = ("The camera pushes in on the raised hand across the whole shot, travelling a hand's breadth; "
       "the spread fingers close into a fist; the fist drops out of the bottom of the frame.")


def test_a_planned_exit_silences_last_vs_cell():
    """ep10 T17 (analyst B): the last frame is bare boards because the fist was
    TOLD to drop out of the bottom of the frame; last-vs-cell 0.20 cost it ten
    points for obeying.  With an exit clause in the segment's motion the row
    reads n/a and cannot fire."""
    coh = {"offboard_share": 0.10, "last_vs_cell": 0.20, "hard_cut": 5.8, "nonrigid": 3.4}
    v = tv.TakeVerdict(17, 0, "T17.mp4", 5.58, "narration", [], [seg("Q17_0.png")], coherence=coh)
    rows = {g.name: g for g in tv.gates(v, None, "", [], motion=T17)}
    assert rows["last-vs-cell"].value is None and rows["last-vs-cell"].ok and "exit" in rows["last-vs-cell"].note
    plain = {g.name: g for g in tv.gates(v, None, "", [], motion=T17.split(";")[0])}
    assert not plain["last-vs-cell"].ok and plain["last-vs-cell"].penalty > 0


def test_a_narration_take_has_no_lip_value_to_fire_on():
    """`value is None` is the one signal `take_dq.row` counts as "cannot fire"."""
    assert tv.lip_gate("narration", None, "").value is None


def test_an_unmeasured_coherence_prints_so_and_fails_nothing():
    """A gate may say it could not read something; it may not be silent."""
    v = verdict([seg()])
    assert "coherence off-board not measured" in v.line() and v.passed


def test_ep09_t02_fails_hard_on_coherence_and_the_row_names_the_rung():
    """ep09 T02, the wagon train that multiplies up a hill: every existing gate
    clean, 100/100.  Its coherence numbers measured 2026-09-16."""
    v = tv.TakeVerdict(2, 0, "T02.mp4", 5.33, "narration", [], [seg("Q02_0.png")],
                       coherence={"offboard_share": 0.60, "last_vs_cell": 0.08, "hard_cut": 14.9, "nonrigid": 10.7})
    v.gates = tv.gates(v, None, "", [])
    v.score, v.passed = tv.score(v.gates)
    assert not v.passed
    assert "coherence off-board 0.60 HARD | last-vs-cell 0.08 HARD | cut 14.9 | churn 10.7 adv" in v.line()
    assert tv.to_json(v)["coherence"]["offboard_share"] == 0.60


def test_a_coherent_moving_take_still_scores_a_hundred():
    """The gate must not become a second stillness meter (test_score_is_honest):
    a dolly on the board with a low churn carries no penalty."""
    v = tv.TakeVerdict(3, 0, "T03.mp4", 6.0, "narration", [], [seg("Q03_0.png", end=0.3)],
                       coherence={"offboard_share": 0.05, "last_vs_cell": 0.55, "hard_cut": 9.0, "nonrigid": 4.5})
    v.gates = tv.gates(v, None, "", [])
    v.score, v.passed = tv.score(v.gates)
    assert v.passed and v.score == 100.0


def test_the_record_is_json_shaped():
    v = verdict([seg()])
    row = tv.to_json(v)
    assert row["passed"] and row["score"] == 100.0 and row["verdict_line"] == v.line()
    assert row["gates"][0]["name"] == "frozen-at-start"
