r"""`camera_ok` is computed on every take, read by nothing, and must stay that way.

It has stood as a known-open item -- "camera_ok computed and read by nothing" --
which reads like an unfinished wiring job. It is not. Wiring it would fail
almost every take in the episode, and this file closes the item with the
measurement instead of leaving it to be picked up by someone who trusts the
name.

MEASURED over all 25 of episode 7's first-pass DQ records:

    camera_ok TRUE   n= 2   mean score 92.95   passed 1/2
    camera_ok FALSE  n=23   mean score 94.48   passed 22/23

It is FALSE on all nineteen takes that score 100.00. The two takes it calls good
are takes 20 and 22, whose `max_scale_per_s` is 0.12 -- the two least-moving
takes in the episode, and take 22 is one of the two hard failures.

The reason is in the constant's own calibration note:

    SCALE_PER_SECOND = 0.15
    "Engine designer, 2026-09-10: the +-10 % wobble over ~2 s after a snap is
     0.10/s; a snap was 0.6-1.8/s; i2v drift is 0.013/s."

Drift and snap are the two regimes of a camera that is HOLDING STILL, and 0.15
is the line between them. A camera pushing in two long strides across a
five-second shot changes scale far faster than a wobble and is not a snap. The
threshold separates "still and clean" from "still and glitched"; asked about a
moving camera it answers "moving", and that is not a fault.

Nor do `scene_events` rank anything on their own: take 9 carries 23 of them and
scores 100.00, take 15 carries 17 and scores 100.00, take 11 carries 14 and
scores 40.00.

What actually caught take 11 was `foreign` -- the take drifted into
`plate_mews_lane.png` at 0.976 while its own start cell fell to 0.176. A gate
that names the picture the take wandered INTO says something; a gate that counts
how fast the framing changed does not, now that the framing is meant to change.

Sixth instance of the same fault class in this session, after CAMERA_MOVE,
FOREIGN_MIN, "from the same camera", END_FLOOR and the drift advisory: a
constant calibrated on a world that has since changed.
"""
import glob
import json
import statistics as st
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DQ = ROOT / "library/20260822113400_a-study-in-scarlet/episodes/ep07/takes/r2v"


def records():
    found = [json.loads(Path(p).read_text(encoding="utf-8")) for p in sorted(glob.glob(str(DQ / "T*.dq.json")))]
    if not found:
        pytest.skip("episode 7 DQ records are not on disk")
    return [r for r in found if "camera" in r and "score" in r]


def test_camera_ok_is_read_by_nothing():
    """The grep that keeps it that way. `camera_dq` writes the key into the
    record and no gate, score or verdict line consumes it."""
    said = (ROOT / "studio/take_verdict.py").read_text(encoding="utf-8")
    assert "camera_ok" not in said, "camera_ok reached the verdict; read this file first"


def test_it_is_false_on_the_takes_that_score_best():
    """If it were a quality signal this would be the other way round."""
    rows = records()
    perfect = [r for r in rows if r["score"] >= 100.0]
    if len(perfect) < 5:
        pytest.skip("too few perfect takes on disk to measure against")
    called_good = [r for r in perfect if r["camera"].get("camera_ok")]
    assert len(called_good) <= len(perfect) / 4, (
        f"camera_ok calls {len(called_good)} of {len(perfect)} perfect takes good; "
        f"it may have become a real signal -- re-measure before wiring it")


def test_the_takes_it_calls_good_are_the_least_moving_ones():
    rows = records()
    good = [r for r in rows if r["camera"].get("camera_ok")]
    rest = [r for r in rows if not r["camera"].get("camera_ok")]
    if not good or not rest:
        pytest.skip("no contrast on disk")
    assert max(r["camera"]["max_scale_per_s"] for r in good) \
        < st.median(r["camera"]["max_scale_per_s"] for r in rest), \
        "camera_ok is no longer simply picking out the stillest takes"


def test_scene_events_do_not_rank_takes_either():
    """Take 9: 23 events, 100.00. Take 11: 14 events, 40.00."""
    rows = records()
    busy = [r for r in rows if len(r["camera"].get("scene_events", [])) >= 10]
    if len(busy) < 2:
        pytest.skip("too few busy takes on disk")
    assert max(r["score"] for r in busy) >= 100.0, \
        "a take with many scene events now always scores badly -- worth re-measuring"
