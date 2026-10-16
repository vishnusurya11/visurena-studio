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
import os
from pathlib import Path

RENDER_NODE = "MiniMaxH3ReferenceToVideo"
UNFINISHED_S = 60.0
"""A graph this much newer than its video belongs to a render that never landed
(a real render takes minutes after its graph is written)."""


def graph_of(take: Path) -> Path:
    """The graph a take ran with, beside it: `T05.mp4` -> `T05.graph.json`."""
    return Path(take).with_suffix(".graph.json")


def stamp_landed(take: Path) -> None:
    """A take that became the kept take NOW has landed now.

    Jekyll HEL ep01 v2 (2026-10-15): `take_dq --attempts` renamed an hour-old
    attempt into T22.mp4; a rename keeps the mtime, the graph beside it was
    younger than UNFINISHED_S allows, and the kept take read as an interrupted
    render -- re-rendered over, twice on T19."""
    os.utime(take)


def prompt_of(graph: dict) -> str | None:
    """The prompt the render node was given, or None if the graph has no
    render node (a partial or a differently-built workflow)."""
    for node in graph.values():
        if isinstance(node, dict) and node.get("class_type") == RENDER_NODE:
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


STUB = {"unknown_provenance": True}
"""What sits beside a kept take whose roll had no graph of its own (audit
2026-10-15, 3.3): `swap_in` used to COPY the displaced take's graph there, so a
record said the roll ran with another render's pictures.  The stub says only
that nobody knows -- and unknown is never current."""


def read_graph(take: Path) -> dict | None:
    """The graph beside a take as a dict, or None (absent, unreadable, not a dict)."""
    beside = graph_of(take)
    if not beside.exists():
        return None
    try:
        graph = json.loads(beside.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    return graph if isinstance(graph, dict) else None


def nodes_of(take: Path) -> list[dict]:
    """The graph's nodes; none for a stub, an absent or an unreadable graph."""
    return [n for n in (read_graph(take) or {}).values() if isinstance(n, dict)]


def write_stub(path: Path) -> None:
    """The unknown-provenance stub at `path` (over whatever orphan sat there)."""
    Path(path).write_text(json.dumps(STUB), encoding="utf-8")


def carry_graph(own: Path, dest: Path) -> None:
    """A render's OWN graph to `dest`, or the stub when it has none: a roll only
    ever carries the record of what it ran with (LESSONS, 3ae4584)."""
    if Path(own).exists():
        Path(own).replace(dest)
    else:
        write_stub(dest)


def provenance_unknown(take: Path) -> bool:
    """No graph beside the take, or the stub: what it ran with cannot be shown."""
    graph = read_graph(take)
    return graph is None or bool(graph.get("unknown_provenance"))


def staged_images(take: Path) -> set[str]:
    """The picture files this take's graph loaded -- content-addressed names,
    so they are the record of which bytes it rendered from."""
    return {n["inputs"]["image"] for n in nodes_of(take)
            if n.get("class_type") == "LoadImage" and isinstance(n.get("inputs", {}).get("image"), str)}


def recorded_canvas(take: Path) -> tuple[int, int] | None:
    """The width and height this take actually rendered at, off its own graph."""
    for node in nodes_of(take):
        inputs = node.get("inputs", {})
        if isinstance(inputs.get("width"), int) and isinstance(inputs.get("height"), int):
            return (inputs["width"], inputs["height"])
    return None


def is_current(built: str, take: Path, pictures: list | None = None,
               canvas: tuple[int, int] | None = None) -> bool:
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
    # THE CANVAS IS AN INPUT: ep14 (2026-09-30) flipped 9:16 -> 1:1, the words
    # and pictures were unchanged, and 7 portrait takes read as current.
    if canvas is not None and recorded_canvas(take) != tuple(canvas):
        return False
    if pictures is None:
        return True
    from studio.comfy import staged_name
    return {staged_name(p) for p in pictures} <= staged_images(take)
