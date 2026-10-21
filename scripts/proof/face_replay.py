#!/usr/bin/env python
"""The face path on a delivered episode as a FIRST pass (2026-10-21_ep02_proof DESIGN 4.1, P6).

    uv run --no-sync python scripts/proof/face_replay.py [--book=<codex>] [--episode=1] [--box=<dir>]
    uv run --no-sync python scripts/proof/face_replay.py panel [--book=<codex>] [--episode=1]
    uv run --no-sync python scripts/proof/face_replay.py instrument [--book=<codex>] [--episode=1]

`replay` copies the episode's records into a sandbox on C: with every take AS IT WAS AT THE FIRST
MASTER, the first-pass attempts and ladder (no refine or tiny-face round), and NO refine.json and NO
repair window.  Which file a take held then is read from the files' own times against
cut/master_iter1.mp4's (a take a later repair displaced is restored from takes/r2v/attempts/): the
first master's eye rubric holds no per-take sha8 and manifest.json is the FINAL master's, so no sha8
of the first master exists to restore by; the report compares the restore with the final manifest.

The engine is package P3's fake ComfyUI (studio/rehearsal/fake_comfy), a real HTTP server on a free
loopback port inside the sandbox, serving the episode's recorded crops as P2's recordings index writes
them (recordings.refine_entries: keyed by the sha256 of the staged `_src` bytes).  Nothing in the
pipeline's call graph is replaced: face_refine.Comfy -> studio.comfy (stage_image, submit,
wait_record, history) is the real client, its host and root bound to the fake as a rehearsal process
binds them.  Each answer is labelled in P3's classes, exact / substituted / canned, in
<sandbox>/engine_log.jsonl; only an exact answer is evidence.  Then, with the write fence armed over
the real roots, the REAL step-09 face path runs in process -- face_refine.refine, step 09's
face_list_note, tiny_face.rung (served the episode's own recorded draw, else it dies), the refine of a
kept draw, the face list again.

Step 10's paste is judged the way step 10 builds it: face_paste.spans_from over the cut's own
takes/work/layout.json, gutter.json and segments (the sandbox's pasted segments cut by
assemble.segment from the sandbox takes), the Paster at cut scale with an identity upscaler.  What
may move is the face rectangle the TRACK RECORD gives (its per-frame faces, else face_track.windows'
centre at the track's face share), mapped to cut pixels here, never by the Paster's placement.

Readers: facenet and the loose MTCNN on the CPU, the MTCNN finder, no CCIP reader -- the production
FALLBACK: the YOLO and CCIP workers run on the portable python, which the fence refuses (DESIGN 2.6).

Writes docs/audit/2026-10-21_ep02_proof/results/face_rows.json (`faces`: one row per (take, person),
plus the kill, agreement, the outside invariant, SR-1, the noise band and the proof rows).  `panel`
writes results/panel_take_size.json (4.4); `instrument` stages the recorded crops for the owner's
labels under docs/audit/2026-10-21_ep02_proof/review/ and writes results/instrument_gate.json (4.2).
The real library is only ever read; no GPU, no real ComfyUI, no network."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import sys
import time
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_home, settings  # noqa: E402
from studio.face_paste import sha8  # noqa: E402
from studio.rehearsal import face_rows as fr_rows, instrument_gate as ig, panel_take_size as pts  # noqa: E402

BOOK = "20260827135504"
PROOF = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof"
RESULTS = PROOF / "results"
REVIEW = PROOF / "review"
ROOM = Path("takes") / "r2v"
WORK = Path("takes") / "work"
HOME_RECORDS = ("plan.json",)
ROOM_RECORDS = ("prompts.json", "shots.json")
READERS = "facenet cpu + loose MTCNN cpu + MTCNN finder (production fallback); CCIP/clip_h unread"
ITER1, ITER3 = "master_iter1.mp4", "master_iter3.mp4"
REPAIR_STEP = "09"
ITER1_BASIS = ("file mtime <= cut/master_iter1.mp4's: its eye rubric (review/eye_<sha8>.json) holds no per-take "
               "sha8 and manifest.json is the final master's, so no first-master sha8 exists to restore by")
AIMED = ("HOST", "COMFY_ROOT")
"""The real client's module constants a rehearsal process binds to its engine (studio/comfy)."""
STEM = re.compile(r"(T\d\d_p\d+)_[0-9a-f]{8}_\d{5}_\.\w+$")
"""A refine render's output name: face_refine/<stem>_<take sha8>_<n:05>_.mp4 (scripts/episode/face_refine)."""


def takes_of(doc: dict) -> list[tuple[str, dict]]:
    """A refine.json's take entries, in order."""
    return sorted((k, v) for k, v in doc.items() if k[:1] == "T" and k[1:].isdigit())


# ---- the sandbox: the episode at its first master (built before the fence, real files only read) -----

def master_time(home: Path, name: str) -> float:
    return (Path(home) / "cut" / name).stat().st_mtime


def copy_named(src: Path, dest: Path, rels) -> list[str]:
    """Copy each named file that exists (mtime kept); the names copied."""
    done = []
    for rel in rels:
        if (Path(src) / rel).is_file():
            (Path(dest) / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(src) / rel, Path(dest) / rel)
            done.append(str(rel))
    return done


def graph_beside(take: Path) -> Path:
    return take.with_name(take.name[:-4] + ".graph.json")


def restore_take(room: Path, box_room: Path, index: int, cutoff: float) -> dict:
    """Take `index` as it was at the first master into the sandbox room, its dq only when it measured
    those bytes, its graph, and one empty placeholder per older attempt (attempts are counted by name)."""
    took, older = fr_rows.iter1_take(room, index, cutoff)
    if took is None:
        return {"take": f"T{index:02d}", "source": None}
    stem = box_room / f"T{index:02d}"
    shutil.copy2(took, stem.with_suffix(".mp4"))
    copy_if(graph_beside(took), stem.with_suffix(".graph.json"))
    dq = fr_rows.read_json(room / f"T{index:02d}.dq.json", {})
    kept = dq.get("take_sha8") == sha8(took)
    if kept:
        shutil.copy2(room / f"T{index:02d}.dq.json", stem.with_suffix(".dq.json"))
    for k in range(len(older)):
        (box_room / "attempts" / f"T{index:02d}_fail{k + 1}.mp4").touch()
    return {"take": f"T{index:02d}", "source": took.relative_to(room).as_posix(), "sha8": sha8(took),
            "dq": "measured these bytes" if kept else "the dq measured other bytes: none given", "attempts": len(older)}


def copy_if(src: Path, dest: Path) -> None:
    if Path(src).is_file():
        shutil.copy2(src, dest)


def first_pass_records(home: Path, box_home: Path, cutoff: float) -> None:
    """attempts.json and ladder.json as the first pass read them (face_rows.first_pass_*)."""
    ladder = fr_rows.read_json(Path(home) / ROOM / "ladder.json", {"rounds": []})
    attempts = fr_rows.read_json(Path(home) / "attempts.json", {})
    episode_home.write_json(box_home / "attempts.json", fr_rows.first_pass_attempts(attempts, ladder, cutoff))
    episode_home.write_json(box_home / ROOM / "ladder.json", fr_rows.first_pass_ladder(ladder, cutoff))


def sheets_of(cards: list[dict]) -> list[str]:
    """The book pictures the cards stage (cast sheets), never the episode's own panels."""
    return sorted({str(r) for c in cards for r in c.get("refs") or [] if str(r).startswith("refs/")})


def build(book: Path, number: int, box: Path) -> tuple[Path, list[dict]]:
    """The sandbox book (its one episode at the first master) and what each take was restored from."""
    home, box_book = episode_home.home(book, number), Path(box) / settings.LIBRARY_DIR / Path(book).name
    box_home = episode_home.home(box_book, number)
    (box_home / ROOM / "attempts").mkdir(parents=True, exist_ok=True)
    copy_named(home, box_home, [*HOME_RECORDS, *[(ROOM / n).as_posix() for n in ROOM_RECORDS],
                                *[(ROOM / p.name).as_posix() for p in sorted((home / ROOM).glob("T[0-9][0-9].content.json"))]])
    cards, cutoff = fr_rows.read_json(home / ROOM / "prompts.json", []), master_time(home, ITER1)
    copy_named(book, box_book, sheets_of(cards))
    first_pass_records(home, box_home, cutoff)
    restored = [restore_take(home / ROOM, box_home / ROOM, int(c["index"]), cutoff) for c in cards]
    return box_book, restored


def manifest_check(home: Path, restored: list[dict]) -> dict:
    """The restore against the FINAL master's manifest.json: a take that differs is one a repair redrew
    after the first master (expected), never proof of a wrong restore."""
    rows = fr_rows.read_json(Path(home) / "manifest.json", {}).get("inputs") or []
    final = {Path(r["path"]).stem: r.get("sha8") for r in rows if re.search(r"takes/r2v/T\d\d\.mp4$", str(r.get("path")))}
    mine = {r["take"]: r.get("sha8") for r in restored if r.get("sha8")}
    both = sorted(set(final) & set(mine))
    return {"basis": ITER1_BASIS, "n": len(both), "same": sum(final[t] == mine[t] for t in both),
            "differ": [t for t in both if final[t] != mine[t]]}


# ---- the engine: P3's fake ComfyUI, the real client aimed at it --------------------------------------

def refine_recordings(home: Path, root: Path) -> list[dict]:
    """The episode's recorded crops as P2's recordings index writes them, their renders made absolute
    for the fake to read; a crop whose render was never kept is no recording."""
    from studio.rehearsal import recordings
    return [{**e, "path": str(Path(root) / e["path"])} for e in recordings.refine_entries(Path(home), Path(root))
            if e.get("path")]


def refine_workflows(box: Path) -> Path:
    """The face-refine workflow and every technique named after it, copied into the sandbox for the fake's
    index (one narrow read of the workflow folder, never an index of every workflow)."""
    from studio import comfy, face_refine as fr
    folder = Path(box) / "workflows" / "video"
    folder.mkdir(parents=True, exist_ok=True)
    for path in Path(comfy.WORKFLOWS).glob(f"*/{fr.WORKFLOW}*.json"):
        shutil.copy2(path, folder / path.name)
    return folder.parent


def start_engine(box: Path, recorded: list[dict]):
    """P3's fake ComfyUI on a free loopback port, its root and engine_log.jsonl in the sandbox."""
    from studio.rehearsal import fake_comfy
    return fake_comfy.FakeComfy(Path(box), recordings=recorded, workflows=refine_workflows(box)).start()


@contextmanager
def aimed(fake):
    """The real client (studio.comfy) bound to the fake for the block, as a rehearsal process binds it."""
    from studio import comfy
    saved = {k: getattr(comfy, k) for k in AIMED}
    comfy.HOST, comfy.COMFY_ROOT = fake.url, fake.root
    try:
        yield fake
    finally:
        for k, v in saved.items():
            setattr(comfy, k, v)


def answer(row: dict) -> dict:
    """One answer of the fake: the crop stem its output names, P3's match class, its clock."""
    stem = next((m.group(1) for o in row.get("outputs") or [] if (m := STEM.search(str(o)))), None)
    return {"stem": stem, "match": row["class"], "clock": row.get("clock"), "seconds": row.get("seconds"),
            "recording": row.get("recording"), "workflow": row.get("workflow"), "kind": row.get("kind")}


def answers(box: Path) -> list[dict]:
    """Every crop request the fake answered, in order (its engine_log.jsonl `prompt` rows)."""
    path = Path(box) / "engine_log.jsonl"
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []
    return [answer(r) for r in rows if r.get("call") == "prompt" and r.get("class")]


def engine_clock(doc: dict, log: list[dict]) -> dict:
    """The sandbox refine's gpu_busy_s (take_phases.window over the fake's /history): a RECORDED clock,
    spaced by the recordings' seconds, never time evidence (R15)."""
    busy = [e["gpu_busy_s"] for _, e in takes_of(doc) if e.get("gpu_busy_s") is not None]
    return {"gpu_busy_s": round(sum(busy), 1), "clock": "recorded" if any(a["clock"] == "recorded" for a in log) else None,
            "time_evidence": False}


# ---- the step context: a log, the learnings, the recorded tiny-face draw ------------------------------

class Ctx:
    """What the real step-09 functions are handed: the sandbox episode, a log, its learnings file, and
    `run_script` answering the tiny-face rung from the episode's own recorded draw and verdicts.  A draw
    the episode never made "dies" (SystemExit) before anything moves: never guessed."""

    def __init__(self, book: Path, number: int, draws: dict[int, dict]):
        self.book_dir, self.number, self.draws = Path(book), number, draws
        self.home = episode_home.home(book, number)
        self.lines, self.served = [], []

    def log(self, line: str, step_id: str = "", level: str = "INFO") -> None:
        self.lines.append(f"{level} {step_id} {line}".strip())

    def learn(self, learning) -> None:
        with open(self.home / "learnings.jsonl", "a", encoding="utf-8") as out:
            out.write(learning.model_dump_json() + "\n")

    def run_script(self, script: str, *args, gpu: bool = False, clock: str = "") -> None:
        from scripts.episode import tiny_face
        indices = retake_indices(args)
        if script == tiny_face.RENDER:
            return self.render(indices)
        if script in (tiny_face.DQ, tiny_face.CONTENT):
            return self.verdicts(".dq.json" if script == tiny_face.DQ else ".content.json", indices)
        raise SystemExit(f"replay: {script} is not answered in a replay")

    def render(self, indices: list[int]) -> None:
        if missing := [i for i in indices if i not in self.draws]:
            raise SystemExit("no recorded tiny-face draw: " + ", ".join(f"T{i:02d}" for i in missing))
        room = self.home / ROOM
        for i in indices:
            episode_home.displace(room / f"T{i:02d}.mp4", i)
            shutil.copyfile(self.draws[i]["mp4"], room / f"T{i:02d}.mp4")
            copy_if(self.draws[i]["graph"], room / f"T{i:02d}.graph.json")
            self.served.append({"take": f"T{i:02d}", "match": "recorded", "sha8": sha8(room / f"T{i:02d}.mp4")})

    def verdicts(self, suffix: str, indices: list[int]) -> None:
        for i in indices:
            copy_if(self.draws.get(i, {}).get(suffix) or Path("-"), self.home / ROOM / f"T{i:02d}{suffix}")


def retake_indices(args) -> list[int]:
    """The takes a script is asked about: `--retake=a,b`, or bare numbers."""
    said = next((a.split("=", 1)[1] for a in map(str, args) if a.startswith("--retake=")), "")
    return [int(v) for v in said.split(",") if v.strip().isdigit()] or [int(a) for a in map(str, args) if a.isdigit()]


def recorded_draws(home: Path, cutoff: float) -> dict[int, dict]:
    """take -> the episode's own tiny-face draw (newer than the first master, its round spent), with its
    graph and the verdicts that measured those bytes."""
    attempts, room, out = fr_rows.read_json(Path(home) / "attempts.json", {}), Path(home) / ROOM, {}
    for key in (k for k in attempts if k.startswith("tiny_face.T") and attempts[k].get("rounds")):
        i = int(key.rsplit("T", 1)[1])
        take = room / f"T{i:02d}.mp4"
        if take.is_file() and take.stat().st_mtime > cutoff:
            out[i] = {"mp4": take, "graph": room / f"T{i:02d}.graph.json",
                      **{s: room / f"T{i:02d}{s}" for s in (".dq.json", ".content.json") if verdict_of(room, i, s, take)}}
    return out


def verdict_of(room: Path, index: int, suffix: str, take: Path) -> bool:
    """The recorded verdict file measured exactly these take bytes."""
    return fr_rows.read_json(room / f"T{index:02d}{suffix}", {}).get("take_sha8") == sha8(take)


def recorded_judge(take: Path):
    """The take judge on a draw, from its recorded dq and content verdicts (the VL eye read is not replayed)."""
    from studio.judges import take_eye
    i = int(Path(take).name[1:3])
    dq = fr_rows.read_json(Path(take).with_name(f"T{i:02d}.dq.json"), {})
    content = fr_rows.read_json(Path(take).with_name(f"T{i:02d}.content.json"), {})
    faults = (take_eye.dq_faults(i, dq) if dq else []) + (take_eye.content_faults(i, content) if content else [])
    return SimpleNamespace(passed=not faults, faults=faults)


# ---- the step-09 face path, the real code -------------------------------------------------------------

def cpu_readers():
    """(loose, detect, embed, find): facenet and the loose MTCNN on the CPU, the MTCNN finder."""
    from scripts.episode import face_refine as cli
    from studio import face_track
    from studio.measure import faces
    detect, embed = faces.embedder("cpu")
    loose = face_track.loose_detector("cpu")
    return loose, detect, embed, cli.frame_finder(loose)


def step09(book: Path, number: int, readers, ctx: Ctx, asked) -> dict:
    """The refine (the real engine client), the face list, the tiny-face rung, the refine of a kept draw,
    the face list again; `asked()` counts the crop requests the engine has answered."""
    from scripts.episode import face_refine as cli, step_09_shoot as s09, tiny_face
    loose, detect, embed, find = readers
    kw = dict(engine=cli.Comfy(), detect=detect, loose=loose, embed=embed, find=find, anime=None)
    first = cli.refine(book, number, None, **kw)
    first_requests = asked()
    s09.face_list_note(ctx)
    try:
        kept, rung = tiny_face.rung(ctx, "", recorded_judge, ()), "ran"
    except SystemExit as died:
        kept, rung = [], f"died: {died}"
    second = cli.refine(book, number, kept, **kw) if kept else {}
    s09.face_list_note(ctx)
    return {"first": sorted(first), "first_requests": first_requests, "rung": rung, "kept_draws": kept,
            "second": sorted(second)}


def arm(box: Path, roots=None, ports=()) -> None:
    """The write fence over the real roots (DESIGN 2.6), armed in this process before any step runs;
    the fake's port is the one loopback port it may connect to."""
    from studio.rehearsal import fence
    fence.install(fence.Fence.of(roots if roots is not None else settings.todays_real_roots(), box, settings.REPO,
                                 ports))


# ---- the step-10 paste: nothing outside the track's face may move ------------------------------------

def to_cut(px: float, py: float, guard, width: int, height: int) -> tuple[float, float]:
    """A take pixel in the cut: through the gutter guard's crop (w, h, left, top), then scaled up to cover
    the canvas and centre-cropped, as assemble's segment filter does (worked here, not by the Paster)."""
    cw, ch, left, top = guard or (width, height, 0, 0)
    s = max(width / cw, height / ch)
    return (px - left) * s - (cw * s - width) / 2, (py - top) * s - (ch * s - height) / 2


def recorded_face(track, t: int) -> tuple[float, float, float]:
    """The face on take frame t as shares of its window, from the TRACK RECORD: the run's own per-frame
    face, else face_track.windows' centre (half across, 0.5 + 0.05 down) at the track's face share."""
    from studio.face_track import MARGIN
    if track.faces and t < len(track.faces) and track.faces[t]:
        return tuple(float(v) for v in track.faces[t])
    return 0.5, 0.55, track.face or 1 / MARGIN


def face_rect(shape: tuple, track, t: int, guard):
    """Where step 10 may change cut frame t for this track: the face's square from the track record, in
    cut pixels (a frame past the track's windows may change nowhere)."""
    import math
    import numpy as np
    h, w = shape[:2]
    out = np.zeros((h, w), bool)
    if not 0 <= t < len(track.windows):
        return out
    (x, y, side), (fx, fy, fh) = track.windows[t], recorded_face(track, t)
    x0, y0 = to_cut(x + (fx - fh / 2) * side, y + (fy - fh / 2) * side, guard, w, h)
    x1, y1 = to_cut(x + (fx + fh / 2) * side, y + (fy + fh / 2) * side, guard, w, h)
    out[max(0, math.floor(y0)):max(0, math.ceil(y1)), max(0, math.floor(x0)):max(0, math.ceil(x1))] = True
    return out


def track_outside(frames: list, span, track, width: int, height: int) -> float:
    """The largest share of pixels outside the track's face that its paste moved on any frame of its
    segment: step 10's own span (re-based to the segment's first frame) through the Paster, alone."""
    from studio import face_paste as fp
    paster = fp.Paster(lambda f: f, [replace(span, start=0, tracks=(track,))], width, height, 1)
    worst = 0.0
    for j, frame in enumerate(frames[:span.frames]):
        allowed = face_rect(frame.shape, track, fp.take_frame(j, span.head, span.slow), span.guard)
        worst = max(worst, fr_rows.outside_moved(frame, paster(frame), allowed))
    return worst


def kept_names(room: Path, index: int) -> list[str]:
    """Who each kept track of a take is, in kept_tracks' order."""
    entry = fr_rows.read_json(Path(room) / "refine.json", {}).get(f"T{index:02d}") or {}
    return [str(p.get("who")) for p in entry.get("people") or [] if p.get("kept")]


def cut_spans(work: Path, room: Path) -> list:
    """Step 10's spans: face_paste.spans_from over the cut's layout.json, its segments' measured frames
    and gutter.json, each take's bytes on disk (assemble.face_paste_wrap less its regate, which writes)."""
    from scripts.episode import assemble
    from studio import face_paste as fp
    rows = fr_rows.read_json(Path(work) / "layout.json", [])
    frames = {int(r["index"]): assemble.video_frames(Path(work) / f"seg{int(r['index']):02d}.mp4") for r in rows}
    return fp.spans_from(rows, frames, fr_rows.read_json(Path(work) / "gutter.json", {}), Path(room),
                         sha_of=lambda i: fp.sha8(Path(room) / f"T{i:02d}.mp4"), fps=assemble.FPS)


def step10_outside(work: Path, room: Path, aspect: str) -> dict[tuple, float]:
    """(take, who) -> the outside share of every paste step 10 would make on this cut (0 is the invariant)."""
    from scripts.episode import face_refine as cli
    from studio import canvas
    width, height = canvas.size(aspect)
    out = {}
    for span in cut_spans(work, room):
        frames = cli.read_frames(Path(work) / f"seg{span.index:02d}.mp4")
        for who, track in zip(kept_names(room, span.index), span.tracks):
            out[(f"T{span.index:02d}", who)] = round(track_outside(frames, span, track, width, height), 6)
    return out


@contextmanager
def canvas_of(module, aspect: str):
    """assemble's W, H bound to the plan's canvas for the block, as its `main` binds them."""
    from studio import canvas
    saved = module.W, module.H
    module.W, module.H = canvas.size(aspect)
    try:
        yield
    finally:
        module.W, module.H = saved


def sandbox_cut(real_home: Path, box_home: Path, pasted: set[int], aspect: str) -> Path:
    """The sandbox's cut records: the real cut's layout.json, each pasted take's segment cut by step 10's
    own assemble.segment from the SANDBOX take (its guard recomputed), every other segment the real one."""
    from scripts.episode import assemble
    real, work, guarded = Path(real_home) / WORK, Path(box_home) / WORK, {}
    work.mkdir(parents=True, exist_ok=True)
    rows = fr_rows.read_json(real / "layout.json", [])
    gutter = {str(k): v for k, v in fr_rows.read_json(real / "gutter.json", {}).items() if int(k) not in pasted}
    with canvas_of(assemble, aspect):
        for r in rows:
            i = int(r["index"])
            if i not in pasted:
                copy_if(real / f"seg{i:02d}.mp4", work / f"seg{i:02d}.mp4")
                continue
            assemble.segment(i, float(r["seconds"]), {i: Path(box_home) / ROOM / f"T{i:02d}.mp4"}, {},
                             {i: float(r.get("head") or 0.0)}, work, guarded, slow=float(r.get("slow") or 1.0))
    episode_home.write_json(work / "layout.json", rows)
    episode_home.write_json(work / "gutter.json", {**gutter, **{str(k): v for k, v in guarded.items()}})
    return work


def aspect_of(home: Path) -> str:
    """The canvas the plan declares (assemble's default when it names none)."""
    return fr_rows.read_json(Path(home) / "plan.json", {}).get("aspect") or "9:16"


# ---- the eye measure's own noise ---------------------------------------------------------------------

def face_box(doc: dict, t: int, side: int) -> tuple | None:
    """The face box on crop frame t (crop pixels): the run's recorded face, else where face_track.windows
    puts it (centre, FACE_Y down) at the track's face share; None when neither is known."""
    from studio import face_paste as fp
    faces = doc.get("faces") or []
    share = fp.face_share(doc)
    if t < len(faces) and faces[t]:
        cx, cy, fh = (float(v) for v in faces[t])
    elif share is not None:
        cx, cy, fh = 0.5, fp.FACE_Y, share
    else:
        return None
    return ((cx - fh / 2) * side, (cy - fh / 2) * side, (cx + fh / 2) * side, (cy + fh / 2) * side)


def crop_eyes(frames: list, doc: dict, ks: list[int]) -> dict[int, float]:
    """crop frame -> the drawn-eye score there, read at the face box (face_box); a frame with no box is
    left out, never read as another frame."""
    from studio import face_eye
    out = {}
    for k in ks:
        box = face_box(doc, int(doc["start"]) + k, frames[0].shape[0]) if 0 <= k < len(frames) else None
        if box is not None:
            out[k] = face_eye.eye_score(face_eye.face_gray(frames[k], box))
    return out


def eye_noise(room: Path, doc: dict) -> dict[tuple, dict]:
    """(take, who) -> the eye measure's band on its accepted crop: read twice, and one frame either way."""
    import numpy as np
    from scripts.episode import face_refine as cli
    out = {}
    for take, entry in takes_of(doc):
        for p in (p for p in entry.get("people") or [] if p.get("kept")):
            track, frames = fr_rows.read_json(Path(room) / p["track"], {}), cli.read_frames(Path(room) / p["crop"])
            life, start = track["life"], int(track["start"])
            ks = sorted({int(v) for v in np.linspace(max(1, life[0] - start), max(1, min(life[1] - start, len(frames) - 2)), 6)})
            near = crop_eyes(frames, track, sorted({k + d for k in ks for d in (1, -1)}))
            out[(take, p["who"])] = fr_rows.noise_band(crop_eyes(frames, track, ks), crop_eyes(frames, track, ks), near)
    return out


# ---- what the real episode decided, and when ---------------------------------------------------------

def decided_in(doc: dict, start: float, stop: float) -> dict:
    """The take entries of a refine.json whose `decided` stamp (local time) falls in [start, stop]."""
    out = {}
    for key, entry in takes_of(doc):
        if entry.get("decided") and start <= datetime.fromisoformat(entry["decided"]).timestamp() <= stop:
            out[key] = entry
    return out


def repair_decided(home: Path, doc: dict) -> dict:
    """The entries a step-09 repair window decided (repair.jsonl's opened_at .. closed_at)."""
    out = {}
    for line in (Path(home) / "repair.jsonl").read_text(encoding="utf-8").splitlines() if (Path(home) / "repair.jsonl").is_file() else []:
        window = json.loads(line)
        if REPAIR_STEP in (window.get("steps") or []):
            out |= decided_in(doc, float(window["opened_at"]), float(window.get("closed_at") or time.time()))
    return out


def iter1_decided(doc: dict, cutoff: float, restored: list[dict]) -> dict:
    """The first-pass decisions still on record: decided by the first master, on the bytes it held."""
    shas = {r["take"]: r.get("sha8") for r in restored}
    return {k: e for k, e in decided_in(doc, 0.0, cutoff).items() if e.get("take_sha8") == shas.get(k)}


# ---- the rows and the report -------------------------------------------------------------------------

def person_matches(log: list[dict], doc: dict) -> dict[tuple, str]:
    """(take, who) -> P3's class for the LAST crop asked for that person (a kept draw is asked again)."""
    by_crop = {p.get("crop"): (take, p.get("who")) for take, e in takes_of(doc) for p in e.get("people") or []}
    return {by_crop[f"refine/{e['stem']}.mp4"]: e["match"] for e in log if f"refine/{e['stem']}.mp4" in by_crop}


def face_table(cards: list[dict], doc: dict, iter1: dict, iter3: dict, log: list[dict], pasted: dict) -> list[dict]:
    """Every take's rows (face_rows.take_rows), the readers named on each."""
    selected = {int(k[1:]) for k, _ in takes_of(doc)}
    matches = person_matches(log, doc)
    rows = [r for c in cards for r in fr_rows.take_rows(int(c["index"]), doc, iter1, iter3, selected, matches, pasted)]
    return [{**r, "readers": READERS} for r in rows]


def agreement_with_repair(doc: dict, repair: dict, restored: list[dict]) -> dict:
    """Take-level agreement with the repair, each row saying whether the repair decided the same bytes."""
    said = fr_rows.agreement(doc, repair, sorted(repair))
    shas = {r["take"]: r.get("sha8") for r in restored}
    said["rows"] = [{**r, "same_bytes": (repair.get(r["take"]) or {}).get("take_sha8") == shas.get(r["take"])}
                    for r in said["rows"]]
    return said


OUTSIDE_HOW = ("step 10's spans (face_paste.spans_from over takes/work/layout.json) through the Paster; allowed: the "
               "face square from the track record (per-frame faces, else face_track.windows' centre -- there the "
               "rectangle shares the Paster's own centring assumption)")


def outside_summary(pasted: dict) -> dict:
    moved = {f"{t} {w}": v for (t, w), v in pasted.items() if v > 0}
    return {"pastes": len(pasted), "moved": len(moved), "worst": max(pasted.values(), default=0.0), "which": moved,
            "how": OUTSIDE_HOW}


def noise_summary(noise: dict) -> dict:
    """The band over every crop that was READ (a crop with no reading is counted apart, never as 0)."""
    read = [b for b in noise.values() if b["repeat"] is not None]
    return {"crops": len(noise), "read": len(read), "repeat_max": max((b["repeat"] for b in read), default=None),
            "shift_max": max((b["shift"] for b in read if b["shift"] is not None), default=None),
            "by_crop": {f"{t} {w}": b for (t, w), b in noise.items()}}


def proof_rows(s: dict, gate: dict) -> list[dict]:
    """The DESIGN 5 rows of the face replay, under the check ids scripts/proof/questions.yaml names."""
    k, a, o, ev = s["kill"], s["agreement"], s["outside"], ["results/face_rows.json"]
    classes = {c: k[c] for c in fr_rows.CLASSES}
    sel, rec, both = s["selection"], s["recorded_outside"], o["pastes"] + s["recorded_outside"]["pastes"]
    return [ig.proof_row("unrecorded_le_half", "Q1", not k["real_run"], k["requests"], k["requests"], ev, classes,
                         "fake_comfy (P3)", "n/a", "mechanism"),
            ig.proof_row("face_replay.selection_agreement", "Q1", sel["agree"] == sel["n"], sel["n"], sel["n"], ev, {},
                         READERS, "n/a", "mechanism"),
            ig.proof_row("refine_decision_recall", "Q1", a["agree"] == a["n"], a["n"], a["n"], ev, classes,
                         "", "n/a (a decision on a canned or substituted render is no evidence)", "mechanism"),
            ig.proof_row("outside_invariant", "Q1", o["moved"] + rec["moved"] == 0, both, both, ev,
                         {"replay": o["pastes"], "recorded": rec["pastes"]}, "face_paste.spans_from + Paster", "n/a",
                         "mechanism"),
            ig.proof_row("tiny_face_path", "Q4", s["step09"]["rung"] == "ran", 1, 1, ev, s["rung_served"],
                         "tiny_face.rung", "n/a", "mechanism"), *eye_rows(s["faces"], gate)]


def eye_pairs(faces: list[dict], col: str | None, tier: str | None = None) -> list[tuple]:
    """(replay eye, the comparison's) on every EXACT row with both read; col None compares with 0 (no eye)."""
    return [(r["eye_cel_replay"], r[col] if col else 0.0) for r in faces if r["match"] == "exact"
            and r["eye_cel_replay"] is not None and (col is None or r[col] is not None) and (tier is None or r["tier"] == tier)]


def eye_rows(faces: list[dict], gate: dict) -> list[dict]:
    """The eye questions: passed only with a calibrated instrument and every pair no worse (mid: an eye drawn)."""
    out = []
    for check, question, col, tier in (("face_first_pass_vs_iter1", "Q1", "eye_cel_iter1", None),
                                       ("face_first_pass_vs_iter3", "Q2", "eye_cel_iter3", None),
                                       ("face_mid_tier", "Q3", None, "mid")):
        pairs = eye_pairs(faces, col, tier)
        better = bool(pairs) and all((a > b) if col is None else (a >= b) for a, b in pairs)
        out.append(ig.proof_row(check, question, gate["passed"] and better, len(pairs), len(pairs),
                                ["results/face_rows.json"], {"exact": len(pairs)}, "face_eye.cel", gate["state"], "quality"))
    return out


def write_result(name: str, doc: dict, folder: Path = RESULTS) -> Path:
    Path(folder).mkdir(parents=True, exist_ok=True)
    path = Path(folder) / name
    path.write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    return path


# ---- the owner's labels (SR-0) and the instrument gate -----------------------------------------------

def cel_score(path: Path) -> float | None:
    """face_eye's cel score of one staged face picture, the whole picture read as the face box."""
    import numpy as np
    from PIL import Image
    from studio import face_eye
    if not Path(path).is_file():
        return None
    rgb = np.asarray(Image.open(path).convert("RGB"))
    return face_eye.eye_score(face_eye.face_gray(rgb, (0, 0, rgb.shape[1], rgb.shape[0])))


def face_picture(video: Path, track: dict) -> bytes:
    """The face at the crop's middle frame as PNG bytes: the face box when the track gives one, else the frame."""
    import numpy as np
    from PIL import Image
    from scripts.episode import face_refine as cli
    frames = cli.read_frames(video)
    k = len(frames) // 2
    box = face_box(track, int(track.get("start") or 0) + k, frames[k].shape[0]) if track else None
    rgb = frames[k] if box is None else frames[k][max(0, int(box[1])):int(box[3]), max(0, int(box[0])):int(box[2])]
    buf = io.BytesIO()
    Image.fromarray(np.ascontiguousarray(rgb)).save(buf, "PNG")
    return buf.getvalue()


def staged_picture(review: Path, name: str, body: bytes) -> str:
    """One picture under review/crops/, named by its bytes and written once; its review-relative path."""
    rel = f"crops/{name}_{hashlib.sha256(body).hexdigest()[:8]}.png"
    if not (Path(review) / rel).is_file():
        (Path(review) / rel).parent.mkdir(parents=True, exist_ok=True)
        (Path(review) / rel).write_bytes(body)
    return rel


def label_rows(room: Path, take: str, p: dict, review: Path) -> list[dict]:
    """A recorded crop's two label rows (its source and its render), each with a blank owner word."""
    render = Path(room) / p["crop"]
    src, track = render.with_name(f"{render.stem}_src.mp4"), fr_rows.read_json(Path(room) / str(p.get("track")), {})
    if not (render.is_file() and src.is_file()):
        return []
    return [{"take": take, "who": p.get("who"), "kind": kind, "owner": "",
             "crop": staged_picture(review, f"{take}_{p.get('who')}_{kind}", face_picture(video, track))}
            for kind, video in (("refine_src", src), ("refine_render", render))]


def stage_labels(room: Path, review: Path) -> Path:
    """The episode's recorded refine crops staged for the owner's labels (SR-0) as
    review/face_labels_<sha8>.json, every `owner` blank.  The sha8 names the staged pictures, so a set
    already staged is returned untouched: the owner's words in it are never rewritten."""
    doc = fr_rows.read_json(Path(room) / "refine.json", {})
    crops = [r for take, e in takes_of(doc) for p in e.get("people") or [] if p.get("crop")
             for r in label_rows(room, take, p, review)]
    path = Path(review) / f"face_labels_{hashlib.sha256(json.dumps([c['crop'] for c in crops]).encode()).hexdigest()[:8]}.json"
    if not path.is_file():
        episode_home.write_json(path, {"labels": list(ig.LABELS), "how": "owner: good = a drawn eye, bad = none",
                                       "crops": crops})
    return path


def label_paths(home: Path, review: Path | None) -> list[tuple[str, Path]]:
    """(where, file) of every owner label file: the episode's review/, then the staged ones."""
    found = [("episode", p) for p in sorted((Path(home) / "review").glob("face_labels_*.json"))]
    return found + ([("proof", p) for p in sorted(Path(review).glob("face_labels_*.json"))] if review else [])


def instrument(home: Path, review: Path | None = None) -> dict:
    """The gate on both candidates over every owner label file, and whether the listed crops could ever
    reach its n (ig.MIN_N) once the owner has labelled them."""
    labels = label_paths(home, review)
    listed = {w: sum(len(fr_rows.read_json(p, {}).get("crops") or []) for x, p in labels if x == w) for w in ("episode", "proof")}
    cel = lambda doc, folder: ig.cel_reads(doc, folder, cel_score)  # noqa: E731
    return {"label_files": [f"{w}:review/{p.name}" for w, p in labels], "crops_staged": listed["proof"],
            "gate_reachable": sum(listed.values()) >= ig.MIN_N,
            "candidates": ig.calibrate([p for _, p in labels], {"face_eye.cel": cel, "eye_judge": ig.eye_judge_reads})}


# ---- the run -----------------------------------------------------------------------------------------

def default_box() -> Path:
    """A fresh sandbox on the NVMe (never the D: spinning disk), one per run."""
    import tempfile
    base = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / "Temp" / "visurena_rehearsal"
    return base / f"face_replay_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def prepare(book: Path, number: int, box: Path) -> SimpleNamespace:
    """Everything read off the real episode BEFORE the fence: the sandbox, the recordings, its record."""
    home = episode_home.home(book, number)
    box_book, restored = build(book, number, box)
    cutoff = master_time(home, ITER1)
    return SimpleNamespace(home=home, box=Path(box), book=box_book, number=number, restored=restored, cutoff=cutoff,
                           iter3=master_time(home, ITER3), real=fr_rows.read_json(home / ROOM / "refine.json", {}),
                           recorded=refine_recordings(home, Path(book).parent), draws=recorded_draws(home, cutoff))


def standing_doc(room: Path, doc: dict) -> dict:
    """The refine entries that decided the CURRENT take bytes (face_refine.standing): what step 10 pastes."""
    from studio import face_refine as fr
    return {k: e for k, e in takes_of(doc) if fr.standing(e, sha8(Path(room) / f"{k}.mp4"))}


def replay_outside(w: SimpleNamespace, doc: dict) -> dict:
    """Step 10's paste of the replay's own accepted crops, on the sandbox's cut."""
    box_home = episode_home.home(w.book, w.number)
    pasted = {int(k[1:]) for k, e in standing_doc(box_home / ROOM, doc).items() if any(p.get("kept") for p in e.get("people") or [])}
    if not pasted:
        return {}
    work = sandbox_cut(w.home, box_home, pasted, aspect_of(w.home))
    return step10_outside(work, box_home / ROOM, aspect_of(w.home))


def on_record(w: SimpleNamespace) -> dict:
    """The same paste and eye measures on the episode's OWN recorded cut (read only): the invariant over
    real crops even when the replay accepted none."""
    room = Path(w.home) / ROOM
    return {"recorded_outside": outside_summary(step10_outside(Path(w.home) / WORK, room, aspect_of(w.home))),
            "recorded_noise": noise_summary(eye_noise(room, standing_doc(room, w.real)))}


def decisions(w: SimpleNamespace, doc: dict) -> dict:
    """The replay's decisions against the repair's (status and selection)."""
    repair = repair_decided(w.home, w.real)
    return {"agreement": agreement_with_repair(doc, repair, w.restored),
            "selection": fr_rows.selection_agreement(doc, repair, sorted(repair))}


def summarize(w: SimpleNamespace, ran: dict, ctx: Ctx) -> dict:
    """The replay's evidence: rows, the kill, agreement, the outside invariant, noise, SR-1, the engine log."""
    room = episode_home.home(w.book, w.number) / ROOM
    doc, cards, log = fr_rows.read_json(room / "refine.json", {}), fr_rows.read_json(room / "prompts.json", []), answers(w.box)
    pasted, first = replay_outside(w, doc), log[:ran["first_requests"]]
    iter1, iter3 = iter1_decided(w.real, w.cutoff, w.restored), decided_in(w.real, 0.0, w.iter3)
    return {"episode": episode_home.home(Path(w.home).parents[1].name, w.number).as_posix(), "sandbox": str(w.box),
            "readers": READERS, "restored": w.restored, "iter1_restore": manifest_check(w.home, w.restored),
            "step09": ran, "rung_served": ctx.served, "faces": face_table(cards, doc, iter1, iter3, log, pasted),
            "engine_log": log, "engine_clock": engine_clock(doc, log), "kill": fr_rows.kill([e["match"] for e in first]),
            **decisions(w, doc), "outside": outside_summary(pasted), "noise": noise_summary(eye_noise(room, doc)),
            **on_record(w), "log": ctx.lines,
            "sr1": fr_rows.sr1_estimate(fr_rows.sr1_inputs(doc, w.real), sorted({e["stem"][:3] for e in first if e["stem"]}))}


def replay(book: Path, number: int, box: Path, readers=None, roots=None, review: Path | None = None) -> dict:
    """DESIGN 4.1 end to end: the sandbox, the fake engine, the fence, the real face path, the rows."""
    w = prepare(book, number, box)
    ctx = Ctx(w.book, number, w.draws)
    with aimed(start_engine(w.box, w.recorded)) as fake:
        arm(w.box, roots, ports=(fake.port,))
        try:
            ran = step09(w.book, number, readers or cpu_readers(), ctx, lambda: len(answers(w.box)))
            said = summarize(w, ran, ctx)
        finally:
            fake.stop()
    gate = instrument(w.home, review)["candidates"]["face_eye.cel"]
    said = {**said, "faces": ig.stamp(said["faces"], gate), "instrument": gate}
    return {**said, "proof_rows": proof_rows(said, gate)}


def panel(home: Path) -> dict:
    """DESIGN 4.4 on one episode: every pair, the line, the pre-registered verdict, its proof row."""
    pairs = pts.episode_pairs(home)
    said = pts.verdict(pairs)
    row = ig.proof_row("panel_take_size", "Q3", said["passed"], said["n"], said["n"], ["results/panel_take_size.json"],
                       [], "panel_dq.face_h x 768 vs take_dq warp min_px", "n/a (not an eye measure)", "quality")
    return {"episode": Path(home).as_posix(), "pairs": pairs, "verdict": said, "proof_rows": [row]}


def instrument_report(home: Path, review: Path | None = None) -> dict:
    said = instrument(home, review)
    rows = [ig.proof_row(f"instrument_gate.{name}", "Q1", g["passed"], g["n"], g["n"], said["label_files"], [], name,
                         g["state"], "mechanism") for name, g in said["candidates"].items()]
    return {**said, "proof_rows": rows}


def options(argv: list[str]) -> dict:
    said = {"book": BOOK, "episode": "1"}
    said |= {a[2:].split("=", 1)[0]: a.split("=", 1)[1] for a in argv if a.startswith("--") and "=" in a}
    return said


def sr1_line(s: dict) -> str:
    """SR-1's estimate said with its standing: what was measured, and what is only a price."""
    unknown = ", ".join(s["unknown_takes"]) or "none"
    return (f"SR-1: {s['measured_s']} GPU s measured on {s['measured_takes']} takes, {s['priced_s']} s PRICED on "
            f"{s['priced_takes']} takes (face_refine.price, not a measurement); unknown: {unknown}")


def headline(cmd: str, doc: dict) -> str:
    if cmd == "panel":
        v = doc["verdict"]
        return f"panel->take: n={v['n']} R^2={v.get('r2')} {'PASS' if v['passed'] else 'KILL: ' + '; '.join(v['kill'])}"
    if cmd == "instrument":
        return "; ".join(f"{n}: {g['agree']}/{g['n']} LB {g['lower']} {g['state']}" for n, g in doc["candidates"].items())
    k, a, o, sel, rec = doc["kill"], doc["agreement"], doc["outside"], doc["selection"], doc["recorded_outside"]
    return (f"crops asked {k['requests']}: exact {k['exact']}, substituted {k['substituted']}, canned {k['canned']} "
            f"({k['share']:.0%} not exact) -> {'Q1/Q2 REAL-RUN (kill)' if k['real_run'] else 'kill not fired'}; "
            f"selection {sel['agree']}/{sel['n']}, status {a['agree']}/{a['n']} vs the repair; outside moved "
            f"{o['moved']}/{o['pastes']} replay, {rec['moved']}/{rec['pastes']} recorded; {sr1_line(doc['sr1'])}; "
            f"eye {doc['instrument']['state']}")


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv and not argv[0].startswith("--") else "replay"
    o = options(argv)
    book, number = episode_home.book_dir(o["book"]), int(o["episode"])
    home = episode_home.home(book, number)
    if cmd == "panel":
        name, doc = "panel_take_size.json", panel(home)
    elif cmd == "instrument":
        print(stage_labels(home / ROOM, REVIEW))
        name, doc = "instrument_gate.json", instrument_report(home, REVIEW)
    else:
        name, doc = "face_rows.json", replay(book, number, Path(o.get("box") or default_box()), review=REVIEW)
    print(write_result(name, doc, Path(o.get("out") or RESULTS)))
    print(headline(cmd, doc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
