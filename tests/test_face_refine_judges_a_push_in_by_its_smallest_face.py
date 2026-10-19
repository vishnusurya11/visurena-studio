"""The face refine judges a take by its SMALLEST face everywhere, the warp gate's shortcut too
(skeptic round, 2026-10-19).  The pre-filter that declines a take before the refine's tracker
runs read each MTCNN track's median height: a dolly-in from 80 to 300 px has a median near
190, so the take was called readable and its soft opening never refined -- the owner's blurry
shot.  The warp gate now records each track's smoothed minimum (`min_px`, a running median
over SIZE_SMOOTH frames, as face_track.track_px) and only that declines a take; a record that
holds a median alone is read by the tracker.  Also here: the refine's price counts only the
faces not already readable, an idle-exited detect worker is reopened (not handed to MTCNN),
and a clock cut keeps a stale row's refunded round."""
from __future__ import annotations

import contextlib
import json
from pathlib import Path

import numpy as np

from scripts.episode import face_refine as cli
from studio import episode_home, face_detect as fd, face_refine as fr, step_attempts, warp_gate


def track(heights, x=100.0):
    """A warp_gate track: (frame, box) at SIDE scale, one detection per EVERY frames."""
    return [(t * warp_gate.EVERY, (x, 50.0, x + h, 50.0 + h)) for t, h in enumerate(heights)]


def push_in(lo=80.0, hi=300.0, n=96):
    return list(np.linspace(lo, hi, n))


def dq(tracks, share=1.0):
    return {"passed": True, "gates": [], "measures": {"warp": {"state": "pass", "S": 0.1, "Se": 0.1,
                                                               "share": share, "tracks": tracks}}}


CARD = {"index": 3, "shots": [3], "faces": ["a"]}


# ---- the warp gate records the smallest face ------------------------------------------------

def test_a_push_in_records_its_small_start_beside_its_median():
    stats = warp_gate.track_stats([track(push_in())], 1.0)[0]
    assert stats["median_px"] >= fr.SMALL_FACE_PX
    assert stats["min_px"] < fr.SMALL_FACE_PX


def test_a_one_detection_dip_is_not_the_smallest_face():
    heights = [200.0] * 40 + [90.0] + [200.0] * 40
    assert warp_gate.track_stats([track(heights)], 1.0)[0]["min_px"] == 200.0


def test_the_smallest_face_is_none_when_a_track_logged_only_its_median():
    assert warp_gate.smallest_face({"tracks": [{"median_px": 190.0, "life": 96}]}) is None
    assert warp_gate.smallest_face({"tracks": [{"median_px": 190.0, "min_px": 80.0, "life": 96}]}) == 80.0


# ---- the refine reads it ----------------------------------------------------------------------

def test_a_push_in_whose_median_is_readable_stays_eligible():
    assert fr.eligible(CARD, ["wide"], dq([{"median_px": 190.0, "min_px": 80.0, "life": 96}]))


def test_a_face_readable_from_its_first_frame_is_declined():
    assert not fr.eligible(CARD, ["wide"], dq([{"median_px": 190.0, "min_px": 150.0, "life": 96}]))


def test_a_median_only_record_is_left_to_the_tracker():
    assert fr.eligible(CARD, ["wide"], dq([{"median_px": 190.0, "life": 96}]))


def test_the_price_counts_only_the_faces_not_already_readable():
    two = {"index": 3, "faces": ["a", "b"]}
    tracks = [{"median_px": 200.0, "min_px": 150.0, "life": 96}, {"median_px": 50.0, "min_px": 40.0, "life": 96}]
    assert fr.soft_faces(two, dq(tracks)) == 1
    assert fr.soft_faces(two, dq([])) == 2
    assert fr.soft_faces(two, None) == 2


# ---- the worker that idled out --------------------------------------------------------------

class IdleWorker:
    def __init__(self, device):
        self.device, self.closed, self.gone = device, False, False

    def exited(self):
        return self.gone

    def __call__(self, take):
        if self.gone:
            raise RuntimeError("the face detect worker had exited (code 0)")
        return {0: [{"box": [1, 1, 9, 9], "score": 0.9}]}

    def close(self):
        self.closed = True


def test_a_worker_that_idled_out_is_reopened_not_handed_to_mtcnn():
    started = []
    start = lambda device: started.append(IdleWorker(device)) or started[-1]
    find = fd.Finder(lambda rgb: [], route=lambda job, gb: "cpu", start=start, busy=lambda: False,
                     claim=lambda job: contextlib.nullcontext())
    frames = [np.zeros((8, 8, 3), np.uint8)] * 4
    find(Path("a.mp4"), frames)
    started[0].gone = True                       # IDLE_S passed between two takes
    assert find(Path("b.mp4"), frames) == {0: [{"box": [1, 1, 9, 9], "score": 0.9}]}
    assert len(started) == 2 and started[0].closed and not find.broken


# ---- a clock cut over a stale row -----------------------------------------------------------

def test_a_cut_over_a_stale_row_keeps_its_refunded_round(tmp_path, monkeypatch):
    book = tmp_path / "book"
    home = episode_home.home(book, 1)
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T06.mp4").write_bytes(b"take")
    (room / "refine.json").write_text(json.dumps({"T06": {"status": "no_faces", "take_sha8": cli.sha8(room / "T06.mp4")}}))
    step_attempts.spend(home, "face_refine.T06")
    monkeypatch.setattr(cli, "selection", lambda b, n: [6])
    cli.record_cut(room, [6], 220.0, book, 1)
    assert cli.pending(book, 1) == [6]
