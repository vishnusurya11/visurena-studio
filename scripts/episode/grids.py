#!/usr/bin/env python
"""Draw one setup's storyboard grid, from the plan's own prose. Local, $0.

    uv run python scripts/episode/grids.py <book_id> <episode> <setup> <cols> <rows> [tag]
                                           [--shots=1,2,3] [--seed-bump=N] [--prompt=v1|v2]

Qwen-Image-2.1 edit-multi, up to three references: cast sheets first (the
identity slots), the setup's own place picture last (the scene and style
slot). Each grid is filed under episodes/epNN/storyboard/grids/ -- the picture,
the prompt it was drawn from, and a manifest naming its shots -- and
`panels.py` cuts the panels out of it from that manifest.

Promoted from a session driver (audit 2026-09-22, items 9, 12, 16, 22). On the
way in:
- the book and the episode come from the command line; the driver once had
  `load_plan(book, 8)` in its body while it was being run for episode 9;
- the place picture is the SETUP's own view (`location_view(view=...)`): the
  driver asked for the book anchor, so after the book rows were restored it
  would have drawn ep09's pit on the old Horsell Common picture;
- grid names carry the episode: `grid_{setup}_{cols}x{rows}` in ComfyUI's one
  shared output folder would let ep10's "pit" overwrite ep09's, and the
  exporter cut the newest file of that name;
- the manifest is written AFTER the render succeeds, beside the grid, with a
  hash of the plan it was drawn from.

The prompt text is exactly the session driver's; its known faults are fixed in
their own commits, measured before and after.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import (book_look, cast_alias, cast_refs, continuity, episode_home, grid_lint, grid_room,  # noqa: F401
                    look_table, pack_refs, plan_gates)
from studio.comfy import load_workflow, stage_image, submit, wait
from studio.episode_home import episode_arg
from studio.episode_ref_official import age_of
from studio.ref_slots import stage_only
from studio.storyboard_grid import (clothes_of, framing, grid_prompt, grid_prompt_v2, no_duplicates,
                                    varied_group, whole_subject)

CLIP = "qwen3vl_8b_fp8_scaled.safetensors"
MAX_SLOTS = 3
"""The vendor's ceiling: 1-3 references, and a fourth makes it no more faithful
(researched 2026-09-20). Slot 1 is the identity anchor, the last is the scene."""

STYLE = ("DRAWN IN EXACTLY THE ART STYLE OF <image{scene}>, copied from it and not invented: a flat "
         "angular stylised 3d CGI look with visible brush-stroke colour texture, broad simplified "
         "shapes, strong flat colour, high chroma, clean poster-like edges and NO photographic "
         "depth of field, NO camera blur, NO photoreal skin or cloth. Match the palette, the "
         "brush texture and the level of stylisation of <image{scene}> exactly")

NEGATIVE = ("text, caption, subtitles, watermark, signature, blurry, photographic, modern "
            "clothing, two men dressed alike, two men in the same hat, duplicated people, "
            "extra limbs, deformed hands, mountains, cliffs, lettering, letters, words, "
            "panel labels, numbers, beard on the narrator")
"""The HOUSE grid: a book with no refs/look.json keeps both lines byte for byte."""

PHOTO_NEGATIVE = ("text, caption, subtitles, watermark, signature, blurry, modern clothing, two men "
                  "dressed alike, two men in the same hat, duplicated people, extra limbs, deformed "
                  "hands, mountains, cliffs, lettering, letters, words, panel labels, numbers")
"""A photoreal book's negative: no "photographic", and no book's own people (WotW's
"beard on the narrator").  A book files its own words as `negative` in refs/look.json."""


def look_for(book: Path, setup=None, prose: str = "") -> dict:
    """The grid prompt's look kwargs: {} keeps the house style (book_look.grid_style);
    the book's atmosphere only for a setup under the sky, solid figures unless a shot dissolves."""
    style = book_look.grid_style(book, setup, prose)
    return {"style": style, "medium": book_look.grid_medium(book)} if style else {}


AIRED_BLUR = "out of focus subject, motion smear"
"""What a book with an atmosphere bans instead of "blurry": Qwen reads "blurry"
against haze and depth, and a fog book's far distance IS soft (Jekyll ep01, LOOK.md)."""


def negative_for(book: Path) -> str:
    """The grid's negative in the book's look, with the book's own declared words.
    A book that declares its own negative is not banned the house's "mountains,
    cliffs" (a London book drew none; Jekyll ep01 G7)."""
    if not book_look.look_name(book):
        return NEGATIVE
    own = declared_negative(book)
    said = PHOTO_NEGATIVE.replace(", mountains, cliffs", "") if own else PHOTO_NEGATIVE
    said += ", photographic" if book_look.drawn(book) else ""
    said = said.replace("blurry", AIRED_BLUR) if book_look.atmosphere(book) else said
    return ", ".join(dict.fromkeys(f"{said}, {own}".split(", "))) if own else said


def declared_negative(book: Path) -> str:
    """The book's own negative words: a top-level `negative`, and the drawn look's
    `refs.negative` where the Hellsing look.json keeps it (G7: the grid read only
    the first and got nothing).  SDXL weights "(x:1.3)" are said as plain "x"."""
    look = book_look.declared(book)
    refs = look.get("refs") if isinstance(look.get("refs"), dict) else {}
    said = [str(look.get("negative", "") or ""), str(refs.get("negative", "") or "")]
    said = [re.sub(r"\(([^():]+):[\d.]+\)", r"\1", s).strip().strip(",").strip() for s in said]
    return ", ".join(s for s in said if s)

SAID = {"wide": "WIDE", "full": "FULL SHOT", "medium": "MEDIUM", "medium_close": "MEDIUM CLOSE",
        "close": "BIG CLOSE-UP", "extreme_close": "EXTREME CLOSE-UP", "insert": "INSERT"}
# every size the contract can sign (episode_spec.Size): ep21 launch16 died on
# KeyError 'full' two grids in, four signed shots sized a word this table lacked

CREATURE = re.compile(r"\b(?:cab horse|horse|pony|mare|dog|cat|cow|ox|donkey|bird)\b", re.I)
PART = re.compile(r"\b(?:head|face|hand|hands|eye|eyes|hoof|hooves|foot|feet|paw|muzzle|nose|ear|ears)\b", re.I)


def grid_name(number: int, setup: str, cols: int, rows: int, tag: str = "") -> str:
    """A grid's name, scoped to its episode so two episodes' grids never collide."""
    return f"ep{number:02d}_grid_{setup}_{cols}x{rows}{('_' + tag) if tag else ''}"


def grids_dir(book: Path, number: int) -> Path:
    return episode_home.home(book, number) / "storyboard" / "grids"


def plan_sha(book: Path, number: int) -> str:
    """Which plan a grid was drawn from, so a panel can be refused once it isn't."""
    return hashlib.sha256(episode_home.plan_path(book, number).read_bytes()).hexdigest()[:16]


SHOT_FIELDS = ("index", "setup", "size", "frame", "at_rest", "faces", "extras")
SETUP_FIELDS = ("location", "view", "described", "geometry", "landmark", "landmark_at", "landmark_size", "light")
"""Exactly what `prompt_for` reads. A shot's `motion` is the take's, not the
grid's: ep09's retakes changed three camera moves, and hashing the whole shot
would have redrawn three good grids for words they never saw.  The geometry
fields joined on 2026-09-28: they were filled in every plan and read by nothing."""


def shots_sha(ep, indices: list[int]) -> str:
    """What a grid is drawn from: the fields of its own shots and their setups
    that its prompt reads, and nothing else of the plan. One hash of the whole
    plan made a word changed in shot 11 stale every grid in ep09."""
    shots = [s for s in ep.shots if s.index in indices]
    setups = sorted({s.setup for s in shots})
    body = {"shots": [s.model_dump(mode="json", include=set(SHOT_FIELDS)) for s in shots],
            "setups": {k: ep.setups[k].model_dump(mode="json", include=set(SETUP_FIELDS))
                       for k in setups}}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def drawn_inputs(book: Path, ep, setup: str, indices: list[int], cols: int, rows: int,
                 version: str, number: int | None = None) -> str:
    """Everything a grid is drawn from: the prompt it would be given now and the
    bytes of every picture it would stage. Plan fields alone missed a rebound
    row, a redrawn sheet or place, and a prompt-builder fix -- so the chapter-6
    wardrobe on every ep09 grid could never have read as stale (2026-09-23).
    The room a chained grid stages is among those bytes: a redrawn anchor
    makes its siblings stale (2026-09-28)."""
    shots = [s for s in ep.shots if s.index in indices]
    room = room_of(book, number, ep, setup, indices) if number is not None else None
    return inputs_sha(*prompt_for(book, ep, setup, shots, cols, rows, version, room=room))


def room_of(book: Path, number: int, ep, setup: str, indices: list[int]) -> Path | None:
    """The setup's first-drawn panel this grid stages as its room, if it is not
    the anchor grid itself and the room is cut (studio/grid_room)."""
    home = episode_home.home(book, number)
    return grid_room.room_for(home, setup, indices, grid_room.anchor_shot(ep.shots, setup))


def place_words(setup) -> str:
    """The setup's GEOMETRY (which frame edge, what apparent size) and its
    landmark: the block Sherlock's sheets carried and the grids never did."""
    parts = [g] if (g := (getattr(setup, "geometry", "") or "").strip()) else []
    if mark := (getattr(setup, "landmark", "") or "").strip():
        end = "far end" if getattr(setup, "landmark_at", "far_end") == "far_end" else "start"
        size = (getattr(setup, "landmark_size", "") or "").strip()
        parts.append(f"{mark} stands at the {end} of the route in every panel"
                     + (f", at most {size}" if size else "") + ".")
    return " ".join(parts)


def inputs_sha(text: str, slots: dict) -> str:
    pictures = sorted(hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in slots.values())
    return hashlib.sha256(json.dumps([text, pictures]).encode()).hexdigest()[:16]


def wide_for(book: Path, setup) -> Path:
    """This setup's own place picture: the SETUP's view, through the same door
    the take uses, so the panel and the take can never open on different
    pictures of one place."""
    location, view = getattr(setup, "location", "") or "", getattr(setup, "view", "") or ""
    try:
        return pack_refs.location_view(book, location, view=view)
    except SystemExit:
        if not DRY:
            raise
        return Path(book) / "refs" / "locations" / location / f"{view or 'MISSING'}.png"   # --prompts reports it


def sheet_of(book: Path, who: str, look: str = "") -> Path | None:
    """The ONE-FIGURE crop of this person's sheet for the drawer, or None (words).

    ep16 (2026-10-02): a four-pose turnaround staged whole was drawn as up to
    four people, and the prompt saying 'exactly once' changed nothing; a sheet
    whose poses overlap is not staged at all.  Takes keep the whole sheet.
    A non-base LOOK stages its own picture, already one figure (2026-10-10) -- known
    by not being the base sheet, never by its folder's name (the replay staged
    the clean suit when its look lived outside refs/.../looks/)."""
    from studio.sheet_front import front_of
    if look and (drawn := pack_refs.look_sheet(book, who, look)) is not None and drawn != pack_refs.character_sheet(book, who):
        return drawn
    p = Path(book) / "refs" / "characters" / who / "sheet.png"
    if DRY:                                  # --prompts writes nothing, a sheet_front.png included
        front = p.with_name("sheet_front.png")
        return front if front.exists() else None
    return front_of(p) if p.exists() else None


def names_of(book: Path) -> dict[str, str]:
    """{name token: entity id} from the bound rows, for who a picture's words name."""
    from studio import plan_gates
    return plan_gates.names_from_refs(cast_refs.load(book).get("refs", []))


def people_in(book: Path, shots: list) -> list[str]:
    """Everyone the panels hold, first-appearance order: faces, and whoever the
    picture words name (`scene_cast.in_frame`) -- an over-the-shoulder holds the
    shoulder's owner (Jekyll ep01 shots 2 and 10)."""
    from studio import scene_cast
    names = names_of(book)
    return list(dict.fromkeys(w for s in shots for w in scene_cast.in_frame(s, names)))


def cast_of(book: Path, shots: list, reserve: int = 1, setup=None,
            aliases: dict | None = None) -> tuple[list[dict], dict]:
    """Every person the panels hold, from the bound rows, and the slots their
    sheets go in -- what is staged and what is said are the same list.
    `reserve` slots are kept for the place and, on a chained grid, the room.

    EVERY SIZE STAGES THE SHEET (owner 2026-10-14, Jekyll ep01 HEL): a wide drew
    its people from words (`wide_only`, 2026-10-02 09:39) and shot 0 held two
    strangers before Enfield "appeared" in shot 1.  The four-pose fault that rule
    answered was fixed at its cause three hours later by the one-figure crop.
    Over the ceiling the closest readable faces win (`scene_cast.pick`); the
    rest are drawn from their wardrobe words, as before."""
    from studio import scene_cast
    who = people_in(book, shots)
    chosen = set(scene_cast.pick([w for w in who if sheet_of(book, w, continuity.look_for(
        setup, w, cast_refs.row(book, w))) is not None], shots, MAX_SLOTS - reserve))
    people, slots, names = [], {}, name_tokens(book)
    for name in who:
        entry, sheet = person(book, name, setup, aliases or {}, names)
        if sheet is not None and name in chosen:
            entry["ref"] = len(slots) + 1
            slots[str(100 + entry["ref"])] = sheet
        people.append(entry)
    return people, slots


def person(book: Path, name: str, setup, aliases: dict, names: list[str]) -> tuple[dict, Path | None]:
    """One person of the grid, unslotted, and the sheet he would be staged by.
    THE ROW THE TAKE READS: refs.json, stamped with this episode's chapter (ep09
    was once dressed from a chapter hard-coded as six, 2026-09-23)."""
    row = cast_refs.row(book, name)
    look = continuity.look_for(setup, name, row)                # the setup's look (2026-10-10)
    layers, noun = layers_for(book, name, look, row), person_noun(row)
    said = re.sub(r"^(my|the|a|an)\s+", "", row["name"].strip(), flags=re.I).upper()
    return {"ref": None, "name": said, "entity": name, "display": row.get("display") or row["name"],
            "wear": " ".join(continuity.words_for(book, name, look, row).split()), "noun": noun,
            "clothes": clothes_for(book, name, layers), "line": layers_line(noun, layers, names),
            "aliases": aliases.get(name, []), "plain": plain_name(noun, layers),
            "against": (f"{said} is no other person in this storyboard: nobody else wears "
                        f"these clothes and {said} never wears anyone else's")}, sheet_of(book, name, look)


def plain_name(noun: str, layers: dict) -> str:
    """How an UNSTAGED person's name is said in the panel prose: 'the man in the
    light-brown top hat' -- lower-case words the drawer cannot letter (ep14)."""
    hat = re.split(r"[,;]", layers.get("headwear") or "")[0].strip().rstrip(".")
    return f"the {noun} in the {hat}" if hat else f"the {noun}"


def person_noun(row: dict) -> str:
    """man, woman, boy, girl or creature from the row's gender and stated age
    (takes_r2v.adopt_names' rule: under 16 is young); 'person' when unsaid."""
    gender, age = row.get("gender"), age_of(row.get("physical", ""))
    if gender == "creature":
        return "creature"
    young = age is not None and age < 16
    if gender == "female":
        return "girl" if young else "woman"
    return ("boy" if young else "man") if gender == "male" else "person"


def layers_for(book: Path, who: str, look: str, row: dict) -> dict:
    """The look's layers (refs/looks.json), the base look's when the setup's is
    not in the table; a book with no table cuts them from the row."""
    card = continuity.card_of(book, who)
    if card is not None:
        return card.looks[look if look in card.looks else card.base].layers.model_dump()
    body, _, worn = str(row.get("physical", "")).partition("Wearing:")
    head = {k: look_table.layer_text(body, "", k) for k in ("headwear", "hair", "face")}
    return {**head, "top": worn.strip()}


def clothes_for(book: Path, who: str, layers: dict) -> list[str] | None:
    """What the binding says he wears: the look table's headwear and top, clothes
    only (G5); None for a book with no table (the row's worn items, as before)."""
    return clothes_of(layers) if continuity.card_of(book, who) is not None else None


def name_tokens(book: Path) -> list[str]:
    """The book's name tokens an unstaged person's line may not carry."""
    from studio import scene_cast
    return [t for t in names_of(book) if t.lower() not in scene_cast.COMMON]


LINE_MOST = 29
"""An unstaged person's line stays under 30 words (lint P15)."""


def _line(noun: str, looks: list[str], wear: list[str]) -> str:
    said = f"a {noun}" + (f" with {', '.join(looks)}" if looks else "")
    return (said + (f", wearing {' and '.join(wear)}" if wear else "")).replace(";", ",")


def layers_line(noun: str, layers: dict, names: list[str]) -> str:
    """An UNSTAGED person in a few plain words from his look layers -- hair, face,
    headwear, top -- never his raw dossier row (Jekyll ep01 G2: "a mr. richard
    enfield (... the doctor, the child's father, and hyde spend a night ...)").
    The longest form under 30 words; '' when none is clean."""
    first = lambda k: re.split(r";", layers.get(k) or "")[0].strip().rstrip(".")  # noqa: E731
    hair, face = first("hair"), first("face")
    worn = clothes_of(layers)
    hat = [worn[0].split(",")[0]] if (layers.get("headwear") or "").strip() and worn else []
    tops = worn[len(hat):]
    short = [", ".join(t.split(", ")[:3]) for t in tops]
    for looks, wear in (([hair, face], hat + tops), ([hair, face], hat + short), ([hair], hat + short),
                        ([], hat + short[:1])):
        said = _line(noun, [x for x in looks if x], [x for x in wear if x])
        if len(said.split()) <= LINE_MOST and said != f"a {noun}":
            return "" if grid_lint.named_in(said, names) else said
    return ""


def creature_insert(shot) -> tuple[str, str] | None:
    """(creature, part) when an INSERT isolates part of a living thing: a horse's
    head cannot exist on its own (owner, 2026-09-20)."""
    if shot.size != "insert":
        return None
    beast, part = CREATURE.search(shot.frame or ""), PART.search(shot.frame or "")
    return (beast.group(0), part.group(0)) if beast and part else None


def body_of(shot) -> str:
    """The plan's own words: what is in frame, then where everything sits."""
    parts = [shot.frame.strip()]
    if rest := (getattr(shot, "at_rest", "") or "").strip():
        parts.append(rest)
    if found := creature_insert(shot):
        parts.append(whole_subject(f"the {found[0]}", f"its {found[1]}"))
    if said := varied_group(" ".join(parts), len(getattr(shot, "faces", None) or []),
                            int(getattr(shot, "extras", 0) or 0)):            # walk-ons, by the plan's count
        parts.append(said)
    return " ".join(parts)


def grid_shots(ep, setup: str, cols: int, rows: int, only: list[int] | None) -> list:
    shots = [s for s in ep.shots if s.index in only] if only else [s for s in ep.shots if s.setup == setup]
    if len(shots) != cols * rows:
        raise SystemExit(f"setup {setup!r} has {len(shots)} shots ({[s.index for s in shots]}), "
                         f"grid {cols}x{rows} wants {cols * rows}")
    return shots


def _v1(blocks: list, cols: int, rows: int, place: tuple, cast: list, style_slot: int,
        props: list | None = None, style: str = "", **_) -> str:
    cast = [{**p, "wear": p["wear"][:600]} for p in cast]      # v1's own cut, kept byte for byte
    said = style.format(n=style_slot).rstrip(".") if style else STYLE.format(scene=style_slot)
    text = grid_prompt(blocks, cols, rows, place=place, cast=cast, style=said)
    return text + "\n\n" + no_duplicates([p["name"] for p in cast])


PROMPTS = {"v1": _v1, "v2": grid_prompt_v2}
"""v2 (subject first, garments not a cut-off identity block, no "panel" in a
single picture) is the default since the same-seed A/B on ep09 (2026-09-22,
docs/calibration/grid_prompt_ab.md): v1 cloned both leads at tea and drew the
lawn's insert as a copy of its wide. v1 stays callable to reproduce old grids."""


def compose(version: str, blocks: list, cols: int, rows: int, place: tuple, cast: list,
            style_slot: int, props: list | None = None, **extra) -> str:
    if version not in PROMPTS:
        raise SystemExit(f"--prompt={version}: known versions are {sorted(PROMPTS)}")
    return PROMPTS[version](blocks, cols, rows, place, cast, style_slot, props, **extra)


def props_of(book: Path, pids: list[str], shots: list) -> list[dict]:
    """The setup's drawn props this grid's own shots NAME -- the take's rule
    (`pack_refs.props_named`), so panel and take stage the same machine.

    G-SHEET-DRAWN: a named-but-undrawn prop REFUSES here instead of being
    silently dropped by props_named's sheet filter (the wall behind step
    03_02's hook; it should never fire in a driven run)."""
    prose = pack_refs.shot_prose(shots)
    bad = pack_refs.undrawn_named(book, list(pids or []), prose)
    if bad:
        raise SystemExit(f"prop(s) {bad} named by this grid's shots and refs/props/<pid>/"
                         f"sheet.png is not drawn; run step 03")
    named = pack_refs.props_named(book, list(pids or []), prose)
    return [{"name": name, "sheet": sheet} for sheet, (name, _text) in named]


def stage_props(props: list[dict], used: int, reserve: int = 1) -> tuple[list[dict], dict]:
    """Props into the slots the cast left, the place (and the room) keeping the last."""
    out, slots = [], {}
    for p in props:
        if used >= MAX_SLOTS - reserve:
            break
        used += 1
        out.append({**p, "ref": used})
        slots[str(100 + used)] = p["sheet"]
    return out, slots


def prompt_version(argv: list[str]) -> str:
    return next((a.split("=", 1)[1] for a in argv if a.startswith("--prompt=")), "v2")


def prompt_for(book: Path, ep, setup: str, shots: list, cols: int, rows: int,
               version: str = "v2", room: Path | None = None) -> tuple[str, dict]:
    """(the grid prompt, {LoadImage node: picture}) -- `built` without its cast."""
    text, slots, _ = built(book, ep, setup, shots, cols, rows, version, room=room)
    return text, slots


def built(book: Path, ep, setup: str, shots: list, cols: int, rows: int,
          version: str = "v2", room: Path | None = None) -> tuple[str, dict, list[dict]]:
    """(the grid prompt, {LoadImage node: picture}, the cast). Only the shots this
    grid OWNS put people in the slots; a borrowed shot's cast drew line-ups.  A
    chained grid stages its setup's ROOM (grid_room) last and NOT the place
    picture: the room IS the place, so two people keep their slots (Jekyll ep01
    shots 6, 7 and 22 drew two of three people from words); the style is
    anchored on the last picture staged."""
    owned = [s for s in shots if s.setup == setup] or shots
    cast, char_slots = cast_of(book, owned, 1, ep.setups[setup], alias_table(book, ep))
    refuse_unsaid(cast)
    props, prop_slots = stage_props(props_of(book, ep.setups[setup].props, owned), len(char_slots), 1)
    slots, place_slots, style_slot, room_slot = place_slots_for(
        book, ep.setups[shots[0].setup], {**char_slots, **prop_slots}, room)
    said_as = {p["entity"]: p["name"] for p in cast}
    blocks = [{"size": SAID[s.size], "body": body_of(s),
               "cut": framing(s.size, bool(s.faces), body_of(s), move_of(s)),
               "who": [said_as[f] for f in people_in(book, [s]) if f in said_as],
               "extras": getattr(s, "extras", 0)} for s in shots]
    here = ep.setups[shots[0].setup]
    text = compose(version, blocks, cols, rows, (place_slots, here.described), cast, style_slot, props,
                   room=room_slot, geometry=place_words(here), light=getattr(here, "light", "") or "",
                   outdoors=bool(getattr(here, "outdoors", False)), **look_for(book, here, " ".join(body_of(s) for s in shots)))
    return text, slots, cast


def move_of(shot) -> str:
    """The shot's catalog move, so the panel draws the room the move needs (a rise: `framing`'s RISE_ROOM)."""
    return plan_gates.move_id(getattr(shot, "motion", "") or "", getattr(shot, "camera", "") or "")


def place_slots_for(book: Path, here, slots: dict, room: Path | None) -> tuple[dict, list, int, int | None]:
    """(every slot, the place picture's slots, the style slot, the room slot): the
    room after the people when the grid is chained, else the place picture."""
    nxt, slots = len(slots) + 1, dict(slots)
    if room is not None:
        slots[str(100 + nxt)] = Path(room)
        return slots, [], nxt, nxt
    slots[str(100 + nxt)] = wide_for(book, here)
    return slots, [nxt], nxt, None


def alias_table(book: Path, ep) -> dict[str, list[str]]:
    """{who: [epithet, ...]} the plan's own tags say (cast_alias): every shot's
    picture and motion words, against every bound row and its look layers."""
    texts = [str(getattr(s, f, "") or "") for s in ep.shots for f in ("frame", "at_rest", "end", "motion")]
    rows = {}
    for r in cast_refs.load(book).get("refs", []):
        if r.get("kind", "character") == "character":
            card = continuity.card_of(book, r["entity_id"])
            layers = [v for lk in (card.looks.values() if card else []) for v in lk.layers.model_dump().values()]
            rows[r["entity_id"]] = " ".join([str(r.get("physical", ""))] + [str(v) for v in
                                            (r.get("wardrobe") or {}).values()] + layers)
    return cast_alias.aliases(texts, rows)


def refuse_unsaid(cast: list[dict]) -> None:
    """A named person with neither a sheet slot nor a clean layers line refuses
    the grid: his raw row is what put the doctor and the child's father in it (G2)."""
    bad = [p["entity"] for p in cast if not p.get("ref") and not p.get("line") and p.get("noun") != "creature"]
    if bad:
        raise SystemExit(f"REFUSED: {bad} would be drawn with no sheet slot and no clean look-layers line "
                         f"(refs/looks.json layers): fix the layers or free a slot")


def staging(book: Path, slots: dict, cast: list[dict]) -> dict:
    """The manifest's record of what was staged, slot order, and who was words only."""
    return {"load_images": [episode_home.relative(book, Path(slots[k])) for k in sorted(slots, key=int)],
            "words_only": [p["entity"] for p in cast if not p.get("ref")]}


def lint_wall(text: str, cast: list[dict], names: list[str], outdoors: bool = False) -> None:
    """A grid whose prompt the lint refuses never reaches the GPU (studio/grid_lint)."""
    nouns = {p["ref"]: p.get("noun", "") for p in cast if p.get("ref")}
    if bad := grid_lint.faults(text, nouns, names, outdoors):
        raise SystemExit("REFUSED: grid lint: " + " | ".join(bad))
    for said in grid_lint.warnings(text):          # never refuses (craft ruling A20, A22)
        print(f"grid lint warning: {said[:200]}", flush=True)


CFG = 1.0
"""The grid sampler's cfg.  AT 1.0 THE NEGATIVE IS NEVER READ: ComfyUI skips the unconditioned pass
(comfy/samplers.py, the cfg-1 optimisation), so NEGATIVE / negative_for reached no grid ever drawn
(craft ruling A20).  Every guard must be said positively in the prompt; grid_lint warns on a negation."""


def sent_negative(negative: str, cfg: float = CFG) -> str:
    """The negative the graph carries: none at cfg 1.0, where it would be dead text."""
    return "" if cfg == 1.0 else negative


def graph_for(text: str, slots: dict, cols: int, rows: int, seed: int, name: str,
              negative: str = NEGATIVE) -> dict:
    template, _ = load_workflow("image_qwen_image_2_1_edit_multi")
    graph = {k: v for k, v in template.items()}
    graph["3"]["inputs"]["clip_name"] = CLIP
    # NOTHING STAGED THAT THE PROMPT DOES NOT NAME: an unused LoadImage holds
    # ComfyUI's example.png -- a doll -- and the encoder reads it.
    stage_only(graph, {node: stage_image(path) for node, path in slots.items()})
    graph["5"]["inputs"].update(prompt=text, negative_prompt=sent_negative(negative), resolution=1024)
    graph["6"]["inputs"].update(width=1024 * cols, height=1024 * rows)
    graph["7"]["inputs"].update(seed=seed, steps=25, cfg=CFG)
    graph["9"]["inputs"]["filename_prefix"] = name
    return graph


def file_grid(book: Path, number: int, name: str, made: list, text: str, manifest: dict) -> Path:
    """Copy the render into the episode, with its prompt and its manifest --
    AFTER it succeeded, so no manifest ever names a grid that was not drawn."""
    folder = grids_dir(book, number)
    folder.mkdir(parents=True, exist_ok=True)
    grid = folder / f"{name}.png"
    shutil.copyfile(made[0], grid)
    (folder / f"{name}.txt").write_text(text, encoding="utf-8")
    (folder / f"{name}.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return grid


def main(book_id: str, number: int, setup: str, cols: int, rows: int, tag: str = "",
         only: list[int] | None = None, seed_bump: int = 0, version: str = "v2") -> None:
    book = episode_home.book_dir(book_id)
    ep = episode_home.load_plan(book, number)
    from studio import cast_refs
    if why := cast_refs.chapter_refusal(book, number):   # this chapter's clothes (audit item 9)
        raise SystemExit(why)
    shots = grid_shots(ep, setup, cols, rows, only)
    room = room_of(book, number, ep, setup, [s.index for s in shots])
    text, slots, cast = built(book, ep, setup, shots, cols, rows, version, room=room)
    lint_wall(text, cast, name_tokens(book), bool(getattr(ep.setups[setup], "outdoors", False)))
    name = grid_name(number, setup, cols, rows, tag)
    seed = 40500 + sum(s.index for s in shots) + seed_bump
    print(f"{name}: shots {[s.index for s in shots]} | slots {sorted(slots)} | prompt {len(text)} chars",
          flush=True)
    began = time.time()
    made = wait(submit(graph_for(text, slots, cols, rows, seed, name, negative_for(book))), timeout=3600)
    grid = file_grid(book, number, name, made, text, {
        "name": name, "episode": number, "setup": setup, "cols": cols, "rows": rows,
        "shots": [s.index for s in shots], "seed": seed, "plan": plan_sha(book, number),
        "drawn_from": shots_sha(ep, [s.index for s in shots]),
        "inputs": inputs_sha(text, slots), "prompt": version,
        "room": episode_home.relative(book, room) if room else None, **staging(book, slots, cast)})
    print(f"{name} in {time.time() - began:.0f}s -> {episode_home.relative(book, grid)}", flush=True)


DRY = False
"""--prompts: build and lint only.  `sheet_of` then never writes a sheet_front.png."""


def layout_rows(book: Path, number: int, ep) -> list[dict]:
    """The episode's grids: storyboard/layout.json, else the rule from the plan."""
    from studio import grid_layout
    path = episode_home.home(book, number) / grid_layout.FILE
    if path.exists():
        return list(episode_home.read_json(path))
    shots = [s.model_dump(mode="json") for s in ep.shots]
    return grid_layout.layout({k: v.model_dump(mode="json") for k, v in ep.setups.items()}, shots)


def dry_run(book: Path, number: int, ep, rows: list[dict]) -> int:
    """Every grid's prompt built and linted, nothing staged or posted: 0 clean, 1 on any fault."""
    names, bad = name_tokens(book), 0
    for row in rows:
        shots = [s for s in ep.shots if s.index in row["shots"]]
        room = room_of(book, number, ep, row["setup"], row["shots"])
        text, slots, cast = built(book, ep, row["setup"], shots, row["cols"], row["rows"], room=room)
        faults = grid_lint.faults(text, {p["ref"]: p.get("noun", "") for p in cast if p.get("ref")}, names,
                                  bool(getattr(ep.setups[row["setup"]], "outdoors", False)))
        faults += [f"UNDRAWN staged picture not on disk: {episode_home.relative(book, Path(p))}"
                   for p in slots.values() if not Path(p).exists()]
        bad += bool(faults)
        name = grid_name(number, row["setup"], row["cols"], row["rows"], row.get("tag", ""))
        print(f"===== {name} shots {row['shots']}\n{json.dumps(staging(book, slots, cast))}\n\n{text}\n\n"
              + ("lint: clean" if not faults else "lint: " + "\n  ".join(["FAULTS"] + faults)), flush=True)
        for said in grid_lint.warnings(text):      # never counted as a fault (A20, A22)
            print(f"lint warning: {said[:200]}", flush=True)
    print(f"{len(rows)} grids, {bad} with lint faults", flush=True)
    return 1 if bad else 0


def prompts(book_id: str, number: int) -> int:
    """`grids.py <book> <n> --prompts`: the dry mode on an episode, no GPU."""
    global DRY
    DRY = True
    book = episode_home.book_dir(book_id)
    ep = episode_home.load_plan(book, number)
    return dry_run(book, number, ep, layout_rows(book, number, ep))


if __name__ == "__main__":
    if "--prompts" in sys.argv:
        raise SystemExit(prompts([a for a in sys.argv[1:] if not a.startswith("--")][0], episode_arg(sys.argv)))
    plain = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = [int(v) for a in sys.argv if a.startswith("--shots=") for v in a.split("=", 1)[1].split(",") if v]
    bump = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--seed-bump=")), "0"))
    main(plain[0], episode_arg(sys.argv), plain[2], int(plain[3]), int(plain[4]),
         plain[5] if len(plain) > 5 else "", only or None, bump, prompt_version(sys.argv))
