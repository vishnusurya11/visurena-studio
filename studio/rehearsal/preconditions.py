"""The chapter precondition audit (2026-10-21_ep02_proof DESIGN 4.3, R5): what a chapter needs that
the book does not hold yet, found before any rehearsal or real run.

Read-only and $0.  Every record is opened BY NAME, never a walk: `source/book.json`, the
chapter's text (`source/chapters/ch_NN.json`), `analysis/registry.json` (who a name is),
`analysis/scenes.json` and `analysis/extraction/ch_NN.json` (who is present, who speaks,
where), `refs/refs.json` (each character's base sheet), `refs/places.json` (each place's
masters), `refs/pack.jsonl` (the seconds each drawn picture took) and, per speaker,
`cast/<id>/voice/design.wav`.  Each gap carries its predicted outcome (a named park, a
just-in-time ref step, or unknown until the plan exists), the step, the code that decides
it, and a cost from the book's own records.  F14 (DESIGN 3.2) plants exactly these gaps."""
from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

NARRATOR = "narrator"
ANCHOR = "wide_establishing"
"""scripts/refs/places.py ANCHOR: the view a location with no master is drawn at."""
REQUIRED_BOOK_FIELDS = ("title", "series", "display_title", "episodes", "chapters")
"""book_title.py:104 reads `title`; youtube_retitle.series_of (step 13) refuses without series,
display_title, episodes (ep01 drive_run08.log); the chapter list names each chapter's text file."""
TITLES = re.compile(r"^(mr|mrs|dr|sir|master|miss)\.?\s+", re.IGNORECASE)
MASTER_PATH = re.compile(r"^refs/locations/[^/]+/[^/]+\.png$")
GAP_RULES = {
    "book_field": ("park", "13", "scripts/publish/youtube_retitle.py series_of: SystemExit 'source/book.json "
                   "does not say its ...' (ep01 drive_run08.log, the step 13 death)"),
    "chapter_text": ("park", "02", "the step-02 writer plans from the chapter text; no text, no plan"),
    "voice": ("park", "04", "scripts/episode/say_lines.py reference_for: FileNotFoundError '<speaker> has no "
              "cast voice' -> a bare 'say_lines.py exit 1' refusal handed to the brain; the cure is "
              "scripts/cast/cast_voices.py, which no episode step runs"),
    "base_sheet": ("jit", "refs", "studio/autopilot.py TABLE _deferred_plan: the plan's CAST BOUND refusal -> "
                   "cure cast_unbound -> the refs runner draws the sheet"),
    "place_picture": ("jit", "03", "scripts/episode/step_03_places (places.py --draw) draws a missing master "
                      "at refs/locations/<location>/<view>.png"),
    "unresolved_name": ("unknown", "02", "no registry row: the step-02 plan decides whether this person is "
                        "shown or spoken; REAL-RUN until the ch2 plan exists (SR-2)"),
}
COST_OF = {"base_sheet": "base_sheet", "place_picture": "place_picture", "voice": "voice"}


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def alias_index(registry: dict) -> dict[str, str]:
    """Every alias (and the name) of every registry character, lowercased, to its id."""
    index = {}
    for row in registry.get("characters", []):
        for name in [row.get("name", ""), *row.get("aliases", [])]:
            if name:
                index.setdefault(name.strip().lower(), row["id"])
    return index


def resolve(name: str, index: dict[str, str]) -> str | None:
    """A name the text uses -> a registry id, trying it bare and without a title."""
    said = (name or "").strip().lower()
    return index.get(said) or index.get(TITLES.sub("", said)) or None


def extraction(book: Path, chapter: int) -> dict:
    return read_json(Path(book) / "analysis" / "extraction" / f"ch_{chapter:02d}.json")


def chapter_rows(scenes: list[dict], chapter: int) -> list[dict]:
    return [s for s in scenes if s.get("chapter") == chapter]


def chapter_places(scenes: list[dict], chapter: int) -> list[str]:
    """The chapter's scene locations, in order, each once."""
    return list(dict.fromkeys(s["location_id"] for s in chapter_rows(scenes, chapter) if s.get("location_id")))


def named(names: list[str], index: dict[str, str], unresolved: set[str]) -> set[str]:
    """The ids of `names`; each name with no registry row lands in `unresolved`."""
    ids = set()
    for name in names:
        cid = resolve(name, index)
        ids.add(cid) if cid else unresolved.add(name)
    return ids


def chapter_cast(book: Path, chapter: int) -> dict:
    """Who speaks (attributed dialogue, plus the narrator), who is present, and the names no row knows."""
    index = alias_index(read_json(Path(book) / "analysis" / "registry.json"))
    scenes = extraction(book, chapter)["scenes"]
    unresolved: set[str] = set()
    said = [d["speaker_text"] for s in scenes for d in s.get("dialogue", [])]
    seen = [c["name_text"] for s in scenes for c in s.get("characters", []) if c.get("presence") == "present"]
    rows = chapter_rows(read_json(Path(book) / "analysis" / "scenes.json"), chapter)
    present = named(seen, index, unresolved) | {c for s in rows for c in s.get("characters", [])}
    return {"speakers": {NARRATOR} | named(said, index, unresolved), "present": present,
            "unresolved": unresolved}


def gap(kind: str, what: str, norms: dict, note: str = "") -> dict:
    """One gap with its predicted outcome, step, deciding code and cost from the norms."""
    outcome, step, basis = GAP_RULES[kind]
    cost = norms.get(COST_OF.get(kind, ""), {})
    return {"kind": kind, "what": what, "outcome": outcome, "step": step, "basis": basis, "note": note,
            "cost_s": cost.get("seconds"), "cost_p90_s": cost.get("p90_s"),
            "cost_basis": cost.get("basis", "no cost: not a draw")}


def book_field_gaps(said: dict) -> list[str]:
    return [k for k in REQUIRED_BOOK_FIELDS if not said.get(k)]


def chapter_text_gaps(book: Path, said: dict, chapter: int) -> list[str]:
    """The chapter's text file as book.json names it, absent or empty."""
    entry = next((c for c in said.get("chapters") or [] if c.get("n") == chapter), None)
    rel = (entry or {}).get("file") or f"chapters/ch_{chapter:02d}.json"
    path = Path(book) / "source" / rel
    return [] if path.is_file() and read_json(path).get("paragraphs") else [rel]


def voice_gaps(book: Path, speakers: set[str]) -> list[str]:
    """Speakers with no cast voice (`cast/<id>/voice/design.wav`, what say_lines clones from)."""
    return sorted(s for s in speakers if not (Path(book) / "cast" / s / "voice" / "design.wav").is_file())


def sheet_gaps(book: Path, refs: dict, present: set[str]) -> dict[str, str]:
    """Present characters whose base sheet (refs.json rel_path) is not on disk, with why."""
    rows = {r.get("entity_id"): r for r in refs.get("refs", []) if r.get("kind") == "character"}
    out = {}
    for cid in sorted(present):
        rel = (rows.get(cid) or {}).get("rel_path")
        if not rel:
            out[cid] = "no refs.json row"
        elif not (Path(book) / rel).is_file():
            out[cid] = f"refs.json names {rel}; the file is absent"
    return out


def place_of(places: dict, location: str) -> dict | None:
    return next((p for p in places.get("places", {}).values() if location in p.get("members", [])), None)


def place_gaps(book: Path, places: dict, location: str) -> list[str]:
    """`location/view` of every master the place needs that is not drawn (the anchor when it has none)."""
    place = place_of(places, location)
    masters = (place or {}).get("masters") or [{"location": location, "view": ANCHOR}]
    wanted = [f"{m['location']}/{m['view']}" for m in masters]
    return [w for w in wanted if not (Path(book) / "refs" / "locations" / f"{w}.png").is_file()]


def median_norm(seconds: list[float], basis: str) -> dict:
    """Median and p90 of the recorded seconds (a cold model load sits in the tail, so both print)."""
    if not seconds:
        return {"seconds": None, "p90_s": None, "n": 0, "basis": f"{basis}: no row"}
    ranked = sorted(seconds)
    return {"seconds": round(statistics.median(ranked), 1), "p90_s": round(ranked[int(0.9 * (len(ranked) - 1))], 1),
            "n": len(ranked), "basis": basis}


def norms(book: Path) -> dict:
    """Cost norms from the book's own draws: medians of refs/pack.jsonl seconds per picture."""
    pack = Path(book) / "refs" / "pack.jsonl"
    rows = [json.loads(l) for l in pack.read_text(encoding="utf-8").splitlines() if l.strip()] if pack.is_file() else []
    sheets = [r["seconds"] for r in rows if r.get("path", "").endswith("/sheet.png") and r.get("seconds")]
    masters = [r["seconds"] for r in rows if MASTER_PATH.match(r.get("path", "")) and "__" not in r["path"]
               and "source" not in r and r.get("seconds")]
    return {"base_sheet": median_norm(sheets, "median of refs/pack.jsonl */sheet.png rows"),
            "place_picture": median_norm(masters, "median of refs/pack.jsonl refs/locations/<loc>/<view>.png rows"),
            "voice": {"seconds": None, "p90_s": None, "n": 0,
                      "basis": "unmeasured: no record of a voice casting's seconds"}}


SOURCES = ("source/book.json", "analysis/registry.json", "analysis/scenes.json", "refs/refs.json",
           "refs/places.json", "refs/pack.jsonl")
"""The book's named records the audit opens, beside the chapter's text and extraction."""


def sources(book: Path, chapter: int) -> list[str]:
    named = [*SOURCES, f"analysis/extraction/ch_{chapter:02d}.json", f"source/chapters/ch_{chapter:02d}.json"]
    return [rel for rel in named if (Path(book) / rel).is_file()]


def book_gaps(book: Path, chapter: int, norm: dict) -> list[dict]:
    """The book.json fields and the chapter text the steps refuse without."""
    said = read_json(Path(book) / "source" / "book.json")
    return ([gap("book_field", k, norm) for k in book_field_gaps(said)]
            + [gap("chapter_text", rel, norm) for rel in chapter_text_gaps(book, said, chapter)])


def cast_gaps(book: Path, cast: dict, norm: dict) -> list[dict]:
    """Speakers with no voice, present characters with no base sheet, names with no row."""
    refs = read_json(Path(book) / "refs" / "refs.json")
    return ([gap("voice", s, norm) for s in voice_gaps(book, cast["speakers"])]
            + [gap("base_sheet", c, norm, why) for c, why in sheet_gaps(book, refs, cast["present"]).items()]
            + [gap("unresolved_name", n, norm) for n in sorted(cast["unresolved"])])


def picture_gaps(book: Path, chapter: int, norm: dict) -> list[dict]:
    """Every master of every chapter place that is not drawn."""
    places = read_json(Path(book) / "refs" / "places.json")
    scenes = read_json(Path(book) / "analysis" / "scenes.json")
    return [gap("place_picture", w, norm, f"chapter place {loc}")
            for loc in chapter_places(scenes, chapter) for w in place_gaps(book, places, loc)]


def audit(book: Path, chapter: int) -> dict:
    """Every gap the chapter meets in this book, with its prediction and cost; the records read."""
    norm, cast = norms(book), chapter_cast(book, chapter)
    gaps = book_gaps(book, chapter, norm)
    if not any(g["kind"] == "chapter_text" for g in gaps):
        gaps += cast_gaps(book, cast, norm) + picture_gaps(book, chapter, norm)
    jit = [g for g in gaps if g["outcome"] == "jit" and g["cost_s"]]
    return {"chapter": chapter, "sources": sources(book, chapter), "norms": norm,
            "cast": {k: sorted(v) for k, v in cast.items()},
            "gaps": gaps, "parks": sum(g["outcome"] == "park" for g in gaps),
            "jit_steps": sum(g["outcome"] == "jit" for g in gaps), "jit_cost_s": round(sum(g["cost_s"] for g in jit), 1),
            "jit_cost_p90_s": round(sum(g["cost_p90_s"] for g in jit), 1),
            "props": {"status": "REAL-RUN", "why": "props are named by the step-02 plan (refs/props/<pid>/"
                      "sheet.png, step 03); none is listed until the ch2 plan exists (SR-2)"}}
