"""Takes as runs of shots with several anchored panels.

One panel over ten seconds repeats itself (measured: the corridor takes of
episode 1 walked, reset and walked again, or invented a second Stamford).
So a TAKE is a run of consecutive shots that fits one H3 budget; every
shot's panel is anchored at that shot's start frame, and the next take's
first panel is anchored at the take's last frame, so the picture always has
somewhere to go and the cut lands on the frame the next take starts from.
(Owner, 2026-09-10.)

HOW MANY PANELS, AMENDED 2026-09-13.  The original rule was "give the model
three".  Measured across episode 3, a third panel is where a take breaks: 3-
segment takes pass 0 of 2 at a mean of 23.5 against 79.3 for two, and they are
the two worst takes in the episode.  `SEGMENT_CAP` holds a take to two.
"""
from __future__ import annotations

from studio.h3 import frames_for

BUDGET = 12.0
"""Seconds of picture per take; H3 is trained to ~15 s (362 frames)."""
HANDLE = 0.25

SEGMENT_CAP = 2
"""How many segments a take may hold.  A take is ALSO capped by seconds, and
that cap alone let a 3-segment take through at 11.6 s of a 12 s budget.

MEASURED over all 22 takes of episode 3:

    1 segment    7/9  pass   mean 76.7
    2 segments   7/11 pass   mean 79.3
    3 segments   0/2  pass   mean 23.5      T02 4.0, T11 43.0

Both 3-segment takes fail and they are the two worst takes in the episode; with
the earlier measurement (3+ segment takes failed 6 of 6) that is 8 of 8.

Every segment after the first is a cut the MODEL places itself, on its own
clock, from a pin.  Two segments give it one cut to get right; three give it
two, and once it is early on the first it is adrift for the rest.  T02 lands 1
of 3, then invents a cut of its own -- and in that invented shot, which no panel
describes, it drew a second figure into a room the plan puts two men in (owner,
2026-09-13: "blurred man at 17 seconds").  A picture nothing specifies is a
picture the model fills in."""


def segments_in(shots: list[dict]) -> int:
    """Panels these shots carry: each shot, plus each of its sub-shots."""
    return sum(1 + len(shot.get("cuts") or []) for shot in shots)


def groups(placed: list[dict], budget: float = BUDGET, cap: int = SEGMENT_CAP) -> list[list[int]]:
    """Consecutive shot indices packed into takes of at most `budget` seconds AND
    at most `cap` segments; a take never crosses a setup (a `setup` key on the
    placed shot, when given).

    The cap can never split a SHOT -- a shot with two sub-shots is three segments
    by itself and has to stay whole -- so the rule is "never START a segment past
    the cap in a take that already holds one", which is why the test is on `run`
    being non-empty."""
    by = {s["index"]: s for s in placed}
    out, run, total, count = [], [], 0.0, 0
    for shot in placed:
        new_setup = run and shot.get("setup") != placed_by(placed, run[-1]).get("setup")
        mine = segments_in([shot])
        if run and (total + shot["seconds"] > budget or new_setup or count + mine > cap):
            out.append(run)
            run, total, count = [], 0.0, 0
        run.append(shot["index"])
        total += shot["seconds"]
        count += mine
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
