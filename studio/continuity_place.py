"""Places as masters, and the two plan gates whose cures are code: G-LOOK, G-PLACE.

Retro 2026-10-10 (B): the narrator's dining room was three rooms under two
location ids, the study six rooms -- every new view was a fresh draw from that
episode's words.  A PLACE owns its member location ids; each member's first
drawn picture is its MASTER; a later view of a member is its master (or one
hop from it, step 03), never a new room.

Membership, until the production designer (phase 2): a location row names its
container ("the dining room, the house"; "the garden behind the narrator's
house") and joins the row whose name or alias matches that container at 0.85.

Both gates have ONE right answer, so their cure is code and never loops the
writer (verdict S; memory: run deterministic cures before the contract):
  G-LOOK   a setup's look pick not allowed this chapter -> dropped (the row's look)
  G-PLACE  a lookalike new location id -> the member; a member with nothing drawn
           whose room another member has drawn -> that member and view; an undrawn
           view of a member with a master -> the master
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

FUZZY = 0.85
CONTAINER = re.compile(r"\b(?:of|behind|in|inside|beside)\s+(the .+)$", re.I)
SUFFIX = re.compile(r"\s+(?:at|in|near|on)\s+[A-Z][\w' ]*$")
ANCHOR = "wide_establishing"


def norm(text: str) -> str:
    """A place name compared: lower case, plain apostrophes, no 'the', no ' at <Town>'."""
    text = SUFFIX.sub("", (text or "").replace("’", "'").replace("�", "'").strip())
    return re.sub(r"^the\s+", "", re.sub(r"\s+", " ", text.lower())).strip(" .")


def names_of(row: dict) -> set[str]:
    raw = [row.get("name") or ""] + [a.split(";")[0] for a in row.get("aliases") or []]
    return {norm(n) for n in raw if norm(n)} | {row.get("id", "").replace("_", " ")}


def containers_of(row: dict) -> set[str]:
    """The places a row says it is inside: an alias's tail after a comma, or a
    name's 'of/behind/in <the X>' phrase."""
    out = set()
    for raw in [row.get("name") or ""] + [a.split(";")[0] for a in row.get("aliases") or []]:
        if "," in raw:
            out.add(norm(raw.rsplit(",", 1)[1]))
        if m := CONTAINER.search(raw.replace("’", "'")):
            out.add(norm(m.group(1)))
    return {c for c in out if c}


def alike(a: str, b: str) -> bool:
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= FUZZY


def parent_of(row: dict, rows: list[dict]) -> str:
    """The id of the row this one is inside, or ''."""
    for container in containers_of(row):
        for other in rows:
            if other["id"] != row["id"] and any(alike(container, n) for n in names_of(other)):
                return other["id"]
    return ""


def groups(rows: list[dict]) -> dict[str, list[str]]:
    """{root id: member ids}: each row joined to its container's root."""
    parent = {r["id"]: parent_of(r, rows) for r in rows}

    def root(i: str, seen=()) -> str:
        return i if not parent.get(i) or parent[i] in seen else root(parent[i], seen + (i,))
    out: dict[str, list[str]] = {}
    for r in rows:
        out.setdefault(root(r["id"]), []).append(r["id"])
    return out


def location_rows(book: Path) -> list[dict]:
    folder = Path(book) / "analysis" / "locations"
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))] if folder.exists() else []
    return [r for r in rows if r.get("id")]


def drawn_views(book: Path, location: str) -> list[str]:
    folder = Path(book) / "refs" / "locations" / location
    return sorted(p.stem for p in folder.glob("*.png")) if folder.exists() else []


def master_view(book: Path, location: str, drawn=drawn_views) -> str:
    """The member's master: its anchor when drawn, else its first drawn view, else ''."""
    views = drawn(book, location)
    return ANCHOR if ANCHOR in views else (views[0] if views else "")


def place_map(book: Path) -> dict[str, list[str]]:
    """{place id: member ids} -- refs/places.json when written, else from the rows."""
    path = Path(book) / "refs" / "places.json"
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
        return {pid: p.get("members") or [] for pid, p in (doc.get("places") or {}).items()}
    return groups(location_rows(book))


def place_of(places: dict[str, list[str]], location: str) -> str:
    return next((pid for pid, members in places.items() if location in members), "")


# ---- G-LOOK ------------------------------------------------------------------------

def bad_picks(table, setup, number: int) -> list[tuple[str, str]]:
    """(who, look) picks the table does not allow in this chapter."""
    out = []
    for pick in getattr(setup, "looks", None) or []:
        card = table.characters.get(pick.who)
        if card is not None and pick.look not in card.allowed_in(number):
            out.append((pick.who, pick.look))
    return out


def look_gate(table, episode) -> list[str]:
    """G-LOOK: every pick is a look the table allows this chapter."""
    if table is None:
        return []
    return [f"G-LOOK setup {name}: {who}'s look {look!r} is not allowed in chapter {episode.number}"
            for name, setup in episode.setups.items() for who, look in bad_picks(table, setup, episode.number)]


def cure_looks(doc: dict, table, number: int) -> dict:
    """G-LOOK's cure: a disallowed pick is dropped, so the chapter's look stands."""
    for setup in (doc.get("setups") or {}).values():
        setup["looks"] = [p for p in setup.get("looks") or []
                          if (card := table.characters.get(p.get("who"))) is None
                          or p.get("look") in card.allowed_in(number)]
    return doc


# ---- G-LOOK-WORDS on the beard (C1_verdict #6, 2026-10-11) ------------------------

TAG = re.compile(r"\(([^()]*)\)")
HEAD = re.compile(r"\b(?:face|eyes?|cheek\w*|jaw|brows?|hair|moustache|whiskers?)\b", re.I)
BEARDED = re.compile(r"\bbeard", re.I)
TAG_FIELDS = ("frame", "at_rest")
"""The prose fields a person's head tag rides in (the grid and the take read both)."""


def beard_phrase(look) -> str:
    """The look's own beard words: the face-layer clause that names the beard."""
    clauses = re.split(r"[;.]", look.layers.face or "")
    return next((c.strip() for c in clauses if BEARDED.search(c)), "")


def bearded_look(table, setup: dict, who: str, number: int):
    """(look id, look) staged for `who` when its marker is a beard, else None."""
    card = table.characters.get(who) if table else None
    if card is None:
        return None
    pick = next((p.get("look") for p in setup.get("looks") or [] if p.get("who") == who), "")
    look_id = pick if pick in card.looks else card.look_id_at(number)
    look = card.looks.get(look_id)
    return (look_id, look) if look is not None and look.markers.facial_hair == "beard" else None


def bare_head_tags(text: str) -> list[str]:
    """Head tags (they name a face, eyes, hair ...) that say no beard."""
    return [t for t in TAG.findall(text or "") if HEAD.search(t) and not BEARDED.search(t)]


def one_face_beards(doc: dict, table, number: int):
    """(shot, who, look id, look) for every one-face shot staging a bearded look."""
    for shot in doc.get("shots") or []:
        faces = shot.get("faces") or []
        found = bearded_look(table, (doc.get("setups") or {}).get(shot.get("setup")) or {}, faces[0], number) \
            if len(faces) == 1 else None
        if found:
            yield shot, faces[0], *found


def cure_beard_tags(doc: dict, table, number: int) -> dict:
    """The deterministic cure: each bare head tag gains the look's beard phrase."""
    for shot, _who, _look_id, look in one_face_beards(doc, table, number):
        phrase = beard_phrase(look)
        for field in TAG_FIELDS:
            for tag in bare_head_tags(shot.get(field) or "") if phrase else []:
                shot[field] = shot[field].replace(f"({tag})", f"({tag.rstrip()}, {phrase})")
    return doc


def look_word_faults(doc: dict, table, number: int) -> list[str]:
    """G-LOOK-WORDS (HARD on the beard): a head tag of a bearded look that says none."""
    return [f"G-LOOK-WORDS shot {shot['index']}: {who}'s look {look_id!r} has a beard; the head tag ({tag}) says none"
            for shot, who, look_id, _look in one_face_beards(doc, table, number)
            for field in TAG_FIELDS for tag in bare_head_tags(shot.get(field) or "")]


# ---- G-PLACE -----------------------------------------------------------------------

def lookalike(location: str, rows: list[dict]) -> str:
    """A known row whose names match an unknown location id at 0.85, or ''."""
    said = location.replace("_", " ")
    return next((r["id"] for r in rows if any(alike(said, n) for n in names_of(r))), "")


def own_tokens(location: str, members: list[str]) -> set[str]:
    """The id words that are this member's own: a word two members share
    ('narrators') is the owner's, not the room's."""
    words = [w for m in members for w in set(m.split("_"))]
    return {w for w in location.split("_") if words.count(w) < 2}


def sibling_view(book: Path, location: str, members: list[str], drawn=drawn_views) -> tuple[str, str]:
    """(member, view) another member has DRAWN of this member's room, or ('', '')."""
    want = own_tokens(location, members)
    for member in members:
        for view in drawn(book, member) if member != location and want else []:
            if want <= set(view.split("_")):
                return member, view
    return "", ""


FRAMING = frozenset(
    "wide medium close closeup insert reverse establishing interior exterior view pov angle shot "
    "panorama panoramic from of the at side front back high low day night dawn dusk evening morning "
    "afternoon noon sunset sunrise twilight unlit lit dark empty deserted burning ruined ruins restored "
    "wrecked flooded flood abandoned epilogue red weed fire smoke smoking ash ashes storm rain snow "
    "summer winter".split())
"""View-id words that name a FRAMING, an hour or a STATE of the same place, never
a new part of it: 'reverse', 'wide_empty', 'wide_restored_epilogue'."""


SHAPE = frozenset("wide medium close closeup insert reverse establishing interior exterior view pov angle "
                  "shot panorama panoramic from of the at side front back high low".split())


def state_words(view: str) -> str:
    """The hour and state a framing-only view id named ('wide_restored_epilogue' ->
    'restored epilogue'): what step 03 derives from the master in one hop."""
    return " ".join(w for w in view.split("_") if w in FRAMING and w not in SHAPE)


def same_place_view(view: str, location: str) -> bool:
    """Does the view id name only a framing, hour or state of this location?  Then
    it is the master (a state is derived from it at step 03); a view naming a new
    subject ('dining_room', 'coal_cellar') is a new side, drawn once and frozen."""
    return not (set(view.split("_")) - FRAMING - set(location.split("_")))


def place_fix(book: Path, places: dict, rows: list[dict], location: str, view: str,
              drawn=drawn_views, recurring: bool = True) -> tuple[str, str]:
    """The (location, view) G-PLACE rewrites a setup to; unchanged when clean."""
    known = {r["id"] for r in rows}
    if location not in known and (twin := lookalike(location, rows)):
        location = twin
    members = places.get(place_of(places, location), [location])
    master = master_view(book, location, drawn)
    if not master and (moved := sibling_view(book, location, members, drawn))[0]:
        return moved
    if recurring and master and view and view != master and "__" not in view             and view not in drawn(book, location) and same_place_view(view, location):
        return location, "" if master == ANCHOR else master
    return location, view


def recurs(book: Path, number: int, location: str) -> bool:
    """Did an earlier episode stage this location?  Then it is a recurring place
    and its views are its master (a one-off place may frame itself freely)."""
    return bool(history(book, number, [location]))


def place_gate(book: Path, episode, places: dict, rows: list[dict], drawn=drawn_views) -> list[str]:
    """G-PLACE: every setup's place is a member's master or a drawn view of it."""
    out = []
    for name, s in episode.setups.items():
        loc, view = getattr(s, "location", "") or "", getattr(s, "view", "") or ""
        again = bool(loc) and recurs(book, episode.number, loc)
        if loc and (fixed := place_fix(book, places, rows, loc, view, drawn, again)) != (loc, view):
            out.append(f"G-PLACE setup {name}: {loc}/{view or ANCHOR} would be a new room; "
                       f"its place holds it as {fixed[0]}/{fixed[1] or ANCHOR}")
    return out


def cure_places(doc: dict, book: Path, places: dict, rows: list[dict]) -> dict:
    """G-PLACE's cure: each setup rewritten to its member and master."""
    for s in (doc.get("setups") or {}).values():
        if loc := s.get("location"):
            again, view = recurs(book, int(doc.get("number") or 0), loc), s.get("view") or ""
            s["location"], s["view"] = place_fix(book, places, rows, loc, view, recurring=again)
            if view and not s["view"] and not s.get("place_state"):
                s["place_state"] = state_words(view)
    return doc


def history(book: Path, number: int, members: list[str]) -> list[str]:
    """'epNN location/view' for every earlier episode's setup in one of `members`."""
    out = []
    for plan in sorted((Path(book) / "episodes").glob("ep*/plan.json")):
        n = int(re.sub(r"\D", "", plan.parent.name) or 0)
        for s in (json.loads(plan.read_text(encoding="utf-8")).get("setups") or {}).values() if n < number else []:
            if s.get("location") in members and (said := f"ep{n:02d} {s['location']}/{s.get('view') or ANCHOR}") not in out:
                out.append(said)
    return out
