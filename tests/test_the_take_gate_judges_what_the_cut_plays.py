"""The take gate judges the take from the head the cut starts on.

ep10 T07 and T12 opened on another picture for about ten frames, twice, on two
seeds, and were right from frame 12 to the end. `heads.json` makes the cut
start past the opening; a gate that still measured frame 0 failed a picture
no viewer would see, and the public flip refuses a failed take.
"""
import subprocess

import cv2

from scripts.episode import take_dq


def clip(path, seconds=2.0):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    f"testsrc=size=64x64:rate=24:duration={seconds}", "-pix_fmt", "yuv420p",
                    str(path)], check=True)
    return path


def frames(path):
    return int(cv2.VideoCapture(str(path)).get(cv2.CAP_PROP_FRAME_COUNT))


def test_no_head_judges_the_take_itself(tmp_path):
    video = clip(tmp_path / "T07.mp4")
    assert take_dq.judged_file(video, 0.0, tmp_path / "work") == video


def test_a_head_judges_the_take_from_that_head(tmp_path):
    video = clip(tmp_path / "T07.mp4")
    cut = take_dq.judged_file(video, 0.5, tmp_path / "work")
    assert cut != video and abs(frames(cut) - 36) <= 1
