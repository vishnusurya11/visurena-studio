"""The take prompt for the ref2va HYBRID (A/B, 2026-09-10, owner's ask):
`<Picture N>` tags bind to the reference slots by position; the storyboard
panel is pinned at frame 0 and the line wav at frame 6 through guide nodes,
which are not picture slots, so the prompt names them in words and lays the
whole timeline out in seconds -- the anchors fix two points, the words steer
every frame between them.
"""
from __future__ import annotations

from studio.episode_spec import Shot
from studio.episode_take_prompt import STYLE

HEAD = 0.25


def name_of(who: str) -> str:
    return who.replace("_", " ").title()


def pictures(cast: list[str], physical: dict[str, str]) -> str:
    """Slots 1..n are the cast sheets, n+1 the storyboard sheet, n+2 the plate.
    A cast sheet is passed ONLY for a face the take shows readable: MEASURED
    2026-09-10, a referenced person whose face the panels hid walked into the
    frame as a second Stamford / a Watson close-up (every element the prompt
    names, the model shows)."""
    lines = [f"<Picture {k}> is {name_of(who)}: {physical.get(who, '')} Keep exactly this face, "
             f"hair, build and clothes whenever the face is on camera." for k, who in enumerate(cast, start=1)]
    lines.append(f"<Picture {len(cast) + 1}> is the storyboard sheet of this scene: match its "
                 f"light, wardrobe and staging exactly.")
    lines.append(f"<Picture {len(cast) + 2}> is the empty location: the room, its furniture, "
                 f"walls, windows and light are these.")
    return "\n".join(lines)


def bands(shot: Shot, seconds: float) -> str:
    """The camera clause (first) holds for the whole shot; the action clauses
    after it are spread over the shot in seconds."""
    clauses = [c.strip().rstrip(".") for c in shot.motion.split(";") if c.strip()]
    if not clauses:
        return ""
    camera, actions = clauses[0], clauses[1:]
    out = [f"{camera} for the whole shot."]
    step = seconds / max(len(actions), 1)
    out += [f"From {k * step:.2f} to {(k + 1) * step:.2f} seconds {c}." for k, c in enumerate(actions)]
    return " ".join(out)


def silent_body(shot: Shot, seconds: float) -> str:
    return (f"[Shot 1] {STYLE} At 0.00 seconds the shot begins exactly on the anchored first "
            f"frame: {shot.frame} {bands(shot, seconds)} Nobody speaks and no lips move. {lock()}")


def speaking_body(shot: Shot, speaker: str, text: str, line_s: float, seconds: float) -> str:
    who, end = name_of(speaker), min(HEAD + line_s, seconds)
    return (f"[Shot 1] {STYLE} At 0.00 seconds the shot begins exactly on the anchored first "
            f"frame: {shot.frame} From 0.00 to {HEAD:.2f} seconds {who} is silent and still, "
            f"mouth closed. From {HEAD:.2f} to {end:.2f} seconds {who} (S1) speaks to the person "
            f"just off-screen, physically speaking with natural lip movement on every syllable, "
            f"in time with the anchored audio: <d>[English] {text}</d> {bands(shot, seconds)} "
            f"From {end:.2f} seconds to the end {who} falls silent, mouth closed, and the frame "
            f"holds to the cut. {lock()}")


def segment(k: int, shot: Shot, start: float, end: float, lines: list, at: dict,
            offset: float) -> str:
    """One shot of a take: its seconds, the frame, the motion, the voice."""
    faces = (f"On camera with a readable face: {', '.join(name_of(w) for w in shot.faces)}."
             if shot.faces else "In this shot no face is readable: people are seen from behind, "
             "in profile or far off, and nobody new enters the frame.")
    out = [f"From {start:.2f} to {end:.2f} seconds [Shot {k}]: {shot.frame} {faces} {shot.motion.rstrip('.')}."]
    for line in lines:
        t0, dur = at[line.index]
        a, b = t0 - offset, t0 - offset + dur
        who = name_of(line.speaker)
        if line.kind == "dialogue":
            out.append(f"From {a:.2f} to {b:.2f} seconds {who} (S1) speaks to the person just "
                       f"off-screen, physically speaking with natural lip movement on every syllable, "
                       f"in time with the anchored audio: <d>[English] {line.text}</d>")
        else:
            out.append(f"From {a:.2f} to {b:.2f} seconds the narrator's voice, off-screen, says "
                       f'"{line.text}" -- nobody on screen speaks; the action keeps this pace.')
    return " ".join(out)


def timeline_body(shots: list[Shot], placed: list[dict], lines: list, at: dict, seconds: float) -> str:
    """The whole take, shot by shot in seconds, the anchored panels named as
    the frames each shot begins on, the voice laid at its measured time."""
    by = {s["index"]: s for s in placed}
    offset = by[shots[0].index]["t_start"]
    parts = [f"[Shot 1] {STYLE} At 0.00 seconds the take begins exactly on the first anchored "
             f"frame; each later shot begins exactly on its own anchored frame, and the picture "
             f"moves continuously from one anchored frame to the next -- no cut, no fade."]
    for k, shot in enumerate(shots, start=1):
        start = by[shot.index]["t_start"] - offset
        end = min(start + by[shot.index]["seconds"], seconds)
        parts.append(segment(k, shot, start, end, [l for l in lines if l.shot == shot.index], at, offset))
    parts.append(f"From {min(sum(by[s.index]['seconds'] for s in shots), seconds):.2f} seconds to the "
                 f"end the picture settles toward the final anchored frame and holds. {lock()}")
    return " ".join(parts)


def lock() -> str:
    return ("Within each shot the camera keeps the distance, height and lens of that shot's "
            "anchored frame: no pull-back, no widening, no re-framing. Everyone and everything "
            "stays as drawn; nobody who is not in the anchored frames appears. Realistic "
            "anatomy and hands, exactly two hands per person. No captions, overlays or text.")


def build(cast: list[str], physical: dict[str, str], body: str, soundscape: str) -> str:
    return (f"{pictures(cast, physical)}\n\nintegrated_multimodal_description: {body}\n\n"
            f"overall_soundscape: {soundscape}\n\nnon_diegetic_music: N/A")
