"""No paid picture is drawn without the owner saying so, in writing, for THAT
picture.

Owner, 2026-09-11: "that is why you need my approval on images; you haven't
asked one for the episode title".  The approval had been a habit, and a habit
failed: a go given for six storyboard sheets was spent on a seventh picture
nobody had approved.  So it stops being a habit and becomes a gate.

Every paid image call in the pipeline passes through `require()` first.  It
raises unless approval was given for that KIND of picture, and the only way to
give it is an explicit `--approved` on the command line, which is the owner
typing it.  An approval for one kind never covers another: `sheets` does not
buy `title`, and neither buys `cast`.
"""
from __future__ import annotations

from pathlib import Path

HOLD = Path(__file__).resolve().parents[1] / "RENDER_HOLD"
"""While this file exists, nothing starts -- no picture, no render, whatever the
command line says.

Owner, 2026-09-12: "only kill your jobs and stop them from running again until I
ask".  An approval typed into a script that is ALREADY RUNNING cannot be untyped,
and a long chain will happily walk on to its next stage and take a GPU somebody
else is using.  A file can be written in a second, from anywhere, by anyone, and
every stage reads it on the way in.  Its contents say who held it and why, and
deleting it is how the hold is lifted."""

KINDS = ("sheets", "title", "cast", "panel", "plates", "render", "publish")
"""`render` is GPU time on the owner's own ComfyUI, which is theirs to give."""


class NotApproved(RuntimeError):
    """Raised instead of spending."""


def plan_line(kind: str, detail: str, usd: float) -> str:
    """The itemised line the owner is owed before any spend.  A render costs no
    money and is still theirs to approve: it takes their GPU and their queue."""
    price = "GPU time on your ComfyUI" if kind == "render" else f"${usd:.2f}"
    return f"{kind}: {detail} — {price}"


def require(kind: str, detail: str, usd: float, approved: bool) -> None:
    """Let a paid call through only for an approval given for this kind."""
    if kind not in KINDS:
        raise ValueError(f"unknown spend kind {kind!r}; one of {KINDS}")
    if HOLD.exists():
        raise NotApproved(
            f"HELD, nothing starts while {HOLD.name} is there.\n  {plan_line(kind, detail, usd)}\n"
            f"  {HOLD.read_text(encoding='utf-8').strip() or 'no reason given'}\n"
            f"  Lift it by deleting {HOLD}")
    if not approved:
        raise NotApproved(
            f"REFUSED, no approval for this picture.\n  {plan_line(kind, detail, usd)}\n"
            f"  Show the owner the prompt, then re-run with --approved once they have said yes.\n"
            f"  An approval for another kind of picture does not count for {kind!r}.")


def approved_for(kind: str, argv: list[str]) -> bool:
    """True when the command line approves THIS kind: `--approved` alone, or
    `--approved=title` naming it.  A named approval never covers another kind."""
    for arg in argv:
        if arg == "--approved":
            return True
        if arg.startswith("--approved="):
            return arg.split("=", 1)[1].strip() == kind
    return False
