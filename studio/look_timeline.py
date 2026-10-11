"""The book's look table, `refs/looks.json`: written once per book (refs 01_03).

Two sources, one contract (`studio.continuity_spec.CharacterLooks`):

  * a dossier that already carries a costume plot (`profile.wardrobe` +
    `wardrobe_by_chapter`, WotW's format) is read as-is: `looks_from_dossier`;
  * every other book: the look-timeline writer reads the script supervisor's
    `state_changes` and returns looks; a non-base look lands only when its quote
    is found in its chapter at SPAN_MATCH (the G-SOURCE matcher):
    `looks_from_draft`.  A book without this table would draw one look for
    everyone (verdict S, fact 2).

The body is the dossier's physical with no hair, beard or hat (`look_table`).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio import look_table as lt
from studio.continuity_spec import CharacterLooks, Layers, Look, LookBook, Markers, Source, Span, StoryTime

SPAN_MATCH = 0.85
"""A look's quote must be in its chapter at this ratio (plan_gates.SPAN_MATCH)."""
APPEARANCE = re.compile(r"\b(?:hair|beard|bald|shav|hat|cap|bonnet|cloth|dress|coat|shirt|suit|naked|"
                        r"wound|injur|blood|scar|bruise|burn|bandag|dust|mud|soot|wet|soak|disguis|"
                        r"wear|wore|cloak|uniform|rags?|filth|grey|gray|gaunt|thin)\w*", re.I)
"""Ledger rows a costume supervisor reads: what the camera would see change."""


def appearance_rows(card: dict) -> list[dict]:
    """The continuity ledger rows about appearance, in story order."""
    rows = [r for r in card.get("state_changes") or []
            if r.get("subtype") == "injury" or APPEARANCE.search(f"{r.get('change', '')} {r.get('evidence', '')}")]
    return sorted(rows, key=lambda r: (r.get("chapter") or 0, r.get("scene") or 0))


def dossier_text(card: dict) -> str:
    """The one character's dossier as the writer reads it."""
    prof = card.get("profile") or {}
    ledger = [f"ch{r.get('chapter')} sc{r.get('scene')}: {r.get('change')} | evidence: \"{r.get('evidence')}\""
              for r in appearance_rows(card)]
    evolution = [f"ch{e.get('chapter')}: {e.get('change')}" for e in prof.get("physical_evolution") or []]
    return "\n".join([f"NAME: {card.get('name') or card.get('id')}",
                      f"FIRST SEEN: chapter {min(card.get('appearances') or [1])}",
                      f"BODY: {prof.get('physical') or ''}",
                      "PHYSICAL EVOLUTION:", *evolution, "CONTINUITY LEDGER:", *ledger])


def quote_found(row, chapter_text) -> bool:
    """Is the look's quote in its chapter at SPAN_MATCH?"""
    from studio import plan_gates
    text = chapter_text(row.quote_chapter or row.start_chapter) if row.quote.strip() else None
    return bool(text) and plan_gates.span_match(row.quote, text) >= SPAN_MATCH


def resolved(row, base) -> Layers:
    """A row's layers, an empty one inheriting the base's (the skill: 'leave a
    layer empty when the look does not change it')."""
    names = ("headwear", "hair", "face", "top", "dirt")
    return Layers(**{k: getattr(row, k) or getattr(base, k) for k in names})


def with_head(layers: Layers, physical: str) -> Layers:
    """Every look carries a whole head: a hair, face or hat layer the look does
    not state is the dossier body's own (the body itself keeps none)."""
    fill = {k: getattr(layers, k) or lt.layer_text(physical, "", k) for k in ("hair", "face", "headwear")}
    return layers.model_copy(update=fill)


def markers_from(layers: Layers, physical: str) -> Markers:
    """Closed markers from explicit layers; hair and beard fall back to the body."""
    body_hair = lt.layer_text(physical, "", "hair")
    body_face = lt.layer_text(physical, "", "face")
    return Markers(headwear=lt.first_of(lt.HEADWEAR, layers.headwear),
                   hair_colour=lt.first_of(lt.HAIR, layers.hair or body_hair),
                   facial_hair=lt.first_of(lt.FACIAL, layers.face or body_face),
                   top=lt.first_of(lt.TOP, layers.top), dirt=lt.first_of(lt.DIRT, layers.dirt))


def face_changed(markers: Markers, base: Markers) -> bool:
    return (markers.hair_colour, markers.facial_hair) != (base.hair_colour, base.facial_hair)


def span_of(row) -> Span:
    until = StoryTime(chapter=row.until_chapter, scene=row.until_scene) if row.until_chapter else None
    return Span(look=row.look_id, start=StoryTime(chapter=row.start_chapter, scene=row.start_scene), until=until)


def kept_rows(draft, chapter_text) -> list:
    """The base (earliest) row, then every later row whose quote is found; a
    second row starting at the same story time is dropped."""
    rows = sorted(draft.looks, key=lambda r: (r.start_chapter, r.start_scene or 1))
    kept, starts = rows[:1], {(rows[0].start_chapter, rows[0].start_scene or 1)} if rows else set()
    for row in rows[1:]:
        at = (row.start_chapter, row.start_scene or 1)
        if at not in starts and quote_found(row, chapter_text):
            kept.append(row)
            starts.add(at)
    return kept


def looks_from_draft(draft, card: dict, chapter_text) -> CharacterLooks:
    """The writer's draft under the contract: quotes verified, layers resolved,
    markers closed, the body cut free of its head."""
    physical = ((card.get("profile") or {}).get("physical") or "").strip()
    rows = kept_rows(draft, chapter_text)
    base_row = rows[0]
    base_markers = markers_from(resolved(base_row, base_row), physical)
    looks = {}
    for row in rows:
        layers = with_head(resolved(row, base_row), physical)
        markers = markers_from(layers, physical)
        looks.setdefault(row.look_id, Look(
            layers=layers, markers=markers, made_by="base" if row is base_row else "fresh",
            source=[Source(chapter=row.quote_chapter or row.start_chapter, quote=row.quote)] if row.quote else [],
            face_change=row is not base_row and face_changed(markers, base_markers)))
    return CharacterLooks(base=base_row.look_id, body=lt.body_of(physical), looks=looks,
                          timeline=[span_of(r) for r in rows])


def plot_spans(plot: dict) -> list[tuple[str, int]]:
    """(look, chapter) wherever the chapter-keyed costume plot changes look."""
    out: list[tuple[str, int]] = []
    for chapter in sorted(int(c) for c in plot if str(c).isdigit()):
        look = plot[str(chapter)]
        if not out or out[-1][0] != look:
            out.append((look, chapter))
    return out


def dossier_look(physical: str, worn: str, base: Markers | None) -> Look:
    """One WotW wardrobe entry as a look: its layers, markers and face change."""
    parsed = lt.parse(worn)
    pick = lambda name: lt.render(lt.keep(parsed, lambda layer: layer == name))   # noqa: E731
    layers = with_head(Layers(headwear=pick("headwear"), hair=pick("hair"), face=pick("face"),
                              top=lt.render(lt.keep(parsed, lambda layer: layer not in lt.HEAD))), physical)
    markers = Markers(**lt.markers_of(physical, worn))
    return Look(layers=layers, markers=markers, made_by="base" if base is None else "fresh",
                face_change=base is not None and face_changed(markers, base))


def looks_from_dossier(card: dict) -> CharacterLooks | None:
    """A dossier's own costume plot as the look table, or None without one."""
    prof = card.get("profile") or {}
    plot, wardrobe = prof.get("wardrobe_by_chapter") or {}, prof.get("wardrobe") or {}
    spans = plot_spans(plot) if wardrobe else []
    if not spans:
        return None
    physical = (prof.get("physical") or "").strip()
    base = dossier_look(physical, wardrobe.get(spans[0][0], ""), None)
    looks = {spans[0][0]: base}
    for look, _ in spans[1:]:
        looks.setdefault(look, dossier_look(physical, wardrobe.get(look, ""), base.markers))
    timeline = [Span(look=look, start=StoryTime(chapter=chapter)) for look, chapter in spans]
    return CharacterLooks(base=spans[0][0], body=lt.body_of(physical), looks=looks, timeline=timeline)


def look_words(card: CharacterLooks, look_id: str) -> str:
    """A look as a row's `physical`: its head first (hair, face, hat -- the
    defining layers lead), the invariant body, then what it wears."""
    layers = card.looks[look_id].layers
    head = "; ".join(x.strip().rstrip(".") for x in (layers.hair, layers.face, layers.headwear) if x.strip())
    worn = " ".join(x.strip() for x in (layers.top, layers.dirt) if x.strip())
    parts = [head[:1].upper() + head[1:] + "." if head else "", card.body.strip(),
             f"Wearing: {worn}" if worn else ""]
    return " ".join(p for p in parts if p)


def path_of(book: Path) -> Path:
    return Path(book) / "refs" / "looks.json"


def load(book: Path) -> LookBook | None:
    """The book's look table, or None: a book without one runs the legacy path."""
    path = path_of(book)
    return LookBook.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


HEAD = ("hair", "face", "headwear")


def head_refusal(who: str, looks: CharacterLooks) -> str | None:
    """Why a NEW table may not carry `who`: every look's head layers are empty, so
    every head marker is blank and LOOK-STATE would pass anything (C1_verdict #9,
    Jekyll and Hyde).  None when any look authors any head layer."""
    if any(getattr(look.layers, k).strip() for look in looks.looks.values() for k in HEAD):
        return None
    return (f"{who}: head unauthored -- no look names hair, face or headwear, so LOOK-STATE "
            f"would judge blank markers; author the head in the dossier's physical first")


def write_looks(book: Path, who: str, looks: CharacterLooks) -> Path:
    """One character's looks merged into the book's table (others kept)."""
    table = load(book) or LookBook(book=Path(book).name)
    table.characters[who] = looks
    path = path_of(book)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(table.model_dump(mode="json"), indent=1, ensure_ascii=False), encoding="utf-8")
    return path
