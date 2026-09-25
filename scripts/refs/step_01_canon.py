#!/usr/bin/env python
"""Step 01 -- canon: which entities this book binds, as refs/refs.json rows.

    uv run python scripts/refs/step_01_canon.py <codex_id> --chapter=N --cast=a,b=Display:gender

Wraps scripts/refs/cast_rows.py: one character row per cast member, dressed in
the chapter's clothes and stamped with the chapter.  The refs stage is book-level,
so the chapter and the cast arrive as flags; without both the step refuses and
says so (a default chapter is a guess about the one thing the command is for).
Free: no model, no GPU.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import step_cli  # noqa: E402

STEP_ID = "01"
NAME = "canon"
GPU = False
SCRIPT = "scripts/refs/cast_rows.py"
USAGE = ("step 01 canon needs --chapter=N and --cast=a,b=Display:gender (who this chapter binds), "
         "e.g. uv run python scripts/refs/step_01_canon.py <codex_id> --chapter=4 --cast=narrator,wife=Wife:female")


def extra_of(ctx) -> list[str]:
    return list(getattr(ctx, "extra", None) or [])


def flag(extra: list[str], name: str) -> str | None:
    """The value of `--name=value`, or None when the flag is not there."""
    return next((a.split("=", 1)[1] for a in extra if a.startswith(f"{name}=")), None)


def chapter_of(ctx) -> int | None:
    value = flag(extra_of(ctx), "--chapter")
    return int(value) if value and value.isdigit() else None


def cast_args(ctx) -> list[str]:
    """Every `who[=Display:gender]` the --cast flag lists, as cast_rows takes them."""
    value = flag(extra_of(ctx), "--cast") or ""
    return [part.strip() for part in value.split(",") if part.strip()]


def cast_ids(ctx) -> list[str]:
    return [part.partition("=")[0] for part in cast_args(ctx)]


def refs_path(ctx) -> Path:
    return ctx.book_dir / "refs" / "refs.json"


def done(ctx) -> bool:
    """refs.json exists, stamped for the chapter asked, with a row for every cast id."""
    path = refs_path(ctx)
    if not path.exists():
        return False
    chapter = chapter_of(ctx)
    if chapter is None:
        return True
    doc = json.loads(path.read_text(encoding="utf-8"))
    have = {r.get("entity_id") for r in doc.get("refs", []) if r.get("kind") == "character"}
    return doc.get("chapter") == chapter and bool(have) and set(cast_ids(ctx)) <= have


def seed_refs(ctx) -> Path:
    """A new book has no refs.json yet; this stage is its only writer, so it opens it."""
    path = refs_path(ctx)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"book_id": ctx.codex_id, "refs": []}, indent=1), encoding="utf-8")
    return path


def run(ctx) -> None:
    chapter, cast = chapter_of(ctx), cast_args(ctx)
    if chapter is None or not cast:
        raise SystemExit(f"REFUSED: {USAGE}")
    seed_refs(ctx)
    ctx.run_script(SCRIPT, str(chapter), *cast, gpu=GPU)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
