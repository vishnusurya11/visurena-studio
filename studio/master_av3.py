"""The av3 master pass: a light temporal denoise at 768, then Real-ESRGAN
realesr-animevideov3 x4, streamed one frame at a time (main session 2026-10-18,
docs/audit/2026-10-18_upscale/UPSCALE.md: background jitter -51..-58 % against RTX VSR
4x ULTRA, face crispness +21..+33 %, ~4.7 min per episode, encode-bound).

The denoise (`hqdn3d=0:0:4:4`: no spatial blur, temporal 4) is recursive in time, so
it runs ONE FFMPEG PER SHOT: its memory starts empty on every cut and the first frame
after a hard cut carries nothing of the shot before it.

Run as a script under ComfyUI's embedded python (CUDA torch + spandrel; the repo
venv's torch is CPU-only):  python -I studio/master_av3.py <job.json>
The job is written by studio/master_upscale.av3_job.  Imported by the repo, the same
loop runs in process with a stand-in model (tests).
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from dataclasses import asdict
from pathlib import Path

if __package__ in (None, ""):        # a script under the portable python: the repo is two up
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import face_paste as fp  # noqa: E402
from studio import master_upscale as mu  # noqa: E402

PREFILTER = "format=yuv444p16le,hqdn3d=0:0:4:4"
"""Luma and chroma spatial 0, temporal 4: the bench's arm `hqdn_av3`.  It filters the
rgb24 frames the RTX path decoded (each part's own colour matrix honoured; raw yuv
would lose the bt709 tag, 0.55 mean / 6 max off on take C) through 16-bit 4:4:4,
which round-trips at 0.18 mean."""


def lengths(cuts: list[int]) -> list[int | None]:
    """Frames per shot from the frames each new shot starts on; the last runs to the end."""
    at, out = 0, []
    for cut in sorted(set(c for c in cuts if c > 0)):
        out.append(cut - at)
        at = cut
    return out + [None]


def filter_argv(width: int, height: int, filt: str) -> list[str]:
    """One shot's raw rgb24 frames in, filtered, rgb24 out; every frame once."""
    return ["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
            "-i", "-", "-vf", filt, "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]


class Segmented:
    """The decoder's frames, filtered shot by shot: `read(n)` hands out one rgb24 frame."""

    def __init__(self, read, width: int, height: int, shots: list[int | None], filt: str = PREFILTER):
        self.upstream, self.size, self.shots, self.filt = read, (width, height), list(shots), filt
        self.proc = self.feeder = None
        self.ended = self.done = False

    def read(self, n: int) -> bytes:
        while not self.done:
            if self.proc is None:
                self.open_next()
                continue
            if len(buf := self.proc.stdout.read(n)) == n:
                return buf
            self.close_current()
        return b""

    def open_next(self) -> None:
        w, h = self.size
        first = b"" if self.ended else self.upstream(w * h * 3)
        if len(first) < w * h * 3:
            self.done = True
            return
        count = self.shots.pop(0) if self.shots else None
        self.proc = subprocess.Popen(filter_argv(w, h, self.filt), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.feeder = threading.Thread(target=self.feed, args=(self.proc, first, count), daemon=True)
        self.feeder.start()

    def feed(self, proc, frame: bytes, count: int | None) -> None:
        need, k = len(frame), 0
        try:
            while True:
                proc.stdin.write(frame)
                k += 1
                if count is not None and k >= count:
                    break
                if len(frame := self.upstream(need)) < need:
                    self.ended = True
                    break
        finally:
            proc.stdin.close()

    def close_current(self) -> None:
        self.feeder.join()
        if self.proc.wait():
            raise RuntimeError(f"the per-shot denoise failed: ffmpeg {self.proc.returncode}")
        self.proc = None
        self.done = self.ended


def streamed(listing: Path, out: Path, width: int, height: int, factor: int, fps: int,
             upscaler, cuts: list[int], filt: str = PREFILTER) -> int:
    """decode | denoise per shot | upscale (+ paste) | encode; refuses a failed ffmpeg."""
    dec = subprocess.Popen(mu.decode_argv(listing, width, height), stdout=subprocess.PIPE)
    enc = subprocess.Popen(mu.encode_argv(listing, out, width * factor, height * factor, fps), stdin=subprocess.PIPE)
    try:
        n = mu.pump(Segmented(dec.stdout.read, width, height, lengths(cuts), filt).read,
                    enc.stdin.write, width, height, upscaler)
    finally:
        enc.stdin.close()
        codes = enc.wait(), dec.wait()
    if any(codes):
        raise RuntimeError(f"the av3 master encode failed: encoder {codes[0]}, decoder {codes[1]}")
    return n


def spans_json(spans: list[fp.Span]) -> list[dict]:
    return [asdict(s) for s in spans]


def spans_back(rows: list[dict]) -> list[fp.Span]:
    """The face paste's spans as the repo built them, rebuilt in the worker."""
    def track(t):
        return fp.Track([tuple(w) for w in t["windows"]], tuple(t["life"]), int(t["start"]), str(t["crop"]))
    return [fp.Span(int(r["index"]), int(r["start"]), int(r["frames"]), int(r["head"]), float(r["slow"]),
                    tuple(r["guard"]) if r["guard"] else None, tuple(track(t) for t in r["tracks"])) for r in rows]


class Av3:
    """realesr-animevideov3 (SRVGGNetCompact x4, BSD-3) through spandrel, fp16 on CUDA:
    HxWx3 uint8 in, 4Hx4Wx3 uint8 out."""

    def __init__(self, weights):
        import spandrel
        import torch
        self.torch = torch
        self.model = spandrel.ModelLoader().load_from_file(str(weights)).model.cuda().half().eval()

    def __call__(self, frame):
        torch = self.torch
        with torch.no_grad():
            x = torch.from_numpy(frame.copy()).cuda().permute(2, 0, 1).float().div(255)
            y = self.model(x[None].half())[0].float()
            return (y.clamp(0, 1) * 255).round().byte().permute(1, 2, 0).contiguous().cpu().numpy()


def run(job: dict, upscaler=None) -> int:
    """One job: the model (or a stand-in), the face paste at master scale when the job
    carries spans, then the streamed pass."""
    effect = upscaler or Av3(job["weights"])
    spans = spans_back(job["spans"])
    frame = fp.Paster(effect, spans, job["width"], job["height"], job["factor"]) if spans else effect
    return streamed(Path(job["listing"]), Path(job["out"]), job["width"], job["height"], job["factor"],
                    job["fps"], frame, job["cuts"])


def main(argv: list[str]) -> None:
    t0 = time.perf_counter()
    n = run(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
    print(json.dumps({"av3_frames": n, "wall_s": round(time.perf_counter() - t0, 1)}), flush=True)


if __name__ == "__main__":
    main(sys.argv)
