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


def bound(book: Path) -> set[str]:
    """The characters the bible binds (rows in refs/refs.json)."""
    import json
    path = Path(book) / "refs" / "refs.json"
    if not path.exists():
        return set()
    return {r["entity_id"] for r in json.loads(path.read_text(encoding="utf-8")).get("refs", [])
            if r.get("kind") == "character"}


def speakers(book: Path) -> set[str]:
    """Everyone a plan of this book gives a line to.  A voice is for a speaker;
    a bound face that never speaks needs none (the first unattended run wanted
    35 voices for a chapter with two speakers)."""
    import json
    out = set()
    for plan in sorted(Path(book).glob("episodes/ep*/plan.json")):
        for line in json.loads(plan.read_text(encoding="utf-8")).get("lines") or []:
            if who := line.get("speaker") or line.get("who"):
                out.add(who)
    return out


def uncast(book: Path) -> list[str]:
    """The bound speakers with a card and no design clip yet."""
    wanted = bound(book) & speakers(book)
    return [who for who in carded(book) if who in wanted and not cast_home.clip(book, who).exists()]


def only_flag(ctx) -> list[str]:
    """The caller's --only when given, else the uncast bound speakers spelled out."""
    extra = extra_of(ctx)
    if any(a.startswith("--only=") for a in extra):
        return []
    return [f"--only={','.join(uncast(ctx.book_dir))}"]


def done(ctx) -> bool:
    if "--recast" in extra_of(ctx):
        return False
    return not uncast(ctx.book_dir)


def run(ctx) -> None:
    cast_home.gather(ctx.book_dir)
    if not uncast(ctx.book_dir) and not any(a.startswith(("--only=", "--recast")) for a in extra_of(ctx)):
        return                                        # nobody bound speaks without a voice; no GPU
    ctx.run_script(SCRIPT, *only_flag(ctx), *passthrough(extra_of(ctx)), gpu=GPU)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
