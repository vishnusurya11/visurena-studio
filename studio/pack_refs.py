"""The book's reference pack, read the way a references-only take needs it.

The pack (`scripts/refs/build_pack.py`) draws, per book:

    refs/characters/<id>/sheet.png     ONE sheet per character
    refs/locations/<id>/<view>.png     the views listed in the location's design
    refs/props/<id>/sheet.png          a short list of props only

A take with no storyboard cell OPENS AT ITS LOCATION PICTURE'S FRAMING (ep14,
2026-09-17: a medium handed a room picture started far too wide).  So the view
is chosen by the shot's size -- a wide gets a wide view, an insert an insert
view -- and a take is never handed a face alone (ep14: it invented a Gothic
hall).  Wardrobe states are not drawn: the chapter's state is said in words.
"""
from __future__ import annotations

import json
from pathlib import Path

PREFER = {
    "insert": ("insert", "medium", "medium-wide", "wide"),
    "close": ("medium", "medium-wide", "wide", "insert"),
    "medium_close": ("medium", "medium-wide", "wide", "insert"),
    "medium": ("medium", "medium-wide", "wide", "insert"),
    "full": ("wide", "medium-wide", "medium", "insert"),
    "wide": ("wide", "medium-wide", "medium", "insert"),
}
"""Which drawn view sizes a shot size takes, best first.  A face close takes a
MEDIUM view before an insert one: every insert view in this pack is an object
(an eyepiece field, a table top), and a face opened on an object is a cut."""


def view_class(shot_size: str) -> str:
    """A view's `shot_size` as one of the four drawn classes."""
    s = (shot_size or "").lower().replace("_", "-")
    if s.startswith("insert") or s == "close":
        return "insert"
    if s == "medium-wide":
        return "medium-wide"
    if s.startswith("medium"):
        return "medium"
    return "wide"


def view_for(size: str, views: list[dict], drawn: set[str], named: str = "") -> str:
    """The view a shot of `size` opens on: `named` when the plan names one, else
    the first drawn view of the best class for that size."""
    if named:
        if named not in drawn:
            raise SystemExit(f"view {named!r} is named by the plan and is not drawn")
        return named
    on_disk = [v for v in views if v["id"] in drawn]
    for cls in PREFER.get(size, PREFER["medium"]):
        hit = next((v["id"] for v in on_disk if view_class(v.get("shot_size", "")) == cls), None)
        if hit:
            return hit
    raise SystemExit(f"no drawn view for a {size} shot among {sorted(drawn) or 'nothing'}")


def views_of(book: Path, location: str) -> list[dict]:
    """The location's designed views, in the design's own order."""
    row = json.loads((Path(book) / "analysis" / "locations" / f"{location}.json").read_text(encoding="utf-8"))
    return (row.get("profile") or {}).get("design", {}).get("views") or []


ANCHOR = "wide_establishing"


def location_view(book: Path, location: str, size: str = "", named: str = "") -> Path:
    """The ONE picture that says WHERE: the establishing wide, else the design's
    first view, whatever the shot's size (owner, 2026-09-18: two views of one
    observatory were two rooms -- a slim refractor and a pier telescope -- and the
    cut jumped between them).  The take's camera finds the closer framing."""
    views = views_of(book, location)
    anchor = next((v["id"] for v in views if v["id"] == ANCHOR), views[0]["id"] if views else ANCHOR)
    path = Path(book) / "refs" / "locations" / location / f"{anchor}.png"
    if not path.exists():
        raise SystemExit(f"location {location!r}: its one picture {anchor}.png is not drawn")
    return path


def character_sheet(book: Path, who: str) -> Path | None:
    """The character's one sheet, or None when the pack has not drawn it."""
    path = Path(book) / "refs" / "characters" / who / "sheet.png"
    return path if path.exists() else None


def prop_sheet(book: Path, pid: str) -> Path | None:
    """The prop's one sheet, or None when the pack has not drawn it."""
    path = Path(book) / "refs" / "props" / pid / "sheet.png"
    return path if path.exists() else None


def prop_row(book: Path, pid: str) -> tuple[str, str]:
    """How a take names and defines a prop: its body and its scale.  A state
    sentence ("Once open, ...") belongs to a later chapter; the shot's own words
    say what the prop is doing now (ep02: the lid is still shut)."""
    card = json.loads((Path(book) / "analysis" / "props" / f"{pid}.json").read_text(encoding="utf-8"))
    prof = card.get("profile") or {}
    body = [s.strip() for s in (prof.get("physical") or "").split(". ") if s.strip()]
    body = [s if s.endswith(".") else s + "." for s in body if not s.startswith("Once ")]
    text = " ".join(body + [(prof.get("scale") or "").strip()]).strip()
    return f"the {card.get('name', pid.replace('_', ' '))}", text


def wardrobe_state(by_chapter: dict, chapter: int) -> str:
    """The chapter's wardrobe state; a chapter with no entry keeps the last one before it."""
    earlier = [int(c) for c in by_chapter if str(c).isdigit() and int(c) <= chapter]
    return by_chapter[str(max(earlier))] if earlier else ""


def character_row(book: Path, who: str, chapter: int) -> dict:
    """A refs.json character row built from the dossier: the invariant body, then
    the chapter's clothes in words (the sheet shows one wardrobe only)."""
    card = json.loads((Path(book) / "analysis" / "characters" / f"{who}.json").read_text(encoding="utf-8"))
    prof = card.get("profile") or {}
    worn = (prof.get("wardrobe") or {}).get(wardrobe_state(prof.get("wardrobe_by_chapter") or {}, chapter), "")
    body = (prof.get("physical") or "").strip()
    physical = f"{body} Wearing: {worn.strip()}" if worn else body
    return {"ref_id": f"char-{who}", "kind": "character", "entity_id": who,
            "name": card.get("name", who), "physical": physical,
            "wardrobe": {"indoor": worn.strip(), "outdoor": worn.strip()},
            "rel_path": f"refs/characters/{who}/sheet.png"}


def props_for(book: Path, pids: list[str]) -> list[tuple[Path, tuple[str, str]]]:
    """The setup's props that have a drawn sheet, each with its definition."""
    return [(sheet, prop_row(book, pid)) for pid in pids if (sheet := prop_sheet(book, pid))]


def rows_for(book: Path, chapter: int, cast: list[str], old: list[dict],
             named: dict[str, tuple[str, str]] | None = None) -> list[dict]:
    """refs.json's character rows for one chapter: the cast rebuilt from the
    dossier in that chapter's clothes, each keeping its display name and gender
    (or taking the ones `named` gives), and every other row kept as it was."""
    before = {r.get("entity_id"): r for r in old}
    rows = []
    for who in cast:
        row = character_row(book, who, chapter)
        display, gender = (named or {}).get(who, (before.get(who, {}).get("display"),
                                                   before.get(who, {}).get("gender")))
        rows.append({**row, **({"display": display} if display else {}), **({"gender": gender} if gender else {})})
    return rows + [r for r in old if r.get("entity_id") not in cast]
