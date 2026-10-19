"""The anime face detector: face_yolov8m.pt (Bingsu/adetailer, Apache-2.0) under ComfyUI's
embedded python, which holds ultralytics and CUDA torch (the repo venv has neither).  It reads
a take itself and answers its boxes on every k-th frame over a line protocol:

    stdout  {"ready": true}                          once the weights are loaded
    stdin   {"video": "<path>", "every": k}          one take per line
    stdout  {"dets": {"<frame>": [{"box": [x1, y1, x2, y2], "score": s}]}} | {"error": "..."}

It exits on EOF, or after IDLE_S without a take (studio/face_detect starts it; the device
router chose its device).  Protocol lines go to the real stdout; everything ultralytics prints
goes to stderr.  Stdlib + numpy + cv2 at import, so the repo's tests import it too.

    python -I studio/face_detect_worker.py <weights> <cpu|cuda> <conf> <threads>
"""
from __future__ import annotations

import json
import queue
import sys
import threading

IDLE_S = 60.0
IMGSZ = 768
"""The take's own size: a 15 px face (ep01 T01) is not shrunk further."""
CONF = 0.6
"""The audit counted a face at >= 0.6; 0.43-0.51 were 12-15 px far figures, possibly false
(docs/audit/2026-10-19_face_blur/pipeline_audit.md section 2)."""


def rows(result) -> list[dict]:
    """One ultralytics result as [{"box", "score"}] rows."""
    xyxy, conf = result.boxes.xyxy.tolist(), result.boxes.conf.tolist()
    return [{"box": [round(float(v), 1) for v in b], "score": round(float(c), 3)} for b, c in zip(xyxy, conf)]


def detect_video(predict, path: str, every: int) -> dict[str, list[dict]]:
    """Boxes on every `every`-th frame of the video, keyed by frame number."""
    import cv2
    cap, out, t = cv2.VideoCapture(str(path)), {}, 0
    if not cap.isOpened():
        raise FileNotFoundError(f"cannot open {path}")
    while cap.grab():
        if t % every == 0:
            ok, bgr = cap.retrieve()
            if ok:
                out[str(t)] = rows(predict(bgr)[0])
        t += 1
    cap.release()
    return out


def answer(predict, ask: dict) -> dict:
    try:
        return {"dets": detect_video(predict, ask["video"], max(int(ask.get("every", 3)), 1))}
    except Exception as failed:
        return {"error": f"{type(failed).__name__}: {failed}"}


def lines(source, idle: float | None):
    """The source's lines, ending at EOF or after `idle` seconds without one."""
    if idle is None:
        yield from source
        return
    got: queue.Queue = queue.Queue()
    threading.Thread(target=lambda: [got.put(l) for l in source] + [got.put(None)], daemon=True).start()
    while (line := got.get(timeout=idle)) is not None:     # queue.Empty after `idle`
        yield line


def serve(source, sink, predict, idle: float | None = None) -> None:
    """One answer line per asked take."""
    try:
        for line in lines(source, idle):
            if line.strip():
                sink.write(json.dumps(answer(predict, json.loads(line))) + "\n")
                sink.flush()
    except queue.Empty:
        return


def load(weights: str, device: str, conf: float, threads: int):
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(threads)
    model = YOLO(weights)
    return lambda bgr: model.predict(bgr, imgsz=IMGSZ, conf=conf, device=device, verbose=False)


def main(argv: list[str]) -> None:
    out, sys.stdout = sys.stdout, sys.stderr
    predict = load(argv[1], argv[2], float(argv[3]), int(argv[4]))
    out.write(json.dumps({"ready": True}) + "\n")
    out.flush()
    serve(sys.stdin, out, predict, IDLE_S)


if __name__ == "__main__":
    main(sys.argv)
