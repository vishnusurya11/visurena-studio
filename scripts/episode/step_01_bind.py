#!/usr/bin/env python
"""Step 01 -- bind: this unit's cast rows, stamped with its chapter.

    uv run python scripts/episode/step_01_bind.py <codex_id> <n> --cast=<who[=Display:gender]>,<who>...

Wraps scripts/refs/cast_rows.py.  refs.json holds one chapter's clothes per
character and every later reader refuses rows stamped for another chapter, so
the step is done when the stamp is this unit's.  Without a stamp and without
a cast on the command line there is nothing to do but ask.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_refs, step_cli  # noqa: E402

STEP_ID = "01"
NAME = "bind"
GPU = False
USAGE = "step_01_bind.py <codex_id> <n> --cast=<who[=Display:gender]>,<who>..."


def cast_of(extra: list[str]) -> list[str]:
    """The members named by `--cast=a,b=Display:gender`, in the order given."""
    flag = next((a for a in extra if a.startswith("--cast=")), "")
    return [w for w in flag.split("=", 1)[1].split(",") if w] if flag else []


def stamped(book: Path, number: int) -> bool:
    """Whether refs.json's rows are this chapter's (the stamp cast_rows writes)."""
    if not (Path(book) / "refs" / "refs.json").exists():
        return False
    return cast_refs.chapter_refusal(book, number) is None


def done(ctx) -> bool:
    return not cast_of(getattr(ctx, "extra", None) or []) and stamped(ctx.book_dir, ctx.number)


def present_in(book: Path, number: int) -> set[str]:
    """The canonical ids PRESENT in the chapter's scenes (analysis/scenes.json,
    the standardize step's remap).  A journey row alone is not presence: a
    figure only spoken of in a chapter has a journey row there too, and binding
    it would order a sheet for someone who is never on screen."""
    import json
    path = Path(book) / "analysis" / "scenes.json"
    if not path.exists():
        return set()
    doc = json.loads(path.read_text(encoding="utf-8"))
    scenes = doc if isinstance(doc, list) else doc.get("scenes") or []
    return {who for s in scenes if s.get("chapter") == number for who in (s.get("characters") or [])}


def chapter_cast(book: Path, number: int) -> list[str]:
    """The chapter's individuals from the analysis, protagonist first then by
    appearances: present in a scene of the chapter (scenes.json), never a
    group, never a figure the chapter only mentions.  Falls back to the
    journey when scenes.json is absent (an older analysis)."""
    import json
    present, rows = present_in(book, number), []
    for f in sorted((Path(book) / "analysis" / "characters").glob("*.json")):
        row = json.loads(f.read_text(encoding="utf-8"))
        if row.get("role") == "group":
            continue
        on_screen = row["id"] in present if present else any(
            j.get("chapter") == number for j in row.get("journey") or [])
        if on_screen:
            rows.append(row)
    rows.sort(key=lambda r: (r.get("role") != "protagonist", -int(r.get("appearances") or 0)))
    return [r["id"] for r in rows]


def run(ctx) -> None:
    cast = cast_of(getattr(ctx, "extra", None) or []) or chapter_cast(ctx.book_dir, ctx.number)
    if not cast:
        raise SystemExit(f"REFUSED: refs.json is not stamped for this unit, no cast was given, and the "
                         f"analysis names nobody in chapter {ctx.number}\n  usage: {USAGE}")
    ctx.run_script("scripts/refs/cast_rows.py", *cast, gpu=GPU, clock="bind")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
