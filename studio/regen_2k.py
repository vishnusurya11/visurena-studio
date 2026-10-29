"""The 4-step 2K pass: Open-H3-Regenerate-2K on every take of the judged cut.

OWNER 2026-10-29: "if it takes references and fixes faces and flickering ... we should eliminate our previous
face fix and upscale steps"; "4 step 2k"; after the side by sides, "Fluttering is definitely gone".

Each take is enlarged 2x on the CPU, injected into H3 (H3InjectVideoLatent) and re-drawn for 4 sa_solver steps
at denoise 0.35 with Kijai's refiner LoRA, conditioned on the take's OWN references (its cast sheets and its
panel): faces gain eyes, lids and structure from the sheets, and the boil settles (bench:
docs/audit/2026-10-29_open_h3_regenerate; ep05 T00's eyeless wide face came back readable).  The regen frames
replace that shot in the master, scaled once more to the master's 4x; av3 stays as the fallback for a shot the
pass did not draw.  The face refine is switched off while this is on (`on`, studio/face_refine.eligible): kept,
not deleted.

A take whose faces outnumber its reference sheets is NOT drawn: with nothing to hold them, faces come back as a
hatched mesh (ep04 T07, two constables the plan never named).  The pass spends what the episode's 6 h clock has
left, people first (`order`); what it cannot afford keeps av3, said in regen.json."""
from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from typing import Callable

SETTING = "VISURENA_REGEN_2K"
WORKFLOW = "video_minimax_h3_regen2k_lms_kijai_visurena"
SCALE = 2
SECONDS_PER_FRAME = 2.9
"""4-step warm, measured 2026-10-29 at 1536: T05 560 s / 192 f, T14 509 / 175, T19 454 / 158, T00 388 / 141
(the H3 reload the 15 GB text encoder forces on every job is inside these)."""
JOB_OVERHEAD_S = 20.0
"""The CPU enlargement, staging and the copy home, per job."""
RESERVE_S = 1200.0
"""What the episode keeps after the pass: the av3 master, the splice encode, the dossier, the audit, the publish."""
SEED = 82202
MIN_FACE_PX = 16
"""A face shorter than this at the take's 768 is not counted: too small to hatch, too small to matter."""
SHEET_PREFIX = "refs/characters/"


def on(env=None) -> bool:
    """The pass runs unless VISURENA_REGEN_2K=0 (then the face refine and av3 come back as they were)."""
    return (os.environ if env is None else env).get(SETTING, "1") != "0"


def canvas(width: int, height: int) -> tuple[int, int]:
    return width * SCALE, height * SCALE


def sheets(refs: list[str]) -> list[str]:
    """The take's references that hold a person (a sheet or a look), not its panel or a place."""
    return [r for r in refs if r.startswith(SHEET_PREFIX)]


def covered(faces: int, refs: list[str]) -> bool:
    """Every face the take shows has a sheet to be drawn from."""
    return faces <= len(sheets(refs))


def order(jobs: list[dict]) -> list[dict]:
    """The takes the eye flagged for a warping face first (the flutter the pass cures; Jekyll ep06's T23/T25/T27
    sat last in cut order and were cut for time), then takes with people, then the rest; cut order within each."""
    return sorted(jobs, key=lambda j: (0 if j.get("warp") else 1, 0 if j.get("people") else 1))


def warped(eye: dict | None) -> set[int]:
    """The takes the current take-eye verdict names a warp fault on."""
    return {int(str(f.get("where", ""))[1:]) for f in (eye or {}).get("faults", [])
            if f.get("kind") == "warp" and str(f.get("where", "")).startswith("T")}


def projected_s(frames: int) -> float:
    return frames * SECONDS_PER_FRAME + JOB_OVERHEAD_S


FLOOR_S = 3600.0
"""The pass always gets this much, people first: the 6 h is a target, not a stop (owner 2026-10-26), and an
episode that spent its clock on repairs still ships its faces drawn (Jekyll ep06: 5.2 h spent before step 11)."""


def left_s(spent: float, limit: float, reserve: float = RESERVE_S) -> float:
    """Seconds the pass may spend: the episode's limit less what it spent and what must follow, never
    under FLOOR_S."""
    return max(FLOOR_S, limit - spent - reserve)


def current(entry: dict | None, take_sha8: str) -> bool:
    """A regen counts only for the take bytes it was drawn from."""
    return bool(entry) and entry.get("take_sha8") == take_sha8


def graph(template: dict, inject: dict, card: dict, video: str, refs: list[str], size: tuple[int, int],
          prefix: str) -> dict:
    """The filled graph: the enlarged take, its prompt and length, and one LoadImage per reference wired to
    ref_images.ref_image_k -- never an empty slot (an empty LoadImage feeds example.png to the encoder)."""
    from studio.comfy import apply_inject
    g = apply_inject(copy.deepcopy(template), inject,
                     {"video": video, "prompt": card["prompt"], "width": size[0], "height": size[1],
                      "frames": int(card["frames"]), "filename_prefix": prefix, "seed": SEED + int(card["index"])})
    r2v = inject["prompt"]["node"]
    for k, name in enumerate(refs):
        g[f"ref{k}"] = {"class_type": "LoadImage", "inputs": {"image": name}}
        g[r2v]["inputs"][f"ref_images.ref_image_{k}"] = [f"ref{k}", 0]
    return g


@dataclass(frozen=True)
class Segment:
    start: int               # the master frame the shot starts on
    frames: int              # its frames in the cut
    index: int               # the take
    head: float              # seconds trimmed from the take's head
    slow: float              # G-DEAD's stretch (1.0 = none)
    guard: tuple | None      # the gutter guard's crop at the take's scale (w, h, left, top)
    regen: str | None        # the regenerated take, or None (the picture's own frames)


def segments(rows: list[dict], seg_frames: dict[int, int], done: dict[int, str], guards: dict) -> list[Segment]:
    """The cut's shots in order (layout.json), each with the regen that replaces it; a still never has one."""
    from studio.face_paste import parse_guard
    out, at = [], 0
    for r in rows:
        i = int(r["index"])
        regen = None if r.get("still") else done.get(i)
        out.append(Segment(at, seg_frames[i], i, float(r.get("head") or 0.0), float(r.get("slow") or 1.0),
                           parse_guard(guards.get(i) or guards.get(str(i))), regen))
        at += seg_frames[i]
    return out


def segment_filter(slow: float, guard: tuple | None, size: tuple[int, int], fps: int) -> str:
    """The regen conformed the way assemble.segment built the cut's shot: the gutter crop (at the regen's
    scale), the slow-down, then fill and crop to the master's size at the cut's rate."""
    pre = []
    if guard:
        w, h, left, top = (v * SCALE for v in guard)
        pre.append(f"crop={w}:{h}:{left}:{top}")
    if slow > 1.0:
        pre.append(f"setpts={slow}*PTS")
    w, h = size
    return ",".join(pre + [f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={w}:{h}",
                           f"fps={fps}", "format=yuv420p"])


def pump(segs: list[Segment], total: int, read_picture: Callable[[], bytes],
         open_regen: Callable[[Segment], Callable[[], bytes]], write: Callable[[bytes], object],
         nbytes: int = 0) -> int:
    """Every master frame once, in order: a regenerated shot's frames from its regen, the rest (and the card
    and chip after the last shot) from the upscaled picture, whose frames under a regen are read and dropped
    so the two stay in step.  A regen frame shorter than `nbytes` (its reader ran dry) is replaced by the
    picture's.  Returns the frames written."""
    n, k = 0, 0
    for seg in segs:
        read_regen = open_regen(seg) if seg.regen else None
        for _ in range(seg.frames):
            frame = read_picture()
            got = read_regen() if read_regen else b""
            write(got if got and len(got) >= nbytes else frame)
            n, k = n + 1, k + 1
    while k < total:
        write(read_picture())
        n, k = n + 1, k + 1
    return n


def frame_bytes(size: tuple[int, int]) -> int:
    """One yuv420p frame: the splice moves frames untouched, so it never converts them."""
    return size[0] * size[1] * 3 // 2


def picture_argv(picture, size: tuple[int, int]) -> list[str]:
    return ["ffmpeg", "-v", "error", "-i", str(picture), "-map", "0:v", "-vf", f"scale={size[0]}:{size[1]}",
            "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"]


def regen_argv(seg: Segment, size: tuple[int, int], fps: int) -> list[str]:
    return ["ffmpeg", "-v", "error", "-ss", f"{seg.head:.6f}", "-i", str(seg.regen), "-map", "0:v",
            "-vf", segment_filter(seg.slow, seg.guard, size, fps), "-frames:v", str(seg.frames),
            "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"]


def encode_argv(out, size: tuple[int, int], fps: int, encoder: str) -> list[str]:
    from studio.master_upscale import ENCODE
    from studio.video_encoder import video_args
    return ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{size[0]}x{size[1]}",
            "-framerate", str(fps), "-i", "-", "-map", "0:v", *video_args(ENCODE, encoder), str(out)]


def splice(picture, out, segs: list[Segment], size: tuple[int, int], fps: int, encoder: str, total: int) -> int:
    """The upscaled picture with every regenerated shot's frames in its place, encoded once at the
    deliverable's settings; the sound is muxed on after (assemble.with_sound_of).  A regen that ends short
    gives its shot's remaining frames back to the picture."""
    import subprocess
    nbytes = frame_bytes(size)
    src = subprocess.Popen(picture_argv(picture, size), stdout=subprocess.PIPE)
    sink = subprocess.Popen(encode_argv(out, size, fps, encoder), stdin=subprocess.PIPE)
    opened = []

    def open_regen(seg: Segment):
        p = subprocess.Popen(regen_argv(seg, size, fps), stdout=subprocess.PIPE)
        opened.append(p)
        return lambda: p.stdout.read(nbytes)
    try:
        n = pump(segs, total, lambda: src.stdout.read(nbytes), open_regen, sink.stdin.write, nbytes)
    finally:
        sink.stdin.close()
        for p in [src, *opened]:
            p.kill()
    if sink.wait():
        raise RuntimeError(f"the splice encode failed (exit {sink.returncode})")
    return n
