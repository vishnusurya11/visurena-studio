"""The recordings index (2026-10-21_ep02_proof DESIGN 2.1): what one source episode recorded, keyed the
way a fake engine will be asked for it.

`build(book, number, library)` reads ONLY named files, never a walk: the take records
(`takes/r2v/shots.json`, `T##.graph.json`, `attempts/T##_fail<k>.graph.json` probed k = 1, 2, ...),
`takes/r2v/phases.jsonl`, `takes/r2v/refine.json`, `storyboard/layout.json` and the grid
records it names, `timing.jsonl`, `audio/lines/lines.json`, the book's `refs/places.json` and
`refs/pack.jsonl`, the library's `vlm_calls.jsonl`, `.vlm_cache/<kk>/<key>.txt` by its computed
key, and `brain*/attempt_<NN>.json` probed by number.  Every entry is
`{kind, workflow_fp, key, fields, tries, path, seconds, source}`, every path relative to the
library root.  `workflow_fp` is the sha of the graph's sorted class_type multiset (a recorded
graph has no inject map; the fake engine joins templates on the same multiset)."""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Callable

TRY_STEP = 101
"""takes_r2v.mark_retake: a retake's seed is the card's seed + 101 * tries (a test pins the line)."""
SAMPLES = 3
"""take_content_check.SAMPLES: frames read per take (a test pins the literal)."""
MAX_PROBE = 99
VL_WORKFLOW = "image_qwen3vl_caption"
MEMO_DIR = "memos/whisper"
"""Where P4's fill_memos.py keeps the REAL whisper reading of each wav, relative to recordings.json."""


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_rows(path: Path) -> list[dict]:
    """A JSONL file's parseable rows ([] when the file is absent)."""
    if not Path(path).is_file():
        return []
    rows = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def rel(path: Path | None, root: Path) -> str | None:
    """A library-relative POSIX path of a file that exists, else None."""
    if path is None or not Path(path).is_file():
        return None
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def entry(kind: str, key, fields: dict, path: str | None, seconds, source: str, tries=None,
          workflow_fp: str | None = None, **extra) -> dict:
    return {"kind": kind, "workflow_fp": workflow_fp, "key": key, "fields": fields, "tries": tries,
            "path": path, "seconds": seconds, "source": source, **extra}


# --- take graphs ---------------------------------------------------------------------------

def nodes(graph: dict) -> list[dict]:
    return [n for n in graph.values() if isinstance(n, dict) and "class_type" in n]


def first_input(graph: dict, names: tuple[str, ...]):
    """The first scalar input under any of `names`, in node order."""
    for n in nodes(graph):
        for name in names:
            value = n.get("inputs", {}).get(name)
            if isinstance(value, (int, float, str)) and not isinstance(value, bool):
                return value
    return None


def inputs_named(graph: dict, names: tuple[str, ...]) -> list[str]:
    """Every string input under any of `names` (links are lists, never kept)."""
    return [v for n in nodes(graph) for k, v in n.get("inputs", {}).items() if k in names and isinstance(v, str)]


def loras_of(graph: dict) -> list[list]:
    """[name, strength] of every LoRA loader node."""
    out = []
    for n in nodes(graph):
        if n["class_type"].startswith("Lora"):
            i = n.get("inputs", {})
            out.append([i.get("lora_name"), i.get("strength_model", i.get("strength"))])
    return out


def graph_fields(graph: dict) -> dict:
    """The fields a take's identity is diffed on (DESIGN section 0)."""
    return {"seed": first_input(graph, ("noise_seed", "seed")), "frames": first_input(graph, ("length", "frames")),
            "prompts": inputs_named(graph, ("prompt", "text")), "loras": loras_of(graph),
            "staged": inputs_named(graph, ("image", "audio", "video")),
            "node_classes": sorted({n["class_type"] for n in nodes(graph)})}


def classes_fp(graph: dict) -> str:
    """sha16 of the graph's sorted class_type multiset."""
    counted = sorted(Counter(n["class_type"] for n in nodes(graph)).items())
    return hashlib.sha256(json.dumps(counted).encode()).hexdigest()[:16]


def tries_from_seed(seed, base) -> int | None:
    """The try count a seed says under the retake rule (seed = base + 101 * tries)."""
    if not isinstance(seed, int) or not isinstance(base, int) or (seed - base) % TRY_STEP:
        return None
    tries = (seed - base) // TRY_STEP
    return tries if tries >= 0 else None


def attempt_graphs(take_dir: Path, index: int) -> list[tuple[Path, Path]]:
    """(graph, video) of `attempts/T##_fail<k>`, k = 1, 2, ... to the first absent graph."""
    out = []
    for k in range(1, MAX_PROBE + 1):
        graph = Path(take_dir) / "attempts" / f"T{index:02d}_fail{k}.graph.json"
        if not graph.is_file():
            break
        out.append((graph, graph.with_name(f"T{index:02d}_fail{k}.mp4")))
    return out


def take_graphs(take_dir: Path, index: int) -> list[tuple[Path, Path]]:
    """Every recorded render of take `index`: the attempts, then the kept take."""
    kept = Path(take_dir) / f"T{index:02d}.graph.json"
    return attempt_graphs(take_dir, index) + ([(kept, kept.with_name(f"T{index:02d}.mp4"))] if kept.is_file() else [])


def phase_rows(take_dir: Path) -> dict[int, list[float]]:
    """Each take's recorded render seconds (`prompt_s`), in the file's order."""
    out: dict[int, list[float]] = {}
    for row in read_rows(Path(take_dir) / "phases.jsonl"):
        if row.get("prompt_s") is not None:
            out.setdefault(row.get("take"), []).append(row["prompt_s"])
    return out


def take_seconds(rows: list[float], tries: int | None, renders: int) -> tuple[float | None, str]:
    """A render's seconds: its own row when the rows count the renders (try order), else their median."""
    if rows and len(rows) == renders and tries is not None and tries < len(rows):
        return rows[tries], "phases.jsonl row, try order"
    if rows:
        return round(statistics.median(rows), 1), f"phases.jsonl median of {len(rows)} rows for the take"
    return None, "no phases.jsonl row"


def take_entry(graph_path: Path, video: Path, base: int | None, rows: list[float], renders: int,
               root: Path) -> dict:
    graph = read_json(graph_path)
    fields = graph_fields(graph)
    tries = tries_from_seed(fields["seed"], base)
    seconds, basis = take_seconds(rows, tries, renders)
    index = int(Path(graph_path).name[1:3])
    return entry("take", [index, tries], fields, rel(video, root), seconds, rel(graph_path, root), tries=tries,
                 workflow_fp=classes_fp(graph), seconds_basis=basis)


def take_entries(home: Path, root: Path) -> list[dict]:
    """Every take render the episode recorded, keyed (index, tries) from the seed rule."""
    take_dir = Path(home) / "takes" / "r2v"
    sheet = take_dir / "shots.json"
    records = read_json(sheet) if sheet.is_file() else []
    phases, out = phase_rows(take_dir), []
    for r in records:
        base = r["seed"] - TRY_STEP * (r.get("tries") or 0) if isinstance(r.get("seed"), int) else None
        renders = take_graphs(take_dir, r["index"])
        out += [take_entry(g, v, base, phases.get(r["index"], []), len(renders), root) for g, v in renders]
    return out


# --- refine crops, grids, places, lines ----------------------------------------------------

def busy_seconds(row: dict, people: int) -> tuple[float | None, str]:
    """A refined take's GPU seconds per crop: `gpu_busy_s` where recorded, else the priced share."""
    nested = [v.get("gpu_busy_s") for v in row.values() if isinstance(v, dict) and v.get("gpu_busy_s")]
    if row.get("gpu_busy_s") or nested:
        return round((row.get("gpu_busy_s") or nested[0]) / max(people, 1), 1), "refine.json gpu_busy_s per crop"
    if row.get("gpu_s_priced"):
        return round(row["gpu_s_priced"] / max(people, 1), 1), "refine.json gpu_s_priced per crop"
    return None, "no refine.json seconds"


def crop_entry(take: str, person: dict, row: dict, refine_dir: Path, root: Path) -> dict | None:
    """One crop keyed by the sha of its staged `_src` bytes; None when the src was never kept."""
    crop = refine_dir.parent / person["crop"]
    src = crop.with_name(f"{crop.stem}_src.mp4")
    if not src.is_file():
        return None
    seconds, basis = busy_seconds(row, len(row.get("people", [])))
    fields = {"take": take, "who": person.get("who"), "kept": person.get("kept"), "why": person.get("why"),
              "src": rel(src, root), "guide": rel(crop.with_name(f"{crop.stem}_guide.wav"), root),
              "track": rel(crop.with_name(f"{crop.stem}.json"), root)}
    return entry("refine_crop", sha(src), fields, rel(crop, root), seconds, rel(refine_dir / "refine.json", root),
                 seconds_basis=basis)


def refine_entries(home: Path, root: Path) -> list[dict]:
    refine_dir = Path(home) / "takes" / "r2v" / "refine"
    sheet = refine_dir.parent / "refine.json"
    rows = read_json(sheet) if sheet.is_file() else {}
    found = [crop_entry(take, p, row, refine_dir, root) for take, row in rows.items() if isinstance(row, dict)
             for p in row.get("people", []) if p.get("crop")]
    return [e for e in found if e is not None]


def grid_seconds(home: Path) -> dict[str, float]:
    """Each grid's last recorded draw seconds from timing.jsonl, keyed `setup cols rows [tag]`."""
    out = {}
    for row in read_rows(Path(home) / "timing.jsonl"):
        if row.get("stage") == "grids" and row.get("note"):
            words = [w for w in row["note"].split() if not w.startswith("--")]
            out[" ".join(words[:4])] = row.get("seconds")
    return out


def grid_entry(home: Path, number: int, row: dict, seconds: dict, root: Path) -> dict | None:
    from studio import grid_layout
    name = grid_layout.name_of(number, row)
    boards = Path(home) / "storyboard"
    record = boards / "grids" / f"{name}.json"
    if not record.is_file():
        return None
    said = read_json(record)
    prompt = boards / "grids" / f"{name}.txt"
    panels = [rel(boards / "h3" / f"shot_{s:02d}.png", root) for s in row.get("shots", [])]
    fields = {"name": name, "shots": row.get("shots", []), "cells": row["cols"] * row["rows"],
              "panels": [p for p in panels if p], "anchor": rel(boards / "anchors" / f"{row['setup']}.png", root)}
    key = [row["setup"], said.get("seed"), sha(prompt) if prompt.is_file() else None]
    ask = " ".join(str(x) for x in (row["setup"], row["cols"], row["rows"], row.get("tag")) if x)
    return entry("grid", key, fields, rel(boards / "grids" / f"{name}.png", root), seconds.get(ask), rel(record, root))


def grid_entries(home: Path, number: int, root: Path) -> list[dict]:
    layout = Path(home) / "storyboard" / "layout.json"
    rows, seconds = (read_json(layout) if layout.is_file() else []), grid_seconds(home)
    return [e for e in (grid_entry(home, number, r, seconds, root) for r in rows) if e is not None]


def pack_rows(book: Path) -> dict[str, dict]:
    """refs/pack.jsonl's last row per drawn picture path."""
    return {r["path"]: r for r in read_rows(Path(book) / "refs" / "pack.jsonl") if r.get("path")}


def place_entries(book: Path, root: Path) -> list[dict]:
    """Every place master the book's places.json holds, keyed (place id, seed, prompt sha)."""
    sheet = Path(book) / "refs" / "places.json"
    places, pack, out = (read_json(sheet) if sheet.is_file() else {}).get("places", {}), pack_rows(book), []
    for pid, place in places.items():
        for m in place.get("masters", []):
            picture = f"refs/locations/{m['location']}/{m['view']}.png"
            drawn = pack.get(picture, {})
            key = [pid, drawn.get("seed"), text_sha(drawn["prompt"]) if drawn.get("prompt") else None]
            fields = {"master_id": m["master_id"], "sha8": m.get("sha8"), "workflow": drawn.get("workflow")}
            out.append(entry("place", key, fields, rel(Path(book) / picture, root), drawn.get("seconds"),
                             rel(sheet, root)))
    return out


def tts_entries(home: Path, root: Path) -> list[dict]:
    """Every recorded line keyed (speaker, sha of the text it was said as), MEASURED seconds kept."""
    sheet = Path(home) / "audio" / "lines" / "lines.json"
    doc = read_json(sheet) if sheet.is_file() else []
    rows = doc.get("lines", []) if isinstance(doc, dict) else doc
    book = Path(home).parents[1]
    return [entry("tts_line", [r.get("speaker"), text_sha(r.get("said_as") or r.get("text"))],
                  {"index": r.get("index"), "text": r.get("text"), "said_as": r.get("said_as"),
                   "delivery": r.get("delivery"), "seed": r.get("seed"), "measured_seconds": r.get("seconds")},
                  rel(book / r["rel_path"], root) if r.get("rel_path") else None, None, rel(sheet, root),
                  tries=r.get("tries"), seconds_basis="render seconds per line are not recorded")
            for r in rows if isinstance(r, dict)]


def transcript_entries(lines: list[dict], root: Path) -> list[dict]:
    """One whisper memo slot per recorded wav, keyed by its bytes; P4 fills the memo."""
    out = []
    for line in lines:
        if line["path"]:
            key = sha(Path(root) / line["path"])
            out.append(entry("transcript", key, {"wav": line["path"], "filled": False}, f"{MEMO_DIR}/{key}.json",
                             None, line["source"]))
    return out


# --- VL reads, SDK streams --------------------------------------------------------------------

def asks() -> list[dict]:
    """Every constant ask a reader sends the local VLM, with the pictures it is sent with.

    panel_content_check.read / read_twins (seed 11 / 17), take_content_check.read_frame /
    read_twin_frame (seed 11+i / 23+i on frame i), picture_read._vision (places).  Their seeds
    and token budgets are literals there; a test pins each one."""
    from studio import panel_content as pc, picture_read
    frames = [(i, f"frame{i}") for i in range(SAMPLES)]
    return ([{"id": "panel_content", "workflow": VL_WORKFLOW, "on": "panel", "prompt": pc.ASK, "seed": 11,
              "max_new_tokens": 1024},
             {"id": "panel_twin", "workflow": VL_WORKFLOW, "on": "panel", "prompt": pc.TWIN_ASK, "seed": 17,
              "max_new_tokens": 256},
             {"id": "place_read", "workflow": picture_read.WORKFLOW, "on": "place", "prompt": picture_read.ASK,
              "seed": picture_read.SEED}]
            + [{"id": "take_frame", "workflow": VL_WORKFLOW, "on": on, "prompt": pc.ASK, "seed": 11 + i,
                "max_new_tokens": 1024} for i, on in frames]
            + [{"id": "take_twin", "workflow": VL_WORKFLOW, "on": on, "prompt": pc.TWIN_ASK, "seed": 23 + i,
                "max_new_tokens": 256} for i, on in frames])


def ask_values(ask: dict, picture: Path) -> dict:
    """The values dict the reader passes `comfy.cached_text`, the image by its staged name (no copy)."""
    from studio import comfy
    values = {"image_1": comfy.staged_name(picture), "prompt": ask["prompt"], "seed": ask["seed"]}
    if "max_new_tokens" in ask:
        values["max_new_tokens"] = ask["max_new_tokens"]
    return values


def pictures(home: Path, takes: list[dict], places: list[dict], root: Path) -> dict[str, list[Path]]:
    """The recorded pictures each ask family reads: panels, frame i of every take, place masters."""
    boards = Path(home) / "storyboard"
    named = read_json_or(Path(home) / "takes" / "r2v" / "shots.json", []) + read_json_or(boards / "layout.json", [])
    shots = sorted({s for row in named for s in row.get("shots", [])})
    panels = [p for s in shots for p in (boards / "h3" / f"shot_{s:02d}.png", boards / f"shot_{s:02d}.png")]
    indices = sorted({t["key"][0] for t in takes})
    content = Path(home) / "takes" / "work" / "content"
    out = {"panel": panels, "place": [Path(root) / e["path"] for e in places if e["path"]]}
    out.update({f"frame{i}": [content / f"T{n:02d}_{i}.png" for n in indices] for i in range(SAMPLES)})
    return {k: [p for p in v if p.is_file()] for k, v in out.items()}


def read_json_or(path: Path, default):
    return read_json(path) if Path(path).is_file() else default


def vl_fit(rows: list[dict]) -> tuple[float, float]:
    """seconds = a + b * answer_tokens, least squares over the logged caption reads."""
    pts = [(r["answer_tokens"], r["seconds"]) for r in rows
           if r.get("workflow") == VL_WORKFLOW and r.get("answer_tokens") and r.get("seconds") is not None]
    if len(pts) < 2 or len({x for x, _ in pts}) < 2:
        return (statistics.mean(y for _, y in pts) if pts else 0.0), 0.0
    b, a = statistics.linear_regression([x for x, _ in pts], [y for _, y in pts])
    return a, b


def chars_per_token(rows: list[dict]) -> float:
    chars = sum(r.get("answer_chars") or 0 for r in rows)
    tokens = sum(r.get("answer_tokens") or 0 for r in rows)
    return chars / tokens if tokens else 4.0


def default_text_key() -> Callable[[str, dict], str]:
    """The REAL cache key (`comfy.text_key`: the workflow, its inject map and the values)."""
    from studio import comfy
    return comfy.text_key


def vl_entry(ask: dict, picture: Path, key: str, cache: Path, fit: tuple, cpt: float, root: Path) -> dict:
    """One (picture, ask) read: the cache file opened by its key's NAME, seconds from the fit."""
    path = Path(cache) / key[:2] / f"{key}.txt"
    text = path.read_text(encoding="utf-8") if path.is_file() else None
    seconds = round(fit[0] + fit[1] * (len(text) / cpt), 2) if text is not None else None
    fields = {"ask": ask["id"], "picture": rel(picture, root), "seed": ask["seed"], "workflow": ask["workflow"],
              "chars": len(text) if text is not None else None}
    return entry("vl_text", key, fields, rel(path, root), seconds, "vlm_calls.jsonl fit a + b * tokens")


def vl_entries(families: dict[str, list[Path]], root: Path, text_key: Callable) -> list[dict]:
    """Every recorded picture x every constant ask of its family, hit or miss, keyed as the reader keys it."""
    calls = read_rows(Path(root) / "vlm_calls.jsonl")
    fit, cpt, cache = vl_fit(calls), chars_per_token(calls), Path(root) / ".vlm_cache"
    return [vl_entry(a, p, text_key(a["workflow"], ask_values(a, p)), cache, fit, cpt, root)
            for a in asks() for p in families.get(a["on"], [])]


def sdk_entries(home: Path, root: Path) -> list[dict]:
    """Each brain attempt kept (`brain/` and `brain_retired_NN/`, attempt_NN.json by number):
    the session's FINAL structured verdict and usage only, so `complete` is False."""
    folders = [Path(home) / "brain"] + [Path(home) / f"brain_retired_{n:02d}" for n in range(1, MAX_PROBE + 1)]
    out = []
    for folder in folders:
        for n in range(1, MAX_PROBE + 1):
            path = folder / f"attempt_{n:02d}.json"
            if not path.is_file():
                break
            said = read_json(path)
            fields = {"verdict": said.get("verdict"), "meta": said.get("meta"), "complete": False}
            out.append(entry("sdk_stream", ["brain verdict", None], fields, rel(path, root), None, rel(path, root)))
    return out


def build(book: Path, number: int, root: Path, text_key: Callable | None = None) -> dict:
    """The recordings index of one source episode: every entry, counted by kind."""
    home = Path(book) / "episodes" / f"ep{number:02d}"
    takes, places, lines = take_entries(home, root), place_entries(book, root), tts_entries(home, root)
    found = (takes + refine_entries(home, root) + grid_entries(home, number, root) + places + lines
             + transcript_entries(lines, root) + sdk_entries(home, root))
    found += vl_entries(pictures(home, takes, places, root), root, text_key or default_text_key())
    counts = Counter(e["kind"] for e in found)
    hits = sum(1 for e in found if e["kind"] == "vl_text" and e["path"])
    return {"source": Path(home).resolve().relative_to(Path(root).resolve()).as_posix(),
            "counts": dict(counts), "vl_hits": hits, "entries": found}
