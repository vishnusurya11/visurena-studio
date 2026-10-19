"""The anime identity terms for the face refine's gate: CCIP (deepghs/ccip_onnx
`ccip-caformer-24-randaug-pruned`, OpenRAIL) and clip_vision_h's image embedding, under ComfyUI's
embedded python, which holds onnxruntime and torch (the repo venv has neither).  It answers,
for a list of pictures, the CCIP distance matrix (`model_metrics.onnx` on the stacked features;
under metrics.json's 0.1785 is the same character) and the clip cosine matrix, over a line
protocol:

    stdout  {"ready": true}                         once the models are loaded
    stdin   {"images": ["<png>", ...]}              one ask per line
    stdout  {"ccip": [[d]], "clip": [[cos]]} | {"error": "..."}

CCIP's preprocessing is ported from deepghs/imgutils (MIT, imgutils/metrics/ccip.py
`_preprocess_image`: RGB, 384x384 bilinear, /255, (x - 0.5) / 0.5, CHW); dghs-imgutils itself is
never installed (it pins numpy<2).  clip_vision_h is ViT-H/14 in Hugging Face key layout
(ComfyUI's comfy/clip_vision_config_h.json).  It exits on EOF or after IDLE_S without an ask.
Stdlib + numpy + PIL at import, so the repo's tests import it too.

    python -I studio/anime_id_worker.py <ccip dir> <clip_vision_h.safetensors> <cpu|cuda> <threads>
"""
from __future__ import annotations

import json
import queue
import sys
from pathlib import Path

import numpy as np

try:
    from studio.face_detect_worker import lines
except ImportError:                       # run as a script under -I: its own folder is not on the path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from face_detect_worker import lines

IDLE_S = 120.0
CCIP_SIZE = 384
CLIP_SIZE = 224
CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)
CLIP_H = dict(hidden_size=1280, intermediate_size=5120, num_attention_heads=16, num_hidden_layers=32,
              patch_size=14, image_size=CLIP_SIZE, projection_dim=1024, hidden_act="gelu", layer_norm_eps=1e-5)
"""ComfyUI's comfy/clip_vision_config_h.json, the numbers that differ from transformers' defaults."""


def ccip_input(rgb: np.ndarray) -> np.ndarray:
    """imgutils' CCIP preprocessing: 384x384 bilinear, scaled to -1..1, CHW float32."""
    from PIL import Image
    img = Image.fromarray(np.ascontiguousarray(rgb)).convert("RGB").resize((CCIP_SIZE, CCIP_SIZE), Image.BILINEAR)
    data = np.asarray(img).transpose(2, 0, 1).astype(np.float32) / 255.0
    return (data - 0.5) / 0.5


def clip_input(rgb: np.ndarray) -> np.ndarray:
    """CLIP's preprocessing for a square crop: 224x224 bicubic, CLIP's mean and std, CHW float32."""
    from PIL import Image
    img = Image.fromarray(np.ascontiguousarray(rgb)).convert("RGB").resize((CLIP_SIZE, CLIP_SIZE), Image.BICUBIC)
    data = np.asarray(img).astype(np.float32) / 255.0
    return ((data - np.array(CLIP_MEAN, np.float32)) / np.array(CLIP_STD, np.float32)).transpose(2, 0, 1)


def cosines(vecs: np.ndarray) -> np.ndarray:
    """Every pair's cosine."""
    v = np.asarray(vecs, np.float64)
    v = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)
    return v @ v.T


def read_rgb(path: str) -> np.ndarray:
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"))


def answer(models, ask: dict) -> dict:
    """Both matrices over the asked pictures; an error line instead of a crash."""
    try:
        rgbs = [read_rgb(p) for p in ask["images"]]
        dist = models.ccip_dist(models.ccip_feats(np.stack([ccip_input(r) for r in rgbs])))
        cos = cosines(models.clip_embeds(np.stack([clip_input(r) for r in rgbs])))
        return {"ccip": np.asarray(dist, float).round(5).tolist(), "clip": np.asarray(cos, float).round(5).tolist()}
    except Exception as failed:
        return {"error": f"{type(failed).__name__}: {failed}"}


def serve(source, sink, models, idle: float | None = None) -> None:
    """One answer line per ask."""
    try:
        for line in lines(source, idle):
            if line.strip():
                sink.write(json.dumps(answer(models, json.loads(line))) + "\n")
                sink.flush()
    except queue.Empty:
        return


class Models:
    """The two ONNX sessions (CCIP) and clip_vision_h on torch, on one device."""

    def __init__(self, ccip_dir: str, clip_path: str, device: str, threads: int):
        import onnxruntime as ort
        import torch
        torch.set_num_threads(threads)
        providers = (["CUDAExecutionProvider"] if device == "cuda" else []) + ["CPUExecutionProvider"]
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = threads
        self.feat = ort.InferenceSession(str(Path(ccip_dir) / "model_feat.onnx"), opts, providers=providers)
        self.metric = ort.InferenceSession(str(Path(ccip_dir) / "model_metrics.onnx"), opts, providers=providers)
        self.device, self.clip = device, load_clip(clip_path, device)

    def ccip_feats(self, batch: np.ndarray) -> np.ndarray:
        return self.feat.run(None, {self.feat.get_inputs()[0].name: batch.astype(np.float32)})[0]

    def ccip_dist(self, feats: np.ndarray) -> np.ndarray:
        return self.metric.run(None, {self.metric.get_inputs()[0].name: feats.astype(np.float32)})[0]

    def clip_embeds(self, batch: np.ndarray) -> np.ndarray:
        import torch
        with torch.no_grad():
            x = torch.from_numpy(batch).to(self.device)
            return self.clip(pixel_values=x).image_embeds.float().cpu().numpy()


def load_clip(path: str, device: str):
    """clip_vision_h (HF key layout) into transformers' CLIPVisionModelWithProjection, float32."""
    from safetensors.torch import load_file
    from transformers import CLIPVisionConfig, CLIPVisionModelWithProjection
    model = CLIPVisionModelWithProjection(CLIPVisionConfig(**CLIP_H))
    state = {k: v.float() for k, v in load_file(path).items() if not k.endswith("position_ids")}
    missing, _ = model.load_state_dict(state, strict=False)
    if missing:
        raise RuntimeError(f"clip_vision_h is missing {len(missing)} weights, e.g. {missing[:3]}")
    return model.eval().to(device)


def main(argv: list[str]) -> None:
    out, sys.stdout = sys.stdout, sys.stderr
    models = Models(argv[1], argv[2], argv[3], int(argv[4]))
    out.write(json.dumps({"ready": True}) + "\n")
    out.flush()
    serve(sys.stdin, out, models, IDLE_S)


if __name__ == "__main__":
    main(sys.argv)
