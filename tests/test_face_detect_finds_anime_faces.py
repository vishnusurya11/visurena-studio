"""The face refine's tracker reads anime faces with face_yolov8m.pt (Bingsu/adetailer,
Apache-2.0, already on disk): it read Jekyll ep01's cel faces at 0.8+ confidence from 37 px up,
where MTCNN dropped far figures and frames (docs/audit/2026-10-19_face_blur/pipeline_audit.md).
Ultralytics and CUDA torch live in ComfyUI's embedded python, so the detector is a worker under
it (studio/face_detect_worker.py), routed GPU-when-idle / CPU-while-rendering; a worker that
fails hands the take to MTCNN.  The model, the process and the router are fakes here."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from studio import face_detect as fd
from studio import face_detect_worker as worker


def video(path: Path, frames: int = 10) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=gray:s=64x64:r=24:d={frames / 24}",
                    "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


class Boxes:
    def __init__(self, xyxy, conf):
        self.xyxy, self.conf = np.array(xyxy, float).reshape(-1, 4), np.array(conf, float)


class Result:
    def __init__(self, xyxy=(), conf=()):
        self.boxes = Boxes(list(xyxy), list(conf))


def one_face(bgr):
    return [Result([[10, 12, 30, 34.06]], [0.876])]


# ---- the worker (embedded python side) ------------------------------------------------------

def test_a_result_becomes_box_and_score_rows():
    assert worker.rows(Result([[1, 2, 3, 4.04]], [0.5])) == [{"box": [1.0, 2.0, 3.0, 4.0], "score": 0.5}]


def test_every_kth_frame_is_detected(tmp_path):
    got = worker.detect_video(one_face, video(tmp_path / "t.mp4", 10), 3)
    assert sorted(int(t) for t in got) == [0, 3, 6, 9]
    assert got["3"] == [{"box": [10.0, 12.0, 30.0, 34.1], "score": 0.876}]


def test_a_bad_ask_is_an_error_line_not_a_crash(tmp_path):
    said = worker.answer(one_face, {"video": str(tmp_path / "missing.mp4"), "every": 3})
    assert "error" in said


def test_the_worker_answers_one_line_per_ask(tmp_path):
    clip = video(tmp_path / "t.mp4", 4)
    out = io.StringIO()
    worker.serve(io.StringIO(json.dumps({"video": str(clip), "every": 2}) + "\n"), out, one_face)
    said = json.loads(out.getvalue())
    assert sorted(said["dets"]) == ["0", "2"]


def test_the_worker_reads_the_frames_at_their_size():
    assert worker.IMGSZ == 768 and worker.CONF == 0.6


# ---- the repo side ---------------------------------------------------------------------------

def test_the_answer_is_keyed_by_frame():
    assert fd.parse({"dets": {"3": [{"box": [1, 2, 3, 4], "score": 0.9}]}}) == {3: [{"box": [1, 2, 3, 4], "score": 0.9}]}


def test_an_error_answer_raises():
    with pytest.raises(RuntimeError, match="no video"):
        fd.parse({"error": "no video"})


def test_the_worker_runs_isolated_on_the_weights_on_disk(tmp_path):
    argv = fd.worker_argv(Path("py.exe"), Path("w.pt"), "cpu")
    assert argv[:2] == ["py.exe", "-I"] and argv[2].endswith("face_detect_worker.py")
    assert argv[3:] == ["w.pt", "cpu", str(fd.CONF), str(fd.THREADS)]
    assert fd.weights_path(Path("C:/portable")).parts[-4:] == ("models", "ultralytics", "bbox", "face_yolov8m.pt")


def test_a_cpu_worker_never_sees_the_card():
    assert fd.worker_env("cpu", {"PATH": "x"})["CUDA_VISIBLE_DEVICES"] == ""
    assert "CUDA_VISIBLE_DEVICES" not in fd.worker_env("cuda", {"PATH": "x"})


class FakeWorker:
    def __init__(self, device, fail=False):
        self.device, self.fail, self.closed, self.asked = device, fail, False, 0

    def __call__(self, take):
        self.asked += 1
        if self.fail:
            raise RuntimeError("the worker died")
        return {0: [{"box": [1, 1, 9, 9], "score": 0.9}]}

    def close(self):
        self.closed = True

    def exited(self):
        return False


def finder(route="cpu", busy=False, fail=False, started=None):
    started = [] if started is None else started

    def start(device):
        started.append(FakeWorker(device, fail))
        return started[-1]
    loose = lambda rgb: [{"box": [2, 2, 8, 8], "score": 0.7}]
    return fd.Finder(loose, route=lambda job, gb: route, start=start, busy=lambda: busy,
                     claim=lambda job: contextlib.nullcontext()), started


def test_the_worker_answers_the_take():
    find, started = finder()
    assert find(Path("T01.mp4"), [np.zeros((8, 8, 3), np.uint8)] * 4) == {0: [{"box": [1, 1, 9, 9], "score": 0.9}]}
    assert [w.device for w in started] == ["cpu"]


def test_one_worker_serves_every_take():
    find, started = finder()
    frames = [np.zeros((8, 8, 3), np.uint8)] * 4
    find(Path("a.mp4"), frames)
    find(Path("b.mp4"), frames)
    assert len(started) == 1 and started[0].asked == 2


def test_a_render_that_arrives_moves_a_gpu_worker_to_the_cpu():
    find, started = finder(route="cuda", busy=True)
    find(Path("a.mp4"), [np.zeros((8, 8, 3), np.uint8)] * 4)
    find(Path("b.mp4"), [np.zeros((8, 8, 3), np.uint8)] * 4)
    assert [w.device for w in started] == ["cuda", "cpu"] and started[0].closed


def test_a_failed_worker_hands_the_take_and_the_rest_to_mtcnn():
    find, started = finder(fail=True)
    frames = [np.zeros((8, 8, 3), np.uint8)] * 7
    assert find(Path("a.mp4"), frames) == {t: [{"box": [2, 2, 8, 8], "score": 0.7}] for t in range(0, 7, fd.EVERY)}
    find(Path("b.mp4"), frames)
    assert len(started) == 1 and started[0].closed


@pytest.mark.local
def test_the_real_worker_starts_on_the_cpu_and_answers(tmp_path):
    """The embedded python's ultralytics on face_yolov8m.pt (ep01 smoke 2026-10-19: ready in 3.4 s,
    10-19 s a take on 4 CPU threads, T01's 15 px faces found)."""
    w = fd.Worker(fd.spawn("cpu"))
    try:
        assert sorted(w(video(tmp_path / "t.mp4", 7))) == [0, 3, 6]
    finally:
        w.close()


def test_the_mtcnn_reading_samples_the_same_frames():
    loose = lambda rgb: []
    assert sorted(fd.by_frames([np.zeros((4, 4, 3), np.uint8)] * 8, loose)) == [0, 3, 6]
