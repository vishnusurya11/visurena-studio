"""G4 -- one consolidated, numeric verdict per rendered take attempt.

Nothing here decodes a video, loads a model, touches the GPU or spends: every
gate is fed the numbers it reads.  The penalties are calibrated so every take
the owner named on 2026-09-11 15:15 fails and every take the reviewers called
clean scores 94-100.
"""
from __future__ import annotations

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
    Below 0.50 with an END cell drawn is hard; 0.50-0.75 is advisory either way."""
    v = verdict([seg(target="Q03_0E.png", end=0.62)])
    g = {x.name: x for x in v.gates}["drift"]
    assert not g.ok and not g.hard and v.passed and v.score < 100
    hold = {x.name: x for x in verdict([seg(end=0.62)]).gates}["drift"]
    assert not hold.ok and not hold.hard


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
    assert tv.lip_gate("dialogue", {"lag_s": 0.01, "lag_measured": True, "heard": "the room suits you"},
                       "the room suits you").ok
    assert not tv.lip_gate("dialogue", {"lag_s": -0.5, "lag_measured": True}, "").ok
    assert tv.lip_gate("dialogue", {"lag_s": 0.0, "lag_measured": False}, "").note == "not measured"


def test_the_word_error_rate_is_actually_scored():
    """Iteration 2's T11/T18/T21 measured WER 1.00-1.06 and were recorded passed:true:
    the docstring promised the check, the code never ran it."""
    heard = {"lag_s": 0.0, "lag_measured": True, "heard": "nothing at all like the line"}
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


def test_the_verdict_line_names_every_gate_in_order():
    v = verdict([seg()])
    assert [g.name for g in v.gates] == ["frozen-at-start", "frozen-share", "foreign", "cut-landing",
                                         "drift", "lip-sync", "identity", "wardrobe"]
    assert v.line().startswith("T01 a0 PASS 100/100")


def test_the_record_is_json_shaped():
    v = verdict([seg()])
    row = tv.to_json(v)
    assert row["passed"] and row["score"] == 100.0 and row["verdict_line"] == v.line()
    assert row["gates"][0]["name"] == "frozen-at-start"
