"""The face refine's anime identity terms (face-blur round 2, 2026-10-19): facenet is a photo
model and reads a cel face weakly (ep01 T01 Utterson 0.04 on his own take), so the gate also
reads CCIP (deepghs/ccip_onnx, OpenRAIL; preprocessing ported from deepghs/imgutils, MIT) and
clip_vision_h's image embedding.  Both run in a worker under ComfyUI's embedded python, which
holds onnxruntime and torch (the repo venv has neither; dghs-imgutils pins numpy<2 and is never
installed).  The models, the process and the router are fakes here."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from studio import anime_id as aid
from studio import anime_id_worker as worker


def png(path: Path, level: int, size: int = 40) -> str:
    Image.new("RGB", (size, size), (level, level, level)).save(path)
    return str(path)


# ---- the worker (embedded python side) ------------------------------------------------------

def test_ccip_reads_a_384_picture_scaled_to_minus_one_one():
    """imgutils.metrics.ccip._preprocess_image: RGB, 384x384 bilinear, /255, (x - 0.5) / 0.5, CHW."""
    rgb = np.zeros((10, 20, 3), np.uint8)
    rgb[..., 0] = 255
    got = worker.ccip_input(rgb)
    assert got.shape == (3, 384, 384) and got.dtype == np.float32
    assert got[0].min() == pytest.approx(1.0) and got[1].max() == pytest.approx(-1.0)


def test_clip_reads_a_224_picture_with_clips_own_mean_and_std():
    got = worker.clip_input(np.full((300, 300, 3), 255, np.uint8))
    assert got.shape == (3, 224, 224)
    assert got[0, 0, 0] == pytest.approx((1.0 - worker.CLIP_MEAN[0]) / worker.CLIP_STD[0], abs=1e-4)


def test_the_cosine_matrix_is_of_unit_vectors():
    got = worker.cosines(np.array([[3.0, 0.0], [0.0, 2.0], [1.0, 1.0]]))
    assert got[0, 0] == pytest.approx(1.0) and got[0, 1] == pytest.approx(0.0)
    assert got[0, 2] == pytest.approx(2 ** -0.5)


class Fake:
    """ccip: features = the picture's mean level; distance = |difference|.  clip: [level, 1]."""

    def ccip_feats(self, batch):
        return batch.mean(axis=(1, 2, 3))[:, None]

    def ccip_dist(self, feats):
        return np.abs(feats - feats.T)

    def clip_embeds(self, batch):
        return np.stack([batch.mean(axis=(1, 2, 3)), np.ones(len(batch))], 1)


def test_the_answer_is_both_matrices_over_the_asked_pictures(tmp_path):
    paths = [png(tmp_path / "a.png", 0), png(tmp_path / "b.png", 255), png(tmp_path / "c.png", 0)]
    said = worker.answer(Fake(), {"images": paths})
    assert np.array(said["ccip"]).shape == (3, 3) and np.array(said["clip"]).shape == (3, 3)
    assert said["ccip"][0][2] == pytest.approx(0.0) and said["ccip"][0][1] == pytest.approx(2.0)


def test_a_missing_picture_is_an_error_line_not_a_crash(tmp_path):
    assert "error" in worker.answer(Fake(), {"images": [str(tmp_path / "nope.png")]})


def test_the_worker_answers_one_line_per_ask(tmp_path):
    paths = [png(tmp_path / "a.png", 10), png(tmp_path / "b.png", 20)]
    out = io.StringIO()
    worker.serve(io.StringIO(json.dumps({"images": paths}) + "\n"), out, Fake())
    assert set(json.loads(out.getvalue())) == {"ccip", "clip"}


# ---- the repo side ---------------------------------------------------------------------------

def test_the_worker_runs_isolated_on_the_models_on_disk():
    argv = aid.worker_argv(Path("py.exe"), Path("C:/portable"), "cpu")
    assert argv[:2] == ["py.exe", "-I"] and argv[2].endswith("anime_id_worker.py")
    assert argv[3].endswith(str(Path("ccip") / "ccip-caformer-24-randaug-pruned"))
    assert argv[4].endswith(str(Path("clip_vision") / "clip_vision_h.safetensors")) and argv[5:] == ["cpu", str(aid.THREADS)]


def test_the_same_character_line_is_metrics_json():
    assert aid.SAME_CHARACTER == pytest.approx(0.1785, abs=1e-4)


def test_the_terms_read_the_sheet_against_each_side():
    """Row 0 is the sheet, then the take's crops, then the refined ones."""
    ccip = np.array([[0, .1, .3, .2, .2], [.1, 0, 0, 0, 0], [.3, 0, 0, 0, 0], [.2, 0, 0, 0, 0], [.2, 0, 0, 0, 0]])
    clip = np.array([[1, .7, .9, .8, .8], [.7, 1, 0, 0, 0], [.9, 0, 1, 0, 0], [.8, 0, 0, 1, 0], [.8, 0, 0, 0, 1]])
    got = aid.terms(ccip, clip, 2)
    assert got == pytest.approx({"ccip_src": 0.2, "ccip_ref": 0.2, "clip_src": 0.8, "clip_ref": 0.8})


def test_an_answer_becomes_two_matrices_and_an_error_raises():
    ccip, clip = aid.parse({"ccip": [[0.0]], "clip": [[1.0]]})
    assert ccip.shape == (1, 1) and clip[0, 0] == 1.0
    with pytest.raises(RuntimeError, match="boom"):
        aid.parse({"error": "boom"})


class FakeWorker:
    def __init__(self, device, fail=False):
        self.device, self.fail, self.closed, self.asked = device, fail, False, []

    def __call__(self, paths):
        self.asked.append([Path(p).name for p in paths])
        if self.fail:
            raise RuntimeError("the worker died")
        n = len(paths)
        return np.zeros((n, n)), np.ones((n, n))

    def close(self):
        self.closed = True

    def exited(self):
        return False


def reader(route="cpu", busy=False, fail=False):
    started = []

    def start(device):
        started.append(FakeWorker(device, fail))
        return started[-1]
    return aid.Reader(route=lambda job, gb: route, start=start, busy=lambda: busy,
                      claim=lambda job: contextlib.nullcontext()), started


def test_the_reader_writes_the_crops_and_asks_once(tmp_path):
    read, started = reader()
    crop = np.zeros((16, 16, 3), np.uint8)
    got = read(crop, [crop, crop], [crop, crop])
    assert got == {"ccip_src": 0.0, "ccip_ref": 0.0, "clip_src": 1.0, "clip_ref": 1.0}
    assert started[0].asked == [["sheet.png", "src0.png", "src1.png", "ref0.png", "ref1.png"]]


def test_a_render_that_arrives_moves_a_gpu_reader_to_the_cpu():
    read, started = reader(route="cuda", busy=True)
    crop = np.zeros((8, 8, 3), np.uint8)
    read(crop, [crop], [crop])
    read(crop, [crop], [crop])
    assert [w.device for w in started] == ["cuda", "cpu"] and started[0].closed


def test_a_failed_reader_leaves_the_terms_unread_and_never_starts_again():
    """One fresh start answers a dead worker (tests/test_anime_reader_restarts_a_dead_worker.py);
    a fresh one that fails too ends the reader for the run."""
    read, started = reader(fail=True)
    crop = np.zeros((8, 8, 3), np.uint8)
    assert read(crop, [crop], [crop]) is None and read(crop, [crop], [crop]) is None
    assert len(started) == 2 and all(w.closed for w in started)


def test_no_sheet_crop_leaves_the_terms_unread():
    read, started = reader()
    assert read(None, [np.zeros((8, 8, 3), np.uint8)], []) is None and started == []


@pytest.mark.local
def test_the_real_worker_reads_a_picture_as_itself(tmp_path):
    """The embedded python's onnxruntime + torch on the two models (CPU)."""
    w = aid.Worker(aid.spawn("cpu"))
    try:
        a, b = png(tmp_path / "a.png", 90, 64), png(tmp_path / "b.png", 200, 64)
        ccip, clip = w([a, a, b])
        assert ccip[0, 1] < aid.SAME_CHARACTER and clip[0, 1] == pytest.approx(1.0, abs=1e-3)
    finally:
        w.close()
