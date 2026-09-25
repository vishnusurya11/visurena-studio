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


def run(ctx) -> None:
    cast = cast_of(getattr(ctx, "extra", None) or [])
    if not cast:
        raise SystemExit(f"REFUSED: refs.json is not stamped for this unit and no cast was given\n"
                         f"  usage: {USAGE}")
    ctx.run_script("scripts/refs/cast_rows.py", *cast, gpu=GPU, clock="bind")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
