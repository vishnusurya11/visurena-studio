"""Owner 2026-10-29: "incorporate face fixes in all shots .. not just selected ones .. if there is human
you fix the eyes and face and make it under 6 hours".  Until now the refine worked only on faces under
SMALL_FACE_PX (a close-up's big face was `all_readable` and left alone).  Every take with a planned face
that its dq lets ship is tracked, every tracked face is refined (its denoise falling with its size inside
DENOISE_BAND), and the refine's wall is sized for every face of an episode, still cut first for time."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.episode import face_refine as cli  # noqa: E402
from studio import face_refine as fr, step_caps  # noqa: E402

PASSED = {"passed": True, "gates": [], "measures": {"warp": {
    "tracks": [{"min_px": 310.0, "median_px": 330.0}], "share": 1.0, "S": 0.0, "Se": 0.0}}}


def test_a_take_whose_faces_already_read_is_still_refined():
    card = {"index": 11, "faces": ["reginald_lanyon"], "shots": [11]}
    assert fr.readable(card, PASSED)                    # the old rule's skip
    assert fr.eligible(card, ["close"], PASSED)


def test_an_insert_or_a_faceless_take_is_still_never_refined():
    assert not fr.eligible({"index": 3, "faces": [], "shots": [3]}, ["wide"], PASSED)
    assert not fr.eligible({"index": 4, "faces": ["a"], "shots": [4]}, ["insert"], PASSED)


def test_a_big_tracked_face_is_kept_for_the_refine():
    work = SimpleNamespace(yolo_min_px=None, status="")
    big = [[0, (100, 100, 400, 420)]]
    kept, _ = cli.soft_tracks(work, [big])
    assert kept == [big] and work.status == ""


def test_no_tracks_is_none_found():
    work = SimpleNamespace(yolo_min_px=None, status="")
    assert cli.soft_tracks(work, [])[0] == [] and work.status == "none_found"


def test_a_big_face_is_redrawn_gently():
    assert fr.denoise_for(320.0) == fr.DENOISE_BAND[0]


def test_every_planned_face_is_priced():
    card = {"index": 11, "faces": ["a", "b"], "shots": [11]}
    assert fr.soft_faces(card, PASSED) == 2


def test_the_wall_is_sized_for_every_face_of_an_episode():
    """28 takes x ~1.3 faces x (11 s + 0.558 s x ~160 frames) ~= 61 min of GPU."""
    assert step_caps.wall_s("face_refine") >= 60 * 60


def test_an_empty_head_crop_is_no_evidence_not_a_crash():
    """A big face's head box at the frame's edge can crop to nothing; OpenCV refused the empty crop."""
    import numpy as np
    from studio import face_track
    empty, head = np.zeros((0, 10, 3), np.uint8), np.full((20, 20, 3), 128, np.uint8)
    assert face_track.hist_similarity(empty, head) == 0.0


def test_an_all_readable_decision_of_the_old_rule_is_owed_again():
    """ep06's first 14 decisions were made under the old rule; an `all_readable` take queued no job
    and spent no round, so under the new rule it is pending again, its big faces refined."""
    room = Path(".")
    import unittest.mock as m
    with m.patch.object(cli, "sha8", lambda path: "abc"):
        assert not cli.current({"T03": {"status": "all_readable", "take_sha8": "abc"}}, room, 3)
        assert cli.current({"T03": {"status": "refined", "take_sha8": "abc"}}, room, 3)
