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
    """The width and height this take IS, off its own graph: the canvas a draw was scaled to
    (`scaled_to`: the tiny-face rung renders at 1024 and lands at the episode's canvas), else
    the size its render node drew."""
    scaled = (read_graph(take) or {}).get("scaled_to")
    if isinstance(scaled, list) and len(scaled) == 2:
        return (int(scaled[0]), int(scaled[1]))
    for node in nodes_of(take):
        inputs = node.get("inputs", {})
        if isinstance(inputs.get("width"), int) and isinstance(inputs.get("height"), int):
            return (inputs["width"], inputs["height"])
    return None


def is_current(built: str, take: Path, pictures: list | None = None,
               canvas: tuple[int, int] | None = None) -> bool:
    """True only when this take exists AND was rendered from this prompt -- and,
    when `pictures` is given, from exactly these pictures' bytes (`stale_why` is None).

    MEASURED 2026-09-22 (audit item 10): with the words alone, 16 ep05 takes
    whose sheet was redrawn and 6 ep07 takes whose panel was redrawn all read
    as current, so a retake round would skip them.

    Unprovable is not current: an episode from before the graph file was
    written cannot show what it ran with, and re-rendering is the safe answer.
    Whitespace is not a picture, so a re-wrap does not spend 200 s of GPU."""
    return stale_why(built, take, pictures, canvas) is None


def stale_why(built: str, take: Path, pictures: list | None = None,
              canvas: tuple[int, int] | None = None) -> str | None:
    """The first input `is_current` refuses -- no take, unfinished render, unknown provenance, prompt,
    canvas, pictures -- or None when the take is current (the dry check prints this very answer)."""
    take = Path(take)
    if not take.exists():
        return "no take"
    # AN UNFINISHED RENDER IS NOT CURRENT: takes_r2v writes the graph before it
    # renders, so ep12 T16's interrupted run left a new graph beside the old
    # video and the runner kept it.  A graph more than a minute newer than
    # its video describes a render that never landed.
    graph = take.with_suffix(".graph.json")
    if graph.exists() and graph.stat().st_mtime - take.stat().st_mtime > UNFINISHED_S:
        return "unfinished render"
    said = recorded_prompt(take)
    if said is None or said.strip() != (built or "").strip():
        return "unknown provenance" if said is None else "prompt"
    # THE CANVAS IS AN INPUT: ep14 (2026-09-30) flipped 9:16 -> 1:1, the words
    # and pictures were unchanged, and 7 portrait takes read as current.
    if canvas is not None and recorded_canvas(take) != tuple(canvas):
        return "canvas"
    return None if pictures is None else pictures_why(take, pictures)


def pictures_why(take: Path, pictures: list) -> str | None:
    """`pictures` when the take's graph did not stage every one of these pictures' bytes."""
    from studio.comfy import staged_name
    return None if {staged_name(p) for p in pictures} <= staged_images(take) else "pictures"


# --- a repair freezes what it was handed (incident 2026-10-19 11:18 PDT) ---------------------

FREEZE_FROM = "09"
"""The takes' own step: a repair redoing it or a later step repairs the takes' faces, the cut or the QC,
never their inputs, so it never re-renders a delivered take over moved prompt code."""


def sha8_of(path: Path) -> str:
    """The first eight hex digits of the file's sha256 (take_dq.take_sha8's rule)."""
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def delivered_sha8(home: Path, take: Path) -> str | None:
    """The take's bytes as step 12 delivered them: its row in the episode's manifest.json."""
    path, tail = Path(home) / "manifest.json", "/".join(Path(take).parts[-3:])
    try:
        rows = json.loads(path.read_text(encoding="utf-8")).get("inputs") or []
    except (ValueError, OSError):
        return None
    return next((r.get("sha8") for r in rows if str(r.get("path", "")).endswith(tail)), None)


def measured_sha8(take: Path) -> str | None:
    """The bytes the take's own dq record measured (`take_sha8`), or None."""
    try:
        return json.loads(Path(take).with_suffix(".dq.json").read_text(encoding="utf-8")).get("take_sha8")
    except (ValueError, OSError, AttributeError):
        return None


def governing(home: Path) -> dict | None:
    """The owner repair that governs the takes: the open window, else the LATEST closed one
    (repair.jsonl).  Fix round 2026-10-19: step 09 completing clears the receipt and the drive's end
    closes the window, and a relaunch with no window read all 28 delivered takes stale again."""
    from studio import repair_clock
    return repair_clock.read(home) or next(iter(repair_clock.history(home)[-1:]), None)


def frozen(take: Path, home: Path) -> str | None:
    """Why this take is current for the render pass -- `delivered` (its bytes are the manifest's) or
    `measured` (its dq record's) -- on an episode an owner repaired at 09 or later, until an owner redo
    of 01-08 governs; None for an episode never repaired (today's rule, exactly)."""
    return frozen_in(governing(home), take, home)


def frozen_in(window: dict | None, take: Path, home: Path) -> str | None:
    """`frozen` under a given window (the dry check prices a window not yet opened): an owner's repair
    of a delivered episode that redoes step 09 or later freezes the bytes a record names."""
    from studio import repair_clock
    take = Path(take)
    if window is None or not repair_clock.delivered(home) or not take.exists():
        return None
    if min(window.get("steps") or ["00"]) < FREEZE_FROM:
        return None
    sha = sha8_of(take)
    return next((why for why, got in (("delivered", delivered_sha8(home, take)),
                                      ("measured", measured_sha8(take))) if got == sha), None)


def held(built: str, take: Path, home: Path, pictures: list | None = None,
         canvas: tuple[int, int] | None = None) -> bool:
    """The one question step 09 and takes_r2v ask before a render, under the repair that governs."""
    return held_in(governing(home), built, take, home, pictures, canvas)


def held_in(window: dict | None, built: str, take: Path, home: Path, pictures: list | None = None,
            canvas: tuple[int, int] | None = None) -> bool:
    """Current to its card (`is_current`), or frozen under `window` (`frozen_in`); the dry check asks it
    under the window a launch would run in."""
    return is_current(built, take, pictures, canvas) or frozen_in(window, take, home) is not None


# --- unit currency: a take is stale when ITS OWN inputs differ (early cutoff) ---

INPUT_ORDER = ("prompt", "pictures", "canvas")
"""The inputs a take is rendered from, in the order the first difference is named."""


def recorded_inputs(take: Path) -> dict | None:
    """What this take ran with, off its own graph: prompt, staged picture names (content
    addressed), canvas; None when nobody can show it (no graph, or the stub)."""
    if provenance_unknown(take):
        return None
    return {"prompt": (recorded_prompt(take) or "").strip(),
            "pictures": sorted(staged_images(take)), "canvas": recorded_canvas(take)}


def _normal(key: str, value):
    """One input as it is compared: prompt words trimmed, pictures sorted, canvas a tuple."""
    if key == "prompt":
        return (value or "").strip()
    return tuple(value) if key == "canvas" and value else (sorted(value or []) if key == "pictures" else value)


def first_difference(recorded: dict | None, now: dict) -> str | None:
    """The first input that differs (`prompt`, `pictures`, `canvas`), `unknown` for an
    unprovable record, None when every input is the same bytes and words."""
    if recorded is None:
        return "unknown"
    return next((k for k in INPUT_ORDER if _normal(k, recorded.get(k)) != _normal(k, now.get(k))), None)


def currency(recorded: dict[str, dict | None], now: dict[str, dict]) -> dict[str, str | None]:
    """{take: first differing input | unknown | None}: each take against ITS OWN inputs only, so
    a redrawn grid whose panels came back byte-equal stales nothing after it (RUNLOG row 43)."""
    return {take: first_difference(recorded.get(take), inputs) for take, inputs in now.items()}


def stale_count(cur: dict[str, str | None]) -> int:
    """How many takes really differ; an unknown one is unproven, not stale."""
    return sum(1 for why in cur.values() if why and why != "unknown")


def verdict_current(report: dict | None, sha8: str) -> bool:
    """A dq/eye verdict counts only when the bytes it names are the file now."""
    return bool(report) and report.get("take_sha8") == sha8
