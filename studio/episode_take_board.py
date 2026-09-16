"""A storyboard sheet PER TAKE (owner, 2026-09-10 evening).

The take's timeline is sliced into nine beats; each cell draws the instant
at that beat -- the active shot's frame, how far its motion has gone, who
is speaking -- so the sheet is the take's own storyboard: every cell is an
anchor candidate, and as a `<Picture>` reference it contains nothing the
take must not show.  Drawn with the plate, the cast, the previous sheet of
the setup and the take's approved panels attached, so the family holds.
"""
from __future__ import annotations

from studio.episode_board import still_line
from studio.episode_spec import Shot

COLS, ROWS = 3, 2
CELLS = COLS * ROWS
CANVAS = (2048, 2048)
"""2x3 (owner + storyboard designer, 2026-09-10 evening): gpt-image re-frames
at ROW boundaries (measured: take_03's three rows were three framings), so a
sheet has one row boundary, not two; six moments over 3-12 s is a beat every
1.5-2 s; ~$0.13 a sheet instead of $0.20."""
FRACTIONS = ("At the very start of", "A fifth of the way through", "A third of the way through",
             "Halfway through", "Two thirds of the way through", "Near the end of", "At the last moment of")


def progress(fraction: float) -> str:
    return FRACTIONS[min(int(fraction * (len(FRACTIONS) - 1) + 0.5), len(FRACTIONS) - 1)]


def segments(shots: list[Shot], placed: list[dict], start: float) -> list[dict]:
    """The take's segments in time order: every shot, then each of its
    sub-shots, with the take-relative second it begins at, its frame, its
    motion and its faces.  A sub-shot is a cut with no line of its own."""
    by = {s["index"]: s for s in placed}
    out = []
    for shot in shots:
        t0 = by[shot.index]["t_start"] - start
        out.append({"shot": shot.index, "sub": 0, "t": round(t0, 3), "frame": shot.frame, "motion": shot.motion,
                    "faces": list(shot.faces), "size": shot.size})
        for k, cut in enumerate(shot.cuts, start=1):
            out.append({"shot": shot.index, "sub": k, "t": round(t0 + cut.at_s, 3), "frame": cut.frame,
                        "motion": cut.motion, "faces": list(cut.faces), "size": cut.size})
    return out


def active(shots: list[Shot], placed: list[dict], t: float, start: float) -> tuple[Shot, float]:
    """The shot playing at `t` seconds into the take, and how far into it we are."""
    by = {s["index"]: s for s in placed}
    for shot in shots:
        s0 = by[shot.index]["t_start"] - start
        if t < s0 + by[shot.index]["seconds"] or shot is shots[-1]:
            return shot, min(max((t - s0) / by[shot.index]["seconds"], 0.0), 1.0)
    return shots[-1], 1.0


def allot(n_segments: int, cells: int = CELLS) -> list[int]:
    """Cells per segment: 3+3 for two, 2+2+2 for three, else as even as possible, never 0."""
    base, extra = divmod(cells, n_segments)
    return [base + (1 if k < extra else 0) for k in range(n_segments)]


def speaking(lines: list, at: dict, t_abs: float) -> str:
    for line in lines:
        t0, dur = at[line.index]
        if line.kind == "dialogue" and t0 <= t_abs <= t0 + dur:
            return f" {line.speaker.replace('_', ' ').title()} is speaking, mouth open on a word."
    return ""


def beats(shots: list[Shot], placed: list[dict], lines: list, at: dict, seconds: float,
          cells: int = CELLS) -> list[dict]:
    """One cell per beat.  With a single segment: `cells` beats over the take.
    With several segments (shots and sub-shots): each segment gets its share
    of cells (3+3, 2+2+2), the first at the segment's start (its pin), the
    rest spread to just before the next segment."""
    start = next(s for s in placed if s["index"] == shots[0].index)["t_start"]
    segs = segments(shots, placed, start)
    ends = [seg["t"] for seg in segs[1:]] + [seconds]
    out, cell = [], 0
    if len(segs) == 1:
        for k in range(cells):
            t = round(seconds * k / (cells - 1), 3)
            shot, frac = active(shots, placed, t, start)
            out.append({"cell": k, "t": t, "shot": shot.index, "sub": 0, "segment": 0, "fraction": round(frac, 2),
                        "text": f"{shot.frame} {progress(frac)} the motion: {shot.motion.rstrip('.')}."
                                f"{speaking(lines, at, start + t)}"})
        return out
    for si, (seg, share, end) in enumerate(zip(segs, allot(len(segs), cells), ends)):
        span = max(end - seg["t"], 0.5)
        for j in range(share):
            frac = j / share if share > 1 else 0.0
            t = round(seg["t"] + span * frac * 0.9, 3)
            out.append({"cell": cell, "t": t, "shot": seg["shot"], "sub": seg["sub"], "segment": si,
                        "fraction": round(frac, 2),
                        "text": f"{seg['frame']} {progress(frac)} the motion: {seg['motion'].rstrip('.')}."
                                f"{speaking(lines, at, start + t)}"})
            cell += 1
    return out


def lock(landmark: str, push: bool) -> str:
    """The opening sentences: the drawer weights the first line most."""
    where = landmark or "the main fixed object of the room"
    if push:
        return (f"ONE camera, six moments of one continuous shot. The camera pushes in evenly and by a "
                f"small amount: each panel is framed a little tighter than the one before, never looser, and "
                f"panel 6 is at most one sixth closer than panel 1. {where} stays at the same place in "
                f"the frame; the second row continues the first row. Only the people move.")
    return (f"ONE locked camera, six moments of one continuous shot. The camera does not move: same "
            f"lens, same height, same distance, same tilt in every panel. {where} sits at the same "
            f"place in every panel; every head is the same size in every panel; the second row "
            f"continues the first row with no change of framing whatsoever. Only the people move.")


def refs_text(cast: list[str], physical: dict[str, str], own_panels: int) -> str:
    """What each attached image is, in the order attached: the take's own
    approved panel(s) FIRST (the exact framing), then the plate, then the cast."""
    lines = []
    for k in range(own_panels):
        lines.append(f"Image {k + 1} is the exact framing of {'every panel' if own_panels == 1 else f'its shot'}"
                     f": same camera, same distance, same crop, same light and wardrobe.")
    n = own_panels + 1
    lines.append(f"Image {n} is the empty location: every panel is set in this exact room.")
    for k, who in enumerate(cast, start=n + 1):
        name = who.replace("_", " ").title()
        lines.append(f"Image {k} is {name}: {physical.get(who, '')} Keep exactly this face, hair, build "
                     f"and clothes whenever {name} is in a panel.")
    return " ".join(lines)


def lock_multi(shares: list[int], landmark: str) -> str:
    """Several locked cameras on one sheet, one per segment (a sub-shot is a real cut)."""
    where = landmark or "the main fixed object of the room"
    parts, first = [], 1
    for k, share in enumerate(shares):
        rng = f"Panel {first}" if share == 1 else f"Panels {first}-{first + share - 1}"
        parts.append(f"{rng} are shot {chr(65 + k)}, one locked camera{', framed as its own picture' if k else ''}")
        first += share
    return (f"{len(shares)} locked cameras, one per shot, on one sheet. " + "; ".join(parts) + ". Within a "
            f"shot's panels nothing moves but the people: same lens, same distance, same tilt, {where} at the "
            f"same place. Between shots the framing changes as each panel says.")


def prompt(beats_: list[dict], described: str, cast: list[str], physical: dict[str, str],
           landmark: str, push: bool, own_panels: int, strict: bool = False) -> str:
    panels = " ".join(f"Panel {b['cell'] + 1} ({b['t']:.1f} s): {b['text']}" for b in beats_)
    n_segments = len({b.get("segment", 0) for b in beats_})
    if n_segments > 1:
        shares = [sum(1 for b in beats_ if b.get("segment", 0) == k) for k in range(n_segments)]
        opening = lock_multi(shares, landmark)
    else:
        opening = lock(landmark, push)
    opening = ("STRICT: identical framing within every shot's panels, as if frames of one photograph. "
               if strict else "") + opening
    return (f"{opening} A {COLS} by {ROWS} grid of {CELLS} equal vertical 9:16 panels filling the whole "
            f"canvas, thin white gutters, read left to right, top to bottom, in time order. Every panel "
            f"is set in: {described} {refs_text(cast, physical, own_panels)} {panels} {still_line()}")


def names_push(motion: str) -> bool:
    head = motion.split(";")[0].lower()
    return any(w in head for w in ("push", "dolly", "pull", "zoom"))
