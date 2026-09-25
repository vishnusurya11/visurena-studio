"""Is the take on disk the take the plan would render now?

MEASURED 2026-09-20 (WotW ep05): a reviewer pass rewrote seven shots and the
prop filter stopped staging a setup's whole prop list on every take of it, so
all 28 take prompts changed -- and `takes_r2v` would have re-rendered none of
them, because its skip asked only whether the SHOT GROUPING matched and the file
existed.  The run prints nothing, DQ repeats the old numbers, and the fix that
changed the prompt never reaches a picture.

The answer is already on disk: every run writes `T<NN>.graph.json` beside its
take, "the exact graph this take ran with".  Currency is that comparison, not a
record field somebody has to remember to keep up to date.
"""
from __future__ import annotations

import json
from pathlib import Path

RENDER_NODE = "MiniMaxH3ReferenceToVideo"
UNFINISHED_S = 60.0
"""A graph this much newer than its video belongs to a render that never landed
(a real render takes minutes after its graph is written)."""


def prompt_of(graph: dict) -> str | None:
    """The prompt the render node was given, or None if the graph has no
    render node (a partial or a differently-built workflow)."""
    for node in graph.values():
        if node.get("class_type") == RENDER_NODE:
            said = node.get("inputs", {}).get("prompt")
            if isinstance(said, str):
                return said
    return None


def recorded_prompt(take: Path) -> str | None:
    """What this take was actually rendered from, read off its own graph."""
    beside = Path(take).with_suffix(".graph.json")
    if not beside.exists():
        return None
    try:
        return prompt_of(json.loads(beside.read_text(encoding="utf-8")))
    except (ValueError, OSError):
        return None


def staged_images(take: Path) -> set[str]:
    """The picture files this take's graph loaded -- content-addressed names,
    so they are the record of which bytes it rendered from."""
    beside = Path(take).with_suffix(".graph.json")
    if not beside.exists():
        return set()
    try:
        graph = json.loads(beside.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return set()
    return {n["inputs"]["image"] for n in graph.values()
            if n.get("class_type") == "LoadImage" and isinstance(n.get("inputs", {}).get("image"), str)}


def is_current(built: str, take: Path, pictures: list | None = None) -> bool:
    """True only when this take exists AND was rendered from this prompt -- and,
    when `pictures` is given, from exactly these pictures' bytes.

    MEASURED 2026-09-22 (audit item 10): with the words alone, 16 ep05 takes
    whose sheet was redrawn and 6 ep07 takes whose panel was redrawn all read
    as current, so a retake round would skip them.

    Unprovable is not current: an episode from before the graph file was
    written cannot show what it ran with, and re-rendering is the safe answer.
    Whitespace is not a picture, so a re-wrap does not spend 200 s of GPU."""
    take = Path(take)
    if not take.exists():
        return False
    # AN UNFINISHED RENDER IS NOT CURRENT: takes_r2v writes the graph before it
    # renders, so ep12 T16's interrupted run left a new graph beside the old
    # video and the runner kept it.  A graph more than a minute newer than
    # its video describes a render that never landed.
    graph = take.with_suffix(".graph.json")
    if graph.exists() and graph.stat().st_mtime - take.stat().st_mtime > UNFINISHED_S:
        return False
    said = recorded_prompt(take)
    if said is None or said.strip() != (built or "").strip():
        return False
    if pictures is None:
        return True
    from studio.comfy import staged_name
    return {staged_name(p) for p in pictures} <= staged_images(take)
