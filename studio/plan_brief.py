"""The writer's brief: everything a plan is written FROM, gathered off disk.

One gather per file kind, each returning what a writer can judge and nothing a
gate reconstructs later (paragraph offsets, time evidence, picture paths).  The
chapter's analysis rows are required; every other input -- the chapter text,
the screenplay elements sourced from it, the bound cast rows, the places it
visits, the camera catalog, the book's dq rules -- is carried when present and
left out when not, so a book at any stage of analysis gets a brief.

The band comes from the contract (`episode_spec`), never retyped here.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import episode_spec, pack_refs

REPO = Path(__file__).resolve().parents[1]
CAMERA_CATALOG = REPO / "docs" / "calibration" / "camera_catalog.md"

SCENE_FIELDS = ("n", "para_start", "para_end", "type", "location_text", "int_ext",
                "time_of_day", "story_day", "frame", "summary", "characters", "events",
                "dialogue", "state_changes")
ELEMENT_FIELDS = ("kind", "text", "character", "parenthetical")
ROW_FIELDS = ("entity_id", "name", "display", "gender", "pronouns", "physical",
              "wardrobe", "marks", "aka")

SECTIONS = {
    "number": "## THE UNIT",
    "band": "## THE BAND (from the contract)",
    "scenes": "## THE CHAPTER'S SCENES (analysis rows)",
    "chapter_text": "## THE CHAPTER'S TEXT",
    "screenplay": "## SCREENPLAY ELEMENTS SOURCED FROM THIS CHAPTER",
    "cast": "## THE BOUND CAST ROWS (name people only through these)",
    "places": "## THE PLACES THIS CHAPTER VISITS",
    "camera_catalog": "## THE CAMERA CATALOG",
    "dq_rules": "## THE BOOK'S DQ RULES",
}
"""Section headings in render order; a brief key with no value renders no section."""


def _read(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pick(row: dict, fields: tuple[str, ...]) -> dict:
    return {k: row[k] for k in fields if k in row and row[k] not in (None, "", [], {})}


# ---- the chapter --------------------------------------------------------------------

def scenes(book_dir: Path, number: int) -> list[dict]:
    """The chapter's analysis rows, trimmed to what a writer judges.  Required."""
    path = Path(book_dir) / "analysis" / "extraction" / f"ch_{number:02d}.json"
    if not path.exists():
        raise FileNotFoundError(f"no analysis rows for chapter {number}: {path}")
    return [_pick(scene, SCENE_FIELDS) for scene in _read(path).get("scenes", [])]


def chapter_text(book_dir: Path, number: int) -> str | None:
    """The chapter's prose: the analysis copy's `text` when one exists, else the
    source paragraphs joined; None when the book has neither."""
    name = f"ch_{number:02d}.json"
    for folder in ("analysis", "source"):
        path = Path(book_dir) / folder / "chapters" / name
        if path.exists():
            doc = _read(path)
            if doc.get("text"):
                return doc["text"]
            return "\n\n".join(p.get("text", "") for p in doc.get("paragraphs", []))
    return None


def chapter_paragraphs(book_dir: Path, number: int) -> tuple[str, list[str]]:
    """(title, paragraph texts) from the source copy, for G-COVER; ('', []) when absent."""
    path = Path(book_dir) / "source" / "chapters" / f"ch_{number:02d}.json"
    if not path.exists():
        return "", []
    doc = _read(path)
    return doc.get("title", ""), [p.get("text", "") for p in doc.get("paragraphs", [])]


# ---- the screenplay -----------------------------------------------------------------

def _targets(book_dir: Path, targets: list[str] | None) -> list[Path]:
    root = Path(book_dir) / "screenplay"
    names = targets if targets is not None else sorted(p.name for p in root.iterdir()) if root.exists() else []
    return [root / t / "screenplay.json" for t in names if (root / t / "screenplay.json").exists()]


def _scene_elements(scene: dict, number: int) -> list[dict]:
    return [_pick(e, ELEMENT_FIELDS) for e in scene.get("elements", [])
            if (e.get("source") or {}).get("chapter") == number]


def screenplay(book_dir: Path, number: int, targets: list[str] | None = None) -> list[dict]:
    """Every screenplay scene holding an element sourced from this chapter, with
    only those elements; every target under `screenplay/` unless told which."""
    out = []
    for path in _targets(book_dir, targets):
        for scene in _read(path).get("scenes", []):
            if elements := _scene_elements(scene, number):
                out.append({"target": path.parent.name, "number": scene.get("number"),
                            "slug": (scene.get("slug") or {}).get("text", ""),
                            "cast": scene.get("cast", []), "elements": elements})
    return out


# ---- the cast -----------------------------------------------------------------------

def _redressed(book_dir: Path, row: dict, number: int) -> dict:
    """The row in THIS chapter's clothes when the dossier can dress it, else as stamped."""
    who = row.get("entity_id", "")
    if not (Path(book_dir) / "analysis" / "characters" / f"{who}.json").exists():
        return row
    kept = {k: row[k] for k in ("display", "gender", "pronouns", "marks", "aka") if k in row}
    return {**pack_refs.character_row(book_dir, who, number), **kept}


def cast_rows(book_dir: Path, number: int) -> list[dict]:
    """The bound character rows for this chapter, trimmed.  refs.json holds one
    chapter's clothes; a row stamped for another chapter is redressed from the
    dossier so the writer quotes the right wardrobe."""
    path = Path(book_dir) / "refs" / "refs.json"
    if not path.exists():
        return []
    doc = _read(path)
    stamped = doc.get("chapter")
    rows = [r for r in doc.get("refs", []) if r.get("kind", "character") == "character"]
    if stamped is not None and int(stamped) != number:
        rows = [_redressed(book_dir, r, number) for r in rows]
    return [_pick(r, ROW_FIELDS) for r in rows]


# ---- the places ---------------------------------------------------------------------

def _place(row: dict) -> dict:
    profile = row.get("profile") or {}
    return _pick({"id": row.get("id"), "name": row.get("name"), "aliases": row.get("aliases"),
                  "visual": profile.get("visual"), "design": profile.get("design")},
                 ("id", "name", "aliases", "visual", "design"))


def _visits(row: dict, number: int) -> bool:
    return any(s.get("chapter") == number for s in row.get("scenes") or [])


def places(book_dir: Path, number: int) -> list[dict]:
    """The location rows this chapter visits (name, visual, design); every
    location when none names the chapter; [] without a locations folder."""
    folder = Path(book_dir) / "analysis" / "locations"
    if not folder.exists():
        return []
    rows = [r for r in (_read(p) for p in sorted(folder.glob("*.json"))) if r.get("id")]
    visited = [r for r in rows if _visits(r, number)]
    return [_place(r) for r in (visited or rows)]


# ---- the rest -----------------------------------------------------------------------

def camera_catalog(path: Path | None = None) -> str | None:
    """The catalog's text; the module's CAMERA_CATALOG when no path is given."""
    path = Path(path or CAMERA_CATALOG)
    return path.read_text(encoding="utf-8") if path.exists() else None


def dq_rules(book_dir: Path) -> dict | None:
    path = Path(book_dir) / "analysis" / "dq_rules.json"
    return _read(path) if path.exists() else None


def band() -> dict:
    """The format band, read off the contract."""
    return {"min_seconds": episode_spec.MIN_SECONDS, "max_seconds": episode_spec.MAX_SECONDS,
            "words_per_second": episode_spec.WORDS_PER_SECOND,
            "max_words_per_line": episode_spec.MAX_WORDS,
            "max_lines_per_shot": episode_spec.MAX_LINES_PER_SHOT,
            "max_voices": episode_spec.MAX_SPEAKING, "max_setups": episode_spec.MAX_SETUPS,
            "dialogue_share": list(episode_spec.DIALOGUE_SHARE),
            "turn_band": list(episode_spec.TURN_BAND)}


# ---- build and render ---------------------------------------------------------------

def build(book_dir: Path, number: int, targets: list[str] | None = None) -> dict:
    """The whole brief; an optional input with nothing in it is left out."""
    book_dir = Path(book_dir)
    found = {"number": number, "band": band(), "scenes": scenes(book_dir, number),
             "chapter_text": chapter_text(book_dir, number),
             "screenplay": screenplay(book_dir, number, targets),
             "cast": cast_rows(book_dir, number), "places": places(book_dir, number),
             "camera_catalog": camera_catalog(), "dq_rules": dq_rules(book_dir)}
    return {k: v for k, v in found.items() if v not in (None, [], {}) or k in ("number", "band", "scenes")}


def _body(key: str, value) -> str:
    if key == "number":
        return f"Unit: chapter {value}. The whole chapter, one episode."
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1)


def render(brief: dict) -> str:
    """The brief as prompt text: one headed section per present input, in SECTIONS order."""
    parts = [f"{heading}\n{_body(key, brief[key])}"
             for key, heading in SECTIONS.items() if key in brief]
    return "\n\n".join(parts)
