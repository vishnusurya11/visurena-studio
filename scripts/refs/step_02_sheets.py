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


def jobs(ctx) -> list:
    """The pictures build_pack would draw now: every job without its file on disk."""
    bp = pack_module()
    extra = extra_of(ctx)
    kinds = values(extra, "--kind") or bp.KINDS
    only = values(extra, "--only") or None
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


def run(ctx) -> None:
    asked = jobs(ctx)
    ctx.run_script(SCRIPT, *passthrough(extra_of(ctx)), gpu=GPU)
    advise(ctx, asked, getattr(ctx, "look", None))


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
