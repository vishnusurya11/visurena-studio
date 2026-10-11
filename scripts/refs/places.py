#!/usr/bin/env python
"""Each setup's place picture, at this episode's hour, from the plan. Local, $0.

    uv run python scripts/refs/places.py <book_id> <episode>                 # report
    uv run python scripts/refs/places.py <book_id> <episode> --draw          # draw what is missing
    uv run python scripts/refs/places.py <book_id> <episode> --new=<loc>="Its name" ...

For every setup with a `location`, the picture its `view` names must exist
under refs/locations/<location>/. `--draw` draws each missing one with Krea2
from the setup's own `described` words and logs it to refs/pack.jsonl.
The hour comes from the picture, never from the words, so a place at a new
hour is a new picture.

Promoted from three ep09 session scripts (audit 2026-09-22). The typed lists
of what to draw are gone -- the plan's setups ARE the list -- and so is the
step that rewrote the book's location rows to point at ep09's pictures. That
moved every earlier episode's Horsell Common into daylight. A setup's `view`
is the choice; an existing row is never touched. A place new to the book gets
a row only with the name given on the command line, because that name is
what the take's style line says.

**Look at every picture this draws before building on it.** Put the defining
state first in `described`: the lawn's fire sat about 55 words in and was not
drawn.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home
from studio.episode_home import episode_arg

ANCHOR = "wide_establishing"


def picture(book: Path, location: str, view: str) -> Path:
    return Path(book) / "refs" / "locations" / location / f"{view or ANCHOR}.png"


def status(book: Path, setups: dict) -> list[tuple[str, str, str, str]]:
    """(setup, location, view, "have" | "missing") for every setup with a place."""
    out = []
    for name, s in setups.items():
        if getattr(s, "location", ""):
            view = s.view or ANCHOR
            out.append((name, s.location, view, "have" if picture(book, s.location, view).exists() else "missing"))
    return out


def ensure_rows(book: Path, setups: dict, names: dict[str, str], number: int) -> list[str]:
    """Write a row for a place new to the book -- only with its given name --
    and NEVER touch a row that exists. Returns the rows written."""
    folder = Path(book) / "analysis" / "locations"
    wrote = []
    for s in setups.values():
        loc = getattr(s, "location", "")
        if not loc or (folder / f"{loc}.json").exists() or loc in wrote:
            continue
        if loc not in names:
            raise SystemExit(f"{loc} has no row in analysis/locations; give it a name: --new={loc}=\"...\"")
        row = {"id": loc, "name": names[loc], "aliases": [], "region": "other", "scenes": [],
               "visitors": [], "state_changes": [], "first_appearance": number,
               "profile": {"summary": s.described,
                           "design": {"views": [{"id": s.view or ANCHOR, "prompt": s.described}]}}}
        (folder / f"{loc}.json").write_text(json.dumps(row, indent=1, ensure_ascii=False), encoding="utf-8")
        wrote.append(loc)
    return wrote


LOOK = ("Rendered as an empty frame from a stylised 3D animated film: {look}, broad simplified "
        "3D shapes, flat high-chroma colour, clean edges -- not a painting and not a photograph.")
"""Root cause 2026-09-26 (D13): with no style words the house model drew places
painterly while it drew the cast as stylised 3D figures, and the storyboard takes
its style from the place picture -- people pasted onto paintings from ep09 on."""


def styled(described: str, look: str) -> str:
    """The setup's words, then the book's look when it declares one."""
    return f"{described} {LOOK.format(look=look.strip().rstrip('.'))}" if look.strip() else described


def draw_missing(book: Path, setups: dict, draw, look: str = "") -> list[Path]:
    """Draw every missing view with `draw(prompt, target)`, from its setup's words
    in the book's look."""
    made = []
    for name, loc, view, state in status(book, setups):
        if state == "missing" and picture(book, loc, view) not in made:
            target = picture(book, loc, view)
            draw(styled(setups[name].described, look), target)
            record_master(book, loc, view)
            made.append(target)
    return made


# ---- continuity (decision 2026-10-10): masters, and states one hop from them ------

EDIT = "image_qwen_image_edit_2511_single_image"
"""The existing one-image edit workflow (2511 + its Lightning LoRA); never edited."""
SAME_PLACE_BAND = 0.80
"""DINOv3 cosine of a variant to the picture it was edited from, under which the
variant FLAGS as maybe another room.  UNCALIBRATED: a flag, never a refusal,
until it is fitted on a book's known-different rooms (WotW's 17 house
pictures) -- that fit needs the GPU embedder and is not run yet."""


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")[:48]


def variant_of(view: str, state: str) -> str:
    """The variant's view id: the picture it is edited from, '__', the state."""
    return f"{view or ANCHOR}__{slug(state)}"


def derive_prompt(state: str) -> str:
    """One edit of one picture: the place kept, only the state changed."""
    return ("The same place as in the picture: the same walls, windows, doors, furniture and landmarks "
            f"in the same places, seen from the same camera position. Change only: {state.strip()}.")


def states_due(book: Path, setups: dict) -> list[tuple[str, str, str, str]]:
    """(setup, location, source view, variant) for every setup with a place
    state whose source picture is drawn and whose variant is not."""
    out = []
    for name, s in setups.items():
        state, loc, view = getattr(s, "place_state", "") or "", getattr(s, "location", ""), s.view or ANCHOR
        if state and loc and "__" not in view and picture(book, loc, view).exists():
            if not picture(book, loc, variant_of(view, state)).exists():
                out.append((name, loc, view, variant_of(view, state)))
    return out


def sha8(path: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def place_book(book: Path):
    """refs/places.json, else every location row grouped into its place."""
    from studio import continuity_place as cp
    from studio.continuity_spec import Place, PlaceBook
    path = Path(book) / "refs" / "places.json"
    if path.exists():
        return PlaceBook.model_validate_json(path.read_text(encoding="utf-8"))
    names = {r["id"]: r.get("name") or r["id"] for r in cp.location_rows(book)}
    return PlaceBook(places={pid: Place(name=names.get(pid, pid), members=members)
                             for pid, members in cp.groups(cp.location_rows(book)).items()})


def save_places(book: Path, pb) -> None:
    path = Path(book) / "refs" / "places.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pb.model_dump(mode="json"), indent=1, ensure_ascii=False), encoding="utf-8")


def place_for(pb, location: str):
    """The Place holding `location`; a location new to the table gets its own."""
    from studio.continuity_spec import Place
    pid = pb.place_of(location)
    if not pid:
        pid = location
        pb.places[pid] = Place(name=location.replace("_", " "), members=[location])
    return pb.places[pid]


def record_master(book: Path, location: str, view: str) -> None:
    """A drawn picture of a location is one of its masters (a side, frozen)."""
    from studio.continuity_spec import Master
    pb = place_book(book)
    place = place_for(pb, location)
    mid = f"{location}/{view}"
    if all(m.master_id != mid for m in place.masters):
        place.masters.append(Master(master_id=mid, location=location, view=view,
                                    sha8=sha8(picture(book, location, view))))
    save_places(book, pb)


def record_variant(book: Path, location: str, view: str, state: str, variant: str, number: int) -> None:
    """The variant into places.json, one hop from its master (by sha8)."""
    from studio.continuity_spec import State, StoryTime, Variant
    record_master(book, location, view)
    pb = place_book(book)
    place = place_for(pb, location)
    if all(s.state_id != slug(state) for s in place.states):
        place.states.append(State(state_id=slug(state), start=StoryTime(chapter=max(1, number)),
                                  until=StoryTime(chapter=max(1, number)), deltas=[state]))
    master = next(m for m in place.masters if m.master_id == f"{location}/{view}")
    place.variants.append(Variant(master_id=master.master_id, state_id=slug(state), view=variant,
                                  parent_sha8=master.sha8, sha8=sha8(picture(book, location, variant))))
    save_places(book, pb)


def derive_missing(book: Path, setups: dict, edit, number: int = 0) -> list[Path]:
    """Every due state edited ONCE from its source picture with
    `edit(prompt, source, target)`, and recorded one hop from its master."""
    made = []
    for name, loc, view, variant in states_due(book, setups):
        target = picture(book, loc, variant)
        if target in made:
            continue
        edit(derive_prompt(setups[name].place_state), picture(book, loc, view), target)
        record_variant(book, loc, view, setups[name].place_state, variant, number)
        made.append(target)
    return made


def resolve_states(doc: dict, book: Path) -> tuple[dict, list[str]]:
    """Each setup whose state variant is drawn names it as its view (a concrete
    id every reader knows -- never a 'derive:' string, A73); the names changed."""
    changed = []
    for name, s in (doc.get("setups") or {}).items():
        state, loc, view = s.get("place_state") or "", s.get("location") or "", s.get("view") or ANCHOR
        if state and loc and "__" not in view and picture(book, loc, variant_of(view, state)).exists():
            s["view"] = variant_of(view, state)
            changed.append(name)
    return doc, changed


def same_place_flag(source: Path, variant: Path, embed) -> str:
    """'' inside the same-place band, else the flag line (never a refusal)."""
    import numpy as np
    a, b = np.asarray(embed(Path(source)), dtype=float), np.asarray(embed(Path(variant)), dtype=float)
    cos = float(a @ b / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1.0))
    if cos >= SAME_PLACE_BAND:
        return ""
    return f"flag: {Path(variant).name} sits at {cos:.2f} to its source, under the same-place band {SAME_PLACE_BAND}"


def qwen_edit(book: Path):
    """The 2511 one-image edit on the local GPU, logged to pack.jsonl."""
    from studio.comfy import run, stage_image

    def edit(prompt: str, source: Path, target: Path) -> None:
        began = time.time()
        out = run(EDIT, {"prompt": prompt, "image_1": stage_image(source), "lightning": True,
                         "seed": zlib_seed(episode_home.relative(book, target))})[0]
        shutil.copyfile(out, target)
        with (Path(book) / "refs" / "pack.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"path": episode_home.relative(book, target), "workflow": EDIT,
                                 "source": episode_home.relative(book, source), "prompt": prompt,
                                 "seconds": round(time.time() - began, 1)}, ensure_ascii=False) + "\n")
        print(f"  derived {episode_home.relative(book, target)}", flush=True)
    return edit


def zlib_seed(key: str) -> int:
    import zlib
    return zlib.crc32(key.encode("utf-8"))


def krea(book: Path):
    """The house drawer: Krea2 + the Cinematic_Artstyle LoRA, logged to pack.jsonl."""
    from studio.comfy import run
    from studio.refs_pack import T2I, Job, values_for

    def draw(prompt: str, target: Path) -> None:
        job = Job("locations", target.parent.name, target.stem, T2I, prompt, 1536, 1024)
        began = time.time()
        out = run(job.workflow, values_for(job))[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out, target)
        with (Path(book) / "refs" / "pack.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"path": episode_home.relative(book, target), "workflow": job.workflow,
                                 "prompt": prompt, "seed": values_for(job)["seed"],
                                 "seconds": round(time.time() - began, 1)}, ensure_ascii=False) + "\n")
        print(f"  drew {episode_home.relative(book, target)}", flush=True)
    return draw


def main(book_id: str, number: int, drawing: bool, names: dict[str, str]) -> int:
    book = episode_home.book_dir(book_id)
    plan = episode_home.load_plan(book, number)
    setups = plan.setups
    for loc in ensure_rows(book, setups, names, number):
        print(f"  new row: {loc}")
    if drawing:
        draw_missing(book, setups, krea(book), look=plan.look)
        derive_missing(book, setups, qwen_edit(book), number=number)
    rows = status(book, setups)
    for name, loc, view, state in rows:
        print(f"  {state:8} {name:10} {loc}/{view}.png")
    return 1 if any(r[3] == "missing" for r in rows) else 0


if __name__ == "__main__":
    new = dict(a.split("=", 1)[1].split("=", 1) for a in sys.argv if a.startswith("--new="))
    names = {k: v.strip('"') for k, v in new.items()}
    raise SystemExit(main(sys.argv[1], episode_arg(sys.argv), "--draw" in sys.argv, names))
