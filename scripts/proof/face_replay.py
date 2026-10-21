#!/usr/bin/env python
"""The face path on a delivered episode as a FIRST pass (2026-10-21_ep02_proof DESIGN 4.1, P6).

    uv run --no-sync python scripts/proof/face_replay.py [--book=<codex>] [--episode=1] [--box=<dir>]
    uv run --no-sync python scripts/proof/face_replay.py panel [--book=<codex>] [--episode=1]
    uv run --no-sync python scripts/proof/face_replay.py instrument [--book=<codex>] [--episode=1]

`replay` copies the episode's records into a sandbox on C: with every take AS IT WAS AT THE FIRST
MASTER (cut/master_iter1.mp4's own time; a take a later repair displaced is restored from
takes/r2v/attempts/), the first-pass attempts and ladder (no refine or tiny-face round), and NO
refine.json and NO repair window.  It then arms the write fence over the real roots and runs, in
process, the REAL step-09 face path -- face_refine.refine, step 09's face_list_note, tiny_face.rung,
the refine again on a kept draw, the face list again -- and the step-10 paste (face_paste.Paster with
an identity upscaler).  The engine answers a crop whose `_src` bytes match a recorded one with the
recorded render (`exact`); any other crop is `unrecorded`, served a canned grey render the gate
refuses, and counted, never guessed.  The tiny-face draw is the episode's own recorded draw when one
exists for that take, else the render "dies" (unrecorded).

Readers: facenet and the loose MTCNN on the CPU, the MTCNN finder, no CCIP reader.  That is the
production FALLBACK (face_detect.Finder and anime_id.Reader fall back to it when their worker fails):
both workers run on the portable python, which the rehearsal fence refuses (DESIGN 2.6); the real
workers' answers enter only through package P4's memos.  Every row says which readers ran.

Writes docs/audit/2026-10-21_ep02_proof/results/face_rows.json (`faces`: one row per (take, person);
the kill, agreement with the repair, the outside invariant, the SR-1 estimate, the noise band, proof rows).  `panel` writes
results/panel_take_size.json (DESIGN 4.4), `instrument` results/instrument_gate.json (4.2).  The real
library is only ever read; no GPU, no ComfyUI, no network."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
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
ROOM = Path("takes") / "r2v"
HOME_RECORDS = ("plan.json",)
ROOM_RECORDS = ("prompts.json", "shots.json")
READERS = "facenet cpu + loose MTCNN cpu + MTCNN finder (production fallback); CCIP/clip_h unread"
ITER1, ITER3 = "master_iter1.mp4", "master_iter3.mp4"
REPAIR_STEP = "09"


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
    home, box_book = episode_home.home(book, number), Path(box) / "library" / Path(book).name
    box_home = episode_home.home(box_book, number)
    (box_home / ROOM / "attempts").mkdir(parents=True, exist_ok=True)
    copy_named(home, box_home, [*HOME_RECORDS, *[(ROOM / n).as_posix() for n in ROOM_RECORDS],
                                *[(ROOM / p.name).as_posix() for p in sorted((home / ROOM).glob("T[0-9][0-9].content.json"))]])
    cards, cutoff = fr_rows.read_json(home / ROOM / "prompts.json", []), master_time(home, ITER1)
    copy_named(book, box_book, sheets_of(cards))
    first_pass_records(home, box_home, cutoff)
    restored = [restore_take(home / ROOM, box_home / ROOM, int(c["index"]), cutoff) for c in cards]
    return box_book, restored


# ---- the engine: recorded crops answer, anything else is unrecorded -----------------------------------

class RecordedEngine:
    """face_refine's engine seam (stage / submit / wait / span) answered from the episode's recorded
    crops by the sha256 of the staged `_src` bytes; every answer logged with its match class."""

    def __init__(self, out: Path, recorded: dict[str, Path]):
        self.out, self.recorded, self.staged, self.graphs, self.log = Path(out), recorded, {}, {}, []
        self.out.mkdir(parents=True, exist_ok=True)

    def stage(self, path: Path) -> str:
        self.staged[Path(path).name] = Path(path)
        return Path(path).name

    def submit(self, graph: dict) -> str:
        job = f"job{len(self.graphs) + 1}"
        src = next(self.staged[v] for v in staged_values(graph) if v in self.staged and v.endswith("_src.mp4"))
        hit = self.recorded.get(fr_rows.sha256_of(src))
        self.graphs[job] = (graph, src, hit)
        self.log.append({"job": job, "stem": src.name[:-len("_src.mp4")], "src_sha8": sha8(src),
                         "match": "exact" if hit else "unrecorded", "recorded": hit.name if hit else None})
        return job

    def wait(self, job: str) -> dict[str, list[Path]]:
        from studio import face_refine as fr
        graph, src, hit = self.graphs[job]
        out = self.out / f"{job}.mp4"
        shutil.copyfile(hit, out) if hit else canned(src, out)
        return {fr.saved_node(graph): [out]}

    def span(self, _job: str) -> tuple[None, None]:
        """No engine clock: a replayed answer has no GPU second of its own."""
        return None, None


def staged_values(graph: dict) -> list[str]:
    return [v for node in graph.values() for v in (node.get("inputs") or {}).values() if isinstance(v, str)]


def canned(src: Path, out: Path) -> Path:
    """A grey render of the source's frames (DESIGN 2.4: a canned picture is grey, so the gate refuses it)."""
    import cv2
    cap = cv2.VideoCapture(str(src))
    n, side = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 768
    cap.release()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=gray:s={side}x{side}:r=24",
                    "-frames:v", str(max(n, 1)), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


# ---- the step context: a log, the learnings, the recorded tiny-face draw ------------------------------

class Ctx:
    """What the real step-09 functions are handed: the sandbox episode, a log, its learnings file, and
    `run_script` answering the tiny-face rung from the episode's own recorded draw and verdicts.  A draw
    the episode never made "dies" (SystemExit) before anything moves: unrecorded, never guessed."""

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
            raise SystemExit("unrecorded tiny-face draw: " + ", ".join(f"T{i:02d}" for i in missing))
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


def step09(book: Path, number: int, engine, readers, ctx: Ctx) -> dict:
    """The refine, the face list, the tiny-face rung, the refine of a kept draw, the face list again."""
    from scripts.episode import face_refine as cli, step_09_shoot as s09, tiny_face
    loose, detect, embed, find = readers
    kw = dict(engine=engine, detect=detect, loose=loose, embed=embed, find=find, anime=None)
    first = cli.refine(book, number, None, **kw)
    asked = len(engine.log)
    s09.face_list_note(ctx)
    try:
        kept, rung = tiny_face.rung(ctx, "", recorded_judge, ()), "ran"
    except SystemExit as died:
        kept, rung = [], f"died: {died}"
    second = cli.refine(book, number, kept, **kw) if kept else {}
    s09.face_list_note(ctx)
    return {"first": sorted(first), "first_requests": asked, "rung": rung, "kept_draws": kept, "second": sorted(second)}


def arm(box: Path, roots=None) -> None:
    """The write fence over the real roots (DESIGN 2.6), armed in this process before any step runs."""
    from studio.rehearsal import fence
    fence.install(fence.Fence.of(roots if roots is not None else settings.todays_real_roots(), box, settings.REPO))


# ---- the step-10 paste: nothing outside the face core may move ----------------------------------------

def allowed_core(shape: tuple, track, t: int):
    """Where the paste may change take frame t: inside the face core's outline, as the Paster places it."""
    import numpy as np
    from studio import face_paste as fp
    h, w = shape[:2]
    box = fp.box_at(track.windows[t], None, w, h, 1)
    x, y, s = placed = fp.to_master(track.windows[t], None, w, h, 1)
    cx, cy, face = fp.face_in_patch(fp.face_at(track, t), box, placed)
    core, out = fp.core_radius(s, face, (cx, cy)) < 1.0, np.zeros((h, w), bool)
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + s, w), min(y + s, h)
    if x0 < x1 and y0 < y1:
        out[y0:y1, x0:x1] = core[y0 - y:y1 - y, x0 - x:x1 - x]
    return out


def paste_outside(frames: list, track) -> float:
    """The largest share of pixels outside the core one track's paste moved on any frame (the step-10
    Paster, identity upscaler, factor 1, the take's own frames)."""
    from studio import face_paste as fp
    h, w = frames[0].shape[:2]
    paster = fp.Paster(lambda f: f, [fp.Span(0, 0, len(frames), 0, 1.0, None, (track,))], w, h, 1)
    worst = 0.0
    for t, frame in enumerate(frames):
        after = paster(frame)
        if fp.fade(t, track.life) > 0 and t < len(track.windows):
            worst = max(worst, fr_rows.outside_moved(frame, after, allowed_core(frame.shape, track, t)))
    return worst


def pastes(room: Path, doc: dict) -> dict[tuple, float]:
    """(take, who) -> outside share, for every accepted crop of the replay."""
    from scripts.episode import face_refine as cli
    from studio import face_paste as fp
    out = {}
    for take, entry in sorted((k, v) for k, v in doc.items() if k[:1] == "T" and k[1:].isdigit()):
        kept = [p for p in entry.get("people") or [] if p.get("kept")]
        frames = cli.read_frames(Path(room) / f"{take}.mp4") if kept else []
        for p in kept:
            (track,) = fp.kept_tracks({"people": [p]}, room)
            out[(take, p["who"])] = round(paste_outside(frames, track), 6)
    return out


# ---- the eye measure's own noise ---------------------------------------------------------------------

def crop_eyes(frames: list, doc: dict, ks: list[int]) -> list[float]:
    """The drawn-eye score at crop frames `ks`, each read at the run's recorded face box."""
    from studio import face_eye
    faces, side, out = doc.get("faces") or [], frames[0].shape[0], []
    for k in ks:
        t = int(doc["start"]) + k
        if 0 <= k < len(frames) and t < len(faces) and faces[t]:
            cx, cy, fh = (float(v) * side for v in faces[t])
            out.append(face_eye.eye_score(face_eye.face_gray(frames[k], (cx - fh / 2, cy - fh / 2, cx + fh / 2, cy + fh / 2))))
    return out


def eye_noise(room: Path, doc: dict) -> dict[tuple, dict]:
    """(take, who) -> the eye measure's band on its accepted crop: read twice, and one frame either way."""
    import numpy as np
    from scripts.episode import face_refine as cli
    out = {}
    for take, entry in sorted((k, v) for k, v in doc.items() if k[:1] == "T" and k[1:].isdigit()):
        for p in (p for p in entry.get("people") or [] if p.get("kept")):
            track, frames = fr_rows.read_json(Path(room) / p["track"], {}), cli.read_frames(Path(room) / p["crop"])
            life, start = track["life"], int(track["start"])
            ks = sorted({int(v) for v in np.linspace(max(1, life[0] - start), max(1, min(life[1] - start, len(frames) - 2)), 6)})
            base = crop_eyes(frames, track, ks)
            out[(take, p["who"])] = fr_rows.noise_band(base, crop_eyes(frames, track, ks),
                                                       crop_eyes(frames, track, [k + 1 for k in ks]),
                                                       crop_eyes(frames, track, [k - 1 for k in ks]))
    return out


# ---- what the real episode decided, and when ---------------------------------------------------------

def decided_in(doc: dict, start: float, stop: float) -> dict:
    """The take entries of a refine.json whose `decided` stamp (local time) falls in [start, stop]."""
    out = {}
    for key, entry in doc.items():
        if key[:1] == "T" and key[1:].isdigit() and entry.get("decided"):
            if start <= datetime.fromisoformat(entry["decided"]).timestamp() <= stop:
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
    """(take, who) -> the match class of the LAST crop asked for that person (a kept draw is asked again)."""
    by_crop = {p.get("crop"): (take, p.get("who")) for take, e in doc.items() if take[:1] == "T"
               for p in e.get("people") or []}
    return {by_crop[f"refine/{e['stem']}.mp4"]: e["match"] for e in log if f"refine/{e['stem']}.mp4" in by_crop}


def face_table(cards: list[dict], doc: dict, iter1: dict, iter3: dict, log: list[dict], pasted: dict) -> list[dict]:
    """Every take's rows (face_rows.take_rows), the readers named on each."""
    selected = {int(k[1:]) for k in doc if k[:1] == "T" and k[1:].isdigit()}
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


def outside_summary(pasted: dict) -> dict:
    moved = {f"{t} {w}": v for (t, w), v in pasted.items() if v > 0}
    return {"pastes": len(pasted), "moved": len(moved), "worst": max(pasted.values(), default=0.0), "which": moved}


def noise_summary(noise: dict) -> dict:
    return {"crops": len(noise), "repeat_max": max((b["repeat"] for b in noise.values()), default=None),
            "shift_max": max((b["shift"] for b in noise.values()), default=None),
            "by_crop": {f"{t} {w}": b for (t, w), b in noise.items()}}


def cel_score(path: Path) -> float | None:
    """face_eye's cel score of one strip crop, the whole crop read as the face box."""
    import numpy as np
    from PIL import Image
    from studio import face_eye
    if not Path(path).is_file():
        return None
    rgb = np.asarray(Image.open(path).convert("RGB"))
    return face_eye.eye_score(face_eye.face_gray(rgb, (0, 0, rgb.shape[1], rgb.shape[0])))


def instrument(home: Path) -> dict:
    """The gate on both candidates over the episode's owner label files (review/face_labels_<sha8>.json)."""
    labels = sorted((Path(home) / "review").glob("face_labels_*.json"))
    cel = lambda doc, folder: ig.cel_reads(doc, folder, cel_score)  # noqa: E731
    return {"label_files": [p.name for p in labels], "candidates": ig.calibrate(labels, {"face_eye.cel": cel,
                                                                                         "eye_judge": ig.eye_judge_reads})}


def proof_rows(s: dict, gate: dict) -> list[dict]:
    """The DESIGN 5 rows of the face replay, under the check ids scripts/proof/questions.yaml names."""
    k, a, o, ev = s["kill"], s["agreement"], s["outside"], ["results/face_rows.json"]
    classes = {"exact": k["requests"] - k["unrecorded"], "unrecorded": k["unrecorded"]}
    sel, rec, both = s["selection"], s["recorded_outside"], o["pastes"] + s["recorded_outside"]["pastes"]
    return [ig.proof_row("unrecorded_le_half", "Q1", not k["real_run"], k["requests"], k["requests"], ev, classes,
                         "", "n/a", "mechanism"),
            ig.proof_row("face_replay.selection_agreement", "Q1", sel["agree"] == sel["n"], sel["n"], sel["n"], ev, {},
                         READERS, "n/a", "mechanism"),
            ig.proof_row("refine_decision_recall", "Q1", a["agree"] == a["n"], a["n"], a["n"], ev, classes,
                         "", "n/a (a decision on an unrecorded crop rests on a canned render)", "mechanism"),
            ig.proof_row("outside_invariant", "Q1", o["moved"] + rec["moved"] == 0, both, both, ev,
                         {"replay": o["pastes"], "recorded": rec["pastes"]}, "face_paste.Paster", "n/a", "mechanism"),
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
                           recorded=fr_rows.recorded_crops(home / ROOM / "refine"), draws=recorded_draws(home, cutoff))


def summarize(w: SimpleNamespace, ran: dict, engine: RecordedEngine, ctx: Ctx) -> dict:
    """The replay's evidence: rows, the kill, agreement, the outside invariant, noise, SR-1, the log."""
    room = episode_home.home(w.book, w.number) / ROOM
    doc, cards = fr_rows.read_json(room / "refine.json", {}), fr_rows.read_json(room / "prompts.json", [])
    pasted, first, repair = pastes(room, doc), engine.log[:ran["first_requests"]], repair_decided(w.home, w.real)
    iter1, iter3 = iter1_decided(w.real, w.cutoff, w.restored), decided_in(w.real, 0.0, w.iter3)
    return {"episode": episode_home.home(Path(w.home).parents[1].name, w.number).as_posix(), "sandbox": str(w.box),
            "readers": READERS, "restored": w.restored, "step09": ran, "rung_served": ctx.served,
            "faces": face_table(cards, doc, iter1, iter3, engine.log, pasted), "engine_log": engine.log,
            "kill": fr_rows.kill([e["match"] for e in first]),
            "agreement": agreement_with_repair(doc, repair, w.restored),
            "selection": fr_rows.selection_agreement(doc, repair, sorted(repair)),
            "outside": outside_summary(pasted), "noise": noise_summary(eye_noise(room, doc)), **on_record(w),
            "sr1": fr_rows.sr1_estimate(fr_rows.sr1_inputs(doc, w.real), sorted({e["stem"][:3] for e in first})),
            "log": ctx.lines}


def standing_doc(room: Path, doc: dict) -> dict:
    """The refine entries that decided the CURRENT take bytes (face_refine.standing): what step 10 pastes."""
    from studio import face_refine as fr
    return {k: e for k, e in doc.items() if k[:1] == "T" and k[1:].isdigit() and fr.standing(e, sha8(Path(room) / f"{k}.mp4"))}


def on_record(w: SimpleNamespace) -> dict:
    """The same paste and eye measures on the episode's OWN recorded pastes (read only): the invariant
    over real crops even when the replay accepted none."""
    room = Path(w.home) / ROOM
    doc = standing_doc(room, w.real)
    return {"recorded_outside": outside_summary(pastes(room, doc)), "recorded_noise": noise_summary(eye_noise(room, doc))}


def replay(book: Path, number: int, box: Path, readers=None, roots=None) -> dict:
    """DESIGN 4.1 end to end: the sandbox, the fence, the real face path, the rows, the instrument's state."""
    w = prepare(book, number, box)
    arm(w.box, roots)
    engine, ctx = RecordedEngine(w.box / "comfy" / "output", w.recorded), Ctx(w.book, number, w.draws)
    ran = step09(w.book, number, engine, readers or cpu_readers(), ctx)
    said = summarize(w, ran, engine, ctx)
    gate = instrument(w.home)["candidates"]["face_eye.cel"]
    said = {**said, "faces": ig.stamp(said["faces"], gate), "instrument": gate}
    return {**said, "proof_rows": proof_rows(said, gate)}


def panel(home: Path) -> dict:
    """DESIGN 4.4 on one episode: every pair, the line, the pre-registered verdict, its proof row."""
    pairs = pts.episode_pairs(home)
    said = pts.verdict(pairs)
    row = ig.proof_row("panel_take_size", "Q3", said["passed"], said["n"], said["n"], ["results/panel_take_size.json"],
                       [], "panel_dq.face_h x 768 vs take_dq warp min_px", "n/a (not an eye measure)", "quality")
    return {"episode": Path(home).as_posix(), "pairs": pairs, "verdict": said, "proof_rows": [row]}


def instrument_report(home: Path) -> dict:
    said = instrument(home)
    rows = [ig.proof_row(f"instrument_gate.{name}", "Q1", g["passed"], g["n"], g["n"], said["label_files"], [], name,
                         g["state"], "mechanism") for name, g in said["candidates"].items()]
    return {**said, "proof_rows": rows}


def options(argv: list[str]) -> dict:
    said = {"book": BOOK, "episode": "1"}
    said |= {a[2:].split("=", 1)[0]: a.split("=", 1)[1] for a in argv if a.startswith("--") and "=" in a}
    return said


def headline(cmd: str, doc: dict) -> str:
    if cmd == "panel":
        v = doc["verdict"]
        return f"panel->take: n={v['n']} R^2={v.get('r2')} {'PASS' if v['passed'] else 'KILL: ' + '; '.join(v['kill'])}"
    if cmd == "instrument":
        return "; ".join(f"{n}: {g['agree']}/{g['n']} LB {g['lower']} {g['state']}" for n, g in doc["candidates"].items())
    k, a, o, sel, rec = doc["kill"], doc["agreement"], doc["outside"], doc["selection"], doc["recorded_outside"]
    return (f"crops asked {k['requests']}, unrecorded {k['unrecorded']} ({k['share']:.0%}) -> "
            f"{'Q1/Q2 REAL-RUN (kill)' if k['real_run'] else 'kill not fired'}; selection {sel['agree']}/{sel['n']}, "
            f"status {a['agree']}/{a['n']} vs the repair; outside moved {o['moved']}/{o['pastes']} replay, "
            f"{rec['moved']}/{rec['pastes']} recorded; SR-1 ~{doc['sr1']['estimate_s']} GPU s priced; "
            f"eye {doc['instrument']['state']}")


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv and not argv[0].startswith("--") else "replay"
    o = options(argv)
    book, number = episode_home.book_dir(o["book"]), int(o["episode"])
    if cmd == "panel":
        name, doc = "panel_take_size.json", panel(episode_home.home(book, number))
    elif cmd == "instrument":
        name, doc = "instrument_gate.json", instrument_report(episode_home.home(book, number))
    else:
        name, doc = "face_rows.json", replay(book, number, Path(o.get("box") or default_box()))
    print(write_result(name, doc, Path(o.get("out") or RESULTS)))
    print(headline(cmd, doc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
