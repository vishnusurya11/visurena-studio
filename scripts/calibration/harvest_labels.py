#!/usr/bin/env python
"""Harvest the casebook's regenerable rows for one book.

    uv run python scripts/calibration/harvest_labels.py <codex> [--rejudge] [--prose <file>...]

Writes library/<book>/casebook/labels.jsonl, one row per (artefact, verdict
source), from two kinds of source:

- the MACHINE json beside each artefact: `T??.dq.json` (the kept take, a
  pass by default because it went out; every losing attempt an agent-refused
  fault of class `unknown` unless its filename names one), `T??.content.json`,
  `storyboard/panel_dq.json` + `panel_content.json` (a pass by default per
  panel), `storyboard_prev_v1/` (a refused panel set), `storyboard/superseded/`
  (refused grids).  The row's `machine` field keeps the values a judge needs to
  re-judge from the row alone, so the bench never decodes video.
- PROSE: the episodes' story.md files and any repo doc that names this book,
  read with a take-id regex and a fault lexicon.  Every hit is a CANDIDATE
  (`verdict_by: unverified`) with its file and line; a person confirms it into
  owner.jsonl.  A span written as "epNN 33-40 s" resolves to its takes through
  the episode's placed.json.

Attempts are read from the records already stored in each dq.json (the take
gate keeps every roll it judged).  `--rejudge` re-runs `take_dq.main(...,
attempts=True)` first, which DECODES VIDEO and takes minutes per episode; the
runner is injectable for tests.  No GPU, no model, no credit.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import casebook, episode_home, take_look  # noqa: E402
from studio.casebook import Row  # noqa: E402

ENGINE = "r2v"
TAKE = re.compile(r"\bT(\d\d)(_fail\d(?:_[a-z_]+)?)?\b")
UNIT = re.compile(r"\bep(\d\d)\b")
SPAN = re.compile(r"\b(ep\d\d)\b[^.\n]{0,40}?\b(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*s\b")
PROSE_DIRS = ("docs/analysis", "docs/audit", "docs/calibration", ".claude/skills/episode")

LEXICON = (
    (r"slop|slid\b|slide|anchored|glued", "anchored_slide"),
    (r"gibberish|wrong[ _]letter", "wrong_letters"),
    (r"letter|label|masthead|headline|caption|\btext\b", "lettering"),
    (r"identical|copies|clone|duplicate", "copies"),
    (r"stacked|two pictures", "stacked_pictures"),
    (r"froze|frozen|freeze", "frozen_share"),
    (r"orbit", "orbit_repeat"),
    (r"corpse|dead body|hair moves", "dead_body_moves"),
    (r"lying|posture|\bstood\b|standing", "posture"),
    (r"\blip\b|\blag\b", "lip_lag"),
    (r"pushed|over-push|tighter", "over_push"),
    (r"no face|clipped|face out", "face_out"),
    (r"\bblack\b|too dark", "no_black_floor"),
    (r"\bhat\b|jacket|shirt|wardrobe|clothes", "wardrobe"),
    (r"extra|crowd|people", "extra_people"),
    (r"repeat", "same_picture_repeat"),
    (r"hard cut|cut early|\bjump\b", "cut_early"),
    (r"off-board|off board|foreign", "off_board"),
    (r"blur|warp|dissolv", "blur_warp"),
    (r"stranger|drift|identity", "identity_drift"),
    (r"pulse", "pulse"),
    (r"landform", "landform"),
)
"""First match wins, so the specific words come before the general ones."""


# ---- words -> class ----------------------------------------------------------

def classify(line: str) -> str | None:
    low = line.lower()
    for pattern, name in LEXICON:
        if re.search(pattern, low):
            return name
    return None


def class_of_name(filename: str) -> str:
    """`T14_fail4_wrong_lettering.mp4` names its own reason; a bare `_failN` does not."""
    tail = Path(filename).stem.split("_fail", 1)[1] if "_fail" in filename else ""
    words = tail.split("_", 1)[1].replace("_", " ") if "_" in tail else ""
    return classify(words) or "unknown"


def take_path(unit: str, number: str | int, suffix: str = "") -> str:
    room = f"episodes/{unit}/takes/{ENGINE}"
    name = f"T{int(number):02d}{suffix}.mp4"
    return f"{room}/attempts/{name}" if suffix else f"{room}/{name}"


# ---- prose -> candidate rows -------------------------------------------------

def candidates(text: str, source_rel: str, codex: str, unit_hint: str | None = None) -> list[Row]:
    """One unverified row per (line, take id) where the line also names a fault."""
    rows = []
    for n, line in enumerate(text.splitlines(), 1):
        unit = f"ep{UNIT.search(line).group(1)}" if UNIT.search(line) else unit_hint
        takes, cls = TAKE.findall(line), classify(line)
        if not (unit and takes and cls):
            continue
        for number, suffix in takes:
            rows.append(Row(codex=codex, unit=unit, kind="take", path=take_path(unit, number, suffix),
                            verdict="fault", fault_class=cls, verdict_by="unverified",
                            source=f"{source_rel}#L{n}"))
    return rows


def takes_at(placed: dict, start: float, end: float) -> list[str]:
    """The takes on screen anywhere in [start, end) seconds of the timeline."""
    return [f"T{s['index']:02d}" for s in placed.get("shots", [])
            if float(s["t_start"]) < end and float(s["t_end"]) > start]


def timestamp_rows(text: str, source_rel: str, codex: str, placed_of) -> list[Row]:
    """A span "epNN 33-40 s" becomes one unverified row per take on screen then."""
    rows = []
    for n, line in enumerate(text.splitlines(), 1):
        for unit, start, end in SPAN.findall(line):
            placed = placed_of(unit)
            if placed is None:
                continue
            for take in takes_at(placed, float(start), float(end)):
                rows.append(Row(codex=codex, unit=unit, kind="take", path=take_path(unit, take[1:]),
                                verdict="fault", fault_class=classify(line) or "unknown",
                                verdict_by="unverified", source=f"{source_rel}#L{n}"))
    return rows


# ---- machine json -> rows ----------------------------------------------------

def zoom_summary(z: dict | None) -> dict | None:
    """The four numbers `take_zoom.judge` reads, per segment; the arrays dropped."""
    if not z:
        return None
    keep = ("ratio", "measured", "monotonic", "camera")
    out = {k: z.get(k) for k in keep}
    out["segments"] = [{k: s.get(k) for k in keep} for s in z.get("segments") or []]
    return out


def dq_summary(rec: dict, planned: dict) -> dict:
    return {"score": rec.get("score"), "passed": rec.get("passed"), "attempt": rec.get("attempt", 0),
            "file": rec.get("file"), "gates": rec.get("gates", []), "zoom": zoom_summary(rec.get("zoom")),
            "planned": planned}


def take_rows(codex: str, unit: str, dq: dict, planned: dict, source: str, version: str,
              content: dict | None = None) -> list[Row]:
    """The kept take (a pass by default) and every losing attempt (an agent fault)."""
    kept = Row(codex=codex, unit=unit, kind="take", path=take_path(unit, dq["take"]), verdict="pass",
               verdict_by="default", source=source, machine_version=version,
               machine={"take_dq": dq_summary(dq, planned), "content": content})
    rows = [kept]
    for att in dq.get("attempts", []):
        stem = Path(att.get("file") or "").stem
        if att.get("file") == dq.get("file") or "_" not in stem:
            continue
        rows.append(Row(codex=codex, unit=unit, kind="take", path=take_path(unit, dq["take"], "_" + stem.split("_", 1)[1]),
                        verdict="fault", fault_class=class_of_name(att["file"]), verdict_by="agent",
                        source=source, machine_version=version,
                        machine={"take_dq": dq_summary(att, planned), "content": None}))
    return rows


def panel_rows(codex: str, unit: str, dq_rows: list, content_rows: list, planned: dict, source: str,
               version: str, folder: str = "storyboard", refused: bool = False) -> list[Row]:
    """One row per panel: a pass by default, or an agent fault for a superseded set."""
    content = {r.get("shot"): r for r in content_rows or []}
    rows = []
    for r in dq_rows or []:
        shot = r.get("shot")
        rows.append(Row(codex=codex, unit=unit, kind="panel", path=f"episodes/{unit}/{folder}/shot_{int(shot):02d}.png",
                        verdict="fault" if refused else "pass", fault_class="unknown" if refused else None,
                        verdict_by="agent" if refused else "default", source=source, machine_version=version,
                        machine={"panel_dq": r, "panel_content": content.get(shot), "planned": planned.get(shot, {})}))
    return rows


def grid_rows(codex: str, unit: str, names: list[str], version: str) -> list[Row]:
    """A superseded grid is a refused grid of unknown class."""
    return [Row(codex=codex, unit=unit, kind="grid", path=f"episodes/{unit}/storyboard/superseded/{name}",
                verdict="fault", fault_class="unknown", verdict_by="agent",
                source=f"episodes/{unit}/storyboard/superseded", machine_version=version) for name in names]


# ---- the plan's side of each row ---------------------------------------------

def plan_info(plan: dict) -> dict:
    """shot index -> what the judges compare against: motion, size, planned faces, daylight."""
    setups = plan.get("setups") or {}
    out = {}
    for shot in plan.get("shots", []):
        setup = setups.get(shot.get("setup"), {}) if isinstance(setups, dict) else {}
        out[shot["index"]] = {"motion": shot.get("motion", ""), "size": shot.get("size", ""),
                              "faces": len(shot.get("faces") or []), "extras": shot.get("extras", 0),
                              "daylight": take_look.is_daylight(setup.get("described", ""), bool(setup.get("outdoors")))}
    return out


def take_planned(info: dict, record: dict | None) -> dict:
    """The take's first shot, plus one motion per shot it spans."""
    shots = (record or {}).get("shots") or [(record or {}).get("index")]
    first = dict(info.get(shots[0], {}))
    first["motions"] = [info.get(s, {}).get("motion", "") for s in shots]
    return first


# ---- one episode ---------------------------------------------------------------

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def unrecorded_attempts(codex: str, unit: str, take_dir: Path, known: set[str], version: str) -> list[Row]:
    """Every losing roll on disk that no dq record judged: a refused take of unknown class,
    with no machine values until `--rejudge` decodes it."""
    rows = []
    for room in (take_dir, take_dir / "attempts"):
        for p in sorted(room.glob("T??_fail*.mp4")):
            rel = f"episodes/{unit}/takes/{ENGINE}/{'attempts/' if room.name == 'attempts' else ''}{p.name}"
            if p.name not in known:
                rows.append(Row(codex=codex, unit=unit, kind="take", path=rel, verdict="fault", fault_class=class_of_name(p.name),
                                verdict_by="agent", source=rel, machine_version=version))
    return rows


def episode_take_rows(codex: str, unit: str, ep_dir: Path, version: str) -> list[Row]:
    take_dir = ep_dir / "takes" / ENGINE
    info = plan_info(read_json(ep_dir / "plan.json") or {})
    records = {r["index"]: r for r in read_json(take_dir / "shots.json") or []}
    rows = []
    for dq_path in sorted(take_dir.glob("T??.dq.json")):
        dq = read_json(dq_path)
        content = read_json(dq_path.with_name(dq_path.name.replace(".dq.", ".content.")))
        source = f"episodes/{unit}/takes/{ENGINE}/{dq_path.name}"
        rows += take_rows(codex, unit, dq, take_planned(info, records.get(dq["take"])), source, version,
                          {"passed": content.get("passed"), "faults": content.get("faults", [])} if content else None)
    return rows + unrecorded_attempts(codex, unit, take_dir, {Path(r.path).name for r in rows}, version)


def episode_panel_rows(codex: str, unit: str, ep_dir: Path, version: str) -> list[Row]:
    info = plan_info(read_json(ep_dir / "plan.json") or {})
    rows = []
    for folder, refused in (("storyboard", False), ("storyboard_prev_v1", True)):
        dq = read_json(ep_dir / folder / "panel_dq.json")
        content = read_json(ep_dir / folder / "panel_content.json")
        if dq:
            rows += panel_rows(codex, unit, dq, content or [], info, f"episodes/{unit}/{folder}/panel_dq.json",
                               version, folder, refused)
    superseded = sorted(p.name for p in (ep_dir / "storyboard" / "superseded").glob("*.png"))
    return rows + grid_rows(codex, unit, superseded, version)


def names_only(text: str, book: Path, library: Path) -> bool:
    """A repo doc attaches to a book only when it names that book and no other."""
    named = {p.name[:14] for p in library.iterdir() if p.is_dir() and (p.name in text or p.name[:14] in text)}
    return named == {book.name[:14]}


def prose_sources(book: Path, root: Path = ROOT) -> list[tuple[Path, str | None]]:
    """(file, unit hint): every episode's story.md, and every repo doc that names this book alone."""
    out = [(p, p.parent.name) for p in sorted(book.glob("episodes/ep??/story.md"))]
    for folder in PROSE_DIRS:
        for p in sorted((root / folder).glob("*.md")):
            if names_only(p.read_text(encoding="utf-8", errors="replace"), book, book.parent):
                out.append((p, f"ep{UNIT.search(p.name).group(1)}" if UNIT.search(p.name) else None))
    return out


def prose_rows(codex: str, book: Path, sources: list[tuple[Path, str | None]], root: Path = ROOT) -> list[Row]:
    """Candidates from every source; a repo doc's candidate must name a take this book has on disk."""
    def placed_of(unit):
        return read_json(book / "episodes" / unit / "placed.json")
    rows = []
    for path, hint in sources:
        text = path.read_text(encoding="utf-8", errors="replace")
        own = path.resolve().is_relative_to(book.resolve())
        rel = path.resolve().relative_to(book.resolve() if own else root.resolve()).as_posix()
        found = candidates(text, rel, codex, hint) + timestamp_rows(text, rel, codex, placed_of)
        rows += found if own else [r for r in found if (book / locate(book, r.path)).is_file()]
    return rows


# ---- stamping --------------------------------------------------------------------

def published_units(book: Path) -> set[str]:
    path = book / "uploads.jsonl"
    if not path.is_file():
        return set()
    docs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {f"ep{int(d['episode']):02d}" for d in docs if d.get("video_id")}


def locate(book: Path, rel: str) -> str:
    """An attempt recorded under attempts/ may sit flat in the take room (older episodes)."""
    if "/attempts/" in rel and not (book / rel).is_file():
        flat = rel.replace("/attempts/", "/")
        return flat if (book / flat).is_file() else rel
    return rel


def stamp(rows: list[Row], book: Path, published: set[str]) -> list[Row]:
    """sha8 from the file on disk, the date it was last written, after_publish for candidates."""
    out = []
    for r in rows:
        rel = locate(book, r.path)
        file = book / rel
        at = datetime.fromtimestamp(file.stat().st_mtime).date().isoformat() if file.is_file() else r.verdict_at
        out.append(r.model_copy(update={"path": rel, "sha8": r.sha8 or casebook.sha8_of(file), "verdict_at": at,
                                        "after_publish": r.verdict_by == "unverified" and r.unit in published}))
    return out


def machine_version(root: Path = ROOT) -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True,
                             text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "unknown"
    return f"git:{sha}"


def rejudge_attempts(book: Path, unit: str) -> None:
    """The slow path: decode every roll and rewrite the dq records (take_dq --attempts)."""
    from scripts.episode import take_dq
    indices = sorted(int(p.name[1:3]) for p in (book / "episodes" / unit / "takes" / ENGINE).glob("T??.dq.json"))
    if indices:
        take_dq.main(book.name[:14], int(unit[2:]), indices, attempts=True)


def counts(rows: list[Row]) -> dict:
    by, cls = {}, {}
    for r in rows:
        by[r.verdict_by] = by.get(r.verdict_by, 0) + 1
        if r.fault_class:
            cls[r.fault_class] = cls.get(r.fault_class, 0) + 1
    return {"rows": len(rows), "by": dict(sorted(by.items())), "class": dict(sorted(cls.items()))}


def harvest(codex: str, book: Path, rejudge=None, extra_prose: list[Path] = ()) -> list[Row]:
    version = machine_version()
    rows = []
    for ep_dir in sorted(book.glob("episodes/ep??")):
        if rejudge:
            rejudge(book, ep_dir.name)
        rows += episode_take_rows(codex, ep_dir.name, ep_dir, version)
        rows += episode_panel_rows(codex, ep_dir.name, ep_dir, version)
    sources = prose_sources(book) + [(Path(p), None) for p in extra_prose]
    rows += prose_rows(codex, book, sources)
    return stamp(rows, book, published_units(book))


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    book = episode_home.book_dir(args[0])
    extra = args[1:] if "--prose" in argv else []
    rows = harvest(book.name[:14], book, rejudge_attempts if "--rejudge" in argv else None, extra)
    out = casebook.write_rows(book / "casebook" / casebook.LABELS, rows)
    print(json.dumps({"wrote": str(out)} | counts(rows), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
