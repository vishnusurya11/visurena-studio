"""The plan gates: free checks on plan.json before anything is drawn.

Four gates, every one calibrated on the four fixtures the owner judged by eye
(tests/fixtures/episodes: ep05 and ep07 looked right, ep08 and ep09 looked
worse) and on the ten-reviewer measurement in
docs/analysis/ep08_ep09_why_worse.md.  Each fault reads

    G-<GATE> shot N: <why>, measured <number> against <threshold>

so the gate and the human are checking the same number.  `faults(episode)` is
the whole verdict; `advisories(episode)` carries the two measurements that the
fixtures showed CANNOT be refusals (see the bottom of the file).

Nothing here reads a picture, spends a credit, or touches a GPU.  Every
threshold is a constant with the fixture numbers in its docstring, because a
constant with no world attached is the fault this repo produces most.
"""
from __future__ import annotations

import json
import math
import re
import statistics
from pathlib import Path

from studio import story_layer
from studio.episode_ref_official import camera_clause
from studio.episode_seq_board import HOLDS, TRAVEL
from studio.episode_spec import Episode, Line, Setup, Shot


def fault(gate: str, where: str, why: str, got, wall) -> str:
    """One line, one number, one threshold -- the format every gate shares."""
    return f"{gate} {where}: {why}, measured {got} against {wall}"


def median_of(values: list) -> float:
    return float(statistics.median(values)) if values else 0.0


def words(text: str) -> int:
    return len((text or "").split())


# ---- G-FIRSTFRAME: the sentence the drawer and H3 get for the first frame ------

AT_REST_WORDS = 40
"""Median `at_rest` words per shot.  MEASURED (median / mean): ep05 76 / 76.8,
ep07 58 / 57.2, ep08 57 / 57.7, ep09 15 / 14.7.  A median, not a mean, so one
terse insert is fine and a plan written terse everywhere is not."""

EDGE_TOKENS = 3
"""Median frame-edge placements per `at_rest` -- LEFT/RIGHT/TOP/BOTTOM/CENTRE as
the plans capitalise them, plus `edge`, `third`, `half`.  MEASURED (median):
ep05 6, ep07 4, ep08 5, ep09 2.  Lower-case `left`/`right` are a hand, not a
frame edge, and are deliberately outside the pattern."""

DESCRIBED_WORDS = 90
"""Median setup `described` words.  MEASURED (median / mean): ep05 163.5 / 144,
ep07 107 / 106.5, ep08 94 / 97, ep09 54 / 59.  ep08 clears it by four words."""

GEOMETRY_WORDS = 60
"""Median setup `geometry` words.  MEASURED (median): ep05 67, ep07 67,
ep08 69.5, ep09 42."""

EDGE_TOKEN = re.compile(r"\b(?:LEFT|RIGHT|TOP|BOTTOM|CENTRE|CENTER|edges?|thirds?|half)\b")


def edge_tokens(text: str) -> int:
    return len(EDGE_TOKEN.findall(text or ""))


def shot_medians(episode: Episode) -> dict[str, float]:
    """The per-shot first-frame measures, as plan medians."""
    return {"at_rest": median_of([words(s.at_rest) for s in episode.shots]),
            "frame-edge": median_of([edge_tokens(s.at_rest) for s in episode.shots])}


def setup_medians(episode: Episode) -> dict[str, float]:
    setups = list(episode.setups.values())
    return {"described": median_of([words(s.described) for s in setups]),
            "geometry": median_of([words(s.geometry) for s in setups])}


def firstframe_faults(episode: Episode) -> list[str]:
    got, walls = shot_medians(episode), {"at_rest": AT_REST_WORDS, "frame-edge": EDGE_TOKENS}
    out = [fault("G-FIRSTFRAME", "plan", f"median {name} per shot is under the floor", got[name], wall)
           for name, wall in walls.items() if got[name] < wall]
    got, walls = setup_medians(episode), {"described": DESCRIBED_WORDS, "geometry": GEOMETRY_WORDS}
    out += [fault("G-FIRSTFRAME", "plan", f"median setup {name} words is under the floor", got[name], wall)
            for name, wall in walls.items() if got[name] < wall]
    return out


# ---- G-VARIETY: the plan cuts between different pictures -----------------------

INSERT_EVERY = 6
"""One insert per six shots, rounded up.  MEASURED: ep05 7 of 25 (needs 5),
ep07 6 of 26 (5), ep08 3 of 30 (5), ep09 0 of 30 (5).  ep08 fails it too."""

MAX_FACE_CLOSES = 6
"""Close or medium_close shots whose `faces` carry ONE person, per person.
MEASURED: ep05 Holmes 4, ep07 Holmes 4, ep08 the child 4, ep09 Lucy 9 (six
single closes and three two-shots).  The report's "same wardrobe list" cannot
be the discriminator: ep05's four Holmes closes carry one byte-similar
"bare-headed, the bottle-green velvet at his open coat" list and looked
right.  The count is what separates."""

MAX_WIDE_SHARE = 0.25
"""wide+full as a share of shots.  MEASURED: ep05 0.20, ep07 0.19, ep08 0.37,
ep09 0.33."""

CLOSE_SIZES = ("close", "medium_close")
TWO_SHOT = re.compile(r"^\s*(?:medium\s+)?two-shot\b", re.I)
"""A `frame` that opens on a two-shot is drawn as one, whatever `size` says:
ep09's three medium_close two-shots drew faces at 0.15-0.23 of frame against
0.33 for a real medium close."""


def inserts_needed(shots: int) -> int:
    return math.ceil(shots / INSERT_EVERY)


def insert_faults(episode: Episode) -> list[str]:
    got, need = sum(s.size == "insert" for s in episode.shots), inserts_needed(len(episode.shots))
    if got >= need:
        return []
    return [fault("G-VARIETY", "plan", f"insert shots for {len(episode.shots)} shots", got, need)]


def mislabelled_two_shot(frame: str, size: str) -> bool:
    return size in CLOSE_SIZES and bool(TWO_SHOT.match(frame or ""))


def two_shot_faults(episode: Episode) -> list[str]:
    return [fault("G-VARIETY", f"shot {s.index}", f"a {s.size} whose frame opens on a two-shot "
                  f"({s.frame.split(':')[0]!r})", "two-shot", s.size)
            for s in episode.shots if mislabelled_two_shot(s.frame, s.size)]


def face_closes(episode: Episode) -> dict[str, int]:
    """How many close/medium_close shots each face appears in."""
    out: dict[str, int] = {}
    for s in episode.shots:
        if s.size in CLOSE_SIZES:
            for who in s.faces:
                out[who] = out.get(who, 0) + 1
    return out


def face_close_faults(episode: Episode) -> list[str]:
    return [fault("G-VARIETY", "plan", f"close/medium_close shots on {who!r}", n, MAX_FACE_CLOSES)
            for who, n in face_closes(episode).items() if n > MAX_FACE_CLOSES]


def wide_share(episode: Episode) -> float:
    return sum(s.size in ("wide", "full") for s in episode.shots) / len(episode.shots)


def wide_share_fault(episode: Episode) -> list[str]:
    got = round(wide_share(episode), 2)
    if got <= MAX_WIDE_SHARE:
        return []
    return [fault("G-VARIETY", "plan", "wide+full share of the shots", got, MAX_WIDE_SHARE)]


def variety_faults(episode: Episode) -> list[str]:
    return (insert_faults(episode) + two_shot_faults(episode)
            + face_close_faults(episode) + wide_share_fault(episode))


# ---- G-MOVE: the camera travels an amount the board can be dollied through ----

AMPLITUDE = {"thumb's width": 0.25, "finger's breadth": 0.25, "hand's breadth": 1.0,
             "hand's width": 1.0, "forearm": 2.5, "tread": 2.5, "head's height": 3.0,
             "short stride": 5.0, "step": 5.0, "pace": 6.0, "arm's length": 6.0,
             "stride": 10.0, "long stride": 10.0, "whole stride": 10.0}
"""Travel per unit, in hand's breadths -- an ORDINAL ladder calibrated to the
eye, not a tape measure.  The one rung the tape would dispute is forearm (2.5)
under head's height (3.0): they are within a few centimetres, but ep07 pushed
in "a forearm" on three closes and looked right, and ep09 pushed in "a head's
height" on seven closes of a 90 mm face and morphed, so the ladder puts them
either side of the close cap.  If a later episode shows a forearm close
morphing, the cap moves to 1.0, not the ladder."""

COUNT = {"a": 1.0, "an": 1.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "half a": 0.5}
AMOUNT = re.compile(
    r"\b(a|an|one|two|three|four|half a)\s+(whole|long|short)?\s*"
    r"(hand's breadth|hand's width|thumb's width|finger's breadth|arm's length|"
    r"head's height|forearm|strides?|paces?|steps?|treads?)\b", re.I)

CAP = {"insert": 2.5, "extreme_close": 2.5, "close": 2.5, "medium_close": 2.5,
       "medium": 20.0, "full": 40.0, "wide": 40.0}
"""The largest travel per size, on the ladder.  MEASURED, the largest each good
episode wrote: ep07 closes a forearm (2.5), medium_close a forearm, medium two
long strides (20), wide four long strides (40); ep05 close a hand's breadth,
medium two long strides.  ep09 writes a head's height (3.0) on seven closes and
one or two long strides (10-20) on five medium_closes.  The report's "medium
<= a forearm" would refuse ep07's seven mediums, so the medium cap is what
ep07 shipped.  ep08 fails on its own: a long stride on medium_close 7, 16, 26."""

CROWD_FIGURES = 6
"""A full or wide shot over a setup whose `crowd` names this many people gets
the crowd cap: H3 cannot dolly through a drawn crowd, it multiplies it (ep09
T02's wagon train "into an endless duplicated line").  MEASURED figures:
ep09 valley_rim 40, high_road 10, the_drove 6, ferrier_land 2; ep08 caravan
column 20, bluff 12, waggon 30; ep07 mews lane 1; ep05 none."""

CROWD_CAP = 5.0
"""One short stride: hold, or a small move.  ep09 writes three long strides
(30) on 0, 8, 13 and four (40) on 10 over those crowds."""

TRAVEL_PER_SECOND = 24.0
"""Hand's breadths of travel per projected second of shot.  MEASURED maximum:
ep07 shot 4 at 20.0 (four long strides down a corridor in a 2.0 s shot, which
passed by eye), ep09 shot 17 at 8.0, ep08 5.2, ep05 3.6.  The cap sits above
ep07's extreme and so fires on none of the four fixtures; it exists for the
plan that writes a wide's travel onto a two-second insert.  It is the one
constant here with no fixture on the failing side."""

NUMBER = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
          "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "dozen": 12, "fifteen": 15,
          "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "hundred": 100}
PEOPLE = (r"men|women|people|persons|figures|immigrants|emigrants|riders|drivers|herdsmen|"
          r"horsemen|hands|boys?|girls?|children|indians|farmers|saints|elders|workmen|"
          r"passengers|soldiers|folk|families|pilgrims|natives|labourers|settlers|travellers|"
          r"mourners|onlookers|bystanders|guests|clerks|porters|cabmen|constables|policemen|"
          r"urchins|sailors|waiters|customers|drinkers|patients|students|worshippers")
FIGURES = re.compile(rf"\b(\d+|{'|'.join(NUMBER)})\s+(?:[\w-]+\s+){{0,3}}?(?:{PEOPLE})\b", re.I)
"""A number within three words of a people noun.  "twelve canvas-topped
waggons" and "thirty pack mules" are counted by nothing."""


def figures(crowd: str) -> int:
    """How many people a setup's `crowd` sentence names."""
    return sum(int(n) if n.isdigit() else NUMBER[n.lower()] for n in FIGURES.findall(crowd or ""))


def unit_of(qualifier: str, unit: str) -> float:
    unit = unit.lower().rstrip("s") if unit.lower().endswith(("strides", "paces", "steps", "treads")) else unit.lower()
    if (qualifier or "").lower() == "short" and unit == "stride":
        return AMPLITUDE["short stride"]
    return AMPLITUDE[unit]


def amount(head: str) -> float | None:
    """The head clause's camera travel on the ladder: 0.0 for a hold, None when
    the head names no camera move at all (that is M2's fault, not this one)."""
    cam, _ = camera_clause(head or "")
    if not cam:
        return None
    if HOLDS.search(cam):
        return 0.0
    said = TRAVEL.search(cam)
    hit = AMOUNT.search(said.group(1) if said else cam)
    if not hit:
        return None
    return COUNT[hit.group(1).lower()] * unit_of(hit.group(2), hit.group(3))


def travel_phrase(head: str) -> str:
    """The words the plan wrote for the amount ("a head's height"), for the fault line --
    found the same way `amount` finds the number, in either shape the plans use."""
    cam, _ = camera_clause(head or "")
    said = TRAVEL.search(cam)
    hit = AMOUNT.search(said.group(1) if said else cam)
    return hit.group(0) if hit else cam.strip()


def head_of(motion: str) -> str:
    return (motion or "").split(";")[0]


def cap_for(shot: Shot, setup: Setup) -> tuple[float, str]:
    """(cap, why) for this shot: its size's cap, or the crowd cap over a crowd."""
    n = figures(setup.crowd)
    if shot.size in ("wide", "full") and n >= CROWD_FIGURES:
        return CROWD_CAP, f"a {shot.size} over a crowd of {n} figures"
    return CAP[shot.size], f"a {shot.size}"


def move_faults(episode: Episode) -> list[str]:
    out = []
    for shot in episode.shots:
        head = head_of(shot.motion)
        got = amount(head)
        if got is None:
            continue
        cap, why = cap_for(shot, episode.setups[shot.setup])
        if got > cap:
            out.append(fault("G-MOVE", f"shot {shot.index}",
                             f"the camera travels {travel_phrase(head)!r} on {why}", got, cap))
    return out


def travel_rate(episode: Episode, shot: Shot) -> float:
    """Ladder units per projected second of this shot."""
    return (amount(head_of(shot.motion)) or 0.0) / episode.shot_seconds(shot)


def rate_faults(episode: Episode) -> list[str]:
    return [fault("G-MOVE", f"shot {s.index}", f"travel per second of a {round(episode.shot_seconds(s), 2)} s shot",
                  round(travel_rate(episode, s), 1), TRAVEL_PER_SECOND)
            for s in episode.shots if travel_rate(episode, s) > TRAVEL_PER_SECOND]


# ---- G-STORY: the episode dramatises before it explains -------------------------

FIRST_DIALOGUE_SHARE = 0.25
"""Where the first dialogue line lands, as a share of the projected runtime.
MEASURED (projected): ep05 0.16, ep07 0.04, ep08 0.18, ep09 0.60 (92.2 s of
153.3; the report's 87.6 of 146 is the same shot on the rendered cut)."""

NARRATION_RUN_S = 75.0
"""The longest run of consecutive shots with no dialogue, projected.  MEASURED:
ep05 70.3 s, ep07 46.0 s, ep08 47.7 s, ep09 92.2 s (17 narration lines in a
row).  The report's 45 s was measured on the rendered cut and, applied to the
projection, would refuse ep05 AND ep07; the wall sits between the good
episodes' 70.3 and ep09's 92.2."""

MIN_SILENT_SHOTS = 1
"""Shots carrying no line.  MEASURED: ep05 1, ep07 2, ep08 1, ep09 0."""

STDEV_FLOOR = 1.0
"""ADVISORY ONLY.  Projected shot-length stdev: ep05 0.82, ep07 1.70, ep08 1.31,
ep09 1.00.  The report's ep09 0.85 was measured on the cut; by projection ep05
is the metronome, so a floor here would refuse the episode that looked right."""

ACTS_ON = (r"catch(?:es|ing)?|caught|takes?|took|taking|draws?|drew|grips?|seizes?|holds?|"
           r"lifts?|pulls?|steadies|steady|hauls?|drags?|throws?|puts?|sets?|hands?|passes|"
           r"grasps?|clasps?|clutch(?:es)?|shakes?|strikes?|push(?:es)?|helps?|kisses|"
           r"embraces?|carries|carry|lays?|leads?|turns?|swings?|holds?|stops?")
"""The rescue verbs: one person's hand on another person, or on what carries
them ("caught the frightened horse by the curb")."""


def first_dialogue_at(episode: Episode) -> tuple[float, int]:
    """(seconds, shot) of the first dialogue line; (runtime, -1) if there is none."""
    elapsed = 0.0
    for shot in episode.shots:
        if any(line.kind == "dialogue" for line in episode.lines_of(shot.index)):
            return elapsed, shot.index
        elapsed += episode.shot_seconds(shot)
    return elapsed, -1


def narration_runs(episode: Episode) -> list[tuple[float, int, int]]:
    """Every run of consecutive dialogue-free shots as (seconds, first, last)."""
    out, run, start = [], 0.0, 0
    for shot in episode.shots:
        if any(line.kind == "dialogue" for line in episode.lines_of(shot.index)):
            if run:
                out.append((run, start, shot.index - 1))
            run, start = 0.0, shot.index + 1
        else:
            run += episode.shot_seconds(shot)
    return out + ([(run, start, episode.shots[-1].index)] if run else [])


def longest_narration_run(episode: Episode) -> float:
    return max((run for run, _, _ in narration_runs(episode)), default=0.0)


def silent_shots(episode: Episode) -> list[int]:
    return [s.index for s in episode.shots if not episode.lines_of(s.index)]


def shot_length_stdev(episode: Episode) -> float:
    secs = [episode.shot_seconds(s) for s in episode.shots]
    return statistics.stdev(secs) if len(secs) > 1 else 0.0


def cast_tokens(cast: list[str]) -> dict[str, str]:
    """{token: entity_id} for every name part only one cast member owns."""
    claims: dict[str, set] = {}
    for who in cast:
        for token in who.lower().split("_"):
            if len(token) > 2:
                claims.setdefault(token, set()).add(who)
    return {t: next(iter(s)) for t, s in claims.items() if len(s) == 1}


def turn_acts_on(episode: Episode) -> str:
    """The turn clause in which one cast member acts on another, or ""."""
    turn = episode.turn()
    names = cast_tokens(episode.setups[turn.setup].cast)
    if len(set(names.values())) < 2:
        return ""
    alt = "|".join(re.escape(t) for t in names)
    acting = re.compile(rf"\b({alt})\b\s+(?:\w+\s+){{0,2}}?(?:{ACTS_ON})\b.*?\b({alt})\b", re.I)
    for clause in turn.motion.split(";")[1:]:
        hit = acting.search(clause)
        if hit and names[hit.group(1).lower()] != names[hit.group(2).lower()]:
            return clause.strip().rstrip(".")
    return ""


def story_faults(episode: Episode) -> list[str]:
    runtime, out = episode.projected_seconds(), []
    at, shot = first_dialogue_at(episode)
    if at / runtime > FIRST_DIALOGUE_SHARE:
        out.append(fault("G-STORY", f"shot {shot}", f"first dialogue line at {at:.1f} s of {runtime:.1f} s projected",
                         round(at / runtime, 2), FIRST_DIALOGUE_SHARE))
    for run, first, last in narration_runs(episode):
        if run > NARRATION_RUN_S:
            out.append(fault("G-STORY", f"shots {first}-{last}", "narration-only run in projected seconds",
                             round(run, 1), NARRATION_RUN_S))
    if len(silent_shots(episode)) < MIN_SILENT_SHOTS:
        out.append(fault("G-STORY", "plan", "shots carrying no line (silent shots)",
                         len(silent_shots(episode)), MIN_SILENT_SHOTS))
    return out + speech_faults(episode) + turn_faults(episode) + tail_faults(episode)


# ---- G-STORY after episode 10: the lead speaks his own words ---------------------
# docs/analysis/ep10_dq_synthesis.md, section B.  Calibrated on the ep10 fixture
# (the faults present) against ep05 and ep07 (clean, or the advisories named).
# The text rules live in `studio.story_layer`; the walls and the wiring live here.

TURN_FACE_HARD_FROM = 10
"""From which episode number the turn shot must hold the protagonist's face.

ep10 shot 16 (`faces=['brigham_young']`, protagonist john_ferrier): the turn
is Young's threat on the threshold, acted superbly, and it is done TO the
lead; Ferrier's own choice reached the picture at 94-100 %, after the button.
ep05's turn is Madame Sawyer's curtsey (faces=['madame_sawyer']) and ep07's
a face-less knife splitting a pill -- both judged right by eye -- so below
this number the rule is an advisory.  It is hard FROM the episode it was
measured on: a gate that does not refuse its own calibration positive is not
the gate.  Never lowered to an advisory for a later plan: write the lead
into the frame of his own turn."""

WORDLESS_TAIL_S = 6.0
"""Projected seconds of picture after the last word: the button shot less its
speech, plus every shot after it.  MEASURED: ep05 4.6, ep07 4.7, ep10 11.5
(measured on the cut 11.25: three silent answer shots of 3.5, 3.0 and 4.5 s,
the bed dead at 166 s and the tile seam at 167.8 s inside that stretch)."""

BUTTON_REST_S = 0.6
"""ADVISORY.  `beat_s + coda_s` on the button shot, so the last line lands on
a held frame and not on a cut.  ep05 1.0, ep07 1.2, ep10 0.0."""

CAPTION_WALL = 0.80
"""ADVISORY.  The share of a narration line's content words already in its
shot's frame+motion (`story_layer.overlap`).  MEASURED, top three per plan:
ep07 0.80 / 0.80 / 0.75 (the milk boy at the ladder, the nightdress under the
sill, the open watch), ep05 0.50 / 0.38 / 0.38, ep10 0.71 / 0.57 / 0.50.  The
wall is ep07's maximum and it does NOT separate ep07 from ep10: on this
measure the episode that read as film captions harder.  What the measure does
give is the ranking INSIDE a plan -- ep10's #2, #3 and #4 (l18 "heavy step
going away down the shingle", l23 "her hand tightening on his", l26 "laughed
through her tears") are the three lines the analyst's ear called captions --
so the top three are printed every time and the wall only marks a line."""

CAPTION_TOP = 3


def episode_cast(episode: Episode) -> list[str]:
    return sorted({who for setup in episode.setups.values() for who in setup.cast})


def reported_lines(episode: Episode) -> list[tuple[Line, str, list[str]]]:
    """(line, speaker token, faces on the line's shot that token resolves to)
    for every narration line reporting speech.  A token that is neither a
    pronoun nor a cast name token ("Nobody said a word") reports nobody."""
    names, who = cast_tokens(episode_cast(episode)), story_layer.pronouns(episode.shots)
    out = []
    for line in episode.lines:
        token = story_layer.reported_speech(line.text) if line.kind == "narration" else ""
        if token in ("he", "she") or token in names:
            out.append((line, token, story_layer.speakers_on(token, episode.shot(line.shot).faces, who, names)))
    return out


def own_face(faces: list[str], who: dict[str, str]) -> str:
    """"brigham_young or john_ferrier's speech over his own face"."""
    pronoun = "her" if who.get(faces[0]) == "she" else "his"
    return f"{' or '.join(faces)}'s speech over {pronoun} own face"


def speech_faults(episode: Episode) -> list[str]:
    """HARD: the speaker's face is on the shot and his words are in the narrator's mouth.
    ep10 lines 15 (over both men) and 24 (over Ferrier); ep08 line 27; ep09 line 23."""
    who = story_layer.pronouns(episode.shots)
    return [fault("G-STORY", f"line {line.index}", f"reports {own_face(faces, who)}: make it dialogue",
                  "narration", "dialogue")
            for line, _, faces in reported_lines(episode) if faces]


def speech_advisories(episode: Episode) -> list[str]:
    """The same pattern on a shot without the speaker: ep10 lines 9, 11, 25, 28 on inserts;
    ep05 lines 8, 10, 21 (Holmes reported over face-less shots, and ep05 looked right)."""
    return [f"G-STORY line {line.index}: reports {token}'s speech on shot {line.shot}, whose faces are "
            f"{episode.shot(line.shot).faces} (advisory: the speaker is off the shot; give the line to "
            f"his face, or keep it narration)"
            for line, token, faces in reported_lines(episode) if not faces]


def turn_face_fault(episode: Episode) -> str:
    """The sentence, or "" when the protagonist is in the frame of the turn."""
    turn, who = episode.turn(), story_layer.pronouns(episode.shots)
    if episode.protagonist in turn.faces:
        return ""
    own = "her" if who.get(episode.protagonist) == "she" else "his"
    return fault("G-STORY", f"turn shot {turn.index}", f"the protagonist {episode.protagonist} is not in "
                 f"the frame of {own} own turn", turn.faces, episode.protagonist)


def turn_faults(episode: Episode) -> list[str]:
    """The turn names a value that flips (always), and holds the lead's face (from TURN_FACE_HARD_FROM)."""
    turn, out = episode.turn(), []
    if not story_layer.turns(turn.turn):
        out.append(fault("G-STORY", f"turn shot {turn.index}", "the turn names no value that flips",
                         repr(turn.turn), "'before -> after'"))
    if episode.number >= TURN_FACE_HARD_FROM and (bad := turn_face_fault(episode)):
        out.append(bad)
    return out


def turn_face_advisories(episode: Episode) -> list[str]:
    bad = turn_face_fault(episode)
    if bad and episode.number < TURN_FACE_HARD_FROM:
        return [f"{bad} (advisory below episode {TURN_FACE_HARD_FROM}: ep05 and ep07 were judged right without it)"]
    return []


def wordless_tail(episode: Episode) -> float:
    """Projected seconds of picture after the last word (see WORDLESS_TAIL_S)."""
    button = episode.button()
    spoken = sum(line.projected_seconds() for line in episode.lines_of(button.shot))
    after = [shot for shot in episode.shots if shot.index >= button.shot]
    return sum(episode.shot_seconds(shot) for shot in after) - spoken


def tail_faults(episode: Episode) -> list[str]:
    got = round(wordless_tail(episode), 2)
    if got <= WORDLESS_TAIL_S:
        return []
    return [fault("G-STORY", f"shots {episode.button().shot}-{episode.shots[-1].index}",
                  "wordless tail after the last line in projected seconds", got, WORDLESS_TAIL_S)]


def button_rest_advisories(episode: Episode) -> list[str]:
    shot = episode.shot(episode.button().shot)
    got = round(shot.beat_s + shot.coda_s, 2)
    if got >= BUTTON_REST_S:
        return []
    return [f"G-STORY button shot {shot.index}: beat_s + coda_s is {got} s, under {BUTTON_REST_S} "
            f"(advisory: the last line lands on a held frame, not on a cut)"]


def caption_ratios(episode: Episode) -> list[tuple[float, int, int]]:
    """(ratio, line, shot) for every narration line, most caption-like first."""
    out = []
    for line in episode.lines:
        if line.kind == "narration":
            shot = episode.shot(line.shot)
            out.append((round(story_layer.overlap(line.text, shot.frame + " " + shot.motion), 2),
                        line.index, line.shot))
    return sorted(out, reverse=True)


def caption_advisories(episode: Episode) -> list[str]:
    out = []
    for ratio, line, shot in caption_ratios(episode)[:CAPTION_TOP]:
        over = " -- over the wall" if ratio > CAPTION_WALL else ""
        out.append(f"G-STORY line {line} (shot {shot}): caption-line, {ratio} of its content words are in "
                   f"the shot's frame+motion{over} (advisory: the wall {CAPTION_WALL} is ep07's top line; "
                   f"a line on a picture adds what the picture cannot show)")
    return out


def series_lines(book: Path, number: int) -> list[str]:
    """Every earlier episode's spoken line texts, from audio/lines/lines.json --
    the `earlier_lines` argument of `advisories` / `name_advisories`."""
    out = []
    for n in range(1, number):
        path = Path(book) / "episodes" / f"ep{n:02d}" / "audio" / "lines" / "lines.json"
        if path.exists():
            out += [line["text"] for line in json.loads(path.read_text(encoding="utf-8"))]
    return out


def name_advisories(episode: Episode, earlier_lines: list[str]) -> list[str]:
    """G-NAMES: a name first heard in the series whose first line carries no role noun.
    ep10 line 3 "Jefferson Hope" (0 hits in ep01-09; ep09 calls him "a stranger")."""
    texts = [line.text for line in episode.lines]
    return [f"G-NAMES line {k}: first hearing of {name!r} in the series carries no role (advisory: say "
            f"once who it is -- {', '.join(story_layer.ROLE_NOUNS[:5])}, ...)"
            for k, name in story_layer.naked_names(texts, earlier_lines)]


# ---- the verdict ---------------------------------------------------------------

def faults(episode: Episode) -> list[str]:
    """Every reason this plan should not be drawn, free to compute."""
    from studio import picture_gates  # G-SIZE and the picture advisories (ep10 synthesis C)
    return (firstframe_faults(episode) + variety_faults(episode)
            + move_faults(episode) + rate_faults(episode) + story_faults(episode)
            + picture_gates.faults(episode))


def advisories(episode: Episode, earlier_lines: list[str] | None = None) -> list[str]:
    """The story measures the fixtures proved cannot be refusals: printed,
    never counted.  ep05/07/08's turns are a curtsey, a knife on a pill and a
    dust column -- none acts on another cast member -- and ep05 is the flattest
    plan by projected stdev.  A gate that refuses the good episodes is one
    somebody switches off.

    After ep10: reported speech off the speaker's face, the turn shot's faces
    below `TURN_FACE_HARD_FROM`, the three most caption-like lines, the button
    shot's rest, and -- only when `earlier_lines` (see `series_lines`) is given
    -- G-NAMES, a name's first hearing in the series with no role beside it."""
    out = []
    got = round(shot_length_stdev(episode), 2)
    if got < STDEV_FLOOR:
        out.append(f"G-STORY plan: projected shot-length stdev {got} s is under {STDEV_FLOOR} "
                   f"(advisory: ep05 measures 0.82 and looked right)")
    if not turn_acts_on(episode):
        out.append(f"G-STORY turn shot {episode.turn().index}: no clause has one cast member acting on "
                   f"another (advisory: true of every delivered plan, ep05-ep09)")
    out += (speech_advisories(episode) + turn_face_advisories(episode)
            + caption_advisories(episode) + button_rest_advisories(episode))
    if earlier_lines is not None:
        out += name_advisories(episode, earlier_lines)
    from studio import picture_gates
    out += picture_gates.advisories(episode)
    return out
