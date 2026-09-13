"""Takes as runs of shots with several anchored panels.

One panel over ten seconds repeats itself (measured: the corridor takes of
episode 1 walked, reset and walked again, or invented a second Stamford).
So a TAKE is a run of consecutive shots that fits one H3 budget; every
shot's panel is anchored at that shot's start frame, and the next take's
first panel is anchored at the take's last frame, so the picture always has
somewhere to go and the cut lands on the frame the next take starts from.
(Owner, 2026-09-10.)
"""
from __future__ import annotations

from studio.h3 import frames_for

BUDGET = 12.0
"""Seconds of picture per take; H3 is trained to ~15 s (362 frames)."""
HANDLE = 0.25


def groups(placed: list[dict], budget: float = BUDGET) -> list[list[int]]:
    """Consecutive shot indices packed into takes of at most `budget` seconds;
    a take never crosses a setup (a `setup` key on the placed shot, when given)."""
    out, run, total = [], [], 0.0
    for shot in placed:
        new_setup = run and shot.get("setup") != placed_by(placed, run[-1]).get("setup")
        if run and (total + shot["seconds"] > budget or new_setup):
            out.append(run)
            run, total = [], 0.0
        run.append(shot["index"])
        total += shot["seconds"]
    if run:
        out.append(run)
    return out


def placed_by(placed: list[dict], index: int) -> dict:
    return next(s for s in placed if s["index"] == index)


def take(placed: list[dict], indices: list[int], following: int | None, fps: int = 24) -> dict:
    """The take's length and its anchors as (shot index, frame)."""
    by = {s["index"]: s for s in placed}
    start = by[indices[0]]["t_start"]
    seconds = round(sum(by[i]["seconds"] for i in indices), 6)
    frames = frames_for(seconds + HANDLE)
    anchors = [(i, round((by[i]["t_start"] - start) * fps)) for i in indices]
    if following is not None:
        anchors.append((following, frames - 1))
    cuts = [(i, k, round((c - start) * fps)) for i in indices
            for k, c in enumerate(by[i].get("cuts") or [], start=1)]
    return {"shots": indices, "t_start": start, "seconds": seconds, "frames": frames, "anchors": anchors,
            "cuts": cuts}


TOKEN_FRAMES = (1, 4, 4, 4, 4)  # H3 packs 17 frames into 5 tokens: FRAME_PER_TOKEN in comfy/ldm/minimax/model.py
GRID = (0, 1, 5, 9, 13)          # token starts inside each 17-frame block


def grid_frame(frame: int) -> int:
    """The first frame at or after `frame` that begins a video token (17 frames
    per 5 tokens, starts at 17k + {0,1,5,9,13}); a pin inside a token smears
    over its four frames (verified in the model source, 2026-09-11)."""
    if frame <= 0:
        return 0
    block, k = divmod(frame, 17)
    ahead = next((r for r in GRID if r >= k), None)
    return block * 17 + ahead if ahead is not None else (block + 1) * 17


def near_grid(frame: int, fps: int = 24) -> int:
    """The token start NEAREST the whole second `frame` falls on (spec 3.20).

    `grid_frame` snaps FORWARD to the next token start, which left T01's cut 0.208 s
    after the `00:03` its prompt states; this lands it 0.042 s away.  NOT wired into
    the take builder: a backward snap moves the picture cut BEFORE the voice cut, and
    the picture is cut to the measured voice (owner, audio-first).  Ties go forward
    for the same reason.  One line in `takes_r2v.on_grid` flips it for the A/B."""
    target = round(frame / fps) * fps
    starts = [b * 17 + r for b in range((max(frame, target) // 17) + 2) for r in GRID]
    return min(starts, key=lambda f: (abs(f - target), -f))


def takes(placed: list[dict], budget: float = BUDGET, fps: int = 24) -> list[dict]:
    runs = groups(placed, budget)
    return [take(placed, run, runs[k + 1][0] if k + 1 < len(runs) else None, fps)
            for k, run in enumerate(runs)]
