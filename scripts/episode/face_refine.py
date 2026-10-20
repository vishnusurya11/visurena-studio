#!/usr/bin/env python
"""Step 09_07 -- the face refine (owner 2026-10-17; decision
architecture/decisions/2026-10-17-face-refine.md; every soft face, 2026-10-19).

    uv run python scripts/episode/face_refine.py <codex_id> <n> [take ...] [--within=takes]

For each take with a planned face that its dq lets ship (studio/face_refine.selected):
every face is tracked (face_yolov8m.pt in a worker, MTCNN behind it; studio/face_detect.py;
weak faces only continue a track, a far figure the face model misses comes from its body,
a lost face re-acquires only its own head), each track whose smallest face is under 120 px
matched to the take's staged cast by identity against the sheets and the plan's side, and
each person's crop -- its soft span with hysteresis, on H3's grid inside its shot, one frozen
side -- re-rendered through H3 with ONLY that person's sheet at a denoise that follows the
face's size (studio/face_refine.WORKFLOW, denoise_for).  Each refined crop is gated --
identity against the sheet (facenet, and CCIP + clip_vision_h in a worker,
studio/anime_id.py), seam, flicker, drift, face count; drawn eyes logged -- and the decision per take lands in
takes/r2v/refine.json (`refined`, `unrefined`, `none_found`, `all_readable`, `no_cast`,
`cut`); a refused crop falls back to the unrefined take.  Assemble pastes the kept crops
at cut scale, then the one upscale (studio/face_paste.py).

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
from dataclasses import dataclass, field, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np  # noqa: E402

from studio import episode_clock, episode_home, face_detect, face_gate, face_paste, face_track, face_refine as fr  # noqa: E402
from studio import step_attempts, step_caps  # noqa: E402
from studio.face_paste import sha8  # noqa: E402

TAKES = Path("takes") / "r2v"
DOC = "refine.json"
OUT = "refine"
GATE_SAMPLES = 6
ID_SAMPLES = 4
"""Crops per side the anime identity terms read (round 1's calibration: 4 + 4 and the sheet;
1.2 s of GPU or 7.5 s of CPU a face)."""
SIDE = 768
TURN_SAMPLES = 12
"""Crop pairs the turn is read on (studio/face_gate.face_turn): at 6, ep01 T09's median swung 3.9 -> 9.8 deg."""
REACQUIRE_FLOOR = 0.4
"""A lost face is re-acquired only by a head whose Lab colour (hist_similarity) reads at least as
much like the track's LATEST head as like any other person's present then, and over this floor.
ep01 round 1's eleven re-acquires: the same person 0.48-1.00 against the latest head, another
person present 0.46-0.89 -- no single line splits them (T07's child 0.48, T01's Utterson 0.68), and
against the track's FIRST head they overlapped wider (same p5 0.70, other p90 0.80)."""
SELF_SLACK = 0.15
SELF_PAIRS = 5
"""A head must read at least the track's own running reading (the median of its SELF_PAIRS consecutive
head pairs nearest the moment) less 0.15: at every sample, and for a lost face with nobody else about.
ep01's bench (9 takes): 520 same-person consecutive pairs read at worst 0.098 under their track's
reading, nine of ten same-person re-acquires within 0.04; other people against a track's latest head
p50 0.33 and p90 0.15 under it, so 36 of 416 other-person pairs pass (fix round, 2026-10-19: a lost
36 px track took a 30 px newcomer on the 0.4 floor alone, asked with no rival)."""
RIVAL_GAP = face_track.EVERY
"""Another track is a rival at frame t when it holds a face within one sample of t: someone present
then.  Wider (12), the child's own later piece on ep01 T07 out-read her and she lost her track."""


# ---- what is owed --------------------------------------------------------------------

def room_of(book: Path, number: int) -> Path:
    return episode_home.home(book, number) / TAKES


def read(path: Path, default):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default


def selection(book: Path, number: int) -> list[int]:
    """The takes the refine works on (studio/face_refine.selected), from the files."""
    home, room = episode_home.home(book, number), room_of(book, number)
    cards = read(room / "prompts.json", [])
    sizes = {int(s["index"]): s.get("size", "") for s in read(home / "plan.json", {}).get("shots", [])}
    dqs = {int(c["index"]): read(room / f"T{int(c['index']):02d}.dq.json", None) for c in cards}
    taken = {int(c["index"]): taken_of(home, room, int(c["index"])) for c in cards}
    return fr.selected(cards, sizes, dqs, taken)


def taken_of(home: Path, room: Path, index: int) -> int:
    """The take's retakes so far; the episode's retake wall spent counts every take as retaken
    (warp_gate.RETAKES), so a take is never stranded between seed and refine."""
    from studio import take_ladder, warp_gate
    return warp_gate.RETAKES if take_ladder.episode_spent(home) else take_ladder.attempts_of(room, index)


STALE = ("no_faces",)
"""A decision under the 60 px wall (before 2026-10-19): `no_faces` meant no face UNDER 60 px, and
its round was spent with no job (fixed by P07, 41fba62).  Jekyll ep01 T05 T06 T13 T21 T23 T24."""


def current(doc: dict, room: Path, index: int) -> bool:
    """A decision exists for exactly these take bytes (a cut or a stale row is still owed)."""
    entry = doc.get(f"T{index:02d}") or {}
    return entry.get("status") not in (None, "cut", *STALE) and entry.get("take_sha8") == sha8(room / f"T{index:02d}.mp4")


def pending(book: Path, number: int, among: list[int] | None = None) -> list[int]:
    """Selected takes with no decision on their current bytes and refines left (the cap table)."""
    room, home = room_of(book, number), episode_home.home(book, number)
    doc = read(room / DOC, {})
    return [i for i in selection(book, number) if (among is None or i in among) and not current(doc, room, i)
            and not refined_out(home, i, refund_of(doc.get(f"T{i:02d}")))]


def refine_key(index: int) -> str:
    return f"face_refine.T{index:02d}"


def refund_of(entry: dict | None) -> int:
    """1 for a STALE row's jobless round, kept by a clock cut that replaced it (`refund`)."""
    entry = entry or {}
    return 1 if entry.get("status") in STALE or entry.get("refund") else 0


def refined_out(home: Path, index: int, refund: int = 0) -> bool:
    """The take has had its refines (owner 2026-10-18: 1 per take, persisted in attempts.json);
    a STALE row's jobless round is refunded until the first decision that is not a cut replaces it,
    and the tiny-face rung's one draw (scripts/episode/tiny_face.py) buys its new bytes one more."""
    granted = step_attempts.count(home, f"tiny_face.T{index:02d}")
    return step_attempts.count(home, refine_key(index)) - refund - granted >= step_caps.rounds("face_refine")


def count_refine(home: Path, index: int) -> None:
    step_attempts.spend(home, refine_key(index))


def count_if_worked(home: Path, work) -> None:
    """A refine round is spent only when a job was queued: none_found, all_readable and no_cast cost none."""
    if work.jobs:
        count_refine(home, work.index)


def wall_spent(began: float, now: float) -> bool:
    """The refine's wall (the cap table's 15 min): no take is queued past it."""
    return now - began >= step_caps.wall_s("face_refine")


def owed(book: Path, number: int, among: list[int] | None = None) -> dict[int, float]:
    """take -> the GPU seconds its refine is priced at, for every pending take
    (one face per planned face the warp gate did not track readable, over the take's frames)."""
    room = room_of(book, number)
    cards = {int(c["index"]): c for c in read(room / "prompts.json", [])}
    return {i: fr.price(fr.soft_faces(cards[i], read(room / f"T{i:02d}.dq.json", None)),
                        int(cards[i].get("frames") or fr.REF_FRAMES)) for i in pending(book, number, among)}


def write_entry(room: Path, index: int, entry: dict) -> None:
    doc = read(room / DOC, {})
    doc[f"T{index:02d}"] = entry
    episode_home.write_json(room / DOC, doc)


def record_cut(room: Path, indices: list[int], price: float, book: Path, number: int, why: str = "") -> None:
    """The clock (or the refine's wall) cut the refine: said in refine.json, the takes still owed one."""
    why = why or f"the clock's reserve needs the time: {price:.0f} s priced, cut first"
    doc = read(room / DOC, {})
    for i in indices:
        refund = {"refund": 1} if refund_of(doc.get(f"T{i:02d}")) else {}
        write_entry(room, i, {"status": "cut", "take_sha8": sha8(room / f"T{i:02d}.mp4"), "people": [],
                              "why": why, "decided": stamp(), **refund})


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


class Same:
    """same(track, box, t, others): the head at `box` on frame `t` is the lost track's own (Lab colour of
    the head and hat): it reads at least as much like the track's latest head as like any rival's (another
    track with a face near `t`) and over the floor -- or, with no rival present, at least as much as the
    track's heads read like each other less SELF_SLACK (`bar`).  `continues` is that bar for a face found
    within a sample; `like` is the likeness the tracker's assignment costs by."""

    def __init__(self, frames: list[np.ndarray]):
        self.frames, self.hists = frames, {}

    def hist(self, t: int, b) -> np.ndarray:
        """The head's Lab histogram at box `b` on frame `t`, read once."""
        key = (t, tuple(b))
        if key not in self.hists:
            self.hists[key] = face_track.lab_hist(head_of(self.frames[t], b))
        return self.hists[key]

    def like(self, track: list, b, t: int) -> float:
        """How much the head at `b` on frame `t` reads like the track's head nearest `t`."""
        t0, b0 = min(track, key=lambda d: abs(d[0] - t))
        return face_track.hist_correlation(self.hist(t, b), self.hist(t0, b0))

    def likeness(self, track: list, head: np.ndarray, t: int) -> float:
        """like, for a head crop already cut."""
        t0, b0 = min(track, key=lambda d: abs(d[0] - t))
        return face_track.hist_correlation(face_track.lab_hist(head), self.hist(t0, b0))

    def self_likeness(self, track: list, t: int) -> float | None:
        """The median likeness of the track's own consecutive heads nearest `t` (SELF_PAIRS of them);
        None for a track with none (ep01 T07's child, 40 px a sample across a changing street, is
        two single detections and a weak one before she has a pair)."""
        pairs = [(u, v) for u, v in zip(track, track[1:]) if v[0] - u[0] <= face_track.EVERY]
        pairs = sorted(pairs, key=lambda p: abs(p[1][0] - t))[:SELF_PAIRS]
        if not pairs:
            return None
        return float(np.median([face_track.hist_correlation(self.hist(*u), self.hist(*v)) for u, v in pairs]))

    def bar(self, track: list, t: int) -> float:
        """The least a head must read like the track's: its own reading less SELF_SLACK, never under
        the floor; the floor alone for a track with no reading of its own."""
        own = self.self_likeness(track, t)
        return REACQUIRE_FLOOR if own is None else max(REACQUIRE_FLOOR, own - SELF_SLACK)

    def continues(self, track: list, b, t: int) -> bool:
        """The head reads at least the track's bar."""
        return self.like(track, b, t) >= self.bar(track, t)

    def __call__(self, track: list, b, t: int, others=()) -> bool:
        own = self.like(track, b, t)
        rivals = [self.like(o, b, t) for o in others if min(abs(u - t) for u, _ in o) <= RIVAL_GAP]
        if not rivals:
            return own >= self.bar(track, t)
        return own >= REACQUIRE_FLOOR and own >= max(rivals)


def take_tracks(frames: list[np.ndarray], dets: dict, cuts: list[int], same=None) -> tuple[list[list], list[str]]:
    """(tracks, their sources): strong faces linked, weak faces continuing them, missed stretches
    stitched, cut at the hard cuts; then far figures from bodies alone.  A body never lengthens a
    face track (ep01 T01: a body-estimated face moved Utterson's track onto Enfield; weak faces
    alone gave T06's Hyde his frames 0-17)."""
    h, w = frames[0].shape[:2]
    strong, weak = face_track.by_strength(dets, face_detect.CONF)
    bodies = face_track.body_faces(face_track.persons_of(dets), w, h)
    faces = face_track.rescue(face_track.link(strong, same=same), weak, same=same)
    faces = face_track.keep(face_track.split(face_track.stitch(faces, same), cuts))
    far = face_track.keep(face_track.split(face_track.body_only(bodies, faces), cuts))
    return faces + far, ["face"] * len(faces) + ["body"] * len(far)


def tracks_of(frames: list[np.ndarray], dets: dict) -> list[list]:
    """Every face's track over the take (take_tracks at the take's own hard cuts)."""
    return take_tracks(frames, dets, cut_frames(frames), Same(frames))[0]


def cut_frames(frames: list[np.ndarray]) -> list[int]:
    """The first frame of every new shot inside the take (PySceneDetect's adaptive detector,
    studio/measure/cuts.py, the cut handling ComfyUI-H3-FaceRefine uses)."""
    from studio.measure.cuts import scene_cuts
    return [c for c in scene_cuts(frames) if 0 < c < len(frames)]


def soft_tracks(work, tracks: list[list], sources: list[str] | None = None) -> tuple[list[list], list[str]]:
    """The tracks the refine works on (smallest face under SMALL_FACE_PX) and their sources; when
    there are none the take's status says why: no face found, or every face already reads."""
    sources = sources or ["face"] * len(tracks)
    keep = [k for k, tr in enumerate(tracks) if face_track.track_px(tr) < fr.SMALL_FACE_PX]
    if not keep:
        work.status = "all_readable" if tracks else "none_found"
    return [tracks[k] for k in keep], [sources[k] for k in keep]


def head_of(rgb: np.ndarray, box) -> np.ndarray:
    x1, y1, x2, y2 = (int(round(v)) for v in face_track.head_box(box, rgb.shape[1], rgb.shape[0]))
    return rgb[y1:max(y2, y1 + 1), x1:max(x2, x1 + 1)]


def band_face(rgb: np.ndarray):
    """The face box inside the figure's head band (studio/judges/sheet_row.head_box):
    a drawn sheet no detector reads (Kawajiri Hyde, 2026-10-18) still has its head
    at the top of the figure.  None when the sheet holds no figure."""
    from studio.judges.sheet_row import head_box
    band = head_box(rgb)
    if band is None:
        return None
    x1, y1, x2, y2 = band
    side = min(x2 - x1, y2 - y1)
    cx = (x1 + x2) / 2
    return cx - side / 2, y2 - side, cx + side / 2, y2


def sheet_box(book: Path, sheet: str, detect, loose=None):
    """(the sheet's pixels, its largest face box) -- facenet, else the loose detector, else the
    head band's face; the box is None when the sheet holds no figure."""
    from PIL import Image
    from studio.measure import faces
    rgb = np.asarray(Image.open(Path(book) / sheet).convert("RGB"))
    found = detect(rgb) or (loose(rgb) if loose else [])     # a drawn child's face can need the loose one
    return rgb, (faces.largest(found)["box"] if found else band_face(rgb))


def sheet_face(book: Path, sheet: str, detect, embed, loose=None):
    """(face vector, head crop) of the largest face on a sheet; (None, None) unread."""
    rgb, box = sheet_box(book, sheet, detect, loose)
    if box is None:
        return None, None
    return embed(rgb, box), head_of(rgb, box)


def sheet_window(rgb: np.ndarray, box) -> np.ndarray:
    """The sheet cut the way a take's window is cut round its face (face_track.windows): what the
    anime identity terms compare the crops with."""
    side = int(min(face_track.height(box) * face_track.MARGIN, rgb.shape[0], rgb.shape[1]))
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 - 0.05 * side
    x = int(np.clip(cx - side / 2, 0, rgb.shape[1] - side))
    y = int(np.clip(cy - side / 2, 0, rgb.shape[0] - side))
    return rgb[y:y + side, x:x + side]


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


def graph_for(person, prompt: str, frames: int, seed: int, names: dict, prefix: str,
              denoise: float = fr.DENOISE) -> dict:
    """F2's graph filled through its manifest; the workflow JSON itself is never edited."""
    from studio import comfy
    template, inject = comfy.load_workflow(fr.WORKFLOW)
    values = {"prompt": fr.crop_prompt(person, fr.style_line(prompt), frames / 24), "frames": frames,
              "seed": seed, "denoise": denoise, "sheet": names["sheet"], "crop_video": names["crop"],
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
    save: str = ""
    """The graph's SaveVideo node: the only output that is the render."""
    denoise: float = fr.DENOISE
    face_px: float = 0.0
    life: tuple | None = None
    """The frames the crop is pasted over (the soft span inside the crop); None = the track's life."""
    soft: bool = False
    source: str = "face"
    lost: int = 0


@dataclass
class TakeWork:
    index: int
    sha: str
    frames: list
    jobs: list = field(default_factory=list)
    status: str = "refined"
    cuts: list = field(default_factory=list)


@dataclass(frozen=True)
class Run:
    """One soft face's crop: its frames, the life it is pasted over, its frozen windows."""
    start: int
    frames: int
    life: tuple
    side: int
    windows: list
    face_px: float
    soft: bool
    faces: list = field(default_factory=list)


def faces_in(boxes: np.ndarray, windows: list) -> list[list[float]]:
    """Each frame's face (x, y, height) as shares of its window: where the paste centres the face core."""
    return [[round(((b[0] + b[2]) / 2 - x) / s, 4), round(((b[1] + b[3]) / 2 - y) / s, 4), round((b[3] - b[1]) / s, 4)]
            for b, (x, y, s) in zip(boxes, windows)]


def run_of(track: list, frames: int, width: int, height_: int, cuts: list[int]) -> Run:
    """The face's soft span (hysteresis), on H3's grid inside its shot, one side for the run."""
    span = face_track.soft_span(track, frames, fr.SMALL_FACE_PX) or face_track.life(track)
    start, n = face_track.crop_span(span, frames, cuts)
    life = (max(span[0], start), min(span[1], start + n - 1))
    boxes = face_track.fill(track, frames)
    side = face_track.frozen_side(boxes, life, width, height_)
    px = round(float(np.median(boxes[life[0]:life[1] + 1, 3] - boxes[life[0]:life[1] + 1, 1])), 1)
    wins = face_track.windows(boxes, width, height_, side)
    return Run(start, n, life, side, wins, px, face_paste.soft(px), faces_in(boxes, wins))


def queue_take(book: Path, number: int, index: int, card: dict, engine, loose, detect, embed, find) -> TakeWork:
    """Track, match, write each soft face's crop, and queue its render (no waiting)."""
    room = room_of(book, number)
    take = room / f"T{index:02d}.mp4"
    work = TakeWork(index, sha8(take), read_frames(take))
    work.cuts = cut_frames(work.frames)
    tracks, sources = soft_tracks(work, *take_tracks(work.frames, find(take, work.frames), work.cuts, Same(work.frames)))
    if not tracks:
        return work
    refs = [str(r) for r in card.get("refs", [])]
    matched = match(card["prompt"], fr.cast_of(card["prompt"], refs), tracks, work.frames, book, detect, embed, loose)
    if not matched:
        work.status = "no_cast"
    for k, person in sorted(matched.items()):
        work.jobs.append(queue_person(room, book, card, work, k, person, tracks[k], engine, sources[k]))
    return work


def queue_person(room: Path, book: Path, card: dict, work: TakeWork, k: int, person, track, engine,
                 source: str = "face") -> Job:
    h, w = work.frames[0].shape[:2]
    run = run_of(track, len(work.frames), w, h, work.cuts)
    out = room / OUT
    out.mkdir(parents=True, exist_ok=True)
    stem = f"T{work.index:02d}_p{k}"
    crop = write_video(crop_frames(work.frames, run.windows, run.start, run.frames), out / f"{stem}_src.mp4")
    names = {"crop": engine.stage(crop), "sheet": engine.stage(Path(book) / person.sheet),
             "audio": engine.stage(silence(run.frames / 24, out / f"{stem}_guide.wav"))}
    graph = graph_for(person, card["prompt"], run.frames, take_seed(room, card, work.index) + person.k, names,
                      f"face_refine/{stem}_{work.sha}", fr.denoise_for(run.face_px))
    job = Job(k, person, track, run.windows, run.start, run.frames, engine.submit(graph), save=fr.saved_node(graph),
              denoise=fr.denoise_for(run.face_px), face_px=run.face_px, life=run.life, soft=run.soft, source=source,
              lost=face_track.lost(track))
    episode_home.write_json(out / f"{stem}.json", track_doc(job, run))
    return job


def track_doc(job: Job, run: Run) -> dict:
    """The track file assemble pastes from (studio/face_paste.kept_tracks)."""
    return {"windows": [list(v) for v in run.windows], "life": list(run.life), "start": run.start,
            "frames": run.frames, "who": job.person.who, "denoise": job.denoise, "face_px": run.face_px,
            "side": run.side, "soft": run.soft, "source": job.source, "lost": job.lost, "faces": run.faces}


# ---- collecting and gating ------------------------------------------------------------

def collect(room: Path, work: TakeWork, job: Job, engine) -> None:
    """Copy the SaveVideo node's render.  Never the first output: on v0.41.2 the
    LoadVideo echoes its input crop first, and every refine since daa4aa9 filed
    the unrefined source as refined (Kawajiri POC, 2026-10-18)."""
    saved = engine.wait(job.prompt_id).get(job.save) or []
    if not saved:
        raise RuntimeError(f"T{work.index:02d} p{job.k}: no output from save node {job.save!r}")
    job.out = Path(shutil.copy(saved[0], room / OUT / f"T{work.index:02d}_p{job.k}.mp4"))


def sampled(seq: list, n: int = GATE_SAMPLES) -> list:
    return [seq[int(i)] for i in np.linspace(0, len(seq) - 1, min(n, len(seq)))] if seq else []


def to768(crops: list[np.ndarray]) -> list[np.ndarray]:
    import cv2
    return [cv2.resize(np.ascontiguousarray(f), (SIDE, SIDE), interpolation=cv2.INTER_LANCZOS4) for f in crops]


def over_life(refined: list[np.ndarray], start: int, life: tuple[int, int]) -> list[np.ndarray]:
    """The refined crop's frames (768) over the track's life."""
    return [refined[t - start] for t in range(life[0], life[1] + 1) if 0 <= t - start < len(refined)]


def turn_of(src_w: list, ref768: list, detect) -> float | None:
    """How far the redraw turned the face (degrees, rounded), over TURN_SAMPLES crop pairs at 768."""
    turn = face_gate.face_turn(to768(sampled(src_w, TURN_SAMPLES)), to768(sampled(ref768, TURN_SAMPLES)), detect)
    return None if turn is None else round(turn, 2)


def anime_terms(anime, book: Path, job: Job, src_w: list, ref768: list, detect, loose=None) -> dict:
    """CCIP and clip_vision_h of the sheet's face window against ID_SAMPLES take and refined crops;
    every term None when no reader runs or the sheet holds no figure."""
    unread = dict.fromkeys(("ccip_src", "ccip_ref", "clip_src", "clip_ref"))
    if anime is None:
        return unread
    rgb, box = sheet_box(book, job.person.sheet, detect, loose)
    said = anime(sheet_window(rgb, box) if box is not None else None, to768(sampled(src_w, ID_SAMPLES)),
                 sampled(ref768, ID_SAMPLES))
    return said or unread


def gate_job(book: Path, work: TakeWork, job: Job, detect, embed, loose=None, anime=None) -> dict:
    """The person's measures, the decision and the row refine.json keeps."""
    life, side = job.life or face_track.life(job.track), face_track.side_of(job.windows)
    refined = read_frames(job.out)
    src_w = face_gate.at_side(face_gate.windows_of(work.frames, job.windows, life), side)
    ref_w = face_gate.shrunk(refined, job.start, life, side)
    ref768 = over_life(refined, job.start, life)
    vec, _ = sheet_face(book, job.person.sheet, detect, embed, loose)
    stem = f"T{work.index:02d}_p{job.k}"
    moved = face_gate.change(sampled(read_frames(job.out.with_name(f"{stem}_src.mp4"))), sampled(refined))
    boxes = face_gate.face_boxes(face_track.fill(job.track, len(work.frames)), job.windows, life, side)
    m = face_gate.measure(src_w, ref_w, to768(sampled(src_w)), sampled(ref768), vec, detect, embed, moved,
                          job.face_px / side, job.soft, face_gate.centres_of(boxes))
    m = replace(m, **face_gate.extras(src_w, ref_w, boxes), **anime_terms(anime, book, job, src_w, ref768, detect, loose),
                turn=turn_of(src_w, ref768, detect))
    kept, why = fr.decide(m)
    return {"who": job.person.who, "crop": f"{OUT}/{stem}.mp4", "track": f"{OUT}/{stem}.json", "kept": kept,
            "why": why, "measures": m.__dict__, "frames": job.frames, "denoise": job.denoise, "face_px": job.face_px,
            "min_px": round(face_track.track_px(job.track), 1), "soft": job.soft, "source": job.source, "lost": job.lost}


def decide_take(room: Path, book: Path, work: TakeWork, detect, embed, engine, seconds: float, loose=None,
                anime=None) -> dict:
    people = []
    for job in work.jobs:
        collect(room, work, job, engine)
        people.append(gate_job(book, work, job, detect, embed, loose, anime))
    status = work.status if not people else ("refined" if any(p["kept"] for p in people) else "unrefined")
    entry = {"status": status, "take_sha8": work.sha, "people": people, "decided": stamp(),
             "gpu_s_priced": round(fr.price(len(work.jobs), len(work.frames)), 1), "seconds": round(seconds, 1)}
    write_entry(room, work.index, entry)
    print(f"T{work.index:02d} {status}: " + ("; ".join(f"{p['who']} {'KEPT' if p['kept'] else 'fell back'} ({p['why']})"
                                                    for p in people) or "nothing to refine"), flush=True)
    return entry


# ---- the regate: a decision made before the paste's walls ------------------------------------

def regate_due(entry: dict) -> bool:
    """A row measured before the band and turn walls (its measures hold no band_warp)."""
    return any(stale_row(p) for p in entry.get("people", []))


def stale_row(row: dict) -> bool:
    return "measures" in row and "band_warp" not in row["measures"]


def centres_from(doc: dict, life: tuple[int, int], side: int) -> list | None:
    """The face's (cx, cy) per frame of the life, in window pixels, from the run's record; None without it."""
    faces = doc.get("faces")
    if not faces:
        return None
    rows = [faces[t] if t < len(faces) else None for t in range(life[0], life[1] + 1)]
    return [(f[0] * side, f[1] * side) if f else (side / 2, face_paste.FACE_Y * side) for f in rows]


def regate_row(room: Path, take: list[np.ndarray], row: dict, read, detect) -> dict:
    """The row re-decided on its stored measures, the paste's measures and the turn taken again (CPU)."""
    doc = json.loads((Path(room) / row["track"]).read_text(encoding="utf-8"))
    life = (int(doc["life"][0]), min(int(doc["life"][1]), len(take) - 1))
    side = face_track.side_of(doc["windows"])
    refined = read(Path(room) / row["crop"])
    src_w = face_gate.at_side(face_gate.windows_of(take, doc["windows"], life), side)
    ref_w = face_gate.shrunk(refined, int(doc["start"]), life, side)
    if not src_w or not ref_w:
        return row
    known = {k: v for k, v in row["measures"].items() if k in fr.Measures.__dataclass_fields__}
    m = replace(fr.Measures(**known), turn=turn_of(src_w, over_life(refined, int(doc["start"]), life), detect),
                **face_gate.paste_measures(src_w, ref_w, face_paste.face_share(doc, row), centres_from(doc, life, side)))
    kept, why = fr.decide(m)
    return {**row, "kept": kept, "why": why, "measures": m.__dict__, "regated": stamp()}


def regate_entry(room: Path, index: int, entry: dict, read=read_frames, detect=None) -> dict:
    """The take's entry with every stale row regated; its status follows what is kept."""
    if not regate_due(entry):
        return entry
    if detect is None:
        from studio.measure import faces
        detect, _ = faces.embedder("cpu")
    take = read(Path(room) / f"T{index:02d}.mp4")
    people = [regate_row(room, take, p, read, detect) if stale_row(p) else p for p in entry["people"]]
    status = entry.get("status")
    if status in ("refined", "unrefined"):
        status = "refined" if any(p.get("kept") for p in people) else "unrefined"
    return {**entry, "people": people, "status": status}


def regate_room(room: Path) -> list[str]:
    """Every current take's stale rows regated in refine.json before a cut pastes them (assemble)."""
    changed = []
    for key, entry in sorted(read(Path(room) / DOC, {}).items()):
        if not (key[:1] == "T" and key[1:].isdigit()):
            continue
        index = int(key[1:])
        if regate_due(entry) and current({key: entry}, Path(room), index):
            new = regate_entry(Path(room), index, entry)
            write_entry(Path(room), index, new)
            changed.append(key)
            print(f"{key} regated: " + "; ".join(f"{p.get('who')} {'KEPT' if p.get('kept') else 'fell back'} "
                                                 f"({p.get('why')})" for p in new["people"]), flush=True)
    return changed


# ---- the run -----------------------------------------------------------------------------

class Comfy:
    """The live engine: content-addressed staging, a queued POST, a wait."""

    def stage(self, path: Path) -> str:
        from studio import comfy
        return comfy.stage_image(path)

    def submit(self, graph: dict) -> str:
        from studio import comfy
        return comfy.submit(graph)

    def wait(self, prompt_id: str) -> dict[str, list[Path]]:
        """node id -> the files it reported (studio/comfy.outputs_by_node)."""
        from studio import comfy
        return comfy.outputs_by_node(comfy.wait_record(prompt_id, poll=5.0))


def detectors():
    """(MTCNN loose detector, facenet detect, facenet embed, the YOLO finder with MTCNN behind it)."""
    from studio.measure import faces
    detect, embed = faces.embedder()
    loose = face_track.loose_detector()
    return loose, detect, embed, face_detect.Finder(loose)


def frame_finder(loose):
    """A finder reading frames with one frame detector (a test's fake, or MTCNN alone)."""
    return lambda take, frames: face_detect.by_frames(frames, loose)


def refine(book: Path, number: int, indices: list[int] | None, *, engine=None, detect=None, loose=None,
           embed=None, find=None, within: str = "", anime=None) -> dict:
    """Queue every owed take's crops as it is tracked, then gate each take in order."""
    if detect is None:
        from studio import anime_id
        loose, detect, embed, find = detectors()
        anime = anime or anime_id.Reader()
    find, engine, room = find or frame_finder(loose), engine or Comfy(), room_of(book, number)
    cards = {int(c["index"]): c for c in read(room / "prompts.json", [])}
    out = {}
    with episode_clock.timed(book, number, "face_refine", note=" ".join(map(str, indices or [])), within=within):
        queued = queue_within_wall(book, number, pending(book, number, indices), cards, engine,
                                   (loose, detect, embed, find))
        for began, work in queued:
            out[work.index] = decide_take(room, book, work, detect, embed, engine, time.time() - began, loose, anime)
            count_if_worked(episode_home.home(book, number), work)
    getattr(anime, "close", lambda: None)()
    return out


def queue_within_wall(book: Path, number: int, owed_takes: list[int], cards: dict, engine, readers) -> list:
    """Each owed take queued in turn until the wall: the rest keep their faces, said as a CAP
    line and recorded `cut` in refine.json (a take in flight is never cut).  The detector
    worker is closed once the last take is tracked.  `readers` = (loose, detect, embed, find)."""
    began, queued = time.time(), []
    for k, i in enumerate(owed_takes):
        if wall_spent(began, time.time()):
            rest = owed_takes[k:]
            record_cut(room_of(book, number), rest, 0.0, book, number, why=f"CAP face_refine: the {step_caps.mmss(step_caps.wall_s('face_refine'))} wall")
            print(step_caps.cap_line("face_refine", k, len(owed_takes), time.time() - began, len(rest)), flush=True)
            break
        queued.append((time.time(), queue_take(book, number, i, cards[i], engine, *readers)))
    getattr(readers[3], "close", lambda: None)()
    return queued


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
