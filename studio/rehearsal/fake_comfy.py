"""A fake ComfyUI for rehearsals: a real HTTP server on 127.0.0.1:<port> that answers the REAL
studio.comfy client from recordings, and labels every answer with how good the match was
(2026-10-21_ep02_proof DESIGN 2.2, package P3).

Routes: POST /prompt, GET /history[/<id>], GET and POST /queue, GET /system_stats, POST /free,
POST /interrupt, GET /internal/logs/raw.  A submitted graph is identified by its workflow
fingerprint (workflow_fingerprint), then answered by the first of:

  exact        a recording of the same workflow with the same fields (or, for a recording that
               carries `values`, the same values at every inject point it names)
  substituted  same workflow, and: for a take the SAME index and try count, trimmed or looped
               with ffmpeg to the asked frames; for TTS the same voice (every inject value but
               the line's own text, seed and prefix), atempo-stretched by the text's length;
               for a grid the same cell count
  canned       nothing matched: a grey picture, a grey video, a silent wav, or CANNED_TEXT,
               which every studio reader's readable() refuses (2.4: canned answers REFUSE)

A job's KIND comes from the workflow it was filled from, never from a recording that happens to
join it: a recording that names that workflow says it; a face-refine workflow (studio/face_refine.
WORKFLOW, or a new technique named after it) is a refine_crop with no take index; any other video
output is a take; anything else takes the first joined recording's kind or its output's.  Only
recordings of that kind may answer.  A take recording joins by its bare class multiset, or by the
template it was identified as (its recorded graph, else P2's section-0 class set), so a take graph
that grew nodes still meets its recording.

A take's try count is how many DISTINCT graphs of that index this engine was asked before (an
identical resubmission is the same try).  Recorded outputs are opened for READ and copied into
<sandbox>/comfy/output/<prefix>_<00001>_.<ext>.  /history spaces execution_start and
execution_success by the recording's seconds; the record carries `rehearsal: {clock: recorded}`
and so does its engine_log row: such a clock is never evidence for a time question (R15).
Every answer writes one row to <sandbox>/engine_log.jsonl; each start writes a header whose
`shape` is `uncalibrated` until the SR-5 transcript exists (R12).

A recording is `{kind, workflow_fp, key, tries, fields | graph | values, path, seconds, source}`
(P2's recordings index; `fields` as workflow_fingerprint.graph_fields gives them, or `graph`, the
recorded graph's file, from which they are computed).  Faults: comfy_faults."""
from __future__ import annotations

import hashlib
import json
import posixpath
import re
import shutil
import socket
import struct
import subprocess
import threading
import time
import urllib.request
import uuid
import wave
import zlib
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from studio.rehearsal import comfy_faults
from studio.rehearsal import workflow_fingerprint as wf

REPO = Path(__file__).resolve().parents[2]
TRANSCRIPT = REPO / "tests" / "fixtures" / "proof" / "comfy_transcript"
CONTRACT_ROUTES = ("post_prompt", "get_history", "history_execution_error", "get_queue", "get_system_stats",
                   "post_free", "post_interrupt", "get_internal_logs_raw")
"""One recorded pair per route the studio uses, plus one execution_error (R12, SR-5)."""
REAL_ENGINE_PORT = 8188
CANNED_TEXT = "[rehearsal canned reply: no recording matched this read]"
LINE_FIELDS = frozenset({"text", "target_text", "seed", "filename_prefix", "max_new_tokens"})
"""The TTS inject values that belong to the line, not the voice."""
OUTPUTS = {"SaveImage": ("images", "png"), "SaveVideo": ("images", "mp4"), "SaveWEBM": ("images", "webm"),
           "VHS_VideoCombine": ("gifs", "mp4"), "SaveAudio": ("audio", "wav"), "SaveAudioMP3": ("audio", "mp3"),
           "SaveAudioOpus": ("audio", "opus"), "PreviewAny": ("text", None)}
KIND_OF_OUTPUT = {"text": "vl_text", "mp4": "take", "webm": "take", "wav": "tts_line", "mp3": "tts_line",
                  "opus": "tts_line", "png": "picture"}
VIDEO = ("mp4", "webm", "mov", "mkv")
AUDIO = ("wav", "flac", "mp3", "opus")
RING = 300
DROP = object()
ADMIN_RESTART = "/rehearsal/restart"
"""The fake's one route the real engine lacks: engine_ops.restart from a drive child reaches the
harness's fake here, and it answers even while the engine is down or lost."""
_LIVE: dict[int, "FakeComfy"] = {}
"""port -> the fake this process serves (a drive child holds none and goes over HTTP)."""
SYSTEM_STATS = {"system": {"os": "win32", "ram_total": 68719476736, "ram_free": 34359738368,
                           "comfyui_version": "rehearsal-fake", "required_frontend_version": "",
                           "installed_templates_version": "", "required_templates_version": "",
                           "comfy_package_versions": [{"name": "rehearsal-fake", "installed": "", "required": ""}],
                           "python_version": "3.12.9", "pytorch_version": "none", "embedded_python": False,
                           "deploy_environment": "rehearsal-fake", "argv": ["main.py", "--rehearsal-fake"]},
                "devices": [{"name": "rehearsal fake (no GPU)", "type": "cpu", "index": 0,
                             "vram_total": 0, "vram_free": 0, "torch_vram_total": 0, "torch_vram_free": 0}]}


# ---- small pure helpers -------------------------------------------------------------------

def free_port() -> int:
    """A loopback port no one holds now (never the real engine's)."""
    while True:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        if port != REAL_ENGINE_PORT:
            return port


def shape_state(transcript: Path | None = None) -> str:
    """`calibrated` when a full SR-5 transcript (every contract route) exists, else `uncalibrated`."""
    folder = Path(transcript or TRANSCRIPT)
    return "calibrated" if all((folder / f"{k}.json").is_file() for k in CONTRACT_ROUTES) else "uncalibrated"


def now_ms() -> int:
    return int(time.time() * 1000)


def stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def listed(value) -> list:
    return [] if value is None else list(value) if isinstance(value, (list, tuple)) else [value]


def resolve(folder: Path, value):
    """A recording path (or list of them) made absolute against its index's folder."""
    if isinstance(value, list):
        return [resolve(folder, v) for v in value]
    return str(folder / value) if value and not Path(value).is_absolute() else value


def load_recordings(path: Path, root: Path | None = None) -> list[dict]:
    """The recordings index (P2's {entries: [...]}, {recordings: [...]} or a list), its relative
    paths resolved against `root` (P2 writes them relative to the library root) or the index's folder."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    rows = (doc.get("entries") or doc.get("recordings") or []) if isinstance(doc, dict) else doc
    base = Path(root) if root else path.parent
    return [{**r, "path": resolve(base, r.get("path")), "graph": resolve(base, r.get("graph")),
             "source_graph": resolve(base, source_graph(r))} for r in rows]


def source_graph(rec: dict) -> str | None:
    """The recorded graph file P2's take entry names as its `source` (`.../T05.graph.json`)."""
    source = rec.get("source")
    return source if isinstance(source, str) and source.endswith(".graph.json") else None


def refine_workflows() -> tuple[str, ...]:
    """The face-refine workflow the studio submits (studio/face_refine.WORKFLOW)."""
    try:
        from studio import face_refine
    except ImportError:
        return ()
    return (face_refine.WORKFLOW,)


def is_refine(name: str | None, refine: tuple[str, ...]) -> bool:
    """A refine workflow, or a new technique named after one (`<base>_<source>`)."""
    return bool(name) and any(name == w or name.startswith(w + "_") for w in refine)


def prompt_graph(body: bytes) -> dict:
    """The graph a POST /prompt carries; ValueError (the engine's 400) when it is not one."""
    try:
        doc = json.loads(body or b"{}")
    except ValueError as err:
        raise ValueError(f"the body is not JSON: {err}") from None
    graph = doc.get("prompt") if isinstance(doc, dict) else None
    if not isinstance(graph, dict) or not graph:
        raise ValueError("the body carries no `prompt` graph")
    return graph


def take_index(values: dict) -> int | None:
    """The take number a graph renders: the digits ending its filename_prefix (`ep_take_05`)."""
    hit = re.search(r"(\d+)$", str(values.get("filename_prefix") or ""))
    return int(hit.group(1)) if hit else None


def voice_of(values: dict) -> dict:
    return {k: v for k, v in values.items() if k not in LINE_FIELDS}


def line_text(values: dict) -> str:
    return str(values.get("target_text") or values.get("text") or "")


def sha_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fields_hash(fields: dict) -> str:
    return hashlib.sha256(json.dumps(fields, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def output_nodes(graph: dict) -> list[tuple[str, str, str | None]]:
    """(node id, history slot, extension) of EVERY node the engine reports outputs for: on v0.41.2
    a Krea2 sheet reports its SaveImage and its PreviewAny (GPU transcript, krea2_sheet)."""
    return [(str(n), *OUTPUTS[cls]) for n in sorted(graph, key=str)
            if (cls := (graph[n] or {}).get("class_type", "")) in OUTPUTS]


def output_node(graph: dict) -> tuple[str | None, str | None, str | None]:
    """The node whose answer the job is: the first media output, else the first text one."""
    nodes = output_nodes(graph)
    return next((n for n in nodes if n[2]), nodes[0] if nodes else (None, None, None))


def video_metadata(path: Path) -> dict:
    import cv2
    cap = cv2.VideoCapture(str(path))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    fps, frames = video_info(path)
    return {"kind": "video", "width": w, "height": h, "duration": frames / fps if fps else 0.0, "fps": fps,
            "frame_count": frames}


def image_metadata(path: Path) -> dict | None:
    import cv2
    frame = cv2.imread(str(path))
    return None if frame is None else {"kind": "image", "width": int(frame.shape[1]), "height": int(frame.shape[0])}


def media_metadata(path: Path) -> dict | None:
    """The `metadata` v0.41.2 puts on an output item: size for a picture, size, fps, frames and
    duration for a video (GPU transcript); None for audio, whose real form is unrecorded."""
    ext = Path(path).suffix.lower().lstrip(".")
    if ext in VIDEO:
        return video_metadata(path)
    return image_metadata(path) if ext in ("png", "jpg", "jpeg", "webp") else None


# ---- media: read the recording, write the sandbox ----------------------------------------

def ffmpeg() -> str:
    """The pinned imageio-ffmpeg binary (comfy_faults.ffmpeg), never whatever PATH holds."""
    return comfy_faults.ffmpeg()


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run([ffmpeg(), "-y", "-v", "error", *args], check=True, capture_output=True)


def copy_read_only(src: Path, dest: Path) -> None:
    """The recording opened for READ, its bytes written into the sandbox."""
    with open(src, "rb") as got, open(dest, "wb") as out:
        shutil.copyfileobj(got, out)


def video_info(path: Path) -> tuple[float, int]:
    """(fps, decoded frame count); (0.0, 0) for a file no decoder opens."""
    import cv2
    cap = cv2.VideoCapture(str(path))
    try:
        if not cap.isOpened():
            return 0.0, 0
        fps, frames = float(cap.get(cv2.CAP_PROP_FPS) or 0.0), 0
        while cap.read()[0]:
            frames += 1
        return fps, frames
    finally:
        cap.release()


def fit_frames(src: Path, dest: Path, frames: int) -> None:
    """The recorded take trimmed, or looped, to exactly `frames` frames (audio kept, cut to match)."""
    fps = round(video_info(src)[0] or 24.0, 3)
    run_ffmpeg(["-stream_loop", "-1", "-i", str(src), "-vf", f"setpts=N/{fps}/TB", "-af", "asetpts=N/SR/TB",
                "-r", str(fps), "-frames:v", str(frames), "-shortest",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(dest)])


def tempo_chain(tempo: float) -> str:
    """`atempo` filters whose product is `tempo`, each inside ffmpeg's 0.5-2.0 band."""
    tempo, parts = min(4.0, max(0.25, tempo)), []
    while tempo < 0.5 or tempo > 2.0:
        step = 0.5 if tempo < 0.5 else 2.0
        parts.append(step)
        tempo /= step
    return ",".join(f"atempo={p:.5f}" for p in [*parts, tempo])


def stretch_wav(src: Path, dest: Path, tempo: float) -> None:
    run_ffmpeg(["-i", str(src), "-filter:a", tempo_chain(tempo), str(dest)])


def grey_png(path: Path, size: int = 64) -> None:
    """A flat mid-grey RGB PNG, written with the standard library only."""
    row = b"\x00" + b"\x80" * (size * 3)
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    body = chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(row * size)) + chunk(b"IEND", b"")
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + body)


def grey_video(path: Path, frames: int, fps: int = 24, size: tuple = (64, 64)) -> None:
    """A flat grey clip of `frames` frames at `size` (w, h) with a silent audio stream (a take always has one)."""
    run_ffmpeg(["-f", "lavfi", "-i", f"color=c=gray:size={size[0]}x{size[1]}:rate={fps}", "-f", "lavfi", "-i",
                "anullsrc=r=16000:cl=mono", "-frames:v", str(frames), "-t", f"{frames / fps:.4f}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path)])


def silent_wav(path: Path, seconds: float = 1.0, rate: int = 16000) -> None:
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1), out.setsampwidth(2), out.setframerate(rate)
        out.writeframes(b"\x00\x00" * int(seconds * rate))


def asked_size(values: dict) -> tuple[int, int] | None:
    """The (width, height) a graph asks for at its inject points, or None when it names neither."""
    w, h = values.get("width"), values.get("height")
    return (int(w), int(h)) if isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0 else None


def canned_media(path: Path, ext: str, frames: int | None, size: tuple | None = None) -> None:
    """Grey media the readers refuse; a video at the graph's asked (width, height), as the engine renders."""
    if ext in VIDEO:
        grey_video(path, int(frames or 24), size=size or (64, 64))
    elif ext in AUDIO:
        silent_wav(path)
    else:
        grey_png(path)


def grey(path: Path) -> bool:
    """Whether a picture, or a video's first frame, is one flat grey."""
    import cv2
    path = Path(path)
    if path.suffix.lower().lstrip(".") in VIDEO:
        ok, frame = cv2.VideoCapture(str(path)).read()
    else:
        frame = cv2.imread(str(path))
        ok = frame is not None
    return bool(ok) and float(frame.std()) < 2.0 and 100 <= float(frame.mean()) <= 160


def silent(path: Path) -> bool:
    with wave.open(str(path), "rb") as got:
        return not any(got.readframes(got.getnframes()))


# ---- a match: which recording answers, and how ------------------------------------------

@dataclass
class Match:
    cls: str
    kind: str | None
    rec: dict | None = None
    tries: int | None = None
    index: int | None = None
    diff: list | None = None
    speaker: str | None = None


@dataclass
class Job:
    pid: str
    number: int
    graph: dict
    name: str | None
    values: dict
    started_ms: int
    ready_at: float
    record: dict = field(default_factory=dict)
    hang: bool = False
    partial: bool = False


JOINS = {"text": ("vl_text",), "mp4": ("take", "refine_crop"), "webm": ("take", "refine_crop"),
         "png": ("grid", "place", "refine_crop", "picture"), "wav": ("tts_line",), "mp3": ("tts_line",),
         "opus": ("tts_line",)}
"""Which recording kinds a job of each output may be answered from when the recording carries no
`workflow_fp` (P2's grids, places, lines and VL reads) and names no workflow."""
MAX_SUBSETS = 10
"""text_keys tries every subset of the inject values that equal the template's: at most 2**10."""


def text_sha(text) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def cells_from_name(name: str | None) -> int | None:
    """A storyboard workflow's cell count from its name (`..._3x3` -> 9)."""
    hit = re.search(r"(\d+)x(\d+)", name or "")
    return int(hit.group(1)) * int(hit.group(2)) if hit else None


def section0(graph: dict) -> dict | None:
    """The take fields P2's recordings index keys a take on (seed, frames, prompts, LoRAs, staged
    refs, node classes), from P2's own function; None when that module is absent."""
    try:
        from studio.rehearsal import recordings
    except ImportError:
        return None
    return recordings.graph_fields(graph)


def subsets(names: list[str]):
    names = names[:MAX_SUBSETS]
    for mask in range(1 << len(names)):
        yield [n for i, n in enumerate(names) if mask >> i & 1]


class Matcher:
    """Which recording answers a job, and how: exact, substituted or canned (module docstring)."""

    def __init__(self, idx: dict, inputs: Path, voices: dict | None = None, refine: tuple | None = None):
        self.idx, self.inputs, self.voices = idx, Path(inputs), dict(voices or {})
        self.refine = tuple(refine) if refine is not None else refine_workflows()
        self.recordings: list[dict] = []
        self.seen: dict[tuple, list[str]] = {}
        self._fields: dict[int, dict] = {}
        self._templates: dict[int, str | None] = {}

    def match(self, job: Job) -> Match:
        joined = self.candidates(job)
        kind = self.kind_of(job, joined)
        recs = [r for r in joined if r.get("kind") == kind]
        index = take_index(job.values) if kind == "take" else None
        tries = self.try_of(job, index) if kind == "take" else None
        exact = next((r for r in recs if self.exact(r, job)), None)
        rec = exact or self.substitute(kind, recs, job, index, tries)
        cls = "exact" if exact else "substituted" if rec else "canned"
        return Match(cls, kind, rec, tries, index, self.diff(kind, rec, recs, job, index),
                     self.speaker(job) if kind == "tts_line" else None)

    # ---- what the job is, and which recordings may answer it -----------------------------

    def kind_of(self, job: Job, recs: list[dict]) -> str | None:
        """The job's kind from the workflow it was filled from (module docstring), never from
        whichever recording joined first."""
        named = next((r.get("kind") for r in recs if job.name and (r.get("fields") or {}).get("workflow") == job.name),
                     None)
        ext = output_node(job.graph)[2] or "text"
        if named:
            return named
        if is_refine(job.name, self.refine):
            return "refine_crop"
        if ext in VIDEO:
            return "take"
        return recs[0]["kind"] if recs else KIND_OF_OUTPUT.get(ext)

    def candidates(self, job: Job) -> list[dict]:
        entry = self.idx.get(job.name) if job.name else None
        fps = {wf.multiset_fp(job.graph)} | ({entry["fp"]} if entry else set())
        kinds = JOINS.get(output_node(job.graph)[2] or "text", ())
        return [r for r in self.recordings if self.joins(r, job, fps, kinds)]

    def joins(self, rec: dict, job: Job, fps: set, kinds: tuple) -> bool:
        """By fingerprint (template or bare multiset) or the template the recording was identified
        as, else by the workflow it names, else by kind."""
        if rec.get("workflow_fp"):
            return rec["workflow_fp"] in fps or (job.name is not None and self.rec_template(rec) == job.name)
        named = (rec.get("fields") or {}).get("workflow")
        return named == job.name if named else rec.get("kind") in kinds

    def rec_template(self, rec: dict) -> str | None:
        """The template a recording was filled from: its recorded graph identified, else the
        template whose class set P2's section-0 `node_classes` covers best."""
        key = id(rec)
        if key not in self._templates:
            graph = self.rec_graph(rec)
            self._templates[key] = (wf.identify(graph, self.idx) if graph else
                                    wf.identify_classes((rec.get("fields") or {}).get("node_classes"), self.idx))
        return self._templates[key]

    @staticmethod
    def rec_graph(rec: dict) -> dict | None:
        """The recording's graph file opened for read (`graph`, or P2's `source_graph`); None if absent."""
        for path in (rec.get("graph"), rec.get("source_graph")):
            try:
                if path and Path(path).is_file():
                    with open(path, "r", encoding="utf-8") as fh:
                        return json.load(fh)
            except (OSError, ValueError):
                continue
        return None

    def try_of(self, job: Job, index: int | None) -> int:
        """How many distinct graphs of this take were asked before this one."""
        seen = self.seen.setdefault((job.name, index), [])
        digest = fields_hash(wf.graph_fields(job.graph))
        if digest not in seen:
            seen.append(digest)
        return seen.index(digest)

    # ---- exact ---------------------------------------------------------------------------

    def exact(self, rec: dict, job: Job) -> bool:
        if rec.get("values"):
            return all(job.values.get(k) == v for k, v in rec["values"].items())
        if rec.get("graph"):
            return self.rec_fields(rec) == wf.graph_fields(job.graph)
        check = {"take": self.exact_take, "vl_text": self.exact_text, "refine_crop": self.exact_staged,
                 "grid": self.exact_seeded, "place": self.exact_seeded, "tts_line": self.exact_line}.get(rec.get("kind"))
        if check:
            return check(rec, job)
        return bool(rec.get("fields")) and rec["fields"] == wf.graph_fields(job.graph)

    def exact_take(self, rec: dict, job: Job) -> bool:
        return bool(rec.get("fields")) and self.fields_like(rec, job.graph) == rec["fields"]

    @staticmethod
    def fields_like(rec: dict, graph: dict) -> dict | None:
        """The asked graph's fields in the recording's own style (P2's section-0, or node.input)."""
        return section0(graph) if "node_classes" in (rec.get("fields") or {}) else wf.graph_fields(graph)

    def exact_text(self, rec: dict, job: Job) -> bool:
        return rec.get("key") in self.text_keys(job)

    def text_keys(self, job: Job) -> set[str]:
        """Every `comfy.text_key` the reader could have computed: the values it changed from the
        template, plus any subset of the ones it passed equal to the template's."""
        from studio import comfy
        entry = self.idx.get(job.name)
        if entry is None:
            return set()
        base = wf.inject_values(entry["template"], entry["inject"])
        changed = {k: v for k, v in job.values.items() if base.get(k) != v}
        keys = set()
        for extra in subsets(sorted(k for k in job.values if k not in changed)):
            values = {**changed, **{k: job.values[k] for k in extra}}
            body = json.dumps([comfy.TEXT_CACHE_VERSION, job.name, entry["template"], entry["inject"], values],
                              sort_keys=True, default=str)
            keys.add(hashlib.sha256(body.encode("utf-8")).hexdigest())
        return keys

    def staged_shas(self, job: Job) -> set[str]:
        """The sha256 of every file the graph names in the engine's input folder."""
        out = set()
        for value in wf.graph_fields(job.graph).values():
            if not (isinstance(value, str) and 0 < len(value) < 200 and "\n" not in value):
                continue
            try:
                if (self.inputs / value).is_file():
                    out.add(sha_of(self.inputs / value))
            except (OSError, ValueError):
                continue
        return out

    def exact_staged(self, rec: dict, job: Job) -> bool:
        return rec.get("key") in self.staged_shas(job)

    @staticmethod
    def exact_seeded(rec: dict, job: Job) -> bool:
        """A grid or place drawn with the same seed and prompt (P2's key: id, seed, prompt sha)."""
        key = rec.get("key")
        return (isinstance(key, list) and len(key) == 3 and key[1] == job.values.get("seed")
                and key[2] == text_sha(job.values.get("prompt")))

    def speaker(self, job: Job) -> str | None:
        """The speaker the voice map names for any reference this graph stages; None when unknown."""
        return next((self.voices[v] for v in wf.graph_fields(job.graph).values()
                     if isinstance(v, str) and v in self.voices), None)

    def exact_line(self, rec: dict, job: Job) -> bool:
        key, speaker = rec.get("key"), self.speaker(job)
        return (isinstance(key, list) and len(key) == 2 and key[1] == text_sha(line_text(job.values))
                and speaker is not None and speaker == key[0])

    # ---- substituted ---------------------------------------------------------------------

    def substitute(self, kind, recs: list[dict], job: Job, index, tries) -> dict | None:
        cells = job.values.get("cells", cells_from_name(job.name))
        test = {"take": lambda r: tries is not None and self.rec_take(r) == (index, tries),
                "tts_line": lambda r: self.same_voice(r, job),
                "grid": lambda r: self.rec_cells(r) == cells}.get(kind)
        return next((r for r in recs if test(r)), None) if test else None

    @staticmethod
    def rec_take(rec: dict) -> tuple[int | None, int | None]:
        """(index, tries) a take recording answers for: P2's [index, tries] key, or {index} + tries."""
        key = rec.get("key")
        index = key.get("index") if isinstance(key, dict) else key[0] if isinstance(key, list) and key else key
        tries = rec.get("tries")
        if tries is None and isinstance(key, list) and len(key) > 1:
            tries = key[1]
        index = index if isinstance(index, int) else take_index(rec.get("values") or {})
        return index, (int(tries) if tries is not None else None)

    def same_voice(self, rec: dict, job: Job) -> bool:
        """Same voice: every non-line inject value (a `values` recording), else P2's speaker by the
        voice map, else, with no map entry, the same line text (the voice then unverified)."""
        if rec.get("values"):
            return voice_of(rec["values"]) == voice_of(job.values)
        key, speaker = rec.get("key"), self.speaker(job)
        if not (isinstance(key, list) and len(key) == 2):
            return False
        return speaker == key[0] if speaker is not None else key[1] == text_sha(line_text(job.values))

    @staticmethod
    def rec_cells(rec: dict):
        return (rec.get("values") or {}).get("cells", (rec.get("fields") or {}).get("cells"))

    def rec_line(self, rec: dict, inject: dict) -> str:
        """The text a recorded line said (its values, its graph, or P2's said_as / text)."""
        if rec.get("values") or rec.get("graph"):
            return line_text(self.rec_values(rec, inject))
        fields = rec.get("fields") or {}
        return str(fields.get("said_as") or fields.get("text") or "")

    # ---- recorded fields and the take diff -----------------------------------------------

    def rec_fields(self, rec: dict) -> dict:
        """A recording's fields: computed from its recorded graph when it names one."""
        key = id(rec)
        if key not in self._fields:
            if rec.get("graph"):
                with open(rec["graph"], "r", encoding="utf-8") as fh:
                    self._fields[key] = wf.graph_fields(json.load(fh))
            else:
                self._fields[key] = dict(rec.get("fields") or {})
        return self._fields[key]

    def rec_values(self, rec: dict, inject: dict) -> dict:
        return dict(rec["values"]) if rec.get("values") else wf.fields_inject(self.rec_fields(rec), inject)

    def diff(self, kind, rec, recs: list[dict], job: Job, index) -> list | None:
        """For a take, the field diff against the answering recording (or the same index's first)."""
        if kind != "take":
            return None
        rec = rec or next((r for r in recs if self.rec_take(r)[0] == index), None)
        if rec is None:
            return None
        asked = wf.graph_fields(job.graph) if rec.get("graph") else self.fields_like(rec, job.graph)
        return wf.field_diff(asked or {}, self.rec_fields(rec))


class FakeComfy:
    """The engine.  `start()` binds and serves; every route answers under one lock."""

    def __init__(self, sandbox: Path, recordings=(), workflows: Path = wf.WORKFLOWS, faults=(), port: int = 0,
                 pace: float = 0.0, transcript: Path | None = None, voices: dict | None = None):
        if int(port) == REAL_ENGINE_PORT:
            raise ValueError(f"the fake never binds {REAL_ENGINE_PORT}: that port is the real ComfyUI")
        self.box, self.port, self.pace = Path(sandbox), int(port), float(pace)
        self.root, self.log_path = self.box / "comfy", self.box / "engine_log.jsonl"
        self.idx, self.workflows = wf.index(workflows), Path(workflows)
        self.matcher = Matcher(self.idx, self.root / "input", voices)
        self.faults, self.transcript = comfy_faults.Faults(faults), transcript
        self.jobs: dict[str, Job] = {}
        self.history: dict[str, dict] = {}
        self.ring: list[dict] = []
        self.number, self.busy_until, self.held = 0, 0.0, False
        self.down_until: float | None = None
        self.gone = False
        self._lock = threading.RLock()
        self._server: ThreadingHTTPServer | None = None
        self.add_recordings(recordings)

    @classmethod
    def from_manifest(cls, sandbox: Path, **kw) -> "FakeComfy":
        """The fake a sandbox's rehearsal.json names: its port, recordings, faults and pace."""
        with open(Path(sandbox) / "rehearsal.json", "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        port = urlsplit(manifest["comfy_host"]).port
        recordings = (load_recordings(manifest["recordings"], manifest.get("real_library"))
                      if manifest.get("recordings") else [])
        return cls(sandbox, recordings=recordings, faults=manifest.get("faults") or (), port=port,
                   pace=float(manifest.get("comfy_pace") or 0.0), voices=manifest.get("voices"), **kw)

    # ---- lifecycle -----------------------------------------------------------------------

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> "FakeComfy":
        self._server = ThreadingHTTPServer(("127.0.0.1", self.port), _Handler)
        self._server.daemon_threads = True
        self._server.fake = self
        self.port = self._server.server_address[1]
        _LIVE[self.port] = self
        for sub in ("input", "output", "temp"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        self._write(self.header())
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05},
                         name=f"fake-comfy-{self.port}", daemon=True).start()
        return self

    def stop(self) -> None:
        if self._server is not None:
            _LIVE.pop(self.port, None)
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def __enter__(self) -> "FakeComfy":
        return self.start() if self._server is None else self

    def __exit__(self, *exc) -> None:
        self.stop()

    def header(self) -> dict:
        return {"header": True, "fake": __name__, "shape": shape_state(self.transcript),
                "transcript": str(self.transcript or TRANSCRIPT), "url": self.url, "started": stamp(),
                "workflows": str(self.workflows), "recordings": len(self.recordings)}

    def fingerprint(self, name: str) -> str:
        return self.idx[name]["fp"]

    @property
    def recordings(self) -> list[dict]:
        return self.matcher.recordings

    def add_recordings(self, recordings) -> None:
        with self._lock:
            self.matcher.recordings.extend(dict(r) for r in recordings)

    def hold(self, on: bool) -> None:
        """Hold every job where it is (a test's paused engine); releasing lets them finish."""
        with self._lock:
            self.held = bool(on)

    def restart(self) -> bool:
        """engine_ops.restart's fake: an engine that comes back EMPTY; False when it is lost for good."""
        with self._lock:
            self._write({"ts": stamp(), "call": "restart", "revived": not self.gone})
            if self.gone:
                return False
            self.jobs.clear(), self.history.clear()
            self.down_until, self.held = None, False
            self._say("rehearsal fake: restarted, queue and history empty")
            return True

    # ---- the door ------------------------------------------------------------------------

    def dispatch(self, method: str, path: str, body: bytes) -> tuple[int, Any]:
        """(status, JSON payload | None | DROP) for one request."""
        if method == "POST" and urlsplit(path).path == ADMIN_RESTART:
            return 200, {"revived": self.restart()}
        with self._lock:
            if self._unreachable():
                return 0, DROP
            self._settle()
            route = urlsplit(path).path
            handler = self._route(method, route)
            if handler is None:
                return 404, {"error": f"the fake has no route {method} {route}"}
            try:
                return handler(route, body)
            except ValueError as err:
                return 400, {"error": {"type": "invalid_prompt", "message": str(err), "details": "",
                                       "extra_info": {}}, "node_errors": {}}

    def _route(self, method: str, route: str):
        table = {("POST", "/prompt"): self._post_prompt, ("GET", "/queue"): self._get_queue,
                 ("POST", "/queue"): self._post_queue, ("GET", "/system_stats"): self._system_stats,
                 ("POST", "/free"): self._free, ("POST", "/interrupt"): self._interrupt,
                 ("GET", "/internal/logs/raw"): self._logs, ("GET", "/history"): self._history}
        if method == "GET" and route.startswith("/history/"):
            return self._history
        return table.get((method, route))

    def _unreachable(self) -> bool:
        """The engine is lost, or still down after a crash; a crash's end empties it."""
        if self.gone:
            return True
        if self.down_until is None:
            return False
        if time.time() < self.down_until:
            return True
        self.down_until = None
        self.jobs.clear(), self.history.clear()
        self._say("rehearsal fake: back after a crash, every job forgotten")
        return False

    def _settle(self) -> None:
        """Move every job whose recorded time has run out into history, in order."""
        if self.held:
            return
        for pid in [p for p, j in self.jobs.items() if not j.hang and time.time() >= j.ready_at]:
            self.history[pid] = self.jobs.pop(pid).record

    # ---- routes --------------------------------------------------------------------------

    def _post_prompt(self, _route: str, body: bytes) -> tuple[int, dict]:
        graph = prompt_graph(body)
        name = wf.identify(graph, self.idx)
        job = self._job(graph, name)
        fault = self.faults.on_submit(name)
        if fault and fault.kind == "rejected":
            return self._rejected(job, fault)
        try:
            row = self._answer(job, fault)
        except (ValueError, OSError, subprocess.CalledProcessError) as err:
            self._write({"ts": stamp(), "call": "prompt", "workflow": name, "error": str(err)})
            return 500, {"error": f"rehearsal fake could not answer: {err}", "node_errors": {}}
        self._write(row)
        self._after(job, fault)
        return 200, {"prompt_id": job.pid, "number": job.number, "node_errors": self._node_errors(job, fault)}

    def _node_errors(self, job: Job, fault) -> dict:
        """A partial accept's errors (the media outputs the broken input feeds); {} otherwise."""
        if not (fault and fault.kind == "partial_accept"):
            return {}
        return comfy_faults.node_errors(fault, job.graph, [n for n, _, ext in output_nodes(job.graph) if ext])

    def _rejected(self, job: Job, fault) -> tuple[int, dict]:
        """Every output fails validation: the engine's 400, nothing queued (GPU transcript, case B)."""
        self._write({"ts": stamp(), "call": "prompt", "workflow": job.name, "fault": fault.kind, "rejected": True})
        errors = comfy_faults.node_errors(fault, job.graph, [n for n, _, _ in output_nodes(job.graph)])
        return 400, {"error": dict(comfy_faults.REJECTED), "node_errors": errors}

    def _job(self, graph: dict, name: str | None) -> Job:
        self.number += 1
        inject = self.idx[name]["inject"] if name else {}
        return Job(str(uuid.uuid4()), self.number, graph, name, wf.inject_values(graph, inject), now_ms(),
                   time.time())

    def _after(self, job: Job, fault) -> None:
        """Queue the job; a crash, a loss or a hang takes the engine with it."""
        self.jobs[job.pid] = job
        kind = fault.kind if fault else None
        if kind in ("hang", "crash", "lost"):
            job.hang = True
        if kind == "crash":
            self.down_until = time.time() + float(fault.detail or 1.0)
        if kind == "lost":
            self.gone = True

    def _history(self, route: str, _body: bytes) -> tuple[int, dict]:
        pid = route[len("/history/"):] if route.startswith("/history/") else None
        if pid is None:
            return 200, dict(self.history)
        return 200, ({pid: self.history[pid]} if pid in self.history else {})

    def _queue_item(self, job: Job) -> list:
        """[number, id, graph, extra, every output node]; a partial accept lists the valid ones only."""
        nodes = [n for n, _, ext in output_nodes(job.graph) if not (job.partial and ext)]
        return [job.number, job.pid, job.graph, {"create_time": job.started_ms}, nodes]

    def _get_queue(self, _route: str, _body: bytes) -> tuple[int, dict]:
        jobs = sorted(self.jobs.values(), key=lambda j: j.number)
        return 200, {"queue_running": [self._queue_item(j) for j in jobs[:1]],
                     "queue_pending": [self._queue_item(j) for j in jobs[1:]]}

    def _post_queue(self, _route: str, body: bytes) -> tuple[int, None]:
        doc = json.loads(body or b"{}")
        running = min(self.jobs.values(), key=lambda j: j.number).pid if self.jobs else None
        doomed = [p for p in self.jobs if p != running] if doc.get("clear") else listed(doc.get("delete"))
        for pid in doomed:
            if pid != running:
                self.jobs.pop(pid, None)
        return 200, None

    def _system_stats(self, _route: str, _body: bytes) -> tuple[int, dict]:
        return 200, json.loads(json.dumps(SYSTEM_STATS))

    def _free(self, _route: str, body: bytes) -> tuple[int, None]:
        self._write({"ts": stamp(), "call": "free", "body": json.loads(body or b"{}")})
        self._say("rehearsal fake: models unloaded")
        return 200, None

    def _interrupt(self, _route: str, body: bytes) -> tuple[int, None]:
        """A hung job ignores it (F9: run 18's six interrupts); a running one ends interrupted.  With no
        prompt_id it is GLOBAL; one naming another prompt is skipped, as the engine logs (SR-5)."""
        running = min(self.jobs.values(), key=lambda j: j.number) if self.jobs else None
        named = (json.loads(body or b"{}") or {}).get("prompt_id")
        if named and (running is None or running.pid != named):
            self._say(f"Prompt {named} is not currently running, skipping interrupt")
            return 200, None
        self._write({"ts": stamp(), "call": "interrupt", "prompt_id": running.pid if running else None,
                     "ignored": bool(running and running.hang)})
        if running and not running.hang:
            cls = running.record.get("rehearsal", {}).get("match", "canned")
            running.record = self._record(running, {}, "error", [self._interrupted(running)], cls, None)
            self.history[running.pid] = self.jobs.pop(running.pid).record
        return 200, None

    def _logs(self, _route: str, _body: bytes) -> tuple[int, dict]:
        return 200, {"entries": self.ring[-RING:], "size": {"cols": 120, "rows": 40}}

    # ---- an answer -----------------------------------------------------------------------

    def _answer(self, job: Job, fault) -> dict:
        """Match, materialise, fault; the job's record and its engine_log row."""
        match = self.matcher.match(job)
        seconds = (match.rec or {}).get("seconds")
        if fault and fault.kind in ("exec_error", "exec_fatal"):
            node = output_node(job.graph)[0] or next(iter(job.graph))
            msg = comfy_faults.error_message(fault, job.pid, node, job.started_ms + 1,
                                             (job.graph.get(node) or {}).get("inputs"))
            job.record, outputs = self._record(job, {}, "error", [msg], match.cls, None), {}
        elif fault and fault.kind in ("hang", "crash", "lost"):
            outputs = {}                                 # the job never finishes: nothing is written
        else:
            outputs = self.produce(job, match, fault)
            job.record = self._record(job, outputs, "success", None, match.cls, seconds)
        job.ready_at = self._ready_at(seconds)
        self._say(f"rehearsal fake: {job.name or 'unknown workflow'} answered {match.cls}"
                  + (f" with fault {fault.kind}" if fault else ""))
        return self._row(job, match, fault, outputs, seconds)

    def _ready_at(self, seconds: float | None) -> float:
        """When a paced job finishes: one job at a time, each for its recorded seconds x pace."""
        self.busy_until = max(time.time(), self.busy_until) + float(seconds or 0.0) * self.pace
        return self.busy_until

    # ---- outputs -------------------------------------------------------------------------

    def produce(self, job: Job, match: Match, fault) -> dict:
        """The history `outputs` of an answered job, its files written into the sandbox: every
        LoadVideo's echo first, the job's own answer, then every other output node (canned)."""
        node, slot, ext = output_node(job.graph)
        if node is None:
            return {}
        job.partial = bool(fault and fault.kind == "partial_accept")
        out = self.echoes(job)
        for other, oslot, oext in output_nodes(job.graph):
            if job.partial and oext:
                continue                                 # its input failed validation: never ran
            out[other] = self.primary(job, match, fault) if other == node else self.secondary(job, other, oslot, oext)
        return out

    def primary(self, job: Job, match: Match, fault) -> dict:
        _node, slot, ext = output_node(job.graph)
        if slot == "text":
            return {"text": [self.text_answer(match, fault)]}
        sub, items = self.media_answer(job, match, ext, fault)
        return self.media_entry(slot, ext, [self.item(p, sub, "output") for p in items])

    def secondary(self, job: Job, node: str, slot: str, ext: str | None) -> dict:
        """Another output node of the same graph (a sheet's PreviewAny): a canned answer."""
        if slot == "text":
            return {"text": [CANNED_TEXT]}
        said = str((job.graph[node].get("inputs") or {}).get("filename_prefix") or "ComfyUI").replace("\\", "/")
        sub, base = posixpath.split(said)
        dest = self.next_path(sub, base or "ComfyUI", ext)
        canned_media(dest, ext, job.values.get("frames"), asked_size(job.values))
        return self.media_entry(slot, ext, [self.item(dest, sub, "output")])

    def echoes(self, job: Job) -> dict:
        """v0.41.2 reports each LoadVideo's INPUT as an output, type input (studio.comfy.outputs_by_node)."""
        out = {}
        for node, spec in job.graph.items():
            name = (spec or {}).get("inputs", {}).get("file") if (spec or {}).get("class_type") == "LoadVideo" else None
            if isinstance(name, str) and (self.root / "input" / name).is_file():
                out[str(node)] = self.media_entry("images", "mp4", [self.item(self.root / "input" / name, "", "input")])
        return out

    @staticmethod
    def item(path: Path, sub: str, kind: str) -> dict:
        meta = media_metadata(path)
        return {"filename": Path(path).name, "subfolder": sub, "type": kind, **({"metadata": meta} if meta else {})}

    @staticmethod
    def media_entry(slot: str, ext: str, items: list[dict]) -> dict:
        return {slot: items, **({"animated": [True]} if ext in VIDEO and slot == "images" else {})}

    def text_answer(self, match: Match, fault) -> str:
        if fault and fault.kind == "unreadable":
            return comfy_faults.UNREADABLE_TEXT
        if match.rec is None:
            return CANNED_TEXT
        with open(listed(match.rec["path"])[0], "r", encoding="utf-8") as fh:
            return fh.read()

    def media_answer(self, job: Job, match: Match, ext: str, fault) -> tuple[str, list[Path]]:
        if fault and fault.kind == "unreadable":
            raise ValueError("an unreadable fault fires on a text job only")
        sub, base = self.prefix(job)
        made = []
        for src in listed((match.rec or {}).get("path")) or [None]:
            dest = self.next_path(sub, base, Path(src).suffix.lstrip(".").lower() if src else ext)
            self.fill(dest, src, match, job)
            made.append(dest)
        if fault and fault.kind == "corrupt":
            comfy_faults.corrupt(made[0], fault.detail, int(job.values.get("frames") or video_info(made[0])[1]))
        return sub, made

    def prefix(self, job: Job) -> tuple[str, str]:
        """(subfolder, base) of the job's filename_prefix, as the engine splits `a/b`."""
        node = output_node(job.graph)[0]
        said = job.values.get("filename_prefix") or (job.graph.get(node) or {}).get("inputs", {}).get(
            "filename_prefix") or "ComfyUI"
        sub, base = posixpath.split(str(said).replace("\\", "/"))
        return sub, base or "ComfyUI"

    def next_path(self, sub: str, base: str, ext: str) -> Path:
        """<prefix>_<n:05>_.<ext>, n one past the highest the folder holds (the engine's counter)."""
        folder = self.root / "output" / sub
        folder.mkdir(parents=True, exist_ok=True)
        taken = [int(m.group(1)) for p in folder.glob(f"{base}_*_.*")
                 if (m := re.fullmatch(re.escape(base) + r"_(\d{5})_\..+", p.name))]
        return folder / f"{base}_{max(taken, default=0) + 1:05d}_.{ext}"

    def fill(self, dest: Path, src: str | None, match: Match, job: Job) -> None:
        """Write one output: canned, a take fitted to its frames, a stretched line, or the copy."""
        asked = job.values.get("frames")
        if match.cls == "canned" or src is None:
            canned_media(dest, dest.suffix.lstrip("."), asked, asked_size(job.values))
        elif match.cls == "substituted" and match.kind == "take" and asked:
            fit_frames(Path(src), dest, int(asked))
        elif match.cls == "substituted" and match.kind == "tts_line":
            recorded = self.matcher.rec_line(match.rec, self.idx[job.name]["inject"])
            stretch_wav(Path(src), dest, len(recorded or "x") / max(1, len(line_text(job.values))))
        else:
            copy_read_only(Path(src), dest)

    # ---- records, rows and the ring ------------------------------------------------------

    def _record(self, job: Job, outputs: dict, status: str, tail: list | None, cls: str, seconds) -> dict:
        """The /history record in the engine's shape, labelled with its match and clock."""
        t0 = job.started_ms
        msgs = [["execution_start", {"prompt_id": job.pid, "timestamp": t0}],
                ["execution_cached", {"nodes": [], "prompt_id": job.pid, "timestamp": t0}]]
        msgs += tail or [["execution_success", {"prompt_id": job.pid,
                                                "timestamp": t0 + int(round(float(seconds or 0) * 1000))}]]
        meta = {n: {"node_id": n, "display_node": n, "parent_node": None, "real_node_id": n} for n in outputs}
        return {"prompt": self._queue_item(job), "outputs": outputs,
                "status": {"status_str": status, "completed": status == "success", "messages": msgs},
                "meta": meta, "rehearsal": {"clock": "recorded" if seconds is not None else None, "match": cls}}

    def _interrupted(self, job: Job) -> list:
        node = output_node(job.graph)[0] or next(iter(job.graph))
        return ["execution_interrupted", {"prompt_id": job.pid, "node_id": node,
                                          "node_type": job.graph[node].get("class_type"), "executed": [],
                                          "timestamp": now_ms()}]

    def _row(self, job: Job, match: Match, fault, outputs: dict, seconds) -> dict:
        files = [self.root / i.get("type", "output") / i.get("subfolder", "") / i["filename"]
                 for node in outputs.values() for slot in ("images", "audio", "gifs") for i in node.get(slot, [])
                 if i.get("type") != "input"]                   # a LoadVideo's echo is no answer
        texts = [t for node in outputs.values() for t in node.get("text", [])]
        sha = sha_of(files[0]) if files else hashlib.sha256(texts[0].encode()).hexdigest() if texts else None
        return {"ts": stamp(), "call": "prompt", "prompt_id": job.pid, "number": job.number,
                "workflow": job.name, "workflow_fp": self.idx[job.name]["fp"] if job.name else None,
                "kind": match.kind, "class": match.cls, "recording": self._source(match.rec),
                "seconds": seconds, "clock": "recorded" if seconds is not None else None,
                "fault": fault.kind if fault else None, "corrupt": fault.detail if fault and fault.kind == "corrupt" else None,
                "index": match.index, "tries": match.tries, "speaker": match.speaker, "diff": match.diff,
                "sha": sha,
                "outputs": [str(f.relative_to(self.box)).replace("\\", "/") for f in files]}

    @staticmethod
    def _source(rec: dict | None) -> str | None:
        return (rec.get("source") or str(listed(rec.get("path"))[:1])) if rec else None

    def _say(self, message: str) -> None:
        self.ring.append({"t": stamp(), "m": message})
        del self.ring[:-RING]

    def _write(self, row: dict) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as out:
            out.write(json.dumps(row, default=str) + "\n")


def restart(host: str | None = None) -> bool:
    """engine_ops.restart / kill_engine in a rehearsal: the fake on the manifest's port comes back
    EMPTY (False when it is lost for good).  In-process when this process serves it, else over HTTP."""
    from studio import settings
    host = (host or settings.comfy_host()).rstrip("/")
    port = urlsplit(host).port
    if port == REAL_ENGINE_PORT:
        raise RuntimeError(f"fake_comfy.restart aimed at {host}: port {REAL_ENGINE_PORT} is the real ComfyUI")
    if port in _LIVE:
        return _LIVE[port].restart()
    request = urllib.request.Request(f"{host}{ADMIN_RESTART}", data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return bool(json.loads(response.read()).get("revived"))


class _Handler(BaseHTTPRequestHandler):
    """One request -> FakeComfy.dispatch; DROP closes the connection unanswered (an engine that is down)."""
    server_version = "ComfyUI-rehearsal-fake"

    def log_message(self, *_args) -> None:
        return None

    def do_GET(self) -> None:
        self._answer("GET")

    def do_POST(self) -> None:
        self._answer("POST")

    def _answer(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        status, payload = self.server.fake.dispatch(method, self.path, body)
        if payload is DROP:
            self.close_connection = True
            return
        data = b"" if payload is None else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
