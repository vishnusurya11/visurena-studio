"""The contract of a chapter episode, AUDIO FIRST.

The plan carries no seconds.  Lines are written in order and each names the
shot it plays on; the lines are rendered and MEASURED, and every shot's
length is derived from the audio it carries (`studio/episode_timeline.py`).
So there are no holes: the picture is cut to the voice, never the voice laid
on a picture with gaps (docs/analysis/research/episode-07-audio-first.md).

The brick.  ONE EVENT split by a title card: a TURN (the lead's choice) and a
BUTTON (the world's answer, the last line, never the lead's).  A NARRATOR
carries ~90 % of the speech over cutaways; the few DIALOGUE lines are spoken
ON CAMERA, the speaker's face readable and the lips driven by the line's own
audio.  Only rules computable from the plan live here.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from studio import canvas
from studio.affirm import negations
from studio.episode_takes import BUDGET as TAKE_BUDGET

"""THE PACKER'S BUDGET IS THE PLAN'S BUDGET, and it is imported rather than
copied.  `episode_takes.groups` caps a RUN of shots at BUDGET seconds; it cannot
split a single shot, so a shot longer than the budget becomes a take longer than
the budget and nothing downstream refuses it.  Measured on episode 4's first
plan, five of nineteen takes ran 9.4-12.25 s and every one was a shot carrying
two lines -- the band that passed 0 of 2 in episode 3 at a mean of 3.75."""

MIN_SECONDS, MAX_SECONDS = 120.0, 180.0
"""An episode is the WHOLE chapter, two to three minutes (owner, 2026-09-10)."""
WORDS_PER_SECOND = 3.0
"""IndexTTS2 on the cast voices, measured on chapter 1: 33 lines, 147 s of
speech for ~430 words (2026-09-10).  Used only to PROJECT the runtime before
the lines exist; the timeline uses the measured files."""
MAX_WORDS = 18
MAX_BEAT = 1.5
"""The longest silence a shot may name between its lines and the cut."""
MAX_CODA = 4.0
"""The picture after the button, with no voice."""
DIALOGUE_SHARE = (0.05, 0.20)
"""Dialogue words as a share of all words: the 90/10 dial, adjustable."""
MAX_LINES_PER_SHOT = 2
MAX_SPEAKING = 3
MAX_SETUPS = 6
BREATH = 0.70  # audio reviewer, iteration 3: 0.50 was the entire pause between two sentences (wavs carry <= 0.04 s of silence)
HANDLE = 0.25
TURN_BAND = (0.50, 0.75)

Section = Literal["hook", "setup", "friction", "payoff", "transition", "turn",
                  "spike", "reaction", "runout", "button", "answer"]
Size = Literal["insert", "extreme_close", "close", "medium_close", "medium", "full", "wide"]
READABLE = {"close", "medium_close"}
"""Where a speaking mouth reads on a phone: a dialogue shot must be one of these."""


class Line(BaseModel):
    index: int = Field(ge=0)
    kind: Literal["dialogue", "narration"]
    speaker: str
    text: str
    shot: int = Field(ge=0)
    """The shot this line plays on.  Lines are in playback order."""

    def words(self) -> int:
        return len(self.text.split())

    def projected_seconds(self) -> float:
        return self.words() / WORDS_PER_SECOND

    @model_validator(mode="after")
    def _short_enough_to_land(self) -> "Line":
        if self.words() > MAX_WORDS:
            raise ValueError(f"line {self.index} is {self.words()} words; the wall is {MAX_WORDS}")
        return self


MIN_SUB = 2.5
BANNED_PROPS = ("glove",)
"""Words no frame or motion may carry: the drawer draws what the text says,
and the render copies the drawing (a tan glove on Watson, 2026-09-11)."""


def banned_prop(text: str) -> str | None:
    low = text.lower()
    return next((w for w in BANNED_PROPS if w in low), None)


PACE = re.compile(r"(?<![\w-])(slow|slowly|slower|slow-motion|slowmotion"
                  r"|gradual|gradually|languid|languidly|leisurely|lingering|linger"
                  r"|unhurried|dawdl\w*|crawl(?:s|ing)?)(?![\w-])", re.IGNORECASE)
"""NO SLOW SHOTS (owner, strict, 2026-09-12).

`episode_ref_official` refused 'slow' in the take PROMPT, which is one stage
too late: the word is written in the plan, printed on the paid storyboard
sheet, drawn into the cell, and only then refused.  gpt-image obeys a pace
word by drawing the drag as POSTURE, and H3 inherits that posture as position
-- so the slow shot survives the take lint that was supposed to stop it.

The turbo LoRA already pulls toward slow motion on its own, which is why the
rule is a refusal and never a repair: there is no amount of slowness this
engine needs to be asked for.  A gait is a gait ("limps along on his stick at
a normal walking pace"); an amount is an amount ("a thumb's width", "one whole
tread").  Neither is a speed."""


def slow_word(text: str) -> str | None:
    """The pace word in `text`, or None.  A whole word: 'slowworm' is a lizard."""
    found = PACE.search(text or "")
    return found.group(1) if found else None
"""A sub-shot must last at least this long (owner: an insert earns three
seconds; a hold with nothing to watch fails on screen)."""


SHEET_TEXT = ("frame", "motion", "camera", "at_rest", "end", "changed", "crowd")
"""Every field of a segment that is written FOR a model.  All of them are
affirmative: a negated noun is still that noun in the prompt, which is how
"no gloves" in a character description reached six storyboard sheets."""


class Framed(BaseModel):
    """The picture half of a shot or a sub-shot: what the STORYBOARD draws.

    Every field here is one sentence the drawer receives, and each exists
    because the drawer got the previous form wrong (owner, 2026-09-11)."""
    frame: str
    motion: str
    camera: str = ""
    """Where the camera STANDS ("low on the cobbles at the near kerb, level
    with the wheel hub").  An unplaced camera is how a cab insert ended up on
    a different axis from its own wide."""
    at_rest: str = ""
    """Where the thing that is about to move IS, right now, as a noun in a
    place ("Stamford's glass stands on the mahogany, his hand beside it").
    "The instant before: <verb phrase>" was drawn as the finished action."""
    end: str = ""
    """The picture AFTER this segment's motion, written from scratch as nouns
    in positions.  The END panel is drawn from this; told "identical to panel
    1" instead, the drawer drew panel 1 again (four of five END cells)."""
    changed: str = ""
    """The one named change between the start picture and `end`, in five
    words, so the gate and the human check the same sentence."""
    crowd: str = ""
    """This panel's own background life, with a count and an activity.  A
    crowd named once for a location is averaged away over nine panels."""

    @model_validator(mode="after")
    def _the_drawer_reads_only_what_is(self) -> "Framed":
        for name in SHEET_TEXT:
            if bad := negations(getattr(self, name)):
                raise ValueError(f"{name!r} asks for an absence the drawer cannot draw ({bad}); "
                                 f"name what occupies that place instead")
        if self.changed and not self.end:
            raise ValueError("'changed' names the change INTO 'end'; write the end picture too")
        return self

    @model_validator(mode="after")
    def _no_slow_shots(self) -> "Framed":
        """The owner's strict rule: nothing in this pipeline is ever asked to be slow."""
        for name in SHEET_TEXT:
            if word := slow_word(getattr(self, name)):
                raise ValueError(f"{name!r} asks for a slow shot ({word!r}); the owner's rule is that "
                                 f"nothing is slow. Name the AMOUNT instead -- a thumb's width, one "
                                 f"whole tread, a hand's breadth -- or the gait at a normal pace")
        return self


class SubShot(Framed):
    """A CUT inside a shot's audio window (owner, 2026-09-11: an 11 s insert
    of a hand on a stick is a carrier, not a cutaway).  Carries no line and
    no seconds: the parent shot keeps its lines and its derived length; the
    take renders `[Shot k] At MM:SS.mmm, the shot cuts to ...` at `at_s`."""
    at_s: float = Field(gt=0)
    size: Size
    faces: list[str] = Field(default_factory=list)
    path: float | None = Field(default=None, ge=0, le=1)
    """Position along the setup's route (0 = its start, 1 = its far end)."""


class Shot(Framed):
    index: int = Field(ge=0)
    section: Section
    setup: str
    size: Size
    faces: list[str] = Field(default_factory=list)
    """Whose face is frontal and readable in the panel."""
    take: int = Field(default=0, ge=0)
    beat_s: float = Field(default=0.0, ge=0, le=MAX_BEAT)
    """Named silence after this shot's lines, before the cut."""
    coda_s: float = Field(default=0.0, ge=0, le=MAX_CODA)
    """Picture with no voice at the very end (the world's answer)."""
    cuts: list[SubShot] = Field(default_factory=list)
    """Sub-shots, in time order, each at least MIN_SUB after the previous
    (the parent's own frame is the implicit first sub-shot at 0)."""
    path: float | None = Field(default=None, ge=0, le=1)
    """Position along the setup's route at this shot's first frame; never
    goes backwards through a setup's shots (the storyboard is one sequence)."""
    turn: str = ""
    """The value this shot puts at stake and how it flips, as "before -> after"
    ("alone -> seen", "hope -> refused").

    McKee: there is no scene without a turn; a scene whose value reads the same
    at the close exists to explain something, and explanation belongs inside
    another scene's picture.  We had already measured this as a RENDER fault --
    a shot with nothing to photograph comes back frozen -- without knowing it
    was a story fault first.  Reported by `studio.story_layer`, never refused,
    because episode 1 was cut before the field existed."""
    why: str = ""
    """Why this shot is in the episode: the new thing it tells, and the thing it
    shows about the protagonist (Hicks: a scene does both or it is cut).

    The ONLY shot string the drawer never reads -- it is reasoning for the
    people and the agents writing the episode, so it is absent from SHEET_TEXT
    and free to explain an absence, which every drawn string is forbidden."""

    @model_validator(mode="after")
    def _no_banned_props(self) -> "Shot":
        texts = [self.frame, self.motion] + [c.frame + " " + c.motion for c in self.cuts]
        for text in texts:
            if word := banned_prop(text):
                raise ValueError(f"shot {self.index}: '{word}' in the frame text; the book gives bare hands")
        return self

    @model_validator(mode="after")
    def _cuts_ascend(self) -> "Shot":
        last = 0.0
        for cut in self.cuts:
            if cut.at_s - last < MIN_SUB:
                raise ValueError(f"shot {self.index}: a sub-shot at {cut.at_s} s is less than "
                                 f"{MIN_SUB} s after the previous ({last} s)")
            last = cut.at_s
        return self


class Setup(BaseModel):
    described: str
    cast: list[str] = Field(default_factory=list)
    landmark: str = ""
    """One fixed object the storyboard drawer keeps at the same place in every
    cell of a take sheet ("the barred window at the far end")."""
    landmark_at: Literal["start", "far_end"] = "far_end"
    """WHICH END of `route` the landmark stands at, and so which way its apparent
    size runs: a corridor door grows as they walk to it, the bench's Bunsen flame
    and the gateway's arch shrink as they walk away.  Told a walk always ENDS at
    its landmark, the sheet put a one-inch flame twenty feet off at "fills the
    frame" and the drawer drew the burner (cell Q19_1, 2026-09-11)."""
    landmark_size: str = ""
    """The biggest this landmark ever stands in this setup, in the size ladder's
    own words ("is the height of a finger").  A door reaches the top rung at
    closest approach; a flame never leaves the bottom one.  Empty means the
    ladder runs to the top."""
    route: str = ""
    """The path the people travel in this setup, start to far end ("from the
    corridor's near end to the dissecting-room doorway at its far end")."""
    geometry: str = ""
    """How the fixed things in this place stand relative to each other, each
    relation restated as WHICH FRAME EDGE at WHAT APPARENT SIZE with what
    between.  "The horse ahead of the wheel" drew a horse level with a wheel
    three times; relational prepositions are the documented weak spot."""
    crowd: str = ""
    """The background life of this place, as a count and an activity ("eight
    or nine men in top hats two deep at the counter, a barman drawing a
    cork").  Reaches every panel that is not an insert."""
    outdoors: bool = False
    """True when this setup stands under the sky.  The hat rule for the whole
    sheet is a function of it, stated flat instead of as a conditional."""
    props: list[str] = Field(default_factory=list)
    """Prop plates attached as references (`plate_<name>.png`): the one that
    binds a vehicle across the setups that share it.  The cab was bound by
    words on one sheet and by nothing on another, and three different vehicles
    came back."""

    @property
    def state(self) -> str:
        """Which WARDROBE STATE this setup is in, and so which cast card binds
        it: the hat on the head, or the hat in the hand.

        The contract has exactly two states and six setups map onto them
        (criterion, corridor, lab and bench indoors; cab and gateway outdoors --
        the cab is open to the street and counts as outdoor).  DERIVED from the
        `outdoors` flag the plan already declares, never declared a second time:
        two fields that can disagree about one fact is exactly the fault
        `cast_agree` exists to catch (R1, one writer).

        A setup cannot get the wrong hat state by accident now, because the
        state is a declared field, it lints once, and it selects the file."""
        return "outdoor" if self.outdoors else "indoor"

    @model_validator(mode="after")
    def _the_drawer_reads_only_what_is(self) -> "Setup":
        for name in ("described", "geometry", "crowd"):
            if bad := negations(getattr(self, name)):
                raise ValueError(f"setup {name!r} asks for an absence ({bad}); name what is there instead")
            if word := slow_word(getattr(self, name)):
                raise ValueError(f"setup {name!r} asks for a slow shot ({word!r}); the owner's rule is "
                                 f"that nothing is slow -- name the amount or the gait instead")
        return self


class Episode(BaseModel):
    number: int = Field(ge=1)
    title: str
    question: str = ""
    """The one question this episode answers, in Armstrong's form: "Today, can
    X do Y?"  Answered before the episode ends, or the episode has no reason to
    stop where it stops.  Reported by `studio.story_layer`, never refused."""
    aspect: Literal["9:16", "1:1"] = canvas.DEFAULT
    """The delivery shape, and the ONE place it is declared (`studio/canvas.py`).

    Every stage -- the plate, the sheet grid and its own wording, the take, the
    cut, the title card -- derives its canvas from this field, because the
    aspect written down seven times is six chances to disagree silently: a
    square take cropped by a vertical assemble loses a third of every frame and
    nothing raises.  The default is what episode 1 shipped; episode 2 is 1:1 on
    the owner's spec (2026-09-12), and the owner's spec outranks the default."""
    protagonist: str
    setups: dict[str, Setup]
    shots: list[Shot]
    lines: list[Line]
    beds: list[dict] = Field(default_factory=list)
    """The music bed's tone spans: `[{"from_shot": 0, "tone": "plain"}, ...]`.

    OWNER 2026-09-14: "different types based on the context of background
    thrilling .. normal".  One drone under a breakfast, a joke, a flashback and
    a murder is why episode 5's bed read as loud at 15 LU under the voice.

    AUTHORED, NOT DERIVED FROM `section`.  "friction" covers both a comic
    invasion of six street boys and a man's hand closing on a woman's wrist, so
    a tone taken from the label would be confidently wrong about one of them.
    Empty means one `plain` span end to end, which is what episodes 1-5 shipped.
    `studio/episode_bed.py` owns the tones and cuts the spans."""

    # ---- lookups -----------------------------------------------------------
    def shot(self, index: int) -> Shot:
        return next(s for s in self.shots if s.index == index)

    def lines_of(self, shot_index: int) -> list[Line]:
        return [line for line in self.lines if line.shot == shot_index]

    def dialogue(self) -> list[Line]:
        return [line for line in self.lines if line.kind == "dialogue"]

    def button(self) -> Line:
        return self.lines[-1]

    def turn(self) -> Shot:
        return next(shot for shot in self.shots if shot.section == "turn")

    def shot_seconds(self, shot: Shot) -> float:
        carried = self.lines_of(shot.index)
        return (2 * HANDLE + sum(line.projected_seconds() for line in carried)
                + BREATH * max(len(carried) - 1, 0) + shot.beat_s + shot.coda_s)

    def projected_seconds(self) -> float:
        """The runtime before any line is rendered: words at the measured pace,
        breaths, handles, beats and codas."""
        return sum(self.shot_seconds(shot) for shot in self.shots)

    def dialogue_share(self) -> float:
        words = sum(line.words() for line in self.lines) or 1
        return sum(line.words() for line in self.dialogue()) / words

    # ---- the rules ---------------------------------------------------------
    @model_validator(mode="after")
    def _shots_are_in_order_and_named(self) -> "Episode":
        if [s.index for s in self.shots] != list(range(len(self.shots))):
            raise ValueError("shots are numbered 0..n-1 in cut order")
        for shot in self.shots:
            if shot.setup not in self.setups:
                raise ValueError(f"shot {shot.index} names setup {shot.setup!r}, which is not defined")
        if len({s.setup for s in self.shots}) > MAX_SETUPS:
            raise ValueError(f"more than {MAX_SETUPS} setups")
        return self

    @model_validator(mode="after")
    def _lines_are_in_playback_order(self) -> "Episode":
        if not self.lines:
            raise ValueError("an episode with no line has no button")
        if [l.index for l in self.lines] != list(range(len(self.lines))):
            raise ValueError("lines are numbered 0..n-1 in playback order")
        shots = [line.shot for line in self.lines]
        if shots != sorted(shots):
            raise ValueError("a line's shot never precedes an earlier line's shot")
        if any(s >= len(self.shots) for s in shots):
            raise ValueError("a line names a shot that does not exist")
        for shot in self.shots:
            if len(self.lines_of(shot.index)) > MAX_LINES_PER_SHOT:
                raise ValueError(f"shot {shot.index} carries more than {MAX_LINES_PER_SHOT} lines")
            if not self.lines_of(shot.index) and not (shot.beat_s or shot.coda_s):
                raise ValueError(f"shot {shot.index} carries no line and names no beat: a hole")
        return self

    def long_shots(self) -> list[tuple[int, float]]:
        """Shots that project longer than a take, with their seconds.

        A QUERY, NOT A VALIDATOR.  This was a validator and it refused episode
        1's already-published plan, whose shot 17 projects 11.40 s -- so every
        tool that merely READS an old plan broke, `story.py` included.  Reading
        a historical plan is not endorsing it; the constraint belongs where a
        plan is about to be DRAWN or RENDERED, before anything is spent, and
        `seq_boards` and `takes_r2v` ask there.

        Measured over the shipped plans: ep01 has one (shot 17, 11.40 s), ep02,
        ep03 and ep04 have none."""
        return [(s.index, round(self.shot_seconds(s), 2))
                for s in self.shots if self.shot_seconds(s) > TAKE_BUDGET]

    def still_motions(self) -> list[tuple[int, str, str]]:
        """Every segment whose motion will render still, as (shot, code, why).

        A QUERY for the same reason `long_shots` is one: episodes 1, 4 and 5 are
        published with 46 shots that fail M2, and reading a historical plan is
        not endorsing it.  `seq_boards` and `takes_r2v` refuse on it, before the
        $0.20 sheets and before the GPU.

        Measured 2026-09-14 -- shots whose head names no camera move: ep01 19/23,
        ep02 2/25, ep03 0/25, ep04 13/24, ep05 19/25.  Episodes 2 and 3 lost
        almost nothing to stillness; 4 and 5 lost 98 % of their score to it."""
        out = []
        for shot in self.shots:
            for seg in [shot] + list(shot.cuts or []):
                out += [(shot.index, code, why) for code, why in motion_faults(seg.motion)]
                out += [(shot.index, "M9", f"{thing!r} moves with nothing to move it; "
                                           f"give the camera the move, or name the hand")
                        for thing in uncaused_motion(seg.motion)]
        return out

    @model_validator(mode="after")
    def _the_shape_is_present(self) -> "Episode":
        sections = [shot.section for shot in self.shots]
        for name in ("hook", "turn", "button"):
            if sections.count(name) != 1:
                raise ValueError(f"an episode has exactly one {name}; found {sections.count(name)}")
        if self.shots[0].section != "hook":
            raise ValueError("the first shot is the hook")
        button = self.button()
        if self.shot(button.shot).section != "button":
            raise ValueError("the last line plays on the button shot")
        if button.speaker == self.protagonist:
            raise ValueError("the last line is not the protagonist's (rule 5)")
        if any(self.lines_of(s.index) for s in self.shots if s.index > button.shot):
            raise ValueError("no line after the button; the coda is picture only")
        if button.shot > 0 and self.shot(button.shot - 1).beat_s < 1.0:
            raise ValueError("the shot before the button names a beat of >= 1.0 s of silence")
        return self

    @model_validator(mode="after")
    def _route_never_goes_backwards(self) -> "Episode":
        for name in self.setups:
            last = -1.0
            for shot in self.shots:
                if shot.setup != name:
                    continue
                for p in [shot.path] + [c.path for c in shot.cuts]:
                    if p is None:
                        continue
                    if p < last - 1e-9:
                        raise ValueError(f"setup {name!r}: shot {shot.index} goes backwards along the route")
                    last = p
        return self

    @model_validator(mode="after")
    def _cuts_sit_on_narration_and_fit(self) -> "Episode":
        for shot in self.shots:
            if not shot.cuts:
                continue
            if any(l.kind == "dialogue" for l in self.lines_of(shot.index)):
                raise ValueError(f"shot {shot.index}: a dialogue shot takes no sub-shots (the driven "
                                 f"lips stay in one readable frame)")
            if self.shot_seconds(shot) - shot.cuts[-1].at_s < MIN_SUB:
                raise ValueError(f"shot {shot.index}: the last sub-shot projects shorter than {MIN_SUB} s")
        return self

    @model_validator(mode="after")
    def _dialogue_is_on_camera(self) -> "Episode":
        for line in self.dialogue():
            shot = self.shot(line.shot)
            if line.speaker not in shot.faces or shot.size not in READABLE:
                raise ValueError(f"dialogue line {line.index}: shot {shot.index} must show "
                                 f"{line.speaker}'s face at close or medium_close (lips are driven)")
        share = self.dialogue_share()
        if not DIALOGUE_SHARE[0] <= share <= DIALOGUE_SHARE[1]:
            raise ValueError(f"dialogue is {share:.0%} of the words; the dial is "
                             f"{DIALOGUE_SHARE[0]:.0%}-{DIALOGUE_SHARE[1]:.0%}")
        if len({line.speaker for line in self.lines}) > MAX_SPEAKING:
            raise ValueError(f"more than {MAX_SPEAKING} voices")
        return self

    @model_validator(mode="after")
    def _projects_to_an_episode(self) -> "Episode":
        seconds = self.projected_seconds()
        if not MIN_SECONDS <= seconds <= MAX_SECONDS:
            raise ValueError(f"projects to {seconds:.0f} s; an episode is {MIN_SECONDS:.0f}-"
                             f"{MAX_SECONDS:.0f} s (words at {WORDS_PER_SECOND} a second)")
        elapsed, turn_at = 0.0, 0.0
        for shot in self.shots:
            if shot.section == "turn":
                turn_at = elapsed
            elapsed += self.shot_seconds(shot)
        share = turn_at / seconds
        if not TURN_BAND[0] <= share <= TURN_BAND[1]:
            raise ValueError(f"the turn projects to {share:.0%} of the runtime; wanted 50-75 %")
        return self


# ---- a thing moves because something moves it -------------------------------

MOVABLE = (r"paper|sheet|note|letter|envelope|card|newspaper|book|page|ring|band|coin|"
           r"cup|saucer|plate|knife|spoon|bottle|box|pipe|hat|key|watch|chain|lamp|"
           r"chair|stool|drawer|lid|violin|bow|pen|light|beam|shaft|patch|shadow|"
           r"jar|tray|glass|boot|glove|purse")
"""Things that are at rest on a surface until somebody touches them.

Deliberately NOT here: fog, flame, smoke, coal, washing, a cab wheel, water.
Those move for reasons the place supplies, and shots built on them are fine --
episode 4's fog and episode 5's firelight are among the takes that scored 100."""

SELF_MOVERS = (r"fog|mist|smoke|steam|flame|fire|coal|ember|embers|rain|snow|sleet|"
               r"wind|draught|draft|breeze|cloud|dust|water|wheel|washing|curtain|"
               r"horse|traffic|crowd|snowflake")
"""The standing natural agents: a clause that names one has its cause in it."""

AGENTS = (r"camera|hand|hands|finger|fingers|thumb|arm|arms|fist|wrist|elbow|knee|"
          r"foot|shoulder|he|she|they|him|her|his|their|holmes|watson|lestrade|"
          r"gregson|rance|man|woman|boy|girl")
"""What can make a thing move: a person, a part of one, or the camera."""

MOVES_ITSELF = re.compile(
    r"\b(" + MOVABLE + r")\b(?:\s+\w+){0,2}\s+"
    r"\b(slides?|moves?|turns?|travels?|drifts?|crosses?|rolls?|falls?|fell|lifts?|"
    r"rises?|rose|tips?|swings?|glides?|creeps?|crept|sweeps?|swept|floats?|shifts?|"
    r"slips?|tilts?|swivels?|spins?|opens?|closes?)\b", re.IGNORECASE)

HAS_CAUSE = re.compile(r"\b(" + AGENTS + r"|" + SELF_MOVERS + r")\b", re.IGNORECASE)

SPLIT_CLAUSE = re.compile(r";|\band\b|(?<!\bM)\.(?:\s|$)", re.IGNORECASE)


def uncaused_motion(motion: str) -> list[str]:
    """Every thing in `motion` that moves with nothing to move it.

    OWNER, 2026-09-14, on episode 5: "remove unnatural movement like paper
    turning on its own on table ... and violin getting a red light ... keep the
    movement simple".

    Both were real.  Both are what I wrote when a shot needed to not be still
    and its head clause named no camera move -- so the motion had to come from
    somewhere and I gave it to the props.  That is the wrong mover: the research
    census (2026-09-14, 92 takes) puts every one of the 10 stillest takes in the
    set of shots whose head names no camera move, and all 19 whose head names
    one at exactly 100.  The camera is what should have been moving.

    Judged per clause, because "The coal settles in the grate and a red light
    moves across the strings" has its cause in the first half and not the
    second."""
    out: list[str] = []
    for clause in SPLIT_CLAUSE.split(motion or ""):
        if not clause or HAS_CAUSE.search(clause):
            continue
        found = MOVES_ITSELF.search(clause)
        if found and (word := found.group(1).lower()) not in out:
            out.append(word)
    return out


# ---- the head clause names a camera move ------------------------------------

TERMINAL = re.compile(r"\b(settles?|comes? to rest|at rest|drops? into|closes? on|"
                      r"stops?|lands?|sinks? to|lies (?:flat|still)|rests?)\b", re.I)
"""Last-clause endings that state an END STATE.

The builder bolts `and <noun> continues to the last frame of the shot` onto the
last clause, so a terminal one produces a sentence that contradicts itself and
the model obeys the terminal half.  Measured: fires on 7 of episodes 4-5's 49
shots, whose mean frozen penalty is 8.13 against 2.60 for the other 42."""

FEATURES = re.compile(r"\b(eyes?|brows?|eyelids?|lashes|pupils?|iris|jaw|"
                      r"lips?|nostrils?|line of (?:his|her|their) mouth)\b", re.I)
"""`lids?` on its own used to be in here and it matched a CIGAR BOX LID on
episode 6's shot 14 -- an object rocking a thumb's width, which is exactly the
kind of tail the rule exists to permit.  An eyelid is `eyelid`."""
"""Face parts too small for the instrument that judges the take.

`motion_gate` bins a 24x24 block of a 192x336 grey frame -- about a MOUTH's size
at 768x1344.  A mouth speaking reads 3-15 against `STILL = 1.2` and registers
fine; an eye moving inside that block does not shift its mean.  So a last clause
whose subject is one of these leaves the tail measurably frozen however
faithfully H3 renders it (ep04 T11, ep05 T15).

KNOWN GAP: ep05 T04's `his fingers spread once on the cloth` is the same fault
with a hand-sized subject, and this does not catch it -- `his thumb runs along
the barrel` is a shipped 100 and no subject-noun rule separates the two.  The
difference is `once` against `runs along`, and one instance is not enough to
write a rule on."""


def motion_faults(motion: str) -> list[tuple[str, str]]:
    """Every reason this motion will render still, as (code, what to do).

    A QUERY, NOT A VALIDATOR -- `long_shots` records what happened the last time
    a rule like this was a `model_validator`: it refused a published plan and
    broke every tool that merely READS one.  Episodes 4 and 5 are published with
    30 shots that fail M2.  The refusal belongs at the steps that SPEND."""
    from studio.episode_ref_official import CAMERA, MOVES, STILL, camera_clause, clauses_of

    if not (motion or "").strip():
        return []
    parts = [c.strip() for c in motion.split(";") if c.strip()]
    head, _ = clauses_of(motion)
    cam, _ = camera_clause(head)
    first = (cam.split() or [""])[0].lower().rstrip(",.;")
    last = parts[-1]
    out = []
    if len(parts) < 3:
        out.append(("M1", f"{len(parts)} clause(s): the builder reads beats from the THIRD "
                          f"onward, so this yields no timed beat and no 'continues to the "
                          f"last frame' sentence. Write `camera; action; action`."))
    if not (first in CAMERA or any(first.startswith(w) for w in MOVES)):
        out.append(("M2", "the head names no camera move. Open with one, before the first "
                          "semicolon, with a measured amount and `across the whole shot` -- "
                          "a move written after a semicolon is deleted by the builder."))
    if STILL.search(last):
        out.append(("M4", f"the LAST clause says the picture is still ({last!r}); `calm()` "
                          f"rewrites that into a positive static assertion the take lint "
                          f"cannot see. A stillness clause is fine anywhere but last."))
    if TERMINAL.search(last):
        out.append(("M5", f"the LAST clause states an end state ({last!r}), and the builder "
                          f"appends `continues to the last frame` to it. End on something "
                          f"still going: `runs along`, `comes down`, `lifts`."))
    if FEATURES.search(last):
        out.append(("M6", f"the LAST clause moves a face part too small to measure "
                          f"({last!r}). The tail needs a limb, a head, a torso or a "
                          f"travelling object."))
    return out


HARD_MOTION = ("M2", "M9")
"""Which motion faults REFUSE a plan, as against merely printing.

Only the two the evidence actually carries.  Measured over the four scored
episodes, the fault codes fire like this:

    ep02  M1 34  M2  3  M4 1  M5 5  M6 10  M9 1     stillness loss ~0
    ep03  M1 21  M2  1  M4 2  M5 1  M6 10  M9 3     stillness loss ~0
    ep04  M1 10  M2 13  M4 8  M5 2  M6  7           59.1 points
    ep05  M1 16  M2 19  M4 1  M5 5  M6  3  M9 2    106.8 points

M1 and M6 fire hardest on the two episodes that lost nothing to stillness, so
as refusals they would be mostly noise -- the pooled effect of clause count is
1.6x against 13-21x for the camera move.  M2 tracks the damage exactly.  M9 is
what the owner saw on screen.

An un-automatable safety gate is one somebody eventually comments out, and a
gate that refuses 34 correct motions is the same thing by a slower route.  The
advisories still print, because they are how a motion gets from passing to
good."""


# ---- a man may only carry his own marks -------------------------------------

def marks_of(refs: list[dict]) -> dict[str, str]:
    """`{mark: entity_id}` from the bible's own `marks` lists.

    A MARK IS A THING ONLY ONE CHARACTER HAS.  It is authored, not derived from
    `physical`: "both hands bare" and "a white collar" are in nearly every
    description and belong to nobody, so a derived list is mostly noise."""
    out: dict[str, str] = {}
    for row in refs:
        if row.get("kind") != "character":
            continue
        for mark in row.get("marks") or []:
            low = mark.lower()
            if low in out and out[low] != row["entity_id"]:
                raise ValueError(f"{mark!r} is claimed by both {out[low]} and "
                                 f"{row['entity_id']}; a mark two men share is not a mark")
            out[low] = row["entity_id"]
    return out


def named_in(text: str, names: dict[str, str]) -> list[str]:
    """Which characters this text names, in the order they first appear."""
    low = (text or "").lower()
    at = sorted((m.start(), who) for word, who in names.items()
                for m in re.finditer(rf"\b{re.escape(word)}\b", low))
    out: list[str] = []
    for _, who in at:
        if who not in out:
            out.append(who)
    return out


def name_map(refs: list[dict]) -> dict[str, str]:
    """`{token: entity_id}` for every token that names exactly ONE character.

    A TOKEN CLAIMED BY TWO PEOPLE IDENTIFIES NEITHER, so it is dropped -- the
    same rule `marks_of` applies to marks.  Madame, Alice and Arthur Charpentier
    all answer to "charpentier", and a map built from surnames alone gave the
    key to whichever row was written last: episode 6's mother was then reported
    as her son wearing her own black bombazine.

    `aka` carries the phrases a PLAN actually uses for someone it does not name.
    Episode 5's shot 20 is "the old woman going small and bent in her brown
    shawl ... and Holmes ... following": Holmes is the only name in it, so
    without the alias her shawl is attributed to him and a correct shot is
    refused."""
    claims: dict[str, set] = {}
    for row in refs:
        if row.get("kind") != "character":
            continue
        who, name = row["entity_id"], row.get("name", "").lower()
        tokens = {name, name.split()[-1].strip(".,") if name else ""}
        tokens |= {w.strip(".,") for w in name.split() if len(w) > 4}
        tokens |= {a.lower().strip() for a in row.get("aka") or []}
        for token in tokens:
            if len(token) > 3:
                claims.setdefault(token, set()).add(who)
    return {token: next(iter(who)) for token, who in claims.items() if len(who) == 1}


def crossed_mark(text: str, owners: dict[str, str],
                 names: dict[str, str]) -> tuple[str, str, str] | None:
    """The first (wearer, mark, true owner) in `text` where they disagree.

    IT ANSWERS ONLY WHEN THE PROSE NAMES EXACTLY ONE MAN, because that is the
    only case where the wearer is not a guess.  Clause attribution was tried and
    measured over the six plans on disk: it produced 17 hits and almost all were
    two-handers describing both men in one sentence, where the mark's own clause
    names nobody.  Episode 3 has the opposite shape -- "Medium on WATSON ...
    where HOLMES has knelt ... his hand on the silver ball knob" -- so nearest
    preceding name is wrong there and first name is wrong in the other.  No
    ordering rule settles both, and a lint that cries wolf on every two-hander
    is one somebody turns off.

    THE FAULT THAT SHIPPED IS EXACTLY THIS SHAPE.  Episode 4's take 2 is an
    insert of nothing but a hand, naming HOLMES alone, carrying Watson's black
    walking stick beside Holmes's own sticking plaster -- both men's identity
    marks in one full-frame picture.

    A segment naming two or more men is NOT MEASURED; `unmeasured_marks` is how
    a caller reports that rather than treating it as a pass."""
    here = named_in(text, names)
    if len(here) != 1:
        return None
    wearer = here[0]
    for mark, owner in owners.items():
        if owner != wearer and mark.lower() in (text or "").lower():
            return wearer, mark, owner
    return None


def unmeasured_marks(text: str, owners: dict[str, str], names: dict[str, str]) -> list[str]:
    """The men named in a segment the mark lint had to stand down on.

    Empty when the segment was measurable.  An unmeasured check that reads as a
    pass is this repo's most-found fault, so the two-hander case is reported
    rather than silently skipped."""
    here = named_in(text, names)
    if len(here) < 2:
        return []
    return here if any(m.lower() in (text or "").lower() for m in owners) else []


MARK_FIELDS = ("frame", "motion", "camera", "at_rest", "end")


def plan_marks(episode, refs: list[dict]) -> tuple[list[str], list[str]]:
    """(crossed, unmeasured) for a whole plan, against the bible's own marks.

    MEASURED over the six plans on disk, 140 shots: ONE crossed mark, and it is
    exactly the take the identity audit found by eye -- episode 4's shot 2,
    "Insert on Holmes's raised hand ... off the head of the black stick", which
    rendered Watson's stick and Holmes's sticking plaster on one hand in one
    full-frame insert.  No false positives.

    37 segments are NOT MEASURED because they name two men, and those are
    returned separately rather than counted as clean."""
    owners, names = marks_of(refs), name_map(refs)
    crossed, vague = [], []
    for shot in episode.shots:
        for seg in [shot] + list(shot.cuts or []):
            for field in MARK_FIELDS:
                said = getattr(seg, field, "") or ""
                if got := crossed_mark(said, owners, names):
                    wearer, mark, owner = got
                    crossed.append(f"shot {shot.index} {field}: {wearer} carries {mark!r}, "
                                   f"which refs.json gives to {owner} alone")
                elif who := unmeasured_marks(said, owners, names):
                    vague.append(f"shot {shot.index} {field}: {' and '.join(who)} both named")
    return crossed, vague
