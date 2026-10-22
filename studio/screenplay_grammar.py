"""The anime-TV screenplay grammar: plan gates on the episode's shape.

OWNER 2026-10-17 (research 04_screenplay.md, approved with the framing grammar).
The compressed anime episode: cold open -> part A -> ACT-OUT (the eyecatch break:
the spike lands, the picture holds, the bed turns) -> part B with the turn ->
button -> an optional picture-only tease.  Interior states go to the face and to
silence -- a silent reaction after each exchange, holds concentrated where they
land, a short inner voice over the thinker's own face -- and narration never
captions what the frame already shows.

Lengths read the VOICE (`placed` from `plan_gates.projected_place`); no seconds
live in the plan -- holds are `beat_s` / `coda_s`, as ever.  Hard on a plan that
declares `grammar: anime_tv` and is not yet drawn (`plan_check.grammar_gate`);
advice on every older plan.  $0.
"""
from __future__ import annotations

import re

from studio import story_layer
from studio.episode_spec import ACTS, HANDLE, INNER_MAX_WORDS
from studio.plan_gates import CAPTION_WALL, fault, held_seconds

COLD_OPEN_WORDS = 10
"""The first line's words (04 P1): the swipe is decided in 2-3 s; ep01's 16-word
hook landed its threat 4.5 s in, after a sentence of scenery."""
SOUND_AT_S = HANDLE
"""A cold-open sound sits at the picture's first frame, within the first handle."""
ACT_OUT_BAND = (0.35, 0.55)
"""Where the act-out starts, as a share of the projected picture (04 section 3)."""
HOLD_S = 1.2
"""A real hold (ma): beat + coda of a shot.  ep01's only real holds: shots 17, 21, 22."""
MIN_HOLDS = 3
"""Holds of HOLD_S or more an episode spends (04 P6)."""


def band() -> dict:
    """Every number these gates measure, for the writer's brief."""
    return {"cold_open_words": COLD_OPEN_WORDS, "cold_open_sound_at_s": SOUND_AT_S,
            "act_out_band": list(ACT_OUT_BAND), "hold_s": HOLD_S, "min_holds": MIN_HOLDS,
            "caption_wall": CAPTION_WALL, "inner_max_words": INNER_MAX_WORDS}


def cut(episode) -> list:
    omit = set(getattr(episode, "omit", None) or [])
    return [s for s in episode.shots if s.index not in omit]


def lines_on(episode, index: int) -> list:
    return [l for l in episode.lines if l.shot == index]


def cold_open_faults(episode) -> list[str]:
    """G-COLD: the first line is COLD_OPEN_WORDS at most; shot 0 sounds at once."""
    out, first = [], episode.lines[0] if episode.lines else None
    if first is not None and len(first.text.split()) > COLD_OPEN_WORDS:
        out.append(fault("G-COLD", "line 0", "the cold open's first line in words -- name the event or its "
                         "victim, never scenery first", len(first.text.split()), COLD_OPEN_WORDS))
    opener = cut(episode)[0]
    if not any(float(getattr(s, "at", 0.0)) <= SOUND_AT_S + 1e-6 for s in opener.sounds or []):
        out.append(fault("G-COLD", f"shot {opener.index}", "the first shot carries a sound at its first frame",
                         sorted(float(getattr(s, "at", 0.0)) for s in opener.sounds or []) or "none",
                         f"<= {SOUND_AT_S} s"))
    return out


def starts(placed: dict) -> tuple[dict[int, float], float]:
    """({shot: start second}, the picture's whole length) from a placement."""
    return {s["index"]: float(s["t_start"]) for s in placed["shots"]}, float(placed["duration_s"]) or 1.0


def bed_turns_at(episode, index: int) -> bool:
    """A bed span starts at `index` or the shot after it, in a tone unlike the span before."""
    beds = list(getattr(episode, "beds", None) or [])
    for k, span in enumerate(beds):
        if span.get("from_shot") in (index, index + 1):
            before = beds[k - 1].get("tone") if k else None
            if before is not None and before != span.get("tone"):
                return True
    return False


def act_out_faults(episode, placed: dict) -> list[str]:
    """G-ACT: one act-out, starting at ACT_OUT_BAND of the picture, held HOLD_S,
    the bed turning there, before the turn."""
    acts = [s for s in cut(episode) if s.section == "act_out"]
    if len(acts) != 1:
        return [fault("G-ACT", "plan", "act_out shots -- end part A on the spike or its first "
                      "consequence, held, the bed turning", len(acts), 1)]
    return act_out_place(acts[0], placed) + act_out_rows(episode, acts[0])


def act_out_place(act, placed: dict) -> list[str]:
    """The act-out starts inside ACT_OUT_BAND of the picture."""
    at, total = starts(placed)
    share, (low, high) = round(at.get(act.index, 0.0) / total, 2), ACT_OUT_BAND
    if low <= share <= high:
        return []
    return [fault("G-ACT", f"shot {act.index}", "where the act-out starts, as a share of the picture",
                  share, f"{low}-{high}")]


def act_out_rows(episode, act) -> list[str]:
    """The act-out holds, the bed turns there, and it comes before the turn."""
    out = []
    if held_seconds(act) < HOLD_S - 1e-6:
        out.append(fault("G-ACT", f"shot {act.index}", "the act-out's hold (beat + coda) in seconds",
                         round(held_seconds(act), 2), HOLD_S))
    if not bed_turns_at(episode, act.index):
        out.append(fault("G-ACT", f"shot {act.index}", "a bed span changing tone at the act-out or the "
                         "shot after it", "none", "a tone change"))
    turns = [s.index for s in cut(episode) if s.section == "turn"]
    if turns and act.index > turns[0]:
        out.append(fault("G-ACT", f"shot {act.index}", "the act-out comes before the turn", act.index, turns[0]))
    return out


def caption_faults(episode) -> list[str]:
    """G-CAPTION: a narration line whose content words the frame already shows.  A line
    in which the narrator acts is the memoir's witness, not a caption (WotW ep03 line 15,
    the one fire on an owner-liked plan, 2026-10-17 replay)."""
    out = []
    for line in episode.lines:
        if line.kind != "narration" or ACTS.search(line.text):    # the witness acting is his voice
            continue
        shot = next(s for s in episode.shots if s.index == line.shot)
        got = round(story_layer.overlap(line.text, f"{shot.frame} {shot.motion}"), 2)
        if got > CAPTION_WALL:
            out.append(fault("G-CAPTION", f"line {line.index}", "share of the narration's content words its "
                             "shot already shows -- tell what the picture cannot", got, CAPTION_WALL))
    return out


def exchanges(episode) -> list[list]:
    """Runs of consecutive cut shots carrying dialogue, spoken by two or more people."""
    runs, run = [], []
    for s in cut(episode):
        if any(l.kind == "dialogue" for l in lines_on(episode, s.index)):
            run.append(s)
            continue
        runs, run = runs + [run] if run else runs, []
    runs = runs + [run] if run else runs
    return [r for r in runs if len({l.speaker for s in r for l in lines_on(episode, s.index)
                                    if l.kind == "dialogue"}) >= 2]


def silent_face(episode, shot) -> bool:
    """A face held with no voice but, at most, a thought."""
    return bool(shot.faces) and all(l.kind == "inner" for l in lines_on(episode, shot.index))


def reaction_faults(episode) -> list[str]:
    """G-REACT: the shot after each exchange is a silent listener (or an inner line)."""
    shots, out = cut(episode), []
    for run in exchanges(episode):
        k = shots.index(run[-1]) + 1
        after = shots[k] if k < len(shots) else None
        if after is None or not silent_face(episode, after):
            where = f"shot {after.index}" if after is not None else f"after shot {run[-1].index}"
            out.append(fault("G-REACT", where, f"the exchange on shots {run[0].index}-{run[-1].index} ends "
                             "without a silent listener's face", "a line or no face", "a silent reaction"))
    return out


def ma_faults(episode) -> list[str]:
    """G-MA: the holds are concentrated -- MIN_HOLDS shots of HOLD_S or more."""
    got = sum(held_seconds(s) >= HOLD_S - 1e-6 for s in cut(episode))
    if got >= MIN_HOLDS:
        return []
    return [fault("G-MA", "plan", f"holds of {HOLD_S} s or more (beat + coda) -- spend the silence after "
                  "the reveals, never as crumbs on every shot", got, MIN_HOLDS)]


def inner_faults(episode) -> list[str]:
    """G-INNER: an inner line sits over its own speaker's face."""
    return [fault("G-INNER", f"line {l.index}", "an inner line plays over its speaker's own face",
                  next(s.faces for s in episode.shots if s.index == l.shot), l.speaker)
            for l in episode.lines if l.kind == "inner"
            and l.speaker not in next(s.faces for s in episode.shots if s.index == l.shot)]


def inner_advisories(episode) -> list[str]:
    """The inner voice is advisory until the owner has heard its treatment."""
    said = [l.index for l in episode.lines if l.kind == "inner"]
    return [f"G-INNER lines {said}: the inner voice (hushed in the speaker's own engine, close-mic in "
            f"assemble) is ADVISORY until the owner has heard it"] if said else []


# ---- G-MUTE: no speech verb on a face that does not speak (craft ruling A8, shadow) -------------------

SPEECH_VERB = re.compile(r"\b(speak|speaks|speaking|spoke|say|says|saying|said|answer|answers|answering|answered|"
                         r"ask|asks|asking|asked|tell|tells|telling|told|reply|replies|replying|replied|"
                         r"shout|shouts|shouting|shouted|scream|screams|screaming|screamed)\b", re.I)
"""What H3 reads as a moving mouth.  Take audio carries dialogue only (takes_r2v.py:693-703)."""
MUTE_SIZES = ("extreme_close", "close", "medium_close", "medium")
"""Sizes whose mouth reads; a full or wide's scream is the take-prompt C13 class, not this one."""
MUTE_FIELDS = ("frame", "motion", "at_rest")


def _get(row, key):
    return row.get(key) if isinstance(row, dict) else getattr(row, key, None)


def speaks_on(lines: list[dict], shot) -> bool:
    """A face of this shot has a DIALOGUE line on it (a tale or narration drives no lips)."""
    faces = set(_get(shot, "faces") or [])
    return any(l.get("kind") == "dialogue" and l.get("shot") == _get(shot, "index") and l.get("speaker") in faces
               for l in lines)


def mute_faults(plan, paragraphs=()) -> list[str]:
    """G-MUTE (shadow): a speech verb in a readable face's frame, motion or at_rest with no dialogue
    line of that face's on the shot.  Jekyll ep01: shots 13 ("speaking") and 15 ("answering")."""
    shots = plan.get("shots") if isinstance(plan, dict) else getattr(plan, "shots", None)
    lines, out = story_layer._rows(plan), []
    for shot in shots or []:
        if _get(shot, "size") not in MUTE_SIZES or not _get(shot, "faces") or speaks_on(lines, shot):
            continue
        verbs = [m.group(0) for f in MUTE_FIELDS for m in SPEECH_VERB.finditer(str(_get(shot, f) or ""))]
        if verbs:
            out.append(fault("G-MUTE", f"shot {_get(shot, 'index')}", "a speech verb on a face with no dialogue "
                             "line on its shot (a tale or narration drives no lips)", ", ".join(verbs), "listens"))
    return out


# ---- G-REVEAL: a withheld face is not lifted to the camera early (craft ruling A12, shadow) ----------

LIFT = re.compile(r"\blifts? (?:his|her|its) chin\b|\bturns? (?:his|her|its) (?:[\w']+ )?face up\b|\blow angle\b"
                  r"|\b(?:light|glow|lamp\w*|flame)\b[^.;]{0,40}\bcheek\b|\bshow\w* (?:[\w']+ ){0,3}face\b", re.I)
"""What lifts a face to the viewer: a raised chin, a face turned up, a low angle, light on the cheek, a
move that widens to show it.  Jekyll ep01: shots 0, 9 and 11, before the book shows Hyde (ch2 index 24)."""
REVEAL_SIZES = ("extreme_close", "close", "medium_close")
REVEAL_FIELDS = ("frame", "motion", "at_rest", "end", "camera")


def lifted(shot) -> list[str]:
    """The lift words of a close or medium close shot; none at any other size."""
    if _get(shot, "size") not in REVEAL_SIZES:
        return []
    return [m.group(0) for f in REVEAL_FIELDS for m in LIFT.finditer(str(_get(shot, f) or ""))]


def too_early(reveal, number: int, shot, paragraphs: list[str]) -> bool:
    """Before the reveal's episode, or in it with no span placing the shot at or after its paragraph."""
    from studio import plan_gates
    if number != reveal.episode:
        return number < reveal.episode
    from types import SimpleNamespace
    at = plan_gates.event_paragraph(SimpleNamespace(source=list(_get(shot, "source") or [])), paragraphs)
    return not at or at - 1 < reveal.paragraph


def reveal_faults(plan, paragraphs: list[str], smap) -> list[str]:
    """G-REVEAL (shadow): a lift verb on a scheduled entity's close or medium close before the series map
    lets the viewer see it."""
    number = int(_get(plan, "number") or 0)
    shots = plan.get("shots") if isinstance(plan, dict) else getattr(plan, "shots", None)
    out = []
    for shot in shots or []:
        for who in _get(shot, "faces") or []:
            reveal, words = smap.of(who), lifted(shot)
            if reveal and words and too_early(reveal, number, shot, paragraphs):
                out.append(fault("G-REVEAL", f"shot {_get(shot, 'index')}", f"{who}'s face lifted to the camera "
                                 f"before episode {reveal.episode}, paragraph {reveal.paragraph} (\"{reveal.words}\")",
                                 ", ".join(words), "no lift"))
    return out


def location_of(episode, setup: str) -> str:
    found = (getattr(episode, "setups", None) or {}).get(setup)
    return str(getattr(found, "location", "") or setup)


NOT_ASKED = "G-TEASE: tease not asked (the brief gave no NEXT CHAPTER rows); advisory, never a fault"


def tease_advisories(episode, next_rows=None) -> list[str]:
    """G-TEASE (advisory): the tease names its image and loops to the hook's place.  Without the
    brief's NEXT CHAPTER rows a tease was never asked (craft ruling A13: the writer is never given
    chapter N+1, and 0 of 30 plans managed one), so it says so and reads nothing else."""
    shots = cut(episode)
    tease = [s for s in shots if s.section == "tease"]
    if not tease:
        return []
    if not next_rows:
        return [NOT_ASKED]
    out = [] if getattr(episode, "tease", "") else ["G-TEASE: the plan's `tease` names no next-chapter image"]
    if location_of(episode, tease[0].setup) != location_of(episode, shots[0].setup):
        out.append(f"G-TEASE shot {tease[0].index}: the tease does not return to the hook's place "
                   f"({location_of(episode, shots[0].setup)}), so the end does not loop (advisory)")
    return out
