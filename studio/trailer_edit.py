"""Turning a measured cue into a shot list.

The rule the whole module serves: SHOT LENGTHS MUST VARY, and they must vary
in the shape the corpus shows -- open around 1.5s, breathe at a third, tighten
to about 0.55s at 85-90%, then hold the title for ~3s.  Uniform shot lengths
are the single most-named amateur tell, and they are what a generated pipeline
produces by default, because the model hands back clips of one fixed size.

An editor watching run 10 named the second half of that rule, which the module
had lost: "the music grid owns every cut ... the viewer starts counting within
4 shots and predicts cuts; picture becomes wallpaper for the audio."  Varying
IS NOT ENOUGH if the variation is predictable, and it is predictable the moment
the pulse is showing.  So `plan_cuts` does three things at once:

  * the ACTS shape the lengths -- act 1 holds a bar and a half, act 3 cuts
    twice a bar, and the medians strictly decrease (`ACT_BARS`);
  * a nine-shot FIGURE turns each act's nominal so no four shots in a row are
    the same length and every 12 s window varies (`FIGURE`);
  * the music owns act 3 and nothing before it -- acts 1-2 cut on the moments
    that EARN a beat (phrase starts, stopdowns, hits, dialogue slots) and land
    off the pulse otherwise (`BEAT_LOCK`).

`act_medians`, `longest_equal_run`, `interval_variation` and `on_beat_fraction`
at the foot of the module measure exactly those three, off any list of cut
points -- the plan's or the delivered master's.

Research: docs/analysis/research/trailer-cut-rhythm.md
"""
from __future__ import annotations

from studio.shot_grammar import MIN_SECONDS
from studio.trailer_cut import target_length

SNAP_TOLERANCE = 0.30
"""How far a cut will move to reach a musical onset.  Beyond this the arc
wins, because a cut dragged a long way to hit a beat stops serving the shot."""

LITERARY_STRETCH = 2.5
"""The corpus arc is measured on horror trailers -- the fastest-cutting kind.
A canonical text has no spoiler to protect, so its trailer sells tone and
world rather than withheld plot, and Woollen's register holds shots far
longer (his Birdman teaser keeps a single 32-second take).  Stretching the
arc keeps its SHAPE -- the variety and the late acceleration -- while cutting
the shot count to something a generated pipeline can actually cover."""

MAX_SHOT = 4.0
"""No shot may run longer than this, wherever the onsets happen to fall.

`cut_points` takes the onset NEAREST the arc's next position, unconditionally,
which is right when the music is dense and wrong when it is not.  The chosen
Scarlet cue has ONE onset in its entire eighth decile -- 81.4s to 91.6s -- and
the corpus arc asks for its fastest cutting at exactly 85-90%.  With nothing
near to land on, one shot stretched to 7.42 seconds at the climax: a static
bearded man held for a quarter of the trailer's final third.

The real fix is upstream -- the cue should have been asked for density there,
and refused for arriving without it.  This is the floor under that.
"""

MIN_SHOT = min(MIN_SECONDS.values())
"""Below this a shot reads as a flash frame rather than an image: the time
the grammar's smallest size (an insert) needs to be read.  ONE floor -- when
this was its own 0.4 the walk emitted a 0.417 s shot at 128 BPM and the
grammar, at 0.5, had no size for it (Scarlet run 3, 2026-09-04)."""


def snap(when: float, grid: list[float], tolerance: float = SNAP_TOLERANCE) -> float:
    """Move a cut onto a musical onset if one is within tolerance."""
    if not grid:
        return when
    nearest = min(grid, key=lambda point: abs(point - when))
    return nearest if abs(nearest - when) <= tolerance else when


def quantise(seconds: float, fps: int = 24) -> float:
    """Round a duration to a whole number of frames.

    `extract` passes `-t` to ffmpeg, which cannot render a fraction of a frame.
    MEASURED, not assumed: it keeps every frame whose timestamp is below t, so
    the rendered count is `ceil(t * fps)` and a fractional duration rounds the
    picture UP -- 1.35s asks for 32.4 frames and gets 33, which is 1.375s.
    (An earlier note here claimed the opposite, that -t truncates downward.  It
    does not; the drift was real but its sign was guessed, and the fix that
    followed from the guess added a frame instead of saving one.)

    Every rounding is under a frame, and thirty-three of them accumulated to
    **1.28 seconds** between the planned picture and the delivered one, so the
    title card cut in early and the cue's braam landed 5.13s into it instead of
    3.85s.  Planning in frames means the plan and the file agree by
    construction, whichever way the renderer would have rounded.
    """
    # No minimum here.  This quantises a TIMESTAMP, and clamping it to one
    # frame made the cut start at 0.042s instead of 0.0.  The one-frame floor
    # belongs to durations, and MIN_SHOT already enforces it.
    return max(0, round(seconds * fps)) / fps


def cut_points(duration: float, grid: list[float], start: float = 0.0,
               stretch: float = LITERARY_STRETCH, fps: int = 24) -> list[float]:
    """Shot boundaries CHOSEN FROM the musical grid, paced by the arc.

    The previous version walked the arc and snapped to an onset only if one
    happened to lie within 0.3s.  With 20 onsets over 100s that is a hit rate
    of about 12%, and measured on the shipped cut it was **2 of 33 = 6%**.  The
    arc was the timeline and the music was decoration, which is the opposite of
    what this module claims to do.

    Now the arc proposes and the grid disposes: for each step we take the onset
    NEAREST the arc's next position, unconditionally.  The music therefore owns
    every cut, and the arc only decides which onset.

    SUPERSEDED for the trailer by `plan_cuts`, and this docstring is why: an
    editor watching run 10's master said "the music grid owns every cut ...
    the viewer starts counting within 4 shots and predicts cuts; picture
    becomes wallpaper for the audio".  Owning every cut is the defect, not
    the fix.  This function survives only for `build_plan.py`, which cuts a
    song video to an onset list rather than a measured metre.
    """
    usable = [g for g in grid if start < g < duration]
    points = [quantise(start, fps)]
    while True:
        position = (points[-1] - start) / max(duration - start, 1e-6)
        nominal = points[-1] + target_length(position) * stretch
        if nominal >= duration - MIN_SHOT:
            break
        ahead = [g for g in usable if g > points[-1] + MIN_SHOT]
        ceiling = points[-1] + MAX_SHOT
        near = [g for g in ahead if g <= ceiling] or ahead
        landed = min(near, key=lambda g: abs(g - nominal)) if near else nominal
        if landed <= points[-1] + MIN_SHOT:
            landed = points[-1] + target_length(position) * stretch
        landed = min(landed, ceiling)
        points.append(quantise(landed, fps))
    if duration - points[-1] < MIN_SHOT and len(points) > 1:
        points.pop()
    points.append(quantise(duration, fps))
    return points


def lengths_of(points: list[float], fps: int = 24) -> list[float]:
    """Shot lengths, in whole frames.

    `round(b - a, 3)` looked harmless and was not.  The difference of two
    frame-aligned points is itself frame-aligned, and three decimals cannot
    hold it: 53 frames is 2.20833...s, which rounds to 2.208.  That particular
    value still renders 53 (see `frames_arg` for the measured rule), but the
    plan is now carrying a number that is not a frame count, and every consumer
    of it has to guess which way the renderer will go.  Returning frames means
    nobody guesses.
    """
    return [round((b - a) * fps) / fps for a, b in zip(points, points[1:])]


# --- the beat walk (research trailer-cut-rhythm.md) -----------------------

EPS = 1e-6
ON_BEAT = 0.04
"""Within a frame of a beat is ON it -- qc.py's own tolerance, so the plan
and the delivered master are graded by one ruler."""

OFF_BEAT = 0.125
"""Three frames.  How far a cut that is NOT serving the music is pushed clear
of the pulse, so nothing accidental reads as a downbeat."""

ACT_BANDS: list[tuple[float, float]] = [(0.0, 0.30), (0.30, 0.66), (0.66, 0.90), (0.90, 1.01)]
"""Where the acts sit in the PICTURE, as fractions of its own duration.

Scaled to the duration handed in, never to the cue: the no-reuse rule (one
take, one shot) makes most trailers far shorter than their cue, and a 25 s
picture still has to open, turn and climax."""

ACT_BARS = (1.40, 0.80, 0.44, 0.44)
"""Nominal shot length per act, IN BARS.

Run 10's act medians were 2.46 / 2.42 / 1.67 s -- act 2 indistinguishable
from act 1, act 3 barely faster.  In bars against its 92.5 BPM cue that is
0.95 / 0.93 / 0.64.  These are the shape the corpus shows: an act 1 that
holds a bar and a half, an act 3 that cuts twice a bar.  Expressed in bars
so a 120 BPM test metre and a 92 BPM cue read the same shape; the absolute
seconds follow the tempo, as they must, because a shot's relation to the
music is what the viewer hears."""

FIGURE = (1.55, 0.40, 1.35, 0.52, 1.50, 0.46, 1.42, 0.34, 1.25)
"""One turn of the rhythmic figure, as multiples of the act's nominal.

Five longs and four stabs, alternating: hold, cut, hold, cut.  Two properties
carry the two rules the walk has to serve at once.

The longs OUTNUMBER the stabs, so the median of any stretch of an act is one
of the longs and the act median is the act's nominal -- with four of each the
median sits between a stab and a long, and one shot cut short by a hit moved
act 2's median from 2.5 s to 1.33 s.

The stabs are DEEP -- about 0.35 of a long.  A long-stab-long window measures
std/mean 0.35 only when the stab is under about 0.4 of the longs around it,
and every 12 s window has to clear 0.35.

Nine is odd against a four-beat bar, so the figure never lines up with the
music.  And there is no RNG here to seed: the figure is a pure function of
the shot index and the metre, so the same cue re-cut gives the same picture,
frame for frame."""

ACT_PHASE = (0, 0, 1, 0)
"""Where each act picks the figure up.

Acts 1 and 2 open on the figure's longest shot -- an act that opened on a
stab held more short shots than long ones and its median collapsed.  Act 3
opens on the stab instead: the climax begins by CUTTING, not by holding, and
a short act 3 (a 25 s picture affords three shots there) otherwise took its
median from two opening longs."""

ACT_CAPS = (2.0, 1.0, 1.0, 1.0)
"""How long a shot may run in each act, in BARS, where that beats `max_shot`.

`MAX_SHOT` (4 s) was put in to stop a 7.42 s shot at the CLIMAX, where the
corpus target is 0.54 s.  Act 1 is the opposite case: it is where a trailer
HOLDS, and a flat 4 s ceiling under a 92 BPM cue pins every opening shot to
the same 4.00 s -- the uniformity this module exists to prevent.  Two bars
is one musical statement; at 120 BPM it IS 4 s, so nothing moves there."""

CAP_CEILING = 6.0
"""No act ceiling passes this, whatever the tempo: the run-3 defect was a
static bearded man held for a quarter of the final third."""

FIGURE_SERVED = 0.75
"""A shot that got at least this much of what the figure asked has SERVED that
turn of the figure.  One cut short by an L0 event has not, and the figure
replays it -- otherwise a single hit flips the act's long/short balance and
with it the act median (measured: act 2 fell from 2.5 s to 1.33 s on one hit).

The figure also restarts at each act boundary, so every act OPENS on its
longest shot.  An act that happened to begin on a stab held more short shots
than long ones and its median fell to the longest of the shorts (measured on
a 25 s picture: act 2 median 1.0 s against an act-3 median of 1.0 s)."""

BEAT_LOCK = 0.66
"""From here -- act 3 -- the music owns every cut.

Before it, the music owns only the cuts it EARNS: phrase starts, stopdowns,
hits and the edges of the dialogue slots.  Run 10 put 76% of its cuts on the
beat from the first frame, and the editor's verdict was that the viewer
starts counting within four shots and the picture becomes wallpaper for the
audio.  The acceleration into the climax is worth nothing if the grid was
already showing."""

ANCHOR_REACH = 0.75
"""How near, in beats, an anchor has to be before acts 1-2 move a cut onto it."""

LEVEL_REACH = 0.60
"""How near, in beats, a higher-level grid point has to be to outrank a
closer one.  At 0.6 a beat always outranks a half-beat -- the furthest a
nominal can sit from a beat is half a beat -- so act 3 cuts on whole beats
and nothing else, which is what carries the >= 0.8 on-beat target there.
The variety act 3 still needs comes from the figure choosing DIFFERENT beat
COUNTS (3, 1, 2, 1, 3, 1, 2, 1, 2), not from landing off the pulse."""

EQUAL_FRAMES = 2
"""Two shots within this many frames of each other read as the same length."""

HOLD_MIN = 3.0
"""Editor's rule 8: the one hold runs at least this long.

Its own number, not `FINAL_HOLD`.  `FINAL_HOLD` sizes the TITLE CARD, and the
sound department moves it (3.0 -> 4.5 s while this was being written) for
reasons that belong to the card's decay tail, not to the picture."""


def max_shot(bar: float, fps: int = 24) -> float:
    """The cap: 4 s or a bar and a quarter, whichever is longer, in whole frames.

    A fixed 4 s cap at 60 BPM allows exactly one bar, so every long shot is
    a bar and the cut turns uniform; a bar and a quarter leaves room to vary.
    The constant `MAX_SHOT` remains the floor of the cap.
    """
    return -(-max(MAX_SHOT, 1.25 * bar) * fps // 1) / fps


def quantise_up(seconds: float, fps: int = 24) -> float:
    """A duration rounded UP to whole frames so a floor stays a floor."""
    return -(-seconds * fps // 1) / fps


def usable_events(events: list[float], duration: float, fps: int = 24) -> list[float]:
    """L0 events the walk can cut on: inside the span, a shot apart, on frames."""
    kept: list[float] = []
    for event in sorted(quantise(e, fps) for e in events):
        if event < MIN_SHOT - EPS or event > duration + EPS:
            continue
        if kept and event - kept[-1] < MIN_SHOT - EPS:
            continue
        kept.append(event)
    return kept


def with_hold(events: list[float], hold: tuple[float, float] | None) -> list[float]:
    """L0 events arranged around the hold: none inside it, none crowding its start.

    `usable_events` drops whatever falls less than a shot after the event
    before it, and what it dropped was the HOLD's own start -- the walk then
    sailed past it and the picture ended with no hold at all (measured: a
    44.96 s walk whose hold opened 0.42 s after the cue's second hit).  The
    hold outranks the events, so the events move.
    """
    if not hold:
        return events
    clear = [e for e in events if e < hold[0] - MIN_SHOT + EPS or e > hold[1] + EPS]
    return sorted(set(clear) | set(hold))


def grid_points(metre, fps: int = 24) -> list[tuple[float, int]]:
    """(time, level) for L1 downbeats, L2 beats and L3 half-beats, on frames."""
    downbeats = set(metre.downbeats)
    points = [(quantise(b, fps), 1 if b in downbeats else 2) for b in metre.beats]
    halves = [(quantise((a + b) / 2, fps), 3) for a, b in zip(metre.beats, metre.beats[1:])]
    return sorted(set(points + halves))


def anchor_points(metre, fps: int = 24) -> list[float]:
    """The only musical moments acts 1-2 will move a cut onto.

    Phrase starts, stopdowns, hits and the edges of the measured dialogue
    slots -- the places where landing on the music MEANS something.  Plain
    beats are not here, and that is the whole point.
    """
    slots = [edge for slot in metre.slots for edge in (slot.start, slot.end)]
    found = set(metre.phrase_starts) | set(metre.stopdowns) | set(metre.hits) | set(slots)
    return sorted(quantise(a, fps) for a in found)


def act_of(position: float) -> int:
    """Which act a fractional position falls in: 1, 2, 3, or 4 for the hold."""
    return next((i + 1 for i, (_, end) in enumerate(ACT_BANDS) if position < end),
                len(ACT_BANDS))


def act_nominal(position: float, bar: float, stretch: float) -> float:
    """The act's nominal shot length in seconds -- bars, scaled by the stretch."""
    return ACT_BARS[act_of(position) - 1] * bar * (stretch / LITERARY_STRETCH)


def act_cap(position: float, bar: float, fps: int = 24) -> float:
    """The longest shot this act may run: `max_shot`, or its own bars if longer."""
    wide = min(ACT_CAPS[act_of(position) - 1] * bar, CAP_CEILING)
    return quantise_up(max(max_shot(bar, fps), wide), fps)


def walk_length(position: float, bar: float, stretch: float, cap: float,
                step: int = 0) -> float:
    """The next shot: the act's nominal turned by the figure, inside floor and cap."""
    length = act_nominal(position, bar, stretch) * FIGURE[step % len(FIGURE)]
    return min(max(length, MIN_SHOT), cap)


def nearest_grid(nominal: float, ahead: list[tuple[float, int]], beat: float) -> float | None:
    """The highest-level grid point near the nominal cut, else the nearest."""
    close = [g for g in ahead if abs(g[0] - nominal) <= LEVEL_REACH * beat]
    if close:
        return min(close, key=lambda g: (g[1], abs(g[0] - nominal)))[0]
    return min(ahead, key=lambda g: abs(g[0] - nominal))[0] if ahead else None


def off_grid(when: float, beats: list[float], floor: float, ceiling: float,
             fps: int = 24) -> float:
    """A cut pushed deliberately clear of the pulse.

    This is what stops the counting: without it roughly one free cut in
    twelve lands on a beat by arithmetic accident, and every accident reads
    to the viewer as the grid still being there.
    """
    point = quantise(min(max(when, floor), ceiling), fps)
    near = min(beats, key=lambda b: abs(b - point)) if beats else None
    if near is None or abs(point - near) > OFF_BEAT - EPS:
        return point
    clear = [quantise(near + side * OFF_BEAT, fps) for side in (1, -1)]
    return next((c for c in clear if floor - EPS <= c <= ceiling + EPS), point)


def free_landing(nominal: float, floor: float, ceiling: float, anchors: list[float],
                 beats: list[float], reach: float, fps: int = 24) -> float:
    """Acts 1-2: an anchor when one is near, else a cut clear of the beat."""
    near = [a for a in anchors if floor - EPS <= a <= ceiling + EPS
            and abs(a - nominal) <= reach]
    if near:
        return min(near, key=lambda a: abs(a - nominal))
    return off_grid(nominal, beats, floor, ceiling, fps)


def respect_event(landed: float, event: float | None, ahead: list[tuple[float, int]],
                  ceiling: float, fps: int = 24) -> float:
    """No shot straddles an L0 event or leaves a flash frame in front of one."""
    if event is None:
        return landed
    if event <= ceiling + EPS:
        return event if landed >= event - MIN_SHOT - EPS else landed
    if event - landed < MIN_SHOT - EPS:
        before = [g for g, _ in ahead if g <= event - MIN_SHOT + EPS]
        return max(before) if before else quantise(event - MIN_SHOT, fps)
    return landed


def land(nominal: float, last: float, grid: list[tuple[float, int]], anchors: list[float],
         events: list[float], cap: float, beat: float, position: float,
         fps: int = 24) -> float:
    """Where the next cut goes: on the music in act 3, off it before."""
    floor, ceiling = last + MIN_SHOT, last + cap
    ahead = [g for g in grid if floor - EPS <= g[0] <= ceiling + EPS]
    event = next((e for e in events if e >= floor - EPS), None)
    if position >= BEAT_LOCK:
        landed = nearest_grid(nominal, ahead, beat)
    else:
        landed = free_landing(nominal, floor, ceiling, anchors,
                              [g for g, level in ahead if level <= 2],
                              ANCHOR_REACH * beat, fps)
    if landed is None:
        landed = quantise_up(min(max(nominal, floor), ceiling), fps)
    landed = respect_event(landed, event, ahead, ceiling, fps)
    return landed if landed >= floor - EPS else quantise_up(floor, fps)


def hold_length(cap: float, beat: float, duration: float) -> float:
    """How long the closing hold runs.

    Past the widest cap, so it reads as a hold rather than a long shot; never
    under `HOLD_MIN`; and never longer than the tail band, because the
    no-reuse rule makes 25 s pictures and a 4.5 s hold there would swallow
    half of act 3.
    """
    return min(max(HOLD_MIN, (1.0 - ACT_BANDS[-1][0]) * duration), cap + beat)


def hold_start(metre, end: float, want: float, fps: int = 24) -> float | None:
    """The beat the hold opens on.

    On the last stopdown before the title hit when the picture reaches the
    hit; otherwise `want` seconds back from the picture's own end.  A
    downbeat start is preferred when it does not cost more than one beat.
    """
    reach = metre.title_hit is not None and abs(metre.title_hit - end) <= want
    last_call = min(metre.title_hit, end) if reach else 0.0
    stop = [s for s in metre.stopdowns if reach and metre.title_hit - 6 <= s < last_call]
    limit = min(stop[-1], end - want) if stop else end - want
    beats = [quantise(b, fps) for b in metre.beats if b <= limit + EPS]
    downs = {quantise(d, fps) for d in metre.downbeats}
    return next((b for b in reversed(beats)
                 if b in downs and end - b <= want + metre.beat + EPS),
                beats[-1] if beats else None)


def hold_span(metre, duration: float, cap: float, fps: int = 24) -> tuple[float, float] | None:
    """(start, end) of the one shot allowed past the cap: the LAST one.

    Run 10 put its only hold at 15% of runtime -- `hold_at_breath`, which fired
    whenever the cue had no title moment, and by run 10 that was every cue.
    A hold there holds nothing: the viewer has been shown one image and has
    no reason to wait.  The hold now ends the picture, so the card follows it
    and the pause is the pause before the title.
    """
    end = quantise(duration, fps)
    want = hold_length(cap, metre.beat, duration)
    start = hold_start(metre, end, want, fps)
    if start is None or start < MIN_SHOT or end - start < HOLD_MIN - EPS:
        return None
    return start, end


def close(points: list[float], duration: float, fps: int = 24) -> list[float]:
    """End the cut ON `duration` -- never past it, no flash frame before it.

    The picture is exactly as long as the takes allow now, so a walk that
    overshot used to hand the assembler a shot with no clip behind it.
    """
    end = quantise(duration, fps)
    kept = [p for p in points if p <= end - MIN_SHOT + EPS] or points[:1]
    return kept + [end] if end - kept[-1] > EPS else kept


def plan_cuts(metre, events: list[float], duration: float,
              stretch: float = LITERARY_STRETCH, fps: int = 24) -> list[float]:
    """The beat walk: acts that shorten, a figure that cannot be counted, the
    music owning act 3 only, every L0 event honoured, one hold at the end.
    """
    beat, widest = metre.beat, act_cap(0.0, metre.bar, fps)
    hold = hold_span(metre, duration, widest, fps)
    l0 = with_hold(usable_events(events, duration, fps), hold)
    grid, anchors = grid_points(metre, fps), anchor_points(metre, fps)
    points, act, step = [0.0], 1, 0
    while points[-1] < duration - MIN_SHOT + EPS:
        if hold and points[-1] >= hold[0] - EPS:
            points.append(hold[1])
            continue
        position, last = points[-1] / max(duration, EPS), points[-1]
        step = ACT_PHASE[act_of(position) - 1] if act_of(position) != act else step
        act = act_of(position)
        cap = act_cap(position, metre.bar, fps)
        want = walk_length(position, metre.bar, stretch, cap, step)
        reached = max(position, (last + want) / max(duration, EPS))
        points.append(land(last + want, last, grid, anchors, l0, cap, beat, reached, fps))
        step += points[-1] - last >= FIGURE_SERVED * want
    return close(points, duration, fps)


# --- measuring the shape (what qc.py reads off the delivered picture) ------


def median(values: list[float]) -> float:
    """The middle value, the mean of the middle two when even, 0.0 for none."""
    if not values:
        return 0.0
    ordered = sorted(values)
    half = len(ordered) // 2
    return ordered[half] if len(ordered) % 2 else (ordered[half - 1] + ordered[half]) / 2


def act_lengths(points: list[float], act: int, duration: float,
                fps: int = 24) -> list[float]:
    """The lengths of the shots that START inside one act, hold excluded."""
    low, high = ACT_BANDS[act - 1]
    lengths = lengths_of(points, fps)[:-1]
    return [x for start, x in zip(points, lengths)
            if low - EPS <= start / max(duration, EPS) < high]


def act_medians(points: list[float], duration: float, fps: int = 24) -> list[float]:
    """Median shot length in acts 1, 2 and 3 -- editor's rule 5.

    The closing hold is left out: it is the button, not a cut length, and
    counting it would make the fastest act measure as the slowest.
    """
    return [median(act_lengths(points, act, duration, fps)) for act in (1, 2, 3)]


def longest_equal_run(points: list[float], fps: int = 24) -> int:
    """The most consecutive shots all within two frames of each other.

    Editor's rule 6.  Run 10 had runs of 8 and 9, and `is_uniform` -- max
    minus min over the WHOLE list -- passed them, because two long shots
    somewhere else in the trailer hid them.
    """
    longest, run = 0, []
    for length in lengths_of(points, fps):
        run.append(length)
        while max(run) - min(run) > EQUAL_FRAMES / fps + EPS:
            run.pop(0)
        longest = max(longest, len(run))
    return longest


def variation(values: list[float]) -> float:
    """Standard deviation over the mean; 0.0 when there is nothing to vary."""
    if len(values) < 2 or not sum(values):
        return 0.0
    mean = sum(values) / len(values)
    return (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5 / mean


def interval_variation(points: list[float], window: float = 12.0, fps: int = 24) -> float:
    """The LEAST std/mean of the cut intervals over any `window` of picture.

    Sound report rule G.  Measured over the whole cut this number lies: run
    10 read as varied and still held ten cuts of 1.21-1.25 s between 83 s
    and 94 s, which is the stretch a viewer actually sits through.
    """
    lengths = lengths_of(points, fps)
    if points[-1] - points[0] <= window:
        return variation(lengths)
    spans = [[x for start, x in zip(points, lengths) if s <= start < s + window]
             for s in points if s + window <= points[-1] + EPS]
    return min((variation(v) for v in spans if len(v) >= 3), default=variation(lengths))


def on_beat_fraction(points: list[float], grid: list[float], act: int | None = None,
                     duration: float | None = None, tolerance: float = ON_BEAT) -> float:
    """The share of one act's cuts that land on the musical grid.

    Editor's rule 7 and sound report rule G: whole-trailer `cuts_on_beat >=
    0.80` is the target that FORCED a music video.  Act 1 wants <= 0.5, act
    3 wants >= 0.8, and one number over the whole cut cannot say either.
    """
    span = duration if duration is not None else points[-1]
    low, high = ACT_BANDS[act - 1] if act else (0.0, 1.01)
    cuts = [c for c in points[1:-1] if low - EPS <= c / max(span, EPS) < high]
    if not cuts:
        return 0.0
    return sum(any(abs(c - g) <= tolerance for g in grid) for c in cuts) / len(cuts)
