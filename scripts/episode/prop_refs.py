#!/usr/bin/env python
"""The book's OBJECT references: bind, check and draw the things it names.

    uv run python scripts/episode/prop_refs.py <codex_id> --check          # FREE
    uv run python scripts/episode/prop_refs.py <codex_id> --bind <file>    # FREE
    uv run python scripts/episode/prop_refs.py <codex_id> --draw <id>      # FREE, LOCAL
    uv run python scripts/episode/prop_refs.py <codex_id> --draw-all       # FREE, LOCAL

The third reference kind, beside the character and the location:

    character   refs/characters/char-<id>.png   build_refs.py / cast_bust.py   free, Krea2
    location    refs/locations/loc-<id>.png     build_refs.py                  free, Krea2
    PROP        refs/props/prop-<id>.png        THIS                           free, Krea2

`--bind` takes a JSON file of prop records (the shape `studio.prop_refs.Prop`
declares), validates every one against the contract, and merges them into
`refs.json` as `kind: "prop"` rows.  The records are AUTHORED -- by a person or
by an agent reading the book -- because what a thing is and how big it is
against a body is judgement, and judgement is not a thing code does.  The
contract is what code checks.

`--draw` renders one prop locally on Krea2, free, exactly as `cast_bust.py`
renders a character.  A picture on disk is never redrawn: it is the size every
later drawing of this object is bound to.

WHY THIS EXISTS.  Episode 2 drew nine props from words alone and they landed
between 0.36x and 3.0x of their stated size -- a violin as a child's fiddle, a
shawl to the knee, a poker drawn as a walking stick.  The one prop with a
picture came back at 1.25x.  See `studio/prop_refs.py` for the numbers.
"""
from __future__ import annotations

import json
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, prop_refs
from studio.prop_refs import Prop

SEED_BASE = 50000
"""Clear of build_refs' 40000 characters/locations band, so a prop and a
character never share a seed."""


def props_dir(book: Path) -> Path:
    return book / "refs" / "props"


def seed_for(entity_id: str, tries: int = 0) -> int:
    """Stable per object, so a redraw is the same picture unless asked otherwise."""
    return SEED_BASE + zlib.crc32(entity_id.encode("utf-8")) % 100_000 + tries


def load_refs(book: Path) -> dict:
    return episode_home.read_json(book / "refs" / "refs.json")


def bound(book: Path) -> list[dict]:
    """Every prop row the book has bound, in refs.json order."""
    return [r for r in load_refs(book).get("refs", []) if r.get("kind") == "prop"]


def bind(book: Path, records: list[dict]) -> list[str]:
    """Validate authored prop records and merge them into refs.json.

    Every record goes through the contract first, so a prop missing one of its
    three measures is refused here and not discovered in a drawn sheet."""
    props = [Prop(**r) for r in records]
    data = load_refs(book)
    rows = data["refs"]
    by_id = {r.get("entity_id"): i for i, r in enumerate(rows) if r.get("kind") == "prop"}
    for prop in props:
        row = prop_refs.refs_row(prop)
        if prop.id in by_id:
            rows[by_id[prop.id]] = row
        else:
            rows.append(row)
    (book / "refs" / "refs.json").write_text(json.dumps(data, indent=1, ensure_ascii=False),
                                             encoding="utf-8")
    return [p.id for p in props]


def check(book: Path) -> dict[str, list[str]]:
    """Every complaint about every bound prop.  Free: no model, no call."""
    out: dict[str, list[str]] = {}
    for row in bound(book):
        says: list[str] = []
        try:
            prop_refs.prop_from_row(row)
        except Exception as bad:
            says.append(str(bad).splitlines()[-1].strip())
        if not (book / row["rel_path"]).exists():
            says.append(f"{Path(row['rel_path']).name}: the row names this picture and it is not on disk")
        if says:
            out[row["entity_id"]] = says
    return out


def render(prompt: str, prefix: str, seed: int, dest: Path) -> Path:
    """The one ComfyUI call.  Injected in tests so no test touches the GPU."""
    from studio.comfy import run

    written = run("image_krea2_turbo_t2i", {
        "prompt": prompt, "aspect_ratio": "1:1 (Square)", "megapixels": 1.0,
        "seed": seed, "steps": 8, "filename_prefix": prefix})
    if not written:
        raise RuntimeError(f"{prefix} produced no image")
    dest.write_bytes(written[0].read_bytes())
    return dest


def draw(book: Path, entity_id: str, render=render, redraw: bool = False) -> Path:
    """One prop's reference picture, drawn once, free and local."""
    row = next((r for r in bound(book) if r["entity_id"] == entity_id), None)
    if row is None:
        raise KeyError(f"{entity_id} has no prop row in refs.json: bind it before you draw it")
    out = book / row["rel_path"]
    if out.exists() and not redraw:
        return out
    prop = prop_refs.prop_from_row(row)
    palette = load_refs(book).get("palette", "")
    out.parent.mkdir(parents=True, exist_ok=True)
    return render(prop_refs.reference_prompt(prop, palette), f"REF-prop-{entity_id}",
                  seed_for(entity_id, 1 if redraw else 0), out)


def main(argv: list[str]) -> None:
    book = episode_home.book_dir(argv[1])
    if "--bind" in argv:
        path = Path(argv[argv.index("--bind") + 1])
        made = bind(book, json.loads(path.read_text(encoding="utf-8")))
        print(f"bound {len(made)} props: {', '.join(made)}")
    if "--draw" in argv:
        print(draw(book, argv[argv.index("--draw") + 1], redraw="--redraw" in argv))
    if "--draw-all" in argv:
        for row in bound(book):
            print(f"  {draw(book, row['entity_id'])}", flush=True)
    rows = bound(book)
    print(f"\n{len(rows)} props bound; "
          f"{sum((book / r['rel_path']).exists() for r in rows)} drawn")
    for who, says in check(book).items():
        print(f"{who}:")
        for line in says:
            print(f"    {line}")


if __name__ == "__main__":
    main(sys.argv)
