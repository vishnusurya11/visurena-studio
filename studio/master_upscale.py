"""The master's one upscale over the joined cut.

MAIN SESSION 2026-10-18 (owner asked for no background jitter and sharp faces):
`av3` -- a light temporal denoise at 768 (`hqdn3d=0:0:4:4`, run per shot so nothing
blends across a cut), then Real-ESRGAN realesr-animevideov3 x4 -> 3072.  Measured
against RTX VSR 4x ULTRA on three Jekyll takes: background jitter -51..-58 %, face
crispness +21..+33 %, ~4.7 min per episode (docs/audit/2026-10-18_upscale).  Its
frame loop runs under ComfyUI's embedded python (studio/master_av3.py): the repo
venv's torch is CPU-only.  Everything upstream stays at H3's 768 fixed point; this
is the one encode that is uploaded, so it is the one that scales.

- `av3` (default): hqdn3d per shot + realesr-animevideov3 4x -> 3072.
- `rtx4x`: RTX VSR ULTRA 4x -> 3072 (owner 2026-10-14; it sharpens H3's grain, which
  boils on walls).  DEBLUR was rejected: it rings on ink lines.
- `rtx2x`: ULTRA 2x -> 1536, the bench's cheaper arm (+0.4 min).
- `lanczos`: the old `scale=...:flags=lanczos` 2x -> 1536, and the FALLBACK when
  the GPU, nvidia-vfx, the portable python or the av3 weights are missing -- logged
  and written on the clock, never silent.

Chosen by `VISURENA_MASTER_UPSCALE`.  RTX VSR is stateless (bench: a frame run fresh
and after ten others differs by 0.0), so one pass over the joined cut equals a pass
per take; av3's denoise is NOT, so it is handed the cut frames (`cuts`).

In process, not through the ComfyUI node: the node holds the whole clip as
float tensors (~30 GB in, ~119 GB out for 4,200 frames) and took 49 s a take.
Frames stream one at a time: ffmpeg decode -> GPU -> VSR -> ffmpeg x264 encode.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from studio.video_encoder import video_args

SETTING = "VISURENA_MASTER_UPSCALE"
ENCODE = ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p",
          "-movflags", "+faststart", "-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
"""`slow` and CRF 14: this runs once per episode and the file it makes is the deliverable."""
START_SHIFT = "-0.0416667"
"""ep15 2026-10-01: the first part's one-frame start offset rides a concat
passthrough; a constant demux shift keeps count and spacing (see assemble.tail)."""


@dataclass(frozen=True)
class Upscale:
    engine: str      # "av3", "rtx" or "lanczos"
    factor: int
    mode: str = ""   # nvvfx QualityLevel name for rtx

    def label(self) -> str:
        return f"{self.engine} {self.factor}x {self.mode}".strip()


CHOICES = {"av3": Upscale("av3", 4), "rtx4x": Upscale("rtx", 4, "ULTRA"),
           "rtx2x": Upscale("rtx", 2, "ULTRA"), "lanczos": Upscale("lanczos", 2)}
DEFAULT = "av3"
LANCZOS = CHOICES["lanczos"]
AV3_WEIGHTS = "ComfyUI/models/upscale_models/realesr-animevideov3.pth"
"""Under the portable root (studio/engine_ops.portable_root, `COMFY_PORTABLE`); source
github.com/xinntao/Real-ESRGAN releases v0.2.5.0, 2.4 MB, BSD-3."""


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


def av3_paths(env=None) -> tuple[Path, Path]:
    """(the portable python, the av3 weights): both under the one portable root."""
    from studio.engine_ops import portable_root
    root = portable_root(os.environ if env is None else env)
    return root / "python_embeded" / "python.exe", root / AV3_WEIGHTS


def av3_missing(paths: tuple[Path, Path]) -> str:
    """Why av3 cannot run here, or '' when it can."""
    gone = [Path(p).name for p in paths if not Path(p).exists()]
    return f"missing {', '.join(gone)}" if gone else ""


def missing_for(want: Upscale) -> str:
    if want.engine == "rtx":
        return rtx_missing()
    return av3_missing(av3_paths()) if want.engine == "av3" else ""


def settle(want: Upscale, missing: str) -> tuple[Upscale, str]:
    """The upscale that will run, and why it is not the one asked for ('' when it is)."""
    if want.engine == "lanczos" or not missing:
        return want, ""
    return LANCZOS, f"{name_of(want)} unavailable ({missing}); fell back to lanczos 2x"


def resolved(env=None) -> tuple[Upscale, str]:
    """The setting's upscale, settled against this machine: (what runs, why not the ask)."""
    want = choice(env)
    return settle(want, missing_for(want))


def lanczos_argv(listing: Path, out: Path, width: int, height: int, up: Upscale,
                 encoder: str = "cpu") -> list[str]:
    """The pre-2026-10-14 master encode: join, Lanczos scale, x264, in one ffmpeg."""
    w, h = size(width, height, up)
    return ["ffmpeg", "-y", "-v", "error", "-itsoffset", START_SHIFT,
            "-f", "concat", "-safe", "0", "-i", str(listing),
            "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p", "-af", "asetpts=PTS-STARTPTS",
            "-fps_mode", "vfr", "-muxdelay", "0", "-muxpreload", "0", *video_args(ENCODE, encoder), str(out)]


def decode_argv(listing: Path, width: int, height: int) -> list[str]:
    """The joined cut as raw RGB frames on stdout, every frame once, in order, each
    at the cut's size: a raw stream has no frame headers, so one part of another
    size would shear every frame after it rather than fail."""
    return ["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
            "-map", "0:v", "-vf", f"scale={width}:{height}", "-fps_mode", "passthrough",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]


def encode_argv(listing: Path, out: Path, width: int, height: int, fps: int, encoder: str = "cpu") -> list[str]:
    """Upscaled raw frames from stdin, the joined cut's sound from the listing; x264, or
    NVENC when the router sent the encode to the GPU (studio/video_encoder)."""
    return ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-framerate", str(fps), "-i", "-",
            "-itsoffset", START_SHIFT, "-f", "concat", "-safe", "0", "-i", str(listing),
            "-map", "0:v", "-map", "1:a", "-af", "asetpts=PTS-STARTPTS",
            "-muxdelay", "0", "-muxpreload", "0", *video_args(ENCODE, encoder), str(out)]


Frame = Callable[["object"], "object"]


def pasted(read: Callable[[int], bytes], paste: Frame | None, width: int, height: int) -> Callable[[int], bytes]:
    """The decoder's frames with the face paste applied at CUT scale (owner 2026-10-18:
    every picture edit before the one upscale, none after it); `read` itself when none."""
    if paste is None:
        return read
    import numpy as np

    def out(n: int) -> bytes:
        buf = read(n)
        if len(buf) != width * height * 3:
            return buf
        return np.ascontiguousarray(paste(np.frombuffer(buf, np.uint8).reshape(height, width, 3))).tobytes()
    return out


def at_cut(wrap) -> Frame | None:
    """assemble's wrap (a partial of face_paste.Paster built for master scale) as a paste
    at the cut's own scale with no upscale inside it; a plain wrap gets the identity."""
    if wrap is None:
        return None
    keywords = getattr(wrap, "keywords", None)
    if keywords is not None and "spans" in keywords:
        return wrap.func(lambda f: f, **{**keywords, "factor": 1})
    return wrap(lambda f: f)


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
             upscaler: Frame, encoder: str = "cpu", paste: Frame | None = None) -> int:
    """decode | paste at cut scale | upscale | encode; refuses a failed ffmpeg on either
    side, and a failure kills the decoder rather than wait on its full pipe."""
    w, h = size(width, height, up)
    dec = subprocess.Popen(decode_argv(listing, width, height), stdout=subprocess.PIPE)
    enc = subprocess.Popen(encode_argv(listing, out, w, h, fps, encoder), stdin=subprocess.PIPE)
    try:
        n = pump(pasted(dec.stdout.read, paste, width, height), enc.stdin.write, width, height, upscaler)
    except BaseException:
        for proc in (dec, enc):
            proc.kill()
        raise
    finally:
        try:
            enc.stdin.close()
        except OSError:
            pass
        codes = enc.wait(), dec.wait()
    if any(codes):
        raise RuntimeError(f"the {up.label()} master encode failed: encoder {codes[0]}, decoder {codes[1]}")
    return n


def master(listing: Path, out: Path, width: int, height: int, up: Upscale, fps: int,
           upscaler: Frame | None = None, wrap: Callable[[Frame], Frame] | None = None,
           cuts: list[int] | None = None, encoder: str = "cpu") -> Path:
    """The joined cut, upscaled and encoded once (`encoder`: the router's device).  `upscaler` replaces the GPU in tests;
    `wrap` is the face refine's paste (studio/face_paste.Paster), applied at CUT scale
    to every frame BEFORE the upscale (owner 2026-10-18: the upscale is the last picture
    operation, only muxing follows it); `cuts` are the frames each new
    shot starts on (av3's denoise starts fresh there)."""
    if up.engine == "lanczos":
        if wrap is not None:
            print("FACE REFINE: the lanczos fallback has no frame loop; nothing pasted", file=sys.stderr, flush=True)
        subprocess.run(lanczos_argv(listing, out, width, height, up, encoder), check=True)
        return out
    if up.engine == "av3":
        return av3_master(listing, out, width, height, up, fps, upscaler, wrap, cuts or [], encoder)
    effect = upscaler or Rtx(width, height, up)
    try:
        streamed(listing, out, width, height, up, fps, effect, encoder, paste=at_cut(wrap))
    finally:
        if upscaler is None:
            effect.close()
    return out


def av3_master(listing: Path, out: Path, width: int, height: int, up: Upscale, fps: int,
               upscaler, wrap, cuts: list[int], encoder: str = "cpu") -> Path:
    """In process with a stand-in model (tests); else the portable python's worker,
    which rebuilds the face paste from its spans and pastes at cut scale BEFORE the 4x.
    A stalled or failed worker falls back to rtx4x (lanczos without RTX), said."""
    from studio import master_av3
    if upscaler is not None:
        master_av3.streamed(listing, out, width, height, up.factor, fps, upscaler, cuts, encoder=encoder,
                            paste=at_cut(wrap))
        return out
    python, weights = av3_paths()
    job = out.with_name(out.stem + ".av3_job.json")
    job.write_text(json.dumps(av3_job(listing, out, width, height, up, fps, spans_of(wrap), cuts, weights,
                                      encoder)), encoding="utf-8")
    from studio import compute_device
    with compute_device.claim("av3 master"):     # the card is ours outside ComfyUI's queue
        code = run_worker(python, job)
    if code:
        return av3_fallback(code, listing, out, width, height, fps, wrap, encoder)
    return out


AV3_STALLED = 75
"""The av3 worker's exit code for a stall (studio/master_av3.STALLED)."""


def run_worker(python: Path, job: Path) -> int:
    """The av3 worker under the portable python; its exit code."""
    return subprocess.run(worker_argv(python, job)).returncode


def av3_fallback(code: int, listing: Path, out: Path, width: int, height: int, fps: int,
                 wrap, encoder: str) -> Path:
    """A stalled or failed av3 worker: the master again through rtx4x, or lanczos
    without RTX here -- said where the run's log reads it, never silent."""
    up = LANCZOS if rtx_missing() else CHOICES["rtx4x"]
    what = "stalled" if code == AV3_STALLED else f"failed (exit {code})"
    print(f"CAP upscale: av3 {what}, fell back to {name_of(up)}", file=sys.stderr, flush=True)
    return master(listing, out, width, height, up, fps, wrap=wrap, encoder=encoder)


def av3_job(listing: Path, out: Path, width: int, height: int, up: Upscale, fps: int,
            spans: list, cuts: list[int], weights: Path, encoder: str = "cpu") -> dict:
    """Everything the worker needs, as JSON (a transient beside the output, never kept)."""
    from studio import master_av3
    return {"listing": str(listing), "out": str(out), "width": width, "height": height, "factor": up.factor,
            "fps": fps, "cuts": list(cuts), "weights": str(weights), "spans": master_av3.spans_json(spans),
            "encoder": encoder}


def worker_argv(python: Path, job: Path) -> list[str]:
    return [str(python), "-I", str(Path(__file__).with_name("master_av3.py")), str(job)]


def spans_of(wrap) -> list:
    """The face paste's spans off assemble's wrap (a functools.partial of Paster)."""
    if wrap is None:
        return []
    spans = getattr(wrap, "keywords", {}).get("spans")
    if spans is None:
        raise TypeError("the av3 worker takes the face paste as a functools.partial of face_paste.Paster")
    return list(spans)


def say(why: str) -> None:
    """A fallback is printed where the run's log reads it, never swallowed."""
    if why:
        print(f"UPSCALE FALLBACK: {why}", file=sys.stderr, flush=True)
