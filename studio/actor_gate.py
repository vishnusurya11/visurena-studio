"""The man the words mean is the man in the frame.

OWNER 2026-09-13, watching episode 3: "sherlock was pointing ... when they
entered, white dude was saying something, it should have been lestrade not
sherlock."  He was right, and nothing in the repo could see it.  What the plan
said, verbatim:

    line 11  "A tall white-faced man met us and said nothing had been touched."
    shot 11  frame "a tall white-faced man in a dark coat"      faces []
    line 12  "Except that, HE said, pointing back at the trampled path."
    shot 12  motion "HOLMES raises one hand and points back out through the
             open door as he speaks the line"                   faces [holmes]

THE BRICK.  `tobias_gregson` was in the hall's cast list the entire time.  The
plan DESCRIBED him instead of CASTING him -- and an actor who is only described
is attached to nothing, so the pronoun in the next line was free to land on
whoever the picture happened to show.  Every identity guarantee in this repo
hangs off `faces`: the cast sheet staged as a reference, the mouth rule, the
lip-sync gate, `cast_agree`.  A man outside `faces` has none of them.

So the rule is not "check pronouns".  It is: AN ACTOR IS A CAST MEMBER.  A1
enforces that; A2 catches the consequence when it has already happened.

This is the same shape as `prop_refs.props_in`: a field that can silently
disagree with the prose is exactly the fault a gate exists to catch.  Free and
model-free -- it reads the plan's own strings and spends nothing.
"""
from __future__ import annotations

import re

PERSON = re.compile(
    r"\b(?:the|a|an|one)\s+(?:\w+[-\s]){0,3}"
    r"(man|woman|fellow|figure|detective|constable|officer|inspector|clerk|porter|driver|"
    r"barman|boy|girl|stranger|gentleman)\b", re.I)
"""An indefinite person: "the tall man", "a tall white-faced man", "one stalwart
police constable".  A proper name is deliberately NOT matched -- a named man is
already bound to the cast and is A1's whole remedy."""

ACTS = re.compile(
    r"\b(turns?|turned|raises?|raised|lifts?|lifted|points?|pointed|walks?|walked|steps?|stepped|"
    r"kneels?|knelt|reaches?|reached|holds?|held|opens?|opened|closes?|closed|looks?|looked|"
    r"nods?|nodded|speaks?|spoke|says?|said|moves?|moved|crosses?|crossed|bends?|bent|"
    r"draws?|drew|puts?|put|takes?|took|comes?|came|goes?|went|shakes?|shook)\b", re.I)
"""A verb a PERSON does.  The camera, the light and the fog also move, which is
why A1 asks whether an indefinite PERSON is the one doing it, not whether the
motion field contains a verb."""

SPEECH = re.compile(r"\b(said|says|told|asked|answered|replied|cried|called|"
                    r"pointing|pointed|gestur\w+|nodding|nodded|beckon\w+)\b", re.I)
"""The verbs that attribute an UTTERANCE OR A GESTURE to someone. "He walked the
pavement" attributes no such thing, and the cut is free to move under it."""

PRONOUN = re.compile(r"(?<![a-z])(he|she|they)\b", re.I)
NAMED = re.compile(r"\b([A-Z][a-z]+)\b")
STOP = {"A", "An", "The", "Except", "Then", "There", "It", "His", "Her", "Their",
        "Twice", "Once", "Well", "Number", "Rachel", "Rache", "Six", "German", "Miss"}
"""Sentence-initial and place words that look like names to a capital-letter
test. A line that truly names its subject carries a cast member's name."""


def acting_person(seg: dict) -> str:
    """The indefinite person this shot's MOTION gives an action to, or "".

    The mention is never the test -- the ACTION is.  Episode 3's shot 13 frames
    "a well-dressed man lying on his face" and moves only the light, and a
    corpse needs no casting."""
    motion = seg.get("motion") or ""
    for m in PERSON.finditer(motion):
        tail = motion[m.end():m.end() + 60]
        if ACTS.search(tail):
            return m.group(0)
    return ""


def a1_uncast_actor(shots: list[dict], cast: dict[str, list[str]]) -> list[str]:
    """A1: a shot whose motion gives an action to an indefinite person, with
    nobody cast in it, in a setup that HAS someone to cast."""
    out = []
    for seg in shots:
        if seg.get("faces"):
            continue
        available = [w for w in cast.get(seg.get("setup", ""), [])]
        if not available or not (who := acting_person(seg)):
            continue
        out.append(f"A1 UNCAST ACTOR shot {seg['index']}: {who!r} acts in the motion and `faces` is "
                   f"empty; the setup casts {', '.join(available)}. An actor outside `faces` gets no "
                   f"cast sheet, no mouth rule and no lip-sync gate, and the next line's pronoun is "
                   f"free to land on whoever the picture shows")
    return out


def names_its_subject(text: str) -> bool:
    """Does this line name a person, rather than leaning on a pronoun?"""
    return any(w not in STOP for w in NAMED.findall(text or ""))


def carries_a_pronoun_subject(line: dict) -> bool:
    """A narration line that attributes an utterance or a gesture to "he"."""
    text = line.get("text") or ""
    return (line.get("kind") == "narration" and bool(PRONOUN.search(text))
            and bool(SPEECH.search(text)) and not names_its_subject(text))


def a2_pronoun_keeps_its_man(shots: list[dict], lines: list[dict]) -> list[str]:
    """A2: consecutive narration lines, the second leaning on a bare pronoun,
    with the actor changing under them.  THE GATE REPORTS AN AMBIGUITY; IT DOES
    NOT SAY WHICH SIDE IS WRONG.

    That distinction cost an episode.  Read as "the picture must follow the
    pronoun", this rule sent me to recast shot 12 from Holmes to Gregson --
    and the SOURCE says the opposite (ch3 P34: '"Except that!" my friend
    answered, pointing at the pathway', and 'my friend' is Holmes, who names
    Gregson in the same breath).  English narration changes speaker across a
    reply all the time; a pronoun does NOT reliably keep its man.

    What the gate actually knows is that a reader cannot tell.  The remedy is
    almost always to NAME THE SUBJECT IN THE LINE -- "Except that, said Holmes"
    -- which fixes the voice-over for the viewer too, and silences this rule
    because the line now carries its own antecedent.  Moving the picture is the
    other remedy, and it is the one to reach for only when the source agrees."""
    where = {s.get("index"): s for s in shots}
    out = []
    for prev, line in zip(lines, lines[1:]):
        if line.get("index") != (prev.get("index") or 0) + 1:
            continue
        if not carries_a_pronoun_subject(line):
            continue
        was, now = where.get(prev.get("shot")), where.get(line.get("shot"))
        if not (was and now):
            continue
        # BOTH shots must cast somebody.  A faceless shot is an INSERT on a thing,
        # and a thing contradicts no pronoun: episode 3 cuts "then he threw me a
        # note" to an insert of the note, which is the cut working, not failing.
        # A1 is what guarantees a shot with an ACTOR in it is never faceless, so
        # between them nothing is missed and inserts stay quiet.
        if not (was.get("faces") and now.get("faces")):
            continue
        if set(was["faces"]) == set(now["faces"]):
            continue
        said = SPEECH.search(line["text"])
        out.append(f"A2 AMBIGUOUS PRONOUN shot {now['index']}: line {line['index']} "
                   f"(\"{PRONOUN.search(line['text']).group(0)} {said.group(0)}\") leans on a bare "
                   f"pronoun after line {prev['index']} introduced someone, and the picture changes "
                   f"from {was.get('faces')} to {now.get('faces')}. A reader cannot tell who acts. "
                   f"CHECK THE SOURCE, then either NAME THE SUBJECT IN THE LINE (usually right, and "
                   f"it helps the viewer too) or move the picture (only when the source agrees)")
    return out


WIDE_ENOUGH = {"medium", "full", "wide"}
"""The same ladder `episode_seq_board.places_the_plate` uses, for the reason
stated there: below it you are looking at a person, not at a place.  Kept as a
literal rather than imported so this gate stays a plain reader of the plan."""

BACKGROUND = re.compile(r"\b(blurred|out of focus|in the background|far behind|small and )\b", re.I)
"""How a panel says someone is BACKGROUND.  Episode 3's shot 10 wrote the defect
into its own prose -- "the constable stands small and blurred at the LEFT" -- so
taking the setup-level crowd block off the prompt changed nothing."""


def a3_background_person_in_a_close(shots: list[dict]) -> list[str]:
    """A3: a panel too tight to hold a place may not place a person in the
    background of its own prose.

    `crowd_clause` stops the SETUP's crowd reaching a close-up.  This stops the
    PANEL putting one there by hand, which is how the constable survived a
    $0.08 redraw that had already dropped the BACKGROUND LIFE block."""
    out = []
    for seg in shots:
        if seg.get("size") in WIDE_ENOUGH:
            continue
        for field in ("frame", "at_rest"):
            said = seg.get(field) or ""
            for m in PERSON.finditer(said):
                near = said[max(0, m.start() - 40):m.end() + 60]
                if BACKGROUND.search(near):
                    out.append(f"A3 BACKGROUND PERSON shot {seg['index']}: {field} puts {m.group(0)!r} "
                               f"in the background of a {seg.get('size')} panel, which has no room to "
                               f"hold a place; at that size a person can only be a smear at the edge")
                    break
            else:
                continue
            break
    return out


def check(shots: list[dict], lines: list[dict], cast: dict[str, list[str]]) -> list[str]:
    """Every actor fault in this plan, A1 first."""
    return (a1_uncast_actor(shots, cast) + a2_pronoun_keeps_its_man(shots, lines)
            + a3_background_person_in_a_close(shots))


def rows_of(episode) -> tuple[list[dict], list[dict], dict[str, list[str]]]:
    """An `Episode` flattened into the plain rows the three rules read.

    Sub-shots are included as their own rows -- A3's whole case is a sub-shot
    (episode 3's shot 10 is a panel, not a shot) -- and carry their parent's
    setup, which a `SubShot` does not have of its own."""
    shots, lines = [], []
    for shot in episode.shots:
        shots.append({"index": shot.index, "setup": shot.setup, "size": shot.size,
                      "faces": list(shot.faces), "frame": shot.frame, "motion": shot.motion,
                      "at_rest": shot.at_rest})
        for k, cut in enumerate(shot.cuts):
            shots.append({"index": f"{shot.index}.{k}", "setup": shot.setup, "size": cut.size,
                          "faces": list(cut.faces), "frame": cut.frame, "motion": cut.motion,
                          "at_rest": cut.at_rest})
    for line in episode.lines:
        lines.append({"index": line.index, "kind": line.kind, "speaker": line.speaker,
                      "text": line.text, "shot": line.shot})
    cast = {name: list(setup.cast) for name, setup in episode.setups.items()}
    return shots, lines, cast


def check_episode(episode) -> list[str]:
    """Every actor fault in a loaded plan.  Free, and the last moment before the
    first paid sheet -- a wrong actor drawn into a sheet is paid for twice, once
    to draw it and once to draw it again."""
    return check(*rows_of(episode))


def hard(shots: list[dict], cast: dict[str, list[str]]) -> list[str]:
    """The faults that BLOCK a run: A1 and A3.

    Both are unambiguous -- an actor with no cast entry has no reference and no
    lip gate, and a person in the background of a close-up cannot be drawn at
    that size.  Neither needs a judgment call to resolve."""
    return a1_uncast_actor(shots, cast) + a3_background_person_in_a_close(shots)


def advisory(shots: list[dict], lines: list[dict]) -> list[str]:
    """A2, which REPORTS and does not rule.

    Kept out of the blocking set deliberately.  A2 cannot know whether the line
    or the picture is wrong -- only the source can say -- and when it was read
    as a verdict it produced the wrong answer on the one case it was written
    for.  A rule that needs a human to resolve it must not stop a run."""
    return a2_pronoun_keeps_its_man(shots, lines)


def hard_episode(episode) -> list[str]:
    shots, _, cast = rows_of(episode)
    return hard(shots, cast)


def advisory_episode(episode) -> list[str]:
    shots, lines, _ = rows_of(episode)
    return advisory(shots, lines)
