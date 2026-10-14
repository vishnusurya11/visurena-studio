"""One RTX VSR arm on one video, outside ComfyUI (one-off bench, 2026-10-14).

The running ComfyUI holds nvidia-vfx 0.1.0.1, which has only LOW..ULTRA. This runs
nvidia-vfx 0.2.0.0 (all 19 modes) from an extracted wheel in its own process.

    python -I vsr_arm.py <nvvfx_dir> <in.mp4> <out.mp4> <scale> <MODE> [PRE_MODE]

PRE_MODE (e.g. DEBLUR_ULTRA) runs first at 1x, then MODE at <scale>.
Frames stream one at a time: decode -> upload -> VSR -> download -> encode.
gpu_s counts only the effect calls (cuda-synced per frame); wall_s is the whole job.
The output is encoded like the assemble master: libx264 slow CRF 14 yuv420p.
"""
import json
import os
import re
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, sys.argv[1])
import nvvfx  # noqa: E402
import torch  # noqa: E402


def probe(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Video: .*?, (\d+)x(\d+)[, ].*?([\d.]+) fps", err)
    return int(m.group(1)), int(m.group(2)), m.group(3)


def effect(mode, ow, oh):
    eff = nvvfx.VideoSuperRes(quality=nvvfx.QualityLevel[mode], strength=1.0, device=0,
                              image_encoding=nvvfx.ImageEncoding.RGB8)
    eff.__enter__()
    eff.output_width, eff.output_height = ow, oh
    eff.load()
    return eff


def main():
    _, _, src, dst, scale, mode, *pre = sys.argv
    w, h, rate = probe(src)
    ow, oh = int(round(w * float(scale) / 8) * 8), int(round(h * float(scale) / 8) * 8)
    down = int(os.environ.get("VSR_DOWN", "0"))  # D-down: area-resize on the GPU before encode
    ew, eh = (down, down) if down else (ow, oh)
    t_all = time.perf_counter()
    effs = ([effect(pre[0], w, h)] if pre else []) + [effect(mode, ow, oh)]
    torch.cuda.synchronize()
    load_s = time.perf_counter() - t_all
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{ew}x{eh}", "-r", rate, "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p",
                            "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
    n, gpu_s, size = 0, 0.0, w * h * 3
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        f = torch.from_numpy(np.frombuffer(buf, np.uint8).reshape(h, w, 3)).cuda()
        f = f.permute(2, 0, 1).float().div(255).contiguous()
        torch.cuda.synchronize()
        t = time.perf_counter()
        for e in effs:
            f = torch.from_dlpack(e.run(f).image).clone()
        if down:
            f = torch.nn.functional.interpolate(f[None], size=(eh, ew), mode="area")[0]
        torch.cuda.synchronize()
        gpu_s += time.perf_counter() - t
        enc.stdin.write((f.clamp(0, 1) * 255).round().byte().permute(1, 2, 0).contiguous().cpu().numpy().tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    for e in effs:
        e.__exit__(None, None, None)
    print(json.dumps({"src": src, "mode": mode, "pre": pre[0] if pre else None, "scale": float(scale),
                      "frames": n, "out": f"{ew}x{eh}" + (f" (VSR {ow}x{oh})" if down else ""), "load_s": round(load_s, 3), "gpu_s": round(gpu_s, 3),
                      "fps": round(n / gpu_s, 1) if gpu_s else None,
                      "wall_s": round(time.perf_counter() - t_all, 2),
                      "vram_peak_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)}))


if __name__ == "__main__":
    main()
