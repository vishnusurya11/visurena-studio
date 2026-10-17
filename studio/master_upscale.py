"""The master's one upscale: NVIDIA RTX Video Super Resolution over the joined cut.

OWNER 2026-10-14: adopt RTX VSR at the HIGHEST quality that costs under 10 min
per episode -- 4x standard ULTRA, delivered at 3072 (+3.8 min on the bench,
docs/audit/2026-10-14_rtx_vsr_test).  Everything upstream stays at H3's 768
fixed point; this is the one encode that is uploaded, so it is the one that scales.

- `rtx4x` (default): ULTRA 4x -> 3072.  DEBLUR was rejected: it rings on ink lines.
- `rtx2x`: ULTRA 2x -> 1536, the bench's cheaper arm (+0.4 min).
- `lanczos`: the old `scale=...:flags=lanczos` 2x -> 1536, and the FALLBACK when
  nvidia-vfx or the GPU is missing -- logged and written on the clock, never silent.

Chosen by `VISURENA_MASTER_UPSCALE`.  The effect is stateless (bench: a frame
run fresh and after ten others differs by 0.0), so one pass over the joined cut,
hard cuts and the title card included, equals a pass per take.

In process, not through the ComfyUI node: the node holds the whole clip as
float tensors (~30 GB in, ~119 GB out for 4,200 frames) and took 49 s a take.
Frames stream one at a time: ffmpeg decode -> GPU -> VSR -> ffmpeg x264 encode.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SETTING = "VISURENA_MASTER_UPSCALE"
ENCODE = ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p",
          "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
"""`slow` and CRF 14: this runs once per episode and the file it makes is the deliverable."""
START_SHIFT = "-0.0416667"
"""ep15 2026-10-01: the first part's one-frame start offset rides a concat
passthrough; a constant demux shift keeps count and spacing (see assemble.tail)."""


@dataclass(frozen=True)
class Upscale:
    engine: str      # "rtx" or "lanczos"
    factor: int
    mode: str = ""   # nvvfx QualityLevel name for rtx

    def label(self) -> str:
        return f"{self.engine} {self.factor}x {self.mode}".strip()


CHOICES = {"rtx4x": Upscale("rtx", 4, "ULTRA"), "rtx2x": Upscale("rtx", 2, "ULTRA"),
           "lanczos": Upscale("lanczos", 2)}
DEFAULT = "rtx4x"
LANCZOS = CHOICES["lanczos"]


def choice(env=None) -> Upscale:
    """The setting's upscale; unset is the owner's default, unknown is refused."""
    name = (os.environ if env is None else env).get(SETTING, DEFAULT) or DEFAULT
    if name not in CHOICES:
        raise SystemExit(f"{SETTING}={name!r} is not one of {', '.join(CHOICES)}")
    return CHOICES[name]


def name_of(up: Upscale) -> str:
    return next(k for k, v in CHOICES.items() if v == up)


def size(width: int, height: int, up: Upscale) -> tuple[int, int]:
    """The delivered canvas."""
    return width * up.factor, height * up.factor


def rtx_missing() -> str:
    """Why RTX VSR cannot run here, or '' when it can."""
    try:
        import cupy
        import nvvfx  # noqa: F401
        if cupy.cuda.runtime.getDeviceCount() < 1:
            return "no CUDA device"
    except Exception as failed:      # an import, a DLL or a driver: each is a reason
        return f"{type(failed).__name__}: {failed}"
    return ""


def settle(want: Upscale, missing: str) -> tuple[Upscale, str]:
    """The upscale that will run, and why it is not the one asked for ('' when it is)."""
    if want.engine != "rtx" or not missing:
        return want, ""
    return LANCZOS, f"{name_of(want)} unavailable ({missing}); fell back to lanczos 2x"


def resolved(env=None) -> tuple[Upscale, str]:
    """The setting's upscale, settled against this machine: (what runs, why not the ask)."""
    want = choice(env)
    return settle(want, rtx_missing() if want.engine == "rtx" else "")


def lanczos_argv(listing: Path, out: Path, width: int, height: int, up: Upscale) -> list[str]:
    """The pre-2026-10-14 master encode: join, Lanczos scale, x264, in one ffmpeg."""
    w, h = size(width, height, up)
    return ["ffmpeg", "-y", "-v", "error", "-itsoffset", START_SHIFT,
            "-f", "concat", "-safe", "0", "-i", str(listing),
            "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p", "-af", "asetpts=PTS-STARTPTS",
            "-fps_mode", "vfr", "-muxdelay", "0", "-muxpreload", "0", *ENCODE, str(out)]


def decode_argv(listing: Path, width: int, height: int) -> list[str]:
    """The joined cut as raw RGB frames on stdout, every frame once, in order, each
    at the cut's size: a raw stream has no frame headers, so one part of another
    size would shear every frame after it rather than fail."""
    return ["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
            "-map", "0:v", "-vf", f"scale={width}:{height}", "-fps_mode", "passthrough",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]


def encode_argv(listing: Path, out: Path, width: int, height: int, fps: int) -> list[str]:
    """Upscaled raw frames from stdin, the joined cut's sound from the listing."""
    return ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-framerate", str(fps), "-i", "-",
            "-itsoffset", START_SHIFT, "-f", "concat", "-safe", "0", "-i", str(listing),
            "-map", "0:v", "-map", "1:a", "-af", "asetpts=PTS-STARTPTS",
            "-muxdelay", "0", "-muxpreload", "0", *ENCODE, str(out)]


Frame = Callable[["object"], "object"]


def pump(read: Callable[[int], bytes], write: Callable[[bytes], object], width: int, height: int,
         upscaler: Frame) -> int:
    """Read frames until the decoder ends, upscale each, write it; the count."""
    import numpy as np
    size_of, n = width * height * 3, 0
    while len(buf := read(size_of)) == size_of:
        frame = np.frombuffer(buf, np.uint8).reshape(height, width, 3)
        write(np.ascontiguousarray(upscaler(frame)).tobytes())
        n += 1
    return n


class Rtx:
    """One loaded VideoSuperRes effect: HxWx3 uint8 in, (factor*H)x(factor*W)x3 uint8 out."""

    def __init__(self, width: int, height: int, up: Upscale):
        import cupy
        import nvvfx
        self.cp = cupy
        self.effect = nvvfx.VideoSuperRes(quality=nvvfx.QualityLevel[up.mode], strength=1.0, device=0)
        self.effect.__enter__()
        self.effect.output_width, self.effect.output_height = size(width, height, up)
        self.effect.load()

    def __call__(self, frame):
        cp = self.cp
        planar = cp.ascontiguousarray(cp.asarray(frame).transpose(2, 0, 1)).astype(cp.float32) / 255.0
        out = cp.from_dlpack(self.effect.run(planar).image)
        return cp.asnumpy((cp.clip(out, 0.0, 1.0) * 255.0).round().astype(cp.uint8).transpose(1, 2, 0))

    def close(self) -> None:
        self.effect.__exit__(None, None, None)


def streamed(listing: Path, out: Path, width: int, height: int, up: Upscale, fps: int,
             upscaler: Frame) -> int:
    """decode | upscale | encode; refuses a failed ffmpeg on either side."""
    w, h = size(width, height, up)
    dec = subprocess.Popen(decode_argv(listing, width, height), stdout=subprocess.PIPE)
    enc = subprocess.Popen(encode_argv(listing, out, w, h, fps), stdin=subprocess.PIPE)
    try:
        n = pump(dec.stdout.read, enc.stdin.write, width, height, upscaler)
    finally:
        enc.stdin.close()
        codes = enc.wait(), dec.wait()
    if any(codes):
        raise RuntimeError(f"the {up.label()} master encode failed: encoder {codes[0]}, decoder {codes[1]}")
    return n


def master(listing: Path, out: Path, width: int, height: int, up: Upscale, fps: int,
           upscaler: Frame | None = None, wrap: Callable[[Frame], Frame] | None = None) -> Path:
    """The joined cut, upscaled and encoded once.  `upscaler` replaces the GPU in tests;
    `wrap` takes each upscaled frame on its way to the encoder (the face refine's
    paste at master scale, studio/face_paste.Paster)."""
    if up.engine == "lanczos":
        if wrap is not None:
            print("FACE REFINE: the lanczos fallback has no frame loop; nothing pasted", file=sys.stderr, flush=True)
        subprocess.run(lanczos_argv(listing, out, width, height, up), check=True)
        return out
    effect = upscaler or Rtx(width, height, up)
    try:
        streamed(listing, out, width, height, up, fps, wrap(effect) if wrap else effect)
    finally:
        if upscaler is None:
            effect.close()
    return out


def say(why: str) -> None:
    """A fallback is printed where the run's log reads it, never swallowed."""
    if why:
        print(f"UPSCALE FALLBACK: {why}", file=sys.stderr, flush=True)
