"""The video codec arguments, routed (owner 2026-10-18: GPU when idle, CPU when rendering).

On "cpu" an x264 argument list comes back exactly as written.  On "cuda" its
`-c:v libx264 -preset P -crf N` becomes NVENC at its highest-quality preset -- p7,
tune hq, constant quality N + CQ_OFFSET, full-resolution two-pass, spatial and
temporal AQ -- and every other argument stays where it was.  NVENC is its own
engine on the card: it does not take the CUDA cores a render uses, but it does
take VRAM and the bus, so it rides the same router as every other heavy job.

Pure stdlib: ComfyUI's embedded python (the av3 worker) imports it too.
"""
from __future__ import annotations

from typing import Callable

CQ_OFFSET = 5
"""NVENC cq minus x264 crf at equal quality: measured 2026-10-18 on a Jekyll ep01 take at 3072,
x264 slow crf 14 SSIM 0.99691 / 22.1 MB vs NVENC p7 cq 19 SSIM 0.99714 / 27.6 MB (cq 14: 0.99800 / 48.7 MB)."""
NVENC_GB = 1.0
"""VRAM one NVENC session at 3072 x 3072 needs, with room."""


def nvenc(crf: str) -> list[str]:
    return ["-c:v", "h264_nvenc", "-preset", "p7", "-tune", "hq", "-rc", "vbr",
            "-cq", str(int(float(crf)) + CQ_OFFSET), "-b:v", "0", "-multipass", "fullres",
            "-spatial-aq", "1", "-temporal-aq", "1", "-rc-lookahead", "32", "-bf", "3"]


def x264_span(args: list[str]) -> tuple[int, int, str] | None:
    """(start, end, crf) of the `-c:v libx264 [-preset P] [-crf N]` run, or None."""
    if "libx264" not in args or args[args.index("libx264") - 1] != "-c:v":
        return None
    start = args.index("libx264") - 1
    end, crf = start + 2, "18"
    while end + 1 < len(args) and args[end] in ("-preset", "-crf", "-tune"):
        crf = args[end + 1] if args[end] == "-crf" else crf
        end += 2
    return start, end, crf


def video_args(args: list[str], device: str) -> list[str]:
    """`args` unchanged (a copy) on the CPU; its x264 run swapped for NVENC on CUDA."""
    span = x264_span(list(args)) if device == "cuda" else None
    if span is None:
        return list(args)
    start, end, crf = span
    return list(args[:start]) + nvenc(crf) + list(args[end:])


def encoder_for(job: str, route: Callable | None = None) -> str:
    """The router's device for one encode."""
    if route is None:
        from studio.compute_device import device_for as route
    return route(job, NVENC_GB)
