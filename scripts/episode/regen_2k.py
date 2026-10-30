"""The 4-step 2K pass over the judged cut's takes (studio/regen_2k, owner 2026-10-29).

    uv run --no-sync python scripts/episode/regen_2k.py <book_id> --episode=N [--engine=r2v]

Every non-still take in cut/ layout order, people first, whose regen is not current: its faces counted
(MTCNN, five frames), refused when they outnumber its sheets; priced; enlarged 2x on the CPU, staged with
its own references, drawn on ComfyUI, landed at takes/r2v_2k/T<NN>.mp4 and recorded in regen.json with
the take bytes it answers.  Stops spending when the episode's 6 h clock (less RESERVE_S) or the regen_2k
cap row cannot hold the next job; what it skips keeps av3 in the master.  Resumable: a current regen is
never drawn twice.  The splice into the master is assemble --upscale's (studio/regen_2k.splice)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_home, regen_2k as rg  # noqa: E402
from studio import youtube_publish as yp  # noqa: E402

ROOM = "r2v_2k"
RECORD = "regen.json"


def room_of(book: Path, number: int, engine: str) -> Path:
    return episode_home.takes_dir(book, number, engine).parent / ROOM


def read_record(room: Path) -> dict:
    path = room / RECORD
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_record(room: Path, doc: dict) -> None:
    room.mkdir(parents=True, exist_ok=True)
    tmp = room / (RECORD + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    tmp.replace(room / RECORD)


def done(book: Path, number: int, engine: str) -> dict[int, str]:
    """take index -> its current regen's path: what the splice may use."""
    room, takes = room_of(book, number, engine), episode_home.takes_dir(book, number, engine)
    out = {}
    for key, entry in read_record(room).items():
        take, regen = takes / f"{key}.mp4", room / f"{key}.mp4"
        if entry.get("drawn") and take.exists() and regen.exists() and rg.current(entry, yp.sha8(take)):
            out[int(key[1:])] = str(regen)
    return out


def faces_in(take: Path, samples: int = 5) -> int:
    """The most faces MTCNN finds in one of `samples` frames of the take, each at least MIN_FACE_PX tall."""
    import numpy as np
    from studio.measure import faces as fz
    detect, _ = fz.embedder()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(take), "-vf", "scale=768:768", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, 768, 768, 3)
    picks = np.linspace(0, len(frames) - 1, samples).astype(int) if len(frames) else []
    return max((sum(1 for f in detect(frames[k]) if f["score"] >= 0.9 and f["box"][3] - f["box"][1] >= rg.MIN_FACE_PX)
                for k in picks), default=0)


def staged_take(take: Path, size: tuple[int, int], work: Path) -> str:
    """The take enlarged (lanczos) to the regen's canvas, staged into ComfyUI's input."""
    from studio.comfy import stage_image
    big = work / f"regen_in_{take.stem}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(take), "-vf", f"scale={size[0]}:{size[1]}:flags=lanczos",
                    "-an", "-c:v", "libx264", "-crf", "10", str(big)], check=True)
    return stage_image(big)


def staged_refs(book: Path, number: int, refs: list[str]) -> list[str]:
    from studio import episode_seq_board as sq
    from studio.comfy import stage_image
    boards = episode_home.boards_dir(book, number)
    return [stage_image(sq.picture_path(boards, book, name)) for name in refs]


def draw(book: Path, number: int, card: dict, take: Path, size: tuple[int, int], work: Path, dest: Path) -> int:
    """One take through the regen graph on ComfyUI, landed at `dest`; its frames."""
    from studio.comfy import load_workflow, outputs_of, submit, wait_record
    from scripts.episode.assemble import video_frames
    template, inject = load_workflow(rg.WORKFLOW)
    g = rg.graph(template, inject, card, staged_take(take, size, work), staged_refs(book, number, card["refs"]),
                 size, f"regen2k/{book.name[:14]}_ep{number:02d}_{take.stem}")
    made = [p for p in outputs_of(wait_record(submit(g), timeout=3600.0)) if p.suffix == ".mp4"]
    if not made:
        raise RuntimeError(f"{take.stem}: the regen graph wrote no video")
    tmp = dest.with_name(dest.stem + ".part.mp4")
    shutil.copy2(made[-1], tmp)
    tmp.replace(dest)
    return video_frames(dest)


def runaway(elapsed: float, wall: float) -> bool:
    """Past the regen_2k row's wall: the only stop (owner 2026-10-29: "Don't skip any shot" -- no take is cut for
    time; a 28-take episode is ~3 h at 2.9 s/frame, the wall 6 h)."""
    return elapsed > wall


def wall_s() -> float:
    from studio import step_caps
    try:
        return step_caps.wall_s("regen_2k")
    except Exception:            # no cap row: six hours
        return 6 * 3600.0


def face_boxes(take: Path) -> list[list[tuple]]:
    """Every frame's faces in the take at 768 (MTCNN, score >= 0.9, >= MIN_FACE_PX), as (x0, y0, x1, y1)."""
    import numpy as np
    from studio.measure import faces as fz
    detect, _ = fz.embedder()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(take), "-vf", "scale=768:768", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, 768, 768, 3)
    return [[tuple(f["box"]) for f in detect(fr) if f["score"] >= 0.9 and f["box"][3] - f["box"][1] >= rg.MIN_FACE_PX]
            for fr in frames]


def masked(take: Path, regen: Path, keep: int, size: tuple[int, int]) -> None:
    """The regen with every face but the `keep` largest put back from the take, frame by frame (rg.paste_back),
    rewritten in place: a take with more faces than sheets is drawn, never skipped (owner 2026-10-29)."""
    import numpy as np
    boxes = face_boxes(take)
    w, h = size

    def frames_of(video: Path, fw: int, fh: int):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"scale={fw}:{fh}", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(-1, fh, fw, 3)
    small, big = frames_of(take, 768, 768), frames_of(regen, w, h)
    tmp = regen.with_name(regen.stem + ".masked.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                            "-framerate", "24", "-i", "-", "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p",
                            str(tmp)], stdin=subprocess.PIPE)
    for k, frame in enumerate(big):
        out = rg.paste_back(frame, small[min(k, len(small) - 1)], boxes[min(k, len(boxes) - 1)] if boxes else [], keep)
        enc.stdin.write(np.ascontiguousarray(out).tobytes())
    enc.stdin.close()
    if enc.wait():
        raise RuntimeError(f"{take.stem}: the masked regen did not encode")
    tmp.replace(regen)


def owed(book: Path, number: int, engine: str) -> bool:
    """A take of the judged cut has no current regen (step 11 then draws it and splices again)."""
    takes, work = episode_home.takes_dir(book, number, engine), episode_home.work_dir(book, number, engine)
    if not (takes / "prompts.json").exists() or not (work / "layout.json").exists():
        return False
    cards = {c["index"]: c for c in json.loads((takes / "prompts.json").read_text(encoding="utf-8"))}
    rows = json.loads((work / "layout.json").read_text(encoding="utf-8"))
    return bool(jobs_of(cards, rows, takes, read_record(room_of(book, number, engine))))


def jobs_of(cards: dict[int, dict], rows: list[dict], takes: Path, record: dict, warp: set[int] = frozenset()) -> list[dict]:
    """The cut's non-still takes whose regen is not current, with their planned people and their warp flag."""
    out = []
    for r in rows:
        i = int(r["index"])
        take = takes / f"T{i:02d}.mp4"
        if r.get("still") or i not in cards or not take.exists():
            continue
        if rg.current(record.get(f"T{i:02d}"), yp.sha8(take)) and record[f"T{i:02d}"].get("drawn"):
            continue
        out.append({"index": i, "take": take, "people": len(rg.sheets(cards[i]["refs"])), "warp": i in warp})
    return out


def run(book: Path, number: int, engine: str) -> dict:
    from scripts.episode import assemble as asm
    asm.set_canvas(book, number)
    size = rg.canvas(asm.W, asm.H)
    home, takes = episode_home.home(book, number), episode_home.takes_dir(book, number, engine)
    work, room = episode_home.work_dir(book, number, engine), room_of(book, number, engine)
    room.mkdir(parents=True, exist_ok=True)
    cards = {c["index"]: c for c in json.loads((takes / "prompts.json").read_text(encoding="utf-8"))}
    rows = json.loads((work / "layout.json").read_text(encoding="utf-8"))
    record = read_record(room)
    began, wall = time.time(), wall_s()
    warp = rg.warped(asm.current_eye(takes))
    for job in rg.order(jobs_of(cards, rows, takes, record, warp)):
        i, take, card = job["index"], job["take"], cards[job["index"]]
        key, sha = f"T{i:02d}", yp.sha8(take)
        if runaway(time.time() - began, wall):
            print(f"CAP regen_2k {key}: the pass ran past its {wall / 60:.0f} min wall; av3 keeps the rest", flush=True)
            break
        faces, sheets = faces_in(take), len(rg.sheets(card["refs"]))
        t0 = time.time()
        frames = draw(book, number, card, take, size, work, room / f"{key}.mp4")
        if not rg.covered(faces, card["refs"]):          # more faces than sheets: the extras stay the take's
            masked(take, room / f"{key}.mp4", sheets, size)
        record[key] = {"take_sha8": sha, "drawn": True, "frames": frames, "faces": faces, "sheets": sheets,
                       "masked": not rg.covered(faces, card["refs"]), "seconds": round(time.time() - t0, 1),
                       "size": list(size)}
        print(f"REGEN 2K {key}: {frames} frames in {record[key]['seconds']:.0f} s"
              + (f" ({faces - sheets} unreferenced face(s) pasted back)" if record[key]["masked"] else ""), flush=True)
        write_record(room, record)
    return record


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run(episode_home.book_dir(args[0]), episode_home.episode_arg(sys.argv), episode_home.engine_arg(sys.argv))
