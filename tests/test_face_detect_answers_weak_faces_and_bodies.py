"""The face detector worker, round 2 of the face-blur fix (2026-10-19): it answers faces down to
0.3 (a weak face only continues a track, studio/face_track.rescue) and, when the person model is
on disk (person_yolov8m-seg.pt, Bingsu/adetailer, Apache-2.0, already in models/ultralytics/segm),
every person's box tagged `"kind": "person"` on the same frames: the body fallback for a face the
face model misses (BSAI FaceRefine v5's idea, ported).  The models and the process are fakes."""
from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

import numpy as np

from studio import face_detect as fd
from studio import face_detect_worker as worker
from studio import face_track as ft


def video(path: Path, frames: int = 7) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=gray:s=64x64:r=24:d={frames / 24}",
                    "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


class Boxes:
    def __init__(self, xyxy, conf):
        self.xyxy, self.conf = np.array(xyxy, float).reshape(-1, 4), np.array(conf, float)


class Result:
    def __init__(self, xyxy=(), conf=()):
        self.boxes = Boxes(list(xyxy), list(conf))


def a_face(bgr):
    return [Result([[10, 12, 30, 34]], [0.45])]


def a_body(bgr):
    return [Result([[5, 5, 40, 60]], [0.9])]


def test_the_worker_asks_for_faces_down_to_the_weak_line():
    argv = fd.worker_argv(Path("py.exe"), Path("w.pt"), "cpu", Path("p.pt"))
    assert argv[5] == str(fd.LOW_CONF) and argv[-1] == "p.pt" and fd.LOW_CONF < fd.CONF


def test_the_person_weights_are_the_segm_model_on_disk():
    assert fd.person_path(Path("C:/portable")) == Path("C:/portable", "ComfyUI", "models", "ultralytics", "segm",
                                                         "person_yolov8m-seg.pt")


def test_a_frame_answers_its_faces_and_its_people(tmp_path):
    got = worker.detect_video(a_face, video(tmp_path / "t.mp4"), 3, persons=a_body)
    assert got["6"] == [{"box": [10.0, 12.0, 30.0, 34.0], "score": 0.45},
                        {"box": [5.0, 5.0, 40.0, 60.0], "score": 0.9, "kind": "person"}]


def test_people_are_read_on_every_second_sample_only(tmp_path):
    """The person model costs as much as the face model on the CPU; a body track needs a second
    (24 frames), which every 2nd sample (6 frames) still sees four times."""
    got = worker.detect_video(a_face, video(tmp_path / "t.mp4", 10), 3, persons=a_body)
    has = sorted(int(t) for t, rows in got.items() if any(r.get("kind") == "person" for r in rows))
    assert has == [0, 6] and worker.PERSON_EVERY == 2


def test_without_a_person_model_only_faces_come_back(tmp_path):
    got = worker.detect_video(a_face, video(tmp_path / "t.mp4"), 3)
    assert all("kind" not in r for rows in got.values() for r in rows)


def test_the_served_answer_carries_the_people(tmp_path):
    clip = video(tmp_path / "t.mp4", 4)
    out = io.StringIO()
    worker.serve(io.StringIO(json.dumps({"video": str(clip), "every": 2}) + "\n"), out, a_face, persons=a_body)
    rows = json.loads(out.getvalue())["dets"]["0"]
    assert [r.get("kind") for r in rows] == [None, "person"]


def test_people_are_not_faces_to_the_tracker():
    found = {0: [{"box": [0, 0, 9, 9], "score": 0.9}, {"box": [0, 0, 50, 90], "score": 0.9, "kind": "person"}]}
    strong, weak = ft.by_strength(found, fd.CONF)
    assert strong == {0: [(0, 0, 9, 9)]} and weak == {}
    assert ft.persons_of(found) == {0: [(0, 0, 50, 90)]}
