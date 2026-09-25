#!/usr/bin/env python
"""Step 03 -- voices: one design clip per character, filed at book level.

    uv run python scripts/refs/step_03_voices.py <codex_id> [--only=a,b] [--recast]

Wraps scripts/cast/cast_voices.py on the local TTS (GPU, $0).  Every character
home under cast/ is gathered first from the analysis dossiers (free, copies).
Done when every card has its design clip; --recast is a decision, so with it the
step always runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_home, step_cli  # noqa: E402

STEP_ID = "03"
NAME = "voices"
GPU = True
SCRIPT = "scripts/cast/cast_voices.py"
PASS = ("--only", "--recast")


def extra_of(ctx) -> list[str]:
    return list(getattr(ctx, "extra", None) or [])


def passthrough(extra: list[str]) -> list[str]:
    """The flags cast_voices takes, as given (its --only is one comma-joined value)."""
    return [arg for arg in extra if arg.partition("=")[0] in PASS]


def carded(book: Path) -> list[str]:
    return [who for who in cast_home.cast_of(book) if cast_home.card(book, who).exists()]


def uncast(book: Path) -> list[str]:
    """Every carded character with no design clip yet."""
    return [who for who in carded(book) if not cast_home.clip(book, who).exists()]


def done(ctx) -> bool:
    if "--recast" in extra_of(ctx):
        return False
    return bool(carded(ctx.book_dir)) and not uncast(ctx.book_dir)


def run(ctx) -> None:
    cast_home.gather(ctx.book_dir)
    ctx.run_script(SCRIPT, *passthrough(extra_of(ctx)), gpu=GPU)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
