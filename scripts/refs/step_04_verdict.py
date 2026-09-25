#!/usr/bin/env python
"""Step 04 -- verdict: ESCALATE LOOK, the owner's one taste gate per (book, style).

    uv run python scripts/refs/step_04_verdict.py <codex_id>

Never passes on its own.  Done only when refs/verdict.json signs the sha8 of
refs/pack.jsonl as it stands; otherwise the step parks the unit with the call-
sheet line and the owner signs with scripts/refs/sign_look.py.  A verdict for
an earlier pack is stale: the ask says how many rows arrived since.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import refs_verdict, step_cli  # noqa: E402
from studio.escalate import Escalation  # noqa: E402

STEP_ID = "04"
NAME = "verdict"
GPU = False
GATE = "LOOK"


def done(ctx) -> bool:
    return refs_verdict.current(ctx.book_dir) is not None


def run(ctx) -> None:
    if refs_verdict.read(ctx.book_dir):
        n = refs_verdict.new_rows(ctx.book_dir)
        ctx.log(f"stale: {refs_verdict.VERDICT} signs another pack; {n} new row(s) since",
                step_id=STEP_ID, level="WARNING")
        raise Escalation(GATE, refs_verdict.VERDICT, f"the pack changed since the last look: {n} new row(s)")
    raise Escalation(GATE, refs_verdict.VERDICT, "look at every sheet in refs/ and sign")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
