#!/usr/bin/env python
"""Step 02 -- sheets: one picture per character, prop and location, drawn locally.

    uv run python scripts/refs/step_02_sheets.py <codex_id> [--kind=characters] [--only=a,b] [--limit=N] [--dry]

Wraps scripts/refs/build_pack.py on the local image model (GPU, $0).  Done when
every job build_pack would draw already has its picture on disk -- a picture is
never redrawn.  After drawing, the look-back agent reads each new picture against
its own prompt's nouns; a miss is a WARNING line, never a refusal (advisory until
calibrated, decision 2026-09-24 D8).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import look_back  # noqa: E402
from studio import step_cli  # noqa: E402

STEP_ID = "02"
NAME = "sheets"
GPU = True
SCRIPT = "scripts/refs/build_pack.py"
PASS = ("--kind", "--only", "--limit", "--dry")


def pack_module():
    """build_pack itself, imported by its package path: no cwd, no sys.path games."""
    return importlib.import_module("scripts.refs.build_pack")


def extra_of(ctx) -> list[str]:
    return list(getattr(ctx, "extra", None) or [])


def values(extra: list[str], name: str) -> list[str]:
    """Every value of a repeatable `--name=a,b` flag, flattened."""
    out = []
    for arg in extra:
        if arg.startswith(f"{name}="):
            out += [v for v in arg.split("=", 1)[1].split(",") if v]
    return out


def passthrough(extra: list[str]) -> list[str]:
    """The flags build_pack takes, one value per flag (its --kind and --only append)."""
    out = []
    for arg in extra:
        name, _, value = arg.partition("=")
        if name in PASS:
            out += [f"{name}={v}" for v in value.split(",") if v] if value else [name]
    return out


BOUND_KINDS = ("characters", "props")
"""What the reference bible draws on its own: the characters and props the
line has BOUND (rows in refs/refs.json).  Never every entity the analysis
knows -- the first unattended run wanted 66 pictures for a chapter that needed
one -- and never locations: a place is drawn per episode at its own hour."""


def bound(book_dir: Path) -> list[str] | None:
    """The entity ids refs.json binds, or None when no bible exists yet (an old
    book before its first bind: then every flag decides, as before)."""
    import json
    path = Path(book_dir) / "refs" / "refs.json"
    if not path.exists():
        return None
    return [r["entity_id"] for r in json.loads(path.read_text(encoding="utf-8")).get("refs", [])
            if r.get("kind") in ("character", "prop", "characters", "props")]


def scope(ctx) -> tuple[tuple[str, ...], list[str] | None]:
    """(kinds, only): the flags when given, else the bound rows of the bible."""
    bp = pack_module()
    extra = extra_of(ctx)
    kinds = tuple(values(extra, "--kind")) or (BOUND_KINDS if bound(ctx.book_dir) is not None else bp.KINDS)
    only = values(extra, "--only") or bound(ctx.book_dir)
    return kinds, only


def jobs(ctx) -> list:
    """The pictures build_pack would draw now: every BOUND job without its file on disk."""
    bp = pack_module()
    kinds, only = scope(ctx)
    return bp.pending(bp.all_jobs(ctx.book_dir, kinds, only), lambda rel: (ctx.book_dir / rel).exists())


def done(ctx) -> bool:
    return not jobs(ctx)


def advise(ctx, asked: list, look=None) -> list[str]:
    """The look-back over the pictures drawn this run: one WARNING per miss, no refusal."""
    bp = pack_module()
    read = look or look_back.look
    misses = []
    for job in asked:
        picture = ctx.book_dir / bp.relpath(job)
        if not picture.exists():
            continue
        reading = read(picture, job.prompt)
        if reading.missing or reading.text:
            line = f"look-back {bp.relpath(job)}: missing {reading.missing}" + ("; lettering" if reading.text else "")
            ctx.log(line, step_id=STEP_ID, level="WARNING")
            print(f"WARNING {line}")
            misses.append(line)
    return misses


def scope_flags(ctx) -> list[str]:
    """What build_pack is told to draw: the caller's flags when given, else the
    bound scope spelled out, so the script can never widen to the whole book."""
    extra = extra_of(ctx)
    if values(extra, "--kind") or values(extra, "--only") or bound(ctx.book_dir) is None:
        return passthrough(extra)
    kinds, only = scope(ctx)
    return [f"--kind={k}" for k in kinds] + [f"--only={w}" for w in (only or [])] + passthrough(extra)


def run(ctx) -> None:
    asked = jobs(ctx)
    if not asked:
        return                                       # nothing bound is missing; no GPU
    ctx.run_script(SCRIPT, *scope_flags(ctx), gpu=GPU)
    advise(ctx, asked, getattr(ctx, "look", None))


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
