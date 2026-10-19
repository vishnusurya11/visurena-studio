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
import os
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
        """One shot's frames into its denoise; a killed pipeline ends it quietly."""
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
        except OSError:
            self.ended = True
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass

    def close_current(self) -> None:
        self.feeder.join()
        if self.proc.wait():
            raise RuntimeError(f"the per-shot denoise failed: ffmpeg {self.proc.returncode}")
        self.proc = None
        self.done = self.ended


STALL_S = 60.0
"""No frame through the pump for this long is a stall: the pipeline is killed."""
STALLED = 75
"""The worker's exit code for a stall (studio/master_upscale.AV3_STALLED)."""
SHORT = 77
"""The worker's exit code for a pass that ended short (studio/master_upscale.AV3_SHORT)."""


class Stalled(RuntimeError):
    """The pump moved no frame for STALL_S; the pipeline was killed."""


class Watchdog:
    """Calls `fire` once when `tick` has not been called for `seconds`."""

    def __init__(self, seconds: float, fire, poll: float = 1.0):
        self.seconds, self.fire, self.poll = seconds, fire, poll
        self.last, self.fired, self.halt = time.monotonic(), False, threading.Event()
        self.thread = threading.Thread(target=self.watch, daemon=True)

    def start(self) -> "Watchdog":
        self.thread.start()
        return self

    def tick(self) -> None:
        self.last = time.monotonic()

    def watch(self) -> None:
        while not self.halt.wait(self.poll):
            if time.monotonic() - self.last > self.seconds:
                self.fired = True
                self.fire()
                return

    def stop(self) -> None:
        self.halt.set()


def kill_all(*procs) -> None:
    """Every live process of the pipeline, killed: no pipe is left blocking another."""
    for proc in procs:
        if proc is not None and proc.poll() is None:
            proc.kill()


def ticking(write, dog: Watchdog):
    def out(data: bytes):
        write(data)
        dog.tick()
    return out


def streamed(listing: Path, out: Path, width: int, height: int, factor: int, fps: int,
             upscaler, cuts: list[int], filt: str = PREFILTER, encoder: str = "cpu",
             paste=None, stall_s: float = STALL_S, hard_exit=None, expected_frames: int | None = None) -> int:
    """decode | face paste at cut scale | denoise per shot | upscale | encode.  A failure
    or a stall kills the whole pipeline and surfaces; it never waits on a blocked pipe.
    A pass that emitted other than `expected_frames` is a ShortPass (K8)."""
    dec = subprocess.Popen(mu.decode_argv(listing, width, height), stdout=subprocess.PIPE)
    enc = subprocess.Popen(mu.encode_argv(listing, out, width * factor, height * factor, fps, encoder),
                           stdin=subprocess.PIPE)
    seg = Segmented(mu.pasted(dec.stdout.read, paste, width, height), width, height, lengths(cuts), filt)
    dog = Watchdog(stall_s, lambda: stall(dec, enc, seg, hard_exit), poll=min(1.0, stall_s / 4)).start()
    try:
        n = mu.pump(seg.read, ticking(enc.stdin.write, dog), width, height, upscaler)
    except BaseException as failed:
        kill_all(dec, enc, seg.proc)
        if dog.fired:
            raise Stalled(f"the av3 pass moved no frame for {stall_s:.0f} s") from failed
        raise
    finally:
        dog.stop()
        codes = finish(dec, enc, seg)
    if dog.fired:
        raise Stalled(f"the av3 pass moved no frame for {stall_s:.0f} s")
    if any(codes):
        raise RuntimeError(f"the av3 master encode failed: encoder {codes[0]}, decoder {codes[1]}")
    return mu.counted(n, expected_frames)


def stall(dec, enc, seg: "Segmented", hard_exit) -> None:
    """The watchdog's act: the pipeline killed, said, and (in the worker) the process ended."""
    print(f"CAP upscale: av3 stalled (no frame for {STALL_S:.0f} s); the pipeline is killed",
          file=sys.stderr, flush=True)
    kill_all(dec, enc, seg.proc)
    if hard_exit is not None:
        hard_exit()


def finish(dec, enc, seg: "Segmented") -> tuple[int, int]:
    """The encoder closed and both ends reaped; the decoder is killed first if it still
    holds frames nobody will read (a short cut, an early end)."""
    try:
        enc.stdin.close()
    except OSError:
        pass
    code = enc.wait()
    try:
        return code, dec.wait(timeout=30)
    except subprocess.TimeoutExpired:
        kill_all(dec, seg.proc)
        return code, dec.wait()


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


def paste_of(job: dict):
    """The face paste at CUT scale (owner 2026-10-18: paste, then the one upscale), or None."""
    spans = spans_back(job["spans"])
    return fp.Paster(lambda f: f, spans, job["width"], job["height"], 1) if spans else None


def run(job: dict, upscaler=None, hard_exit=None) -> int:
    """One job: the model (or a stand-in), the face paste at cut scale ahead of it when
    the job carries spans, then the streamed pass."""
    effect = upscaler or Av3(job["weights"])
    return streamed(Path(job["listing"]), Path(job["out"]), job["width"], job["height"], job["factor"],
                    job["fps"], effect, job["cuts"], encoder=job.get("encoder", "cpu"), paste=paste_of(job),
                    hard_exit=hard_exit, expected_frames=job.get("expected_frames"))


def main(argv: list[str]) -> None:
    """The worker: a stall exits with STALLED (even when the main thread is stuck in
    CUDA, the watchdog ends the process), so the repo can fall back."""
    t0 = time.perf_counter()
    try:
        n = run(json.loads(Path(argv[1]).read_text(encoding="utf-8")), hard_exit=lambda: os._exit(STALLED))
    except Stalled as stuck:
        print(f"CAP upscale: av3 stalled: {stuck}", file=sys.stderr, flush=True)
        raise SystemExit(STALLED)
    except mu.ShortPass as short:
        print(f"CAP upscale: av3 ended short: {short} frames", file=sys.stderr, flush=True)
        raise SystemExit(SHORT)
    print(json.dumps({"av3_frames": n, "wall_s": round(time.perf_counter() - t0, 1)}), flush=True)


if __name__ == "__main__":
    main(sys.argv)
