#!/usr/bin/env python
"""Step 09_07 -- the wide-shot face refine (owner 2026-10-17; decision
architecture/decisions/2026-10-17-face-refine.md).

    uv run python scripts/episode/face_refine.py <codex_id> <n> [take ...] [--within=takes]

For each wide or full take (or one whose face is under 60 px) that passed take DQ:
every face is tracked, each track matched to the take's staged cast by identity
against the sheets and the plan's side, and each person's crop re-rendered through
H3 at denoise 0.45 with ONLY that person's sheet (studio/face_refine.WORKFLOW).  Each
refined crop is gated -- identity against the sheet, seam, flicker, face count -- and
the decision per take lands in takes/r2v/refine.json; a refused crop falls back to
the unrefined take.  Assemble pastes the kept crops into the master after the 4x
upscale (studio/face_paste.py).

Step 09 runs it inside its two lanes, right after a take passes its dq, and once
more after the ladder for any take still owed one.  Pipelined: a take's crops are
queued on ComfyUI the moment it is tracked, so the GPU renders while the CPU
tracks the next take and gates the last.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np  # noqa: E402

from studio import episode_clock, episode_home, face_gate, face_track, face_refine as fr  # noqa: E402
from studio.face_paste import sha8  # noqa: E402

TAKES = Path("takes") / "r2v"
DOC = "refine.json"
OUT = "refine"
GATE_SAMPLES = 6
SIDE = 768


# ---- what is owed --------------------------------------------------------------------

def room_of(book: Path, number: int) -> Path:
    return episode_home.home(book, number) / TAKES


def read(path: Path, default):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default


def canvas_height(home: Path) -> int:
    from studio import canvas
    return canvas.size(read(home / "plan.json", {}).get("aspect") or canvas.DEFAULT)[1]


def selection(book: Path, number: int) -> list[int]:
    """The takes the refine works on (studio/face_refine.selected), from the files."""
    home, room = episode_home.home(book, number), room_of(book, number)
    cards = read(room / "prompts.json", [])
    sizes = {int(s["index"]): s.get("size", "") for s in read(home / "plan.json", {}).get("shots", [])}
    dqs = {int(c["index"]): read(room / f"T{int(c['index']):02d}.dq.json", None) for c in cards}
    return fr.selected(cards, sizes, dqs, canvas_height(home))


def current(doc: dict, room: Path, index: int) -> bool:
    """A decision exists for exactly these take bytes (a cut is still owed)."""
    entry = doc.get(f"T{index:02d}") or {}
    return entry.get("status") not in (None, "cut") and entry.get("take_sha8") == sha8(room / f"T{index:02d}.mp4")


def pending(book: Path, number: int, among: list[int] | None = None) -> list[int]:
    """Selected takes with no decision on their current bytes."""
    room = room_of(book, number)
    doc = read(room / DOC, {})
    return [i for i in selection(book, number) if (among is None or i in among) and not current(doc, room, i)]


def write_entry(room: Path, index: int, entry: dict) -> None:
    doc = read(room / DOC, {})
    doc[f"T{index:02d}"] = entry
    episode_home.write_json(room / DOC, doc)


def record_cut(room: Path, indices: list[int], price: float, book: Path, number: int) -> None:
    """The clock cut the refine: said in refine.json, the takes still owed one."""
    for i in indices:
        write_entry(room, i, {"status": "cut", "take_sha8": sha8(room / f"T{i:02d}.mp4"), "people": [],
                              "why": f"the clock's reserve needs the time: {price:.0f} s priced, cut first",
                              "decided": stamp()})


def stamp() -> str:
    from datetime import datetime
    return datetime.now().isoformat(timespec="seconds")


# ---- tracking and matching -----------------------------------------------------------

def read_frames(path: Path) -> list[np.ndarray]:
    import cv2
    cap, out = cv2.VideoCapture(str(path)), []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        out.append(bgr[:, :, ::-1].copy())
    cap.release()
    return out


def tracks_of(frames: list[np.ndarray], loose) -> list[list]:
    """Every small face's track over the take (detected every EVERY frames), its
    missed stretches stitched; a face big enough to read is left alone."""
    dets = {t: [tuple(f["box"]) for f in loose(frames[t])] for t in range(0, len(frames), face_track.EVERY)}
    return face_track.small(face_track.keep(face_track.stitch(face_track.link(dets))), fr.SMALL_FACE_PX)


def head_of(rgb: np.ndarray, box) -> np.ndarray:
    x1, y1, x2, y2 = (int(round(v)) for v in face_track.head_box(box, rgb.shape[1], rgb.shape[0]))
    return rgb[y1:max(y2, y1 + 1), x1:max(x2, x1 + 1)]


def sheet_face(book: Path, sheet: str, detect, embed, loose=None):
    """(face vector, head crop) of the largest face on a sheet; (None, None) unread."""
    from PIL import Image
    from studio.measure import faces
    rgb = np.asarray(Image.open(Path(book) / sheet).convert("RGB"))
    found = detect(rgb) or (loose(rgb) if loose else [])     # a drawn child's face can need the loose one
    if not found:
        return None, None
    box = faces.largest(found)["box"]
    return embed(rgb, box), head_of(rgb, box)


def identity(track: list, frames, sheet, embed) -> float:
    """Mean of the facenet cosine and the head-and-hat colour match, over the
    track's three biggest detections."""
    from studio.measure import faces
    vec, head = sheet
    if vec is None:
        return 0.0
    big = sorted(track, key=lambda d: face_track.height(d[1]), reverse=True)[:3]
    cos = [faces.cosine(embed(frames[t], b), vec) for t, b in big]
    hist = [face_track.hist_similarity(head_of(frames[t], b), head) for t, b in big]
    return 0.5 * float(np.mean(cos)) + 0.5 * float(np.mean(hist))


def match(prompt: str, cast: list, tracks: list, frames, book: Path, detect, embed, loose=None) -> dict:
    """track number -> the staged Person it is (studio/face_refine.assign)."""
    width, priors = frames[0].shape[1], fr.positions(prompt)
    sheets = {p.who: sheet_face(book, p.sheet, detect, embed, loose) for p in cast}
    scores = {}
    for k, tr in enumerate(tracks):
        x = float(np.mean([face_track.centre(b)[0] for _, b in tr])) / width
        for p in cast:
            scores[(k, p.who)] = fr.match_score(identity(tr, frames, sheets[p.who], embed), x, priors.get(p.k))
    by = {p.who: p for p in cast}
    return {k: by[who] for k, who in fr.assign(scores, list(range(len(tracks))), list(by)).items()}


# ---- the crops and their renders ---------------------------------------------------------

def ffmpeg() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def write_video(frames: list[np.ndarray], path: Path, fps: int = 24) -> Path:
    h, w = frames[0].shape[:2]
    p = subprocess.Popen([ffmpeg(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                          "-r", str(fps), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "10", str(path)],
                         stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError(f"ffmpeg could not write {path}")
    return path


def crop_frames(frames, wins, start: int, n: int) -> list[np.ndarray]:
    """The track's windows over the crop span, each scaled to H3's 768."""
    import cv2
    return [cv2.resize(np.ascontiguousarray(frames[t][y:y + s, x:x + s]), (SIDE, SIDE), interpolation=cv2.INTER_LANCZOS4)
            for t, (x, y, s) in zip(range(start, start + n), wins[start:start + n])]


def silence(seconds: float, path: Path) -> Path:
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-t", f"{seconds:.3f}", str(path)], check=True)
    return path


def take_seed(room: Path, card: dict, index: int) -> int:
    """The seed the kept take rendered with (its graph), else its card's."""
    graph = read(room / f"T{index:02d}.graph.json", {})
    return int((graph.get("12") or {}).get("inputs", {}).get("noise_seed") or card.get("seed") or 0)


def graph_for(person, prompt: str, frames: int, seed: int, names: dict, prefix: str) -> dict:
    from studio import comfy
    template, inject = comfy.load_workflow(fr.WORKFLOW)
    values = {"prompt": fr.crop_prompt(person, fr.style_line(prompt), frames / 24), "frames": frames,
              "seed": seed, "denoise": fr.DENOISE, "sheet": names["sheet"], "crop_video": names["crop"],
              "guide_audio": names["audio"], "filename_prefix": prefix}
    return comfy.apply_inject(template, inject, values)


@dataclass
class Job:
    k: int
    person: object
    track: list
    windows: list
    start: int
    frames: int
    prompt_id: str = ""
    out: Path | None = None


@dataclass
class TakeWork:
    index: int
    sha: str
    frames: list
    jobs: list = field(default_factory=list)
    status: str = "refined"


def queue_take(book: Path, number: int, index: int, card: dict, engine, loose, detect, embed) -> TakeWork:
    """Track, match, write each person's crop, and queue its render (no waiting)."""
    room = room_of(book, number)
    take = room / f"T{index:02d}.mp4"
    work = TakeWork(index, sha8(take), read_frames(take))
    tracks = tracks_of(work.frames, loose)
    if not tracks:
        work.status = "no_faces"
        return work
    refs = [str(r) for r in card.get("refs", [])]
    matched = match(card["prompt"], fr.cast_of(card["prompt"], refs), tracks, work.frames, book, detect, embed, loose)
    if not matched:
        work.status = "no_cast"
    for k, person in sorted(matched.items()):
        work.jobs.append(queue_person(room, book, card, work, k, person, tracks[k], engine))
    return work


def queue_person(room: Path, book: Path, card: dict, work: TakeWork, k: int, person, track, engine) -> Job:
    h, w = work.frames[0].shape[:2]
    wins = face_track.windows(face_track.fill(track, len(work.frames)), w, h)
    start, n = face_track.crop_span(face_track.life(track), len(work.frames))
    out = room / OUT
    out.mkdir(parents=True, exist_ok=True)
    stem = f"T{work.index:02d}_p{k}"
    crop = write_video(crop_frames(work.frames, wins, start, n), out / f"{stem}_src.mp4")
    names = {"crop": engine.stage(crop), "sheet": engine.stage(Path(book) / person.sheet),
             "audio": engine.stage(silence(n / 24, out / f"{stem}_guide.wav"))}
    seed = take_seed(room, card, work.index) + person.k
    graph = graph_for(person, card["prompt"], n, seed, names, f"face_refine/{stem}_{work.sha}")
    job = Job(k, person, track, wins, start, n, engine.submit(graph))
    episode_home.write_json(out / f"{stem}.json", {"windows": [list(v) for v in wins],
                                                    "life": list(face_track.life(track)), "start": start,
                                                    "frames": n, "who": person.who})
    return job


# ---- collecting and gating ------------------------------------------------------------

def collect(room: Path, work: TakeWork, job: Job, engine) -> None:
    got = engine.wait(job.prompt_id)
    job.out = Path(shutil.copy(got[0], room / OUT / f"T{work.index:02d}_p{job.k}.mp4"))


def sampled(seq: list, n: int = GATE_SAMPLES) -> list:
    return [seq[int(i)] for i in np.linspace(0, len(seq) - 1, min(n, len(seq)))] if seq else []


def gate_job(book: Path, work: TakeWork, job: Job, detect, embed, loose=None) -> dict:
    """The person's measures, the decision and the row refine.json keeps."""
    import cv2
    life, side = face_track.life(job.track), job.windows[0][2]
    refined = read_frames(job.out)
    src_w = face_gate.windows_of(work.frames, job.windows, life)
    ref_w = face_gate.shrunk(refined, job.start, life, side)
    src768 = [cv2.resize(np.ascontiguousarray(f), (SIDE, SIDE), interpolation=cv2.INTER_LANCZOS4) for f in sampled(src_w)]
    ref768 = sampled([refined[t - job.start] for t in range(life[0], life[1] + 1) if 0 <= t - job.start < len(refined)])
    vec, _ = sheet_face(book, job.person.sheet, detect, embed, loose)
    m = face_gate.measure(src_w, ref_w, src768, ref768, vec, detect, embed)
    kept, why = fr.decide(m)
    stem = f"T{work.index:02d}_p{job.k}"
    return {"who": job.person.who, "crop": f"{OUT}/{stem}.mp4", "track": f"{OUT}/{stem}.json", "kept": kept,
            "why": why, "measures": m.__dict__, "frames": job.frames}


def decide_take(room: Path, book: Path, work: TakeWork, detect, embed, engine, seconds: float, loose=None) -> dict:
    people = []
    for job in work.jobs:
        collect(room, work, job, engine)
        people.append(gate_job(book, work, job, detect, embed, loose))
    status = work.status if not people else ("refined" if any(p["kept"] for p in people) else "unrefined")
    entry = {"status": status, "take_sha8": work.sha, "people": people, "decided": stamp(),
             "gpu_s_priced": round(fr.price(len(work.jobs), len(work.frames)), 1), "seconds": round(seconds, 1)}
    write_entry(room, work.index, entry)
    print(f"T{work.index:02d} {status}: " + ("; ".join(f"{p['who']} {'KEPT' if p['kept'] else 'fell back'} ({p['why']})"
                                                    for p in people) or "nothing to refine"), flush=True)
    return entry


# ---- the run -----------------------------------------------------------------------------

class Comfy:
    """The live engine: content-addressed staging, a queued POST, a wait."""

    def stage(self, path: Path) -> str:
        from studio import comfy
        return comfy.stage_image(path)

    def submit(self, graph: dict) -> str:
        from studio import comfy
        return comfy.submit(graph)

    def wait(self, prompt_id: str) -> list[Path]:
        from studio import comfy
        return comfy.wait(prompt_id)


def detectors():
    """(loose detector for tracking, facenet detect, facenet embed), CPU."""
    from studio.measure import faces
    detect, embed = faces.embedder()
    return face_track.loose_detector(), detect, embed


def refine(book: Path, number: int, indices: list[int] | None, *, engine=None, detect=None, loose=None,
           embed=None, within: str = "") -> dict:
    """Queue every owed take's crops as it is tracked, then gate each take in order."""
    if detect is None:
        loose, detect, embed = detectors()
    engine, room = engine or Comfy(), room_of(book, number)
    cards = {int(c["index"]): c for c in read(room / "prompts.json", [])}
    out = {}
    with episode_clock.timed(book, number, "face_refine", note=" ".join(map(str, indices or [])), within=within):
        queued = [(time.time(), queue_take(book, number, i, cards[i], engine, loose, detect, embed))
                  for i in pending(book, number, indices)]
        for began, work in queued:
            out[work.index] = decide_take(room, book, work, detect, embed, engine, time.time() - began, loose)
    return out


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    within = next((a.split("=", 1)[1] for a in argv if a.startswith("--within=")), "")
    book = episode_home.book_dir(args[0])
    indices = [int(a) for a in args[2:]] or None
    done = refine(book, int(args[1]), indices, within=within)
    print(f"face refine: {len(done)} take(s) decided -> {room_of(book, int(args[1])) / DOC}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
