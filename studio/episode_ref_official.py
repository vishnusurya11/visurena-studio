"""The take prompt in MiniMax's own reference-to-video grammar.

Source: MiniMax-AI/MiniMax-H3, `docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md` and
`..._base_en.md` (fetched 2026-09-11).  Six sections in order.  A cast sheet is
cited INSIDE its subject line; the location plate is a subject and a DEFINITION,
never a framing; every pinned cell is its own `<Picture N>` first frame; the
take's storyboard strip is a `weak_reference` that carries shot order alone.

Spec: `docs/calibration/ref2v_prompt_spec.md`, approved 2026-09-11.

Where the guide and the owner disagree the OWNER's form is kept and the guide's
rule is named in a comment beside it, so the A/B can flip one line:

  OWNER 5.13  `[Shot 1]` carries a time range (ref-en §5.1 gives it none), every
              range touches the next, and the last ends on the CEILING of the
              latent, so no second of the video is unnamed.
  OWNER 5.14  whole-second stamps (the format is MM:SS.mmm).  Worst measured
              text-vs-pin gap on ep01 is 0.208 s; L7 caps it at 0.5 s.
  OWNER 5.15  narration is never `says in an off-screen voiceover` (base-en
              §4.4): it is not in `<Audio 1>` at all, so the take states the
              closed mouth positively and binds it to an action.
  OWNER 5.16  the plate reads `(the location behind [Shot 1] ...)`, not ref-en
              §4.1's `(appears in ...)`; `appears in` is the phrasing that
              measurably invited the plate in as a cutaway (0.88-0.996).
  OWNER 5.17  a 3-shot take runs past the guide's 500-word ceiling; the gate is
              per shot block (L14, 150-240 words) so length comes from shots.
  OWNER 5.18  every segment carries a body-scale action (the guide is silent):
              51 % of iteration 4's segment time was frozen.

The block is written from the panel's OWN prose: `Framed.camera` says where the
camera stands, `Framed.at_rest` what is at rest in the first frame, `Framed.crowd`
(else `Setup.crowd`) the life behind it, and `Framed.end` the last frame.  All of
it is authored for a DRAWER, so it reaches the prompt through `calm()` -- the
stillness vocabulary said as position -- and only as much of it as the block is
short of the owner's 150-240 word band (`budget`).
"""
from __future__ import annotations

import math
from studio import house_style
import re

from studio.episode_spec import BANNED_PROPS, Line, Setup, Shot

def style_line(setup=None) -> str:
    """The style line for this run, from `studio.house_style`, under the
    SETUP's own light when one is given.

    This was a constant reading "1881 London". Episode 8 was drawn and
    rendered under it over an 1847 Utah desert, because `Episode.palette`
    was wired into the location plate alone and the fix was called done --
    13 of 13 sheet prompts and 28 of 28 take prompts carried the wrong
    place. The place is declared once per run now, in one module.

    MEASURED, episode 10: the one episode light ("low side sun, deep black
    shadow") reached 30/30 take blocks including the moon, lamp and candle
    setups (dq10/J.md §4).  `house_style.light_for` reads the setup's own
    source clause; the episode light is its fallback.
    """
    return house_style.live(setup)
LEAD = "Watson"
"""The one character the limp rule watches (owner: Watson limps on his stick)."""
MAX_PICTURES = 9
"""`MiniMaxH3ReferenceToVideo.ref_images` is an Autogrow with min=0, max=9."""


def name_of(who: str) -> str:
    return who.replace("_", " ").title()


def surname(who: str) -> str:
    return who.split("_")[-1].title()


def stamp(seconds: float) -> str:
    """MM:SS, whole seconds (OWNER 5.14).  The pin is what cuts; the text is
    guidance, and MiniMax's own examples read whole seconds."""
    m, s = divmod(round(max(seconds, 0.0)), 60)
    return f"{int(m):02d}:{int(s):02d}"


def span(start: float, end: float) -> str:
    """A shot, a sub-shot and a line are all stated as a range: what to sustain for
    that long.  Every caller passes bounds ALREADY CLIPPED to the segment -- a span
    never leaves its own segment (3.2).  A range that rounds flat still spans one
    second."""
    a, b = round(max(start, 0.0)), round(max(end, 0.0))
    return f"From {stamp(a)} to {stamp(max(b, a + 1))}"


def during(start: float, end: float) -> str:
    """The same range mid-sentence: `..., from 00:00 to 00:03.`"""
    return "f" + span(start, end)[1:]


def take_end(frames: int, fps: int = 24) -> int:
    """The second the last range ends on: the CEILING of the latent, so no second of
    the video is unnamed (OWNER 5.13).  The exact length is stated once, in `summary`."""
    return math.ceil(frames / fps)


def stated_end(frames: int, fps: int = 24) -> int:
    """The last second the video ACTUALLY REACHES, floored.

    `take_end` ceils, and that ceiling is announced to the model as the take's
    last second: a 294-frame take (12.25 s) was described as running to 00:13.
    MEASURED, 16 of 22 episode 3 prompts named up to 0.75 s of time the latent
    does not contain, and the model laid its shots across the longer timeline --
    every one of them arriving early.  Coverage (L5) still uses the ceiling so no
    second goes unnamed; what the model is TOLD is the truth."""
    return max(1, int(frames / fps))


def beats(t0: int, t1: int, n: int) -> list[int]:
    """`n` whole seconds evenly spread strictly inside `(t0, t1)`, strictly ascending.
    When the range holds fewer seconds than clauses the list is short and the surplus
    clauses share the last stamp (3.4)."""
    out: list[int] = []
    for k in range(n):
        want = round(t0 + (t1 - t0) * (k + 1) / (n + 1))
        want = max(want, out[-1] + 1 if out else t0 + 1)
        if want >= t1:
            break
        out.append(want)
    return out


def shot_list(numbers) -> str:
    """`[Shot 1], [Shot 2] and [Shot 3]` -- the guide's own join (ref-en §2.2)."""
    names = [f"[Shot {k}]" for k in numbers]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + f" and {names[-1]}"


# ---- the drawer's prose, read by a camera -----------------------------------

CALM = ((r"\bstays\b", "is"), (r"\bstay\b", "are"), (r"\bremains\b", "is"), (r"\bremain\b", "are"),
        (r"\bholds\b", "keeps"), (r"\bhold\b", "keep"), (r"\bheld\b", ""), (r"\bwaits\b", "stands"),
        (r"\bwait\b", "stand"), (r"\bpauses\b", "settles"), (r"\bpause\b", "settle"),
        (r"\b(still|motionless|unmoving|frozen|unchanged)\b", ""))
"""Every stillness word, rewritten as the POSITION it describes.  The plan's
prose is written for a storyboard artist drawing one frame, so it says `held`,
`stays` and `waits`; measured, a segment carrying two or more stillness words
rendered 0.77 frozen against 0.47 (L2).  The picture is the same, the verb is
one a camera can roll on."""


def calm(text: str) -> str:
    """The drawer's still-frame vocabulary, said as position instead of arrest."""
    for pattern, word in CALM:
        text = re.sub(pattern, word, text, flags=re.I)
    return " ".join(text.split())


def trim(text: str, cap: int) -> str:
    """The first whole clauses of a plan field that fit in `cap` words; a field is
    authored long (`at_rest` runs to 382 words) and a block has a ceiling."""
    out: list[str] = []
    for part in re.split(r"(?<=[;,])\s+", " ".join(text.split())):
        if out and len(" ".join(out + [part]).split()) > cap:
            break
        out.append(part)
    return " ".join(out).strip().rstrip(";,.").rstrip()


# ---- the frame text --------------------------------------------------------

OPENERS = (("Close on ", "a close shot of "), ("Close ", "a close shot "),
           ("Extreme close-up ", "an extreme close-up "),
           ("Medium close-up ", "a medium close-up "), ("Medium close ", "a medium close shot "),
           ("Medium two-shot ", "a medium two-shot "), ("Medium three-shot ", "a medium three-shot "),
           ("Medium shot ", "a medium shot "), ("Medium ", "a medium shot "),
           ("Full three-shot ", "a full three-shot "), ("Full two-shot ", "a full two-shot "),
           ("Full shot ", "a full shot "), ("Full ", "a full shot "),
           ("Insert ", "an insert "), ("Wide ", "a wide "))


def names_of(cast) -> tuple[str, ...]:
    """Every word of every cast name: `lucy_ferrier` -> Lucy, Ferrier.  The plan
    names people by first name as often as by surname."""
    return tuple(sorted({w for who in cast for w in name_of(who).split()}))


def is_name(word: str, names) -> bool:
    return word.strip(",.;:").removesuffix("'s") in names


def noun_phrase(frame: str, names=()) -> str:
    """The plan writes a frame as a shot-size heading; ref-en §5.3 reads `the shot
    begins from <Picture 1>: ...`, which needs a noun phrase after the colon.

    A proper name keeps its capital: episode 9 closed 12 of 29 blocks on
    "By 00:07, ferrier's head..." because the first character was lowered blind."""
    text = calm(frame).rstrip(".")
    for head, phrase in OPENERS:
        if text.startswith(head):
            return phrase + text[len(head):]
    if not text or is_name(text.split()[0], names):
        return text
    return text[0].lower() + text[1:]


def split_frame(phrase: str) -> tuple[str, str]:
    """The framing and what it holds; `<Picture N>` sits between them (D2b)."""
    for mark in (": ", ", "):
        if mark in phrase:
            head, rest = phrase.split(mark, 1)
            return head, rest
    return phrase, ""


def tagged(text: str, faces: list[str]) -> str:
    """People become their `<Subject k>` labels; a person with no sheet staged keeps
    his name -- ref-en §2 lets only a DEFINED label be cited."""
    for k, who in enumerate(faces, start=1):
        for word in (name_of(who), surname(who)):
            text = re.sub(rf"\b{re.escape(word)}\b", f"<Subject {k}>", text)
    return text


def people_in(text: str, cast) -> list[str]:
    """Whoever a frame text names, in the order the cast gives."""
    return [w for w in cast if re.search(rf"\b{re.escape(surname(w))}\b", text)]


INDOORS = ("room", "bar", "laboratory", "corridor", "chamber", "cab", "interior", "hall", "ward")
INDOOR_WORDS = re.compile(r"\b(" + "|".join(INDOORS) + r")\b", re.I)


def place_word(described: str, outdoors: bool = False) -> str:
    """Whole words only: `bar` matched inside `Bartholomew` and called a street a room.

    A setup that stands under the sky (`Setup.outdoors`) is a PLACE whatever nouns
    its description carries: episode 9's farm was "this room" because its log house
    had "grown room by room"."""
    if outdoors:
        return "place"
    return "room" if INDOOR_WORDS.search(described) else "place"


LABEL = ("interior", "exterior")
"""A stage direction the drawer needs, and not what the place is called.
MEASURED on ep13's and ep14's prompts (2026-09-17): every interior setup opens
"Interior, inside ...", so the model was told the take happens "in <Subject 2>,
Interior" and that "the ambience of Interior runs under the whole take"."""


def short_place(described: str) -> str:
    """The location's own name: the described text up to its first comma, past
    any Interior/Exterior label."""
    parts = [p.strip() for p in (described or "").split(",")]
    head = next((p for p in parts if p and p.lower() not in LABEL), parts[0] if parts else "")
    head = head.rstrip(".")
    return re.sub(r"^(The|A|An)\b", lambda m: m.group(0).lower(), head)


def subject_of(who: str, faces: list[str]) -> str:
    """The `<Subject k>` label of a staged face, and NOTHING for anyone else.  It
    used to fall back to the bare name, which is how episode 9 wrote "John
    Ferrier's mouth is closed" into four blocks whose `faces` were empty."""
    return f"<Subject {faces.index(who) + 1}>" if who in faces else ""


def lead_tag(faces: list[str]) -> str:
    """How the limp rule (L9) and the block guarantee both name the lead: his
    `<Subject k>` where his sheet is staged, his own name where it is not."""
    return subject_of("john_watson", faces) or name_of("john_watson")


# ---- 1.1  subject_definitions ----------------------------------------------

def picture_numbers(n_faces: int, n_segs: int, ends: list[int],
                    has_plate: bool = True) -> tuple[int | None, dict, dict, int]:
    """Every reference's picture slot, in `graph_for`'s staging order: cast sheets,
    plate, pinned cells in first-pin order, END cells (1.1).  The fourth value is
    the slot AFTER the last picture, kept so callers that took a strip number still
    work; nothing is staged there now.

    `has_plate=False` closes the gap rather than leaving the slot empty: a take
    of nothing but close and insert cells stages no plate (it has no wide frame
    to place one against, and the plate then becomes the only whole picture the
    model can fall back on -- 13 of episode 2's 14 foreign frames were exactly
    that).  A skipped slot would make the prompt cite a picture the graph never
    staged, which is what L11 refuses."""
    plate = n_faces + 1 if has_plate else None
    first = (plate + 1) if has_plate else n_faces + 1
    cells = {i: first + i for i in range(n_segs)}
    last = {k: first + n_segs + j for j, k in enumerate(ends)}
    return plate, cells, last, first + n_segs + len(ends)


def last_frame_text(seg: dict) -> str:
    """S5: where the body has arrived.  The plan's own `Framed.end` picture when it has
    one, else the action of that shot completed."""
    return noun_phrase(seg["end_frame"]) if seg.get("end_frame") else "with the action of that shot completed"


GERUND = {"tracks": "tracking", "pushes": "pushing", "pulls": "pulling", "dollies": "dollying",
          "zooms": "zooming", "pans": "panning", "tilts": "tilting", "cranes": "craning",
          "orbits": "orbiting", "moves": "moving", "holds": "holding"}
"""Every value `CAMERA` can produce, spelled out.

English is not regular enough to derive these: `pushes` needs -es off (not -s,
which leaves `pushe`), `pans` doubles its n, `dollies` and `moves` change stem.
`CAMERA` is a CLOSED vocabulary of ten verbs, so the table is shorter and more
honest than the rules would be."""


def gerund(verb_phrase: str) -> str:
    """`pushes in a hand's breadth` -> `pushing in a hand's breadth`.

    The camera vocabulary is a closed set (`CAMERA`), so this needs no grammar
    engine: drop the third-person -s and add -ing, with four irregular stems
    named above."""
    if not verb_phrase.strip():
        return ""
    head, _, rest = verb_phrase.strip().partition(" ")
    stem = GERUND.get(head.lower()) or (head.lower().rstrip("s") + "ing")
    return f"{stem} {rest}".strip()


LAYOUT = re.compile(r"\b(edges?|corners?|twice|taller|smaller|larger|half again|left half|right half|"
                    r"reduced|inside the frame|in the frame|fills? the|filling the|from edge to edge)\b", re.I)
"""What marks a sentence as a FRAME LAYOUT -- nouns at edges and sizes -- rather
than a movement.  `Framed.end` is written for the drawer as exactly that ("the
log house stands twice its size along the left edge"), and episode 9 closed 29
of 30 blocks on one: a still composition as the shot's destination, where ep06
and ep07 ended with the camera moving through the last frame."""

LEFT_FRAME = re.compile(r"\b(?:ha(?:s|ve) left|leaves?|gone|out of frame|carried out)\b", re.I)
NP_END = re.compile(r"\b(stands?|fills?|filling|has|have|is|are|sits?|lies?|rests?|holds?|at|in|on|along|"
                    r"with|over|under|from|to|by|inside)\b", re.I)
CLAUSE = re.compile(r",|\band (?=(?:the|a|an|both|his|her|their|its|two|three|four|five|six)\b|[A-Z])")
"""Where a layout's clauses part: a comma, or an `and` that opens a new subject --
"head and shoulders" is one subject, "and the wheat reduced" is the next."""


def is_layout(end: str) -> bool:
    return bool(LAYOUT.search(end))


def end_noun(end: str, names=()) -> str:
    """The one noun a layout lends the arrival: the subject of its first clause
    that has COME INTO frame (a clause that says something has left lends nothing),
    its size opener off, cut before its first verb or preposition and, past five
    words, at its first `of`."""
    text = end.rstrip(".")
    text = next((text[len(h):] for h, _ in OPENERS if text.startswith(h)), text)
    for clause in CLAUSE.split(text):
        if not clause.strip() or LEFT_FRAME.search(clause):
            continue
        head = NP_END.split(clause.strip(), maxsplit=1)[0].strip()
        if len(head.split()) > 5 and " of " in head:
            head = head.split(" of ")[0]
        return noun_phrase(head, names) if head else ""
    return ""


def arrival_end(end: str, names=()) -> tuple[str, str]:
    """What a written `end` lends the arrival: a layout lends one noun now in
    frame; anything else trails the camera as its own clause."""
    if not end:
        return "", ""
    if is_layout(end):
        noun = end_noun(end, names)
        return (f", with {noun} now in frame" if noun else ""), ""
    return "", f", and {lower_lead(noun_phrase(end, names))}"


def arrival_clause(seg: dict, names=()) -> str:
    """Where the shot ARRIVES, said in words instead of shown as a picture: the
    CAMERA arriving, never a static layout.

    A written `end` is the drawer's last-frame LAYOUT, and episode 9 pasted it in
    as the block's closing motion sentence -- "By 00:05, the log house stands
    twice its size along the left edge" -- a still composition as the destination,
    on 29 of 30 blocks (L21).  Now the camera's own move is the arrival in every
    case; a layout lends one noun as what is now in frame, and a written end that
    is not a layout ("the door stands open") trails the camera as its own clause.

    `last_frame_text` says the same thing, but it lives in `subject_definitions`
    bolted to a `<Picture N>`.  MEASURED on episodes 2 and 3: that picture is
    declared at the same second as the NEXT shot's first frame in 5 of 7 takes,
    both `fully_preserved`, and it is never anchored in the graph -- so the model
    is handed an unpinned whole-frame composition it may cut to at will, and
    twice it did, finishing the take there.

    Said as a clause in the shot's own block it costs no reference slot, cites no
    picture, and cannot be mistaken for a second shot.

    WITH NO WRITTEN `end`, THE CAMERA SAYS IT.  Episode 3 carries a written `end`
    on 0 of its 37 segments, so `last_frame_text`'s fallback -- "with the action
    of that shot completed" -- would have been the arrival for every one of them,
    and it names nothing a model can aim at.  The motion's own camera half does:
    the shot arrives where the move ends."""
    held, tail = arrival_end(seg.get("end_frame") or "", names)
    cam, _subject = camera_clause(clauses_of(seg.get("motion", ""))[0])
    move = move_verb(cam) if cam else ""
    if move:
        # Two gates shaped this sentence and both were right: `holds` is on the L2
        # stillness list (a stillness verb in a block measured 0.77 frozen against
        # 0.47), and "goes no further" is a NEGATION, which MiniMax cannot read.
        #
        # IT USED TO END `with the action of that shot completed`, and that is the
        # LAST thing the block says about motion -- on 18 of episode 5's 25 takes.
        # `frozen-share` is measured over exactly the tail it describes, and it is
        # 67.2 of that episode's 92.2 lost points.  Nothing above argued for
        # `completed`; it arrived with the no-`end` fallback and was never the
        # point.  The two constraints stand and rule out the obvious repair -- "is
        # still pushing in" puts `still` in an L2-linted sentence.  `continues ...
        # through the last frame` is what the timed beats already say.
        #
        # AND THE MOVE IS NAMED ONCE.  MEASURED, episode 10 (dq10/J.md §5-6): the
        # arrival repeated the whole camera head -- "pushing in on <Subject 1>'s
        # face across the whole shot, travelling a hand's breadth" -- 11.6 words a
        # block verbatim, "across the whole shot" twice in 34/34 blocks, and the
        # amount word a second time where the model scales by it 0/16.  The 16
        # blocks that overran the ceiling overran on this duplicate, not content.
        # So the arrival carries the verb and its particle and nothing else of
        # the head; the timed beats and the camera sentence already say the rest.
        return (f"By {stamp(seg['end'])} the camera is {move} through the last frame{held}, "
                f"and the action continues with it{tail}.")
    return (f"By {stamp(seg['end'])} the action of that shot continues "
            f"through the last frame{held}{tail}.")


PARTICLES = ("in", "out", "back", "up", "down", "left", "right", "off", "away", "forward", "handheld")
"""What may follow the verb into the arrival: the particle that says which
way.  `on <Subject 1>'s face`, `a hand's breadth`, `along the counter` stay
with the camera sentence."""


def move_verb(cam: str) -> str:
    """`pushes in on his face across the whole shot, travelling a hand's breadth`
    -> `pushing in`: the verb and its particle, the ONE thing the arrival may
    repeat of the camera head."""
    words = camera_verb(cam).split()
    if not words:
        return ""
    keep = words[:2] if len(words) > 1 and words[1].lower().strip(",.;") in PARTICLES else words[:1]
    return gerund(" ".join(keep))


def audio_line(spoken) -> str:
    """S7 / S7'.  OWNER 5.15: on a narration take the file really is silence, and
    claiming speech that is not in it is what made the face on screen mouth the
    narrator's words."""
    if not spoken:
        return "<Audio 1> is the take's complete audio track and runs silent for its whole length."
    when = (f"the one line spoken on camera at {stamp(spoken[0][1])}" if len(spoken) == 1
            else f"the {len(spoken)} lines spoken on camera at their own times")
    return f"<Audio 1> is the take's complete audio track: {when}, over silence for the rest of its length."


def subjects(faces: list[str], physical: dict[str, str], described: str, segs: list[dict],
             ends: list[int] | None = None, spoken=None,
             has_plate: bool = True, outdoors: bool = False) -> tuple[str, dict[int, int], int]:
    """subject_definitions; returns the text, `{segment -> its first-frame picture}`
    and the strip's picture number."""
    ends, names = ends or [], names_of(list(physical) or faces)
    plate, cells, last, strip = picture_numbers(len(faces), len(segs), ends, has_plate)
    # A CAST SHEET DEFINES A MAN; IT IS NOT A FRAMING.  Measured on episode 3 T02:
    # the take held a full-length studio portrait AND the storyboard cell of the
    # same man, both `fully_preserved`, and at 4.0 s the render put a full-length
    # figure with a cane in the middle of the sitting-room -- the cast card's pose
    # and framing, re-rendered into the room (matching no reference pixel-wise,
    # best 0.118).  This is OWNER 5.16's plate fix, owed to people all along.
    out = [f"<Subject {k}> is {name_of(who)} in <Picture {k}>: {physical.get(who, '')} "
           f"<Picture {k}> defines this man alone; each shot keeps the framing of its own "
           f"first-frame picture.".rstrip()
           for k, who in enumerate(faces, start=1)]
    if plate is not None:
        out.append(f"<Subject {plate}> is the location in <Picture {plate}>: {described} <Picture {plate}> "
                   f"defines this {place_word(described, outdoors)} alone; each shot keeps the framing of "
                   f"its own first-frame picture.")
    for i, seg in enumerate(segs):
        out.append(f"<Picture {cells[i]}> is the first frame of [Shot {i + 1}], "
                   f"{split_frame(tagged(noun_phrase(seg['frame'], names), faces))[0]}.")
    out += [f"<Picture {last[k]}> is the last frame of [Shot {k}], {last_frame_text(segs[k - 1])}."
            for k in ends]
    # OWNER 2026-09-11: the strip is gone.  Its only unique content was shot order,
    # and every cell above already names its own shot in order, at full resolution.
    out.append(audio_line(spoken or []))
    return "\n".join(out), cells, strip


# ---- 1.3  retention_analysis -----------------------------------------------

def retention(faces: list[str], segs: list[dict], cells: dict, strip: int, ends: list[int],
              described: str, has_plate: bool = True, outdoors: bool = False) -> str:
    """R1-R7.  The plate is `partially_preserved` and never `appears in` a shot
    (OWNER 5.16).  Every pinned cell is `fully_preserved` as its shot's first frame;
    there is no strip to mark `weak_reference` any more."""
    plate, cells, last, strip = picture_numbers(len(faces), len(segs), ends, has_plate)
    every = list(range(1, len(segs) + 1))
    out = []
    for k, who in enumerate(faces, start=1):
        seen = [i for i, seg in enumerate(segs, start=1) if people_in(seg["frame"], [who])] or [1]
        out.append(f"<Subject {k}> (the man in {shot_list(seen)}): partially_preserved - the face, hair, "
                   f"build and clothes of <Picture {k}> carry into every shot that shows him; "
                   f"<Picture {k}> serves as a definition of the man and each shot keeps the framing "
                   f"of its own first-frame picture.")
    if plate is not None:
        out.append(f"<Subject {plate}> (the location behind {shot_list(every)}): partially_preserved - the "
                   f"materials, furniture and light of <Picture {plate}> carry into every shot behind the "
                   f"people; <Picture {plate}> serves as a definition of the "
                   f"{place_word(described, outdoors)} and each shot keeps the framing of its own "
                   f"first-frame picture.")
    # NOT `viewpoint`: 22 of 22 prompts asked for a preserved viewpoint in a block
    # whose own camera sentence pushes the camera THROUGH it.  Told to hold the
    # viewpoint and to change it, the render held -- episode 3 T02's Holmes sits at
    # similarity 1.000 to his cell with 0.12 frame-to-frame change, the still
    # reproduced and frozen.  The camera sentence owns the viewpoint now.
    out += [f"<Picture {cells[i]}> ([Shot {i + 1}] first frame): fully_preserved - subject "
            f"placement, wardrobe and light." for i in range(len(segs))]
    out += [f"<Picture {last[k]}> ([Shot {k}] last frame): fully_preserved - the same viewpoint with the "
            f"action completed." for k in ends]
    # OWNER 2026-09-11: no strip line either.  Citing a picture the graph no longer stages
    # is what L11 PICTURES exists to catch, and it caught this.
    out.append("<Audio 1>: fully_copy - <Audio 1> is reused 1:1 as the take's complete final audio track.")
    return "\n".join(out)


# ---- 1.4  the voices -------------------------------------------------------

def voice_id(lines: list[Line], narrator: str) -> dict[str, str]:
    """(Sx) in order of first spoken line; only dialogue is in the take's audio."""
    order: list[str] = []
    for line in sorted(lines, key=lambda l: l.index):
        if line.kind == "dialogue" and line.speaker not in order:
            order.append(line.speaker)
    return {who: f"S{k}" for k, who in enumerate(order, start=1)}


def voice_of(physical: str) -> str:
    """The speaker's identity clause (base-en §4.4 wants character type, age,
    on-screen, pace).  A `voice` field on the cast sheet would override this."""
    first = (physical.split(",")[0].strip().rstrip(".") or "a person")
    return f"{first[0].lower() + first[1:]}, with a clipped English voice at an even pace"


def speaker_intro(who: str, sid: str, physical: str, seen, faces: list[str]) -> str:
    """D8.  The identity comes once, at the speaker's first vocal event (ref-en §5.3
    forbids re-describing him afterwards).  A speaker with no sheet staged keeps
    his name: a voice needs a body to be attributed to."""
    tag = subject_of(who, faces) or name_of(who)
    if who in seen:
        return f"{tag} ({sid}) says:"
    return f"{tag} ({sid}), on screen, {voice_of(physical)}, says:"


def voice_events(shot_lines: list[Line], at: dict, offset: float, ids: dict, faces: list[str],
                 physical: dict, mouth: str, action: str, t0: int, t1: int, seen) -> str:
    """D7 / D8 / D9.  A narration line states a CLOSED MOUTH bound to an action, with
    its range clipped to this segment; an insert (`mouth` empty) states nothing at all
    (review7 #1: a hand insert has no corresponding character)."""
    out = []
    for line in shot_lines:
        a, dur = at[line.index]
        a -= offset
        if line.kind == "narration":
            if mouth:
                out.append(f"{mouth}'s mouth is closed {during(max(a, t0), min(a + dur, t1))} "
                           f"while {action}.")
            continue
        out.append(f"{speaker_intro(line.speaker, ids[line.speaker], physical.get(line.speaker, ''), seen, faces)} "
                   f"<d>[English] {line.text}</d> His mouth shapes every syllable as the line is heard "
                   f"and closes on the last word.")
        seen.add(line.speaker)
    return " ".join(out)


# ---- 1.4  the camera and the beats -----------------------------------------

MOVES = ("push", "dolly", "pull", "zoom", "track", "handheld", "pan", "tilt", "crane", "orbit")
CAMERA = {"tracking": "tracks", "track": "tracks", "push": "pushes", "pushing": "pushes",
          "pull": "pulls", "pulling": "pulls", "dolly": "dollies", "dollying": "dollies",
          "zoom": "zooms", "zooming": "zooms", "pan": "pans", "panning": "pans",
          "tilt": "tilts", "tilting": "tilts", "handheld": "moves handheld", "crane": "cranes",
          "craning": "cranes", "orbit": "orbits", "orbiting": "orbits"}


TIMED = re.compile(r"\b(over|by|at|for|within|during|after)\s+(the\s+)?(first\s+|last\s+|next\s+)?"
                   r"[\d.]+(\s*-\s*[\d.]+)?\s*seconds?\b", re.I)
MOUTH_NOTE = re.compile(r"^[^;]*\b(lips?|mouths?)\b[^;]*\b(closed|together)\b[^;]*$", re.I)


def untimed(clause: str) -> str:
    """The clause without the author's own seconds.  The BUILDER owns the clock now
    (D1/D4, owner: whole-second stamps that cover the take), so `At 00:06 by 3.5
    seconds the knob stands alone` states two different times for one beat."""
    out = " ".join(TIMED.sub(" ", clause).split()).strip(" ,")
    out = re.sub(r"^(then|and|so|but)\s+", "", out, flags=re.I)   # the stamp is the sequence now
    return re.sub(r"\s+([.,;])", r"\1", out)      # `the arch , and` is the removed phrase's gap


def clauses_of(motion: str) -> tuple[str, list[str]]:
    """A plan motion is `head; action; action; ...`.  A clause that only says a mouth
    is closed is dropped: D7 and D9 state the mouth ONCE, bound to an action, and a
    second stillness sentence is what measured 0.77 frozen."""
    parts = [untimed(calm(c)).rstrip(".") for c in motion.split(";") if c.strip()]
    parts = [c for c in parts if c and not MOUTH_NOTE.match(c)] or parts[:1]
    return (parts[0] if parts else ""), parts[1:]


def camera_verb(head: str) -> str:
    """base-en §4.3: the move is a natural English action inside the shot, never a
    stacked label, and medium amplitude and normal speed are left unsaid."""
    words = head.split()
    return " ".join([CAMERA.get(words[0].lower(), words[0].lower())] + words[1:]) if words else ""


CAMERA_LEAD = re.compile(r"\b(?:as|while|and)\s+(?=the camera\b)", re.I)
"""Where a motion hands over from the subject's action to the camera's move.

The plan is authored for a storyboard ARTIST, and a person writes the subject
first with the camera trailing: "his hand comes up ... as the camera pushes in".
41 of episode 2's 42 motions are that shape and the 42nd is "The camera pushes
in ..." WITH the article.  The old code assumed a bare verb at the head of the
string, so every one of the 42 shipped as "The camera <the whole subject
phrase>" -- including the camera-first one, which came out "The camera the
camera pushes in".  So the builder finds the camera clause wherever it sits,
and camera-first stays an unstated convention nobody has to remember."""


STATIC_HEAD = re.compile(r"^\s*(?:the camera\s+)?(?:holds?\s+a\s+)?(?:static|locked)(?:[-\s]off)?"
                         r"\s*(?:shot)?\s*$", re.I)
"""A head that only declares a locked camera -- episode 1's own convention,
`Static shot; he lifts the glass`.  It is a CAMERA statement with no subject, so
the subject comes from the next clause."""


def camera_clause(head: str) -> tuple[str, str]:
    """(what the CAMERA does, what the SUBJECT does) from a motion head, either order.

    Both halves may be empty: a locked-off shot names no camera move, and a
    camera-only head names no subject."""
    if STATIC_HEAD.match(head):
        return "", ""
    parts = CAMERA_LEAD.split(head.strip(), maxsplit=1)
    if len(parts) == 2:
        return (re.sub(r"^the camera\s+", "", parts[1].strip(), flags=re.I).strip(" ,.;"),
                parts[0].strip(" ,.;"))
    bare = re.sub(r"^the camera\s+", "", head.strip(), flags=re.I)
    if bare != head.strip() or _opens_on_a_move(bare):
        return bare.strip(" ,.;"), ""
    return "", head.strip(" ,.;")


def _opens_on_a_move(text: str) -> bool:
    """Does this clause start with a camera verb, with or without its -s?"""
    first = (text.split() or [""])[0].lower().rstrip(",.;")
    return first in CAMERA or any(first.startswith(w) for w in MOVES)


LEADS = ("the", "a", "an", "his", "her", "their", "its", "one", "both", "two", "three")
"""Words that can only ever open a subordinate clause, never a name."""


def lower_lead(clause: str) -> str:
    """The half after `as` is subordinate, so it opens in lower case.

    MEASURED on episode 2: 21 mid-sentence capitals across the 19 take prompts --
    "pushes in a hand's breadth as The right forefinger lifts".  The motion half
    arrives from the plan as its own sentence, capital and all, and a capital
    mid-sentence reads to the model as a second sentence.

    Only the closed list is lowered: `Watson's hand turns` keeps its capital,
    because inventing a rule that lowercases names would cost more than the
    fault it fixes."""
    first = (clause.split(" ", 1)[0] if clause else "").lower().rstrip(",.;")
    # `.rstrip("'s")` would be a CHARACTER SET and would eat the s of `his`.
    return clause[0].lower() + clause[1:] if first.removesuffix("'s") in LEADS else clause


def camera_sentence(motion: str, t0: int, t1: int, line_end: int | None = None) -> str:
    """D3 / D3', base-en §4.3's own example shape: `The camera holds a static shot as
    the runner exits the frame.`  The action runs to the first beat, or to the end of
    the line when the segment carries one.

    Each half is printed ONCE.  `action` used to fall back to the head that `move`
    had already consumed, so 32 of 42 blocks contained the plan's whole motion
    clause twice inside one sentence -- and the duplicate made the block longer,
    so the L14 length gate scored it as healthier."""
    head, clauses = clauses_of(motion)
    cam, subject = camera_clause(head)
    action = subject or (clauses[0] if clauses else "")
    after = beats(t0, t1, max(len(clauses) - 1, 0))
    end = line_end if line_end is not None else (after[0] if after else t1)
    move = f"The camera {camera_verb(cam)}" if cam else "The camera holds a static shot"
    return (f"{move} as {lower_lead(action)}, {during(t0, end)}." if action
            else f"{move}, {during(t0, end)}.")


NOUNS = (("limp", "the step"), ("walk", "the walk"), ("climb", "the climb"), ("step", "the step"),
         ("lean", "the lean"), ("turn", "the turn"), ("lift", "the lift"), ("rais", "the lift"),
         ("reach", "the reach"), ("swing", "the swing"), ("plant", "the step"), ("push", "the push"),
         ("pull", "the pull"), ("drink", "the drink"), ("cross", "the crossing"), ("shrug", "the shrug"),
         ("roll", "the roll"), ("drop", "the drop"), ("pour", "the pour"), ("open", "the opening"))


def motion_noun(clause: str) -> str:
    """The noun D5 hands to `continues to the last frame of the shot`."""
    low = clause.lower()
    return next((noun for stem, noun in NOUNS if re.search(rf"\b{stem}", low)), "the movement")


def beat_sentences(motion: str, t0: int, t1: int, line_end: int | None = None) -> list[str]:
    """D4 / D10 / D5: every clause after the first gets its own whole second, a
    dialogue segment times its first follow-on from the LINE END, and the last clause
    runs on to the last frame (measured: the untimed tails are where the holds sat)."""
    rest = clauses_of(motion)[1][1:]
    if not rest:
        return []
    marks = ([line_end] + beats(line_end, t1, len(rest) - 1)) if line_end is not None else beats(t0, t1, len(rest))
    if not marks:   # a segment too short for a first beat: every clause rides the tail (ep11 shot 5, 1.5 s)
        return [f"Then {', then '.join(rest)}, and {motion_noun(rest[-1])} continues to the last frame of the shot."]
    out: list[str] = []
    for k, clause in enumerate(rest):
        if k >= len(marks):                                   # the seconds ran out (3.4)
            out[-1] = out[-1].rstrip(".") + f", then {clause}."
            continue
        lead = f"At {stamp(marks[k])}, as the line ends," if line_end is not None and k == 0 else f"At {stamp(marks[k])}"
        out.append(f"{lead} {clause}.")
    out[-1] = out[-1].rstrip(".") + f", and {motion_noun(rest[-1])} continues to the last frame of the shot."
    return out


# ---- 1.4  the owner's two content rules ------------------------------------

def life_sentence(crowd: str, t0: int, t1: int, behind: str = "") -> str:
    """D6, owner verbatim: 'i liked you added some background folks in public shots,
    that is having people regular work sells that thing'.  The clause is the segment's
    own `Framed.crowd`, falling back to its `Setup.crowd`; a private setup names none
    and an insert takes none (Setup.crowd: 'reaches every panel that is not an insert').

    `behind` is who the crowd is behind -- `them`, one face's own label, or nobody:
    episode 9 said "Behind him" over twelve shots whose `faces` were empty."""
    if not crowd:
        return ""
    lead = f"Behind {behind}" if behind else "Beyond the foreground"
    return f"{lead} {crowd}, {during(t0, t1)}."


def staged(seg: dict, faces: list[str]) -> list[str]:
    """Whose face this BLOCK shows among the take's staged sheets: the shot's own
    `faces` (readable in the panel) that have a `<Subject k>`.  A take's sheets
    are staged once for all its shots; a man on the second shot's sheet is not
    in the first shot's picture."""
    return [w for w in seg.get("faces", faces) if w in faces]


def behind(shown: list[str], faces: list[str] | None = None) -> str:
    """The subject the life sentence agrees with: the faces the block shows,
    labelled against the take's staged list."""
    faces = shown if faces is None else faces
    if len(shown) > 1:
        return "them"
    return subject_of(shown[0], faces) if shown else ""


def normal_crowd(text: str, names=()) -> str:
    """`Setup.crowd` is a drawer's caption -- a capital and a full stop -- and
    wrapped untouched it gave every episode 9 block "Behind him Forty immigrants
    ... in the yoke., from 00:00 to 00:05".  Trailing stop off; a leading capital
    lowered unless it is a name (or opens one: "Salt Lake")."""
    text = " ".join(text.split()).rstrip(".; ")
    words = text.split()
    if not words or is_name(words[0], names) or (len(words) > 1 and words[1][:1].isupper()):
        return text
    return text[0].lower() + text[1:]


def crowd_of(seg: dict, names=()) -> str:
    """This segment's background life: its own crowd, else the setup's, normalised."""
    if seg["size"] == "insert":
        return ""
    return normal_crowd(calm(seg.get("crowd") or getattr(seg.get("setup"), "crowd", "") or ""), names)


WIDE_ENOUGH = ("wide", "full", "medium")
"""The sizes in which background life is a picture rather than a rumour: a close
or an insert has no room behind the subject for thirty pack mules."""


def crowd_block(segs: list[dict]) -> int | None:
    """Which segment carries the take's ONE life sentence: the first wide enough
    to show it, else the first that is not an insert -- a take of closes in a
    public bar still has the drinkers behind the man, which is the episode 4-7
    shape the owner praised.  Episode 9 put the same 36-word caption into 30 of
    30 blocks."""
    wide = next((i for i, seg in enumerate(segs) if seg["size"] in WIDE_ENOUGH and crowd_of(seg)), None)
    return wide if wide is not None else next((i for i, seg in enumerate(segs) if crowd_of(seg)), None)


LIFE_WRAP = 5
"""What `life_sentence` adds around the crowd, in scrubbed words."""


def life_for(k: int, seg: dict, ctx: dict, used: int) -> str:
    """The life sentence for block `k`, if this is the take's crowd block and the
    crowd fits under the ceiling with everything else already said -- cut to its
    first clauses to fit, and gone when its first clause does not: the crowd is
    what a full block does without.  What was said is recorded in `ctx['life']`
    so L10 asks for it exactly where it is."""
    if ctx.get("crowd_at") != k - 1:
        return ""
    crowd = trim(crowd_of(seg, ctx["names"]), max(0, HIGH_BLOCK - used - LIFE_WRAP))
    said = life_sentence(crowd, int(round(seg["t"])), seg["end"], behind(staged(seg, ctx["faces"]), ctx["faces"]))
    if not said or used + words(said) > HIGH_BLOCK:
        return ""
    ctx["life"][k] = crowd
    return said


SLOW = re.compile(r"\bslow(ly)?\b", re.I)
GAIT = re.compile(r"\b(walks?|walking(?!\s+(?:stick|sticks|height|pace|speed))|walked|limps?|limping|"
                  r"limped|climbs?|climbing|climbed|trots?|trotting|rides?|riding|"
                  r"(?<!porch )(?<!stone )(?<!front )(?<!\bthe )steps|stepping|"
                  r"stepped|strides(?!\s+(?:from|behind|of|away))|striding)\b", re.I)
"""L8 and L9 read a gait VERB (spec §4).  The nouns `step`, `stride` and `pace` are
out -- INCLUDING THE PLURAL, which they were not.  `strides` sat in the verb
alternation, so this repo's commonest camera idiom tripped it: "level with
Holmes's chest and two long STRIDES from him" refused episode 4's take 15, a man
standing still in a parlour, for "a walk with no pace named".  A gait verb is
never followed by `from`, `behind`, `of` or `away`, so "he strides across the
room" still reads as a gait while a measured distance no longer does.

And `walking` inside a compound is out too: the camera's own position says `one step
farther along the counter`, `a stride behind the two men`, `at walking height` and
`down the length of the black walking stick`, and a blind injection there wrote `The
camera is one step limping on his stick farther along the counter`."""


MEASURED_STRIDE = re.compile(
    r"\b(?:a|one|two|three|four|five|six|seven|eight|nine|ten|several|a few|half)\s+"
    r"(?:long|short|full|whole|good|easy)?\s*strides?\b", re.I)
"""A STRIDE YOU COUNT IS A DISTANCE, whatever preposition follows it.

The first version of this fix listed the prepositions -- `from`, `behind`, `of`,
`away` -- and a camera's distance takes any preposition of place.  Episode 5's
camera stands "two strides inside the room" and L8 refused a shot of an old
woman standing still in a doorway.

The discriminator is the MEASURE, not the preposition: "two long strides",
"a stride", "three strides" are all lengths, and "Holmes strides into the room"
has no measure and is still a gait.  `walked` is the same shape and needs no
help, because nobody writes "two walked"."""


def without_measures(text: str) -> str:
    """The body with every measured stride removed, so a gait rule reads only gaits."""
    return MEASURED_STRIDE.sub(" ", text or "")


def blank_measures(text: str) -> str:
    """The same, blanked IN PLACE, so a match's position still indexes the original
    text: `paced` and `limp` write at the position they matched."""
    return MEASURED_STRIDE.sub(lambda m: " " * len(m.group(0)), text or "")


BOUNDARY = re.compile(r"[,;:]|\b(?:as|while|where)\b", re.I)
PERSON = re.compile(r"<Subject \d+>|\b(he|she|they|him|her|them|his|their|man|men|woman|women|boy|boys|"
                    r"girl|girls|child|children|people|folk|figures?|riders?|drivers?|herdsm[ae]n|"
                    r"porters?|clerks?|barman|farmers?|immigrants?|guards?|soldiers?|both|horses?|"
                    r"mules?|pony|ponies|mustang|ox|oxen|dog|cat|cattle|herd|drove)\b", re.I)
STOP_CAPS = {"The", "A", "An", "At", "By", "From", "Behind", "Beyond", "In", "On", "With", "Across", "Over",
             "Under", "Then", "And", "As", "While", "Close", "Medium", "Wide", "Full", "Insert", "Extreme",
             "Static", "Camera", "Shot", "Picture", "Subject", "Audio", "English", "One", "Two", "Three",
             "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Twelve", "Twenty", "Thirty", "Forty",
             "Fifty", "Several"}
"""Who can WALK: a pronoun, a label, a closed list of people and animals, or a
capitalised name that is not a sentence opener or a number.  The sun, the wheat
and a curtain are none of these (L23)."""


def clause_head(text: str, at: int) -> str:
    """The clause position `at` sits in, from its last boundary: a comma, a
    semicolon or a subordinator.  `and` is not one -- "he walks to the door and
    opens it" is still his clause."""
    starts = [m.end() for m in BOUNDARY.finditer(text, 0, at)]
    return text[starts[-1] if starts else 0:at]


def is_person(head: str) -> bool:
    """Does this clause belong to somebody who can walk?"""
    if PERSON.search(head):
        return True
    return any(w[0].isupper() and not w.isupper() and not is_name(w, STOP_CAPS)
               for w in head.split() if w[:1].isalpha())


def gaits(text: str) -> list[re.Match]:
    """Every gait verb in `text` whose clause is a person's or an animal's, read
    with the measured strides blanked -- "three long strides as the low sun
    lifts" is a distance, and the sun has no gait (L8, L9, L23)."""
    body = blank_measures(text)
    return [m for m in GAIT.finditer(body) if is_person(clause_head(body, m.start()))]

TROT = re.compile(r"\b(trot|trots|trotting|ride|rides|riding)\b", re.I)


def limp(text: str) -> str:
    """D12's clause at the gait word it belongs to.  The stick is named ONCE: the plan
    usually says `on his stick` itself, and `a full step limping on his stick back from
    the doorway on his stick` is what the blind injection wrote into T10."""
    if not (found := gaits(text)):
        return text
    m = found[0]
    tail = "limping" if "stick" in text.lower() else "limping on his stick"
    return f"{text[:m.end()]} {tail}{text[m.end():]}"


def limp_clause(text: str, who: str = LEAD) -> str:
    """D12, owner verbatim: Watson limps and walks on his stick while Stamford walks at
    a normal pace.  The word 'slowly' never reaches the prompt -- the limp carries the
    slowness -- so a plan that says it is REFUSED rather than repaired (3.12)."""
    if SLOW.search(text):
        raise ValueError(f"the plan says 'slow' where the limp carries the slowness: {text!r}")
    return text if who not in text or "limp" in text.lower() else limp(text)


def paced(text: str) -> str:
    """D11, owner: the motion runs at normal speed and the pace is NAMED.  It lands at
    the end of the clause carrying the gait, where it reads as speed rather than as a
    label stacked on the verb (base-en §4.3).  The clause must be a PERSON's:
    episode 9 wrote "the low sun lifts along the far peaks at a normal walking
    pace", episode 7 the same onto a curtain and a gas flame."""
    if not (found := gaits(text)) or any(p in text.lower() for p in PACE):
        return text
    m = found[0]
    rate = "at a normal trot" if TROT.match(m.group(0)) else "at a normal walking pace"
    end = next((i for i in range(m.end(), len(text)) if text[i] in ",;."), len(text))
    return f"{text[:end].rstrip()} {rate}{text[end:]}"


def guarantee(parts: list[tuple[str, bool]], who: str) -> list[str]:
    """L8 and L9 are BLOCK rules, and the gait is as often in the frame text as in the
    motion (`Watson seen from behind, his boot on the third step`).  The pace and the
    limp land on the first WRITABLE clause that carries the gait, so the spoken line
    and the setup's own life sentence are never written into."""
    body, out = " ".join(t for t, _ in parts), [t for t, _ in parts]
    spots = [i for i, (text, writable) in enumerate(parts) if writable and gaits(text)]
    if not spots:
        return out
    if who and who in body and "limp" not in body.lower():
        i = next((i for i in spots if who in out[i]), spots[0])
        out[i] = limp(out[i])
    if not any(p in body.lower() for p in PACE):
        out[spots[0]] = paced(out[spots[0]])
    return out


def short_action(clause: str, cap: int = 12) -> str:
    """The `while ...` of D7: the leading person becomes a pronoun -- a label may not be
    cited twice in one sentence -- the clause is cut at its first aside, and at the last
    `and` that keeps it short enough to read as one thing."""
    body = re.sub(r"^(<Subject \d+>|[A-Z][a-z]+)'s\s+", "his ", clause.strip())
    body = re.sub(r"^(<Subject \d+>|[A-Z][a-z]+)\s+", "he ", body)
    out: list[str] = []
    for part in re.split(r",| while ", body)[0].strip().split(" and "):
        if out and len(" ".join(out + [part]).split()) > cap:
            break
        out.append(part)
    return " and ".join(out)


def mouth_action(motion: str, who: str) -> str:
    """Which action D7's closed mouth is bound to: the clause whose subject is the
    PERSON.  Measured: the first clause is often the scenery, and T05 read
    `<Subject 1>'s mouth is closed ... while the street and shopfronts stream past`."""
    head, clauses = clauses_of(motion)
    clauses = clauses or [head]
    lead = re.compile(rf"^(?:{re.escape(who)}|(?:he|his)\b)" if who else r"^(?:he|his)\b", re.I)
    return short_action(next((c for c in clauses if lead.match(c)),
                             next((c for c in clauses if re.search(r"\b(he|his|him)\b", c, re.I)),
                                  clauses[0])))


# ---- 1.4  the segments -----------------------------------------------------

def grid_seconds(t: float, fps: int = 24) -> float:
    """The second of the grid frame a pin at `t` actually lands on, so the text and
    the pin agree to the frame."""
    from studio.episode_takes import grid_frame
    return grid_frame(round(t * fps)) / fps


def cell(framed) -> dict:
    """The picture half of a shot or a sub-shot, as the builder reads it."""
    return {"frame": framed.frame, "motion": framed.motion, "faces": list(framed.faces),
            "size": framed.size, "crowd": framed.crowd, "end_frame": framed.end,
            "camera": framed.camera, "at_rest": framed.at_rest, "changed": framed.changed}


def segments(shots: list[Shot], placed: list[dict], offset: float, frames: int,
             setup: Setup | None = None, fps: int = 24) -> list[dict]:
    """Shots and their sub-shots in time order, with the take-relative start."""
    by = {s["index"]: s for s in placed}
    out = []
    for shot in shots:
        start = by[shot.index]["t_start"] - offset
        out.append(dict(cell(shot), shot=shot.index, sub=0, t=grid_seconds(start, fps), setup=setup))
        for k, cut in enumerate(shot.cuts, start=1):
            out.append(dict(cell(cut), shot=shot.index, sub=k,
                            t=grid_seconds(start + cut.at_s, fps), setup=setup))
    return close_segments(out, frames, fps)


def close_segments(segs: list[dict], frames: int, fps: int = 24) -> list[dict]:
    """3.14: a segment's end IS the next segment's start, and the last one ends on the
    last second the latent ACTUALLY REACHES.

    OWNER 5.13 put the ceiling here so no second of the video went unnamed.  The
    cost was measured on 2026-09-13: a 294-frame take (12.25 s) was announced as
    running to 00:13, and 16 of 22 episode 3 prompts named up to 0.75 s that does
    not exist.  Told a longer timeline than it has, the model spreads its shots
    across it and every one arrives early -- episode 3 T02's second cell landed
    1.50 s before its pin.  An unnamed tail of a shot already described costs
    less than phantom time the model plans against."""
    for i, seg in enumerate(segs):
        ahead = segs[i + 1]["t"] if i + 1 < len(segs) else frames / fps
        seg["t_to"] = ahead
        seg["end"] = round(ahead) if i + 1 < len(segs) else stated_end(frames, fps)
        seg["last"] = i == len(segs) - 1
    return segs


def lines_under(lines: list[Line], at: dict, offset: float, t0: float, t1: float) -> list[Line]:
    """A narration line that crosses a cut is stated in BOTH segments, clipped to each
    (D7); a dialogue line belongs to the segment it starts in."""
    out = []
    for line in lines:
        a = at[line.index][0] - offset
        b = a + at[line.index][1]
        if line.kind == "dialogue":
            if t0 - 1e-6 <= a < t1 - 1e-6:
                out.append(line)
        elif a < t1 - 1e-6 and b > t0 + 1e-6:
            out.append(line)
    return out


def mouth_of(seg: dict, faces: list[str], cast) -> str:
    """Whose closed mouth D7 speaks about: the staged face the frame names, else
    the one staged face.  An insert shows nobody, so it says nothing (D7'), and
    so does a shot with no face staged: "Ferrier's farm" in a `frame` named a
    man, and four episode 9 blocks told an absent man to keep his mouth shut."""
    shown = staged(seg, faces)
    if seg["size"] == "insert" or not shown:
        return ""
    named = people_in(seg["frame"], cast)
    who = next((w for w in shown if w in named), shown[0] if len(shown) == 1 else None)
    return subject_of(who, faces) if who else ""


def framing(k: int, seg: dict, pic: int, faces: list[str], names=()) -> str:
    """D2a / D2b: the first shot BEGINS FROM its picture (ref-en §5.3) and every later
    shot says at what second it cuts (base-en §4.2's `the shot cuts to`)."""
    phrase = tagged(noun_phrase(seg["frame"], names), faces)
    if k == 1:
        text = f"The shot begins from <Picture {pic}>: {phrase}."
    else:
        head, rest = split_frame(phrase)
        text = (f"At {stamp(seg['t'])} the shot cuts to {head}, beginning from <Picture {pic}>"
                f"{': ' + rest if rest else ''}.")
    if seg["size"] == "insert":
        return text[:-1] + f"; only what <Picture {pic}> shows is in frame."
    return text


LOW_BLOCK, HIGH_BLOCK, MARGIN, CAMERA_CAP = 150, 240, 15, 45
"""OWNER 5.17: the gate is per `[Shot k]` block, so a take is long because it has
more shots and never because one shot is padded.  A block is filled to the floor
plus a margin and no further (ref-en §5.2 asks 350-500 words a take)."""


SCRUB_RATIO = 0.70
"""What fraction of a raw block survives `words()`.

MEASURED on episode 7's shot 0: the built block runs 209 raw words and `words()`
-- which strips `<Picture N>`, `<Subject N>` and the timestamps before counting
-- calls it 146.  146/209 = 0.70.  The same ratio holds across episode 6's
blocks, because every block carries the same furniture of tags and stamps."""


def budget(core: int, low: int = LOW_BLOCK, high: int = HIGH_BLOCK) -> int:
    """How many RAW words of the panel's own detail this block may still spend.

    `core` arrives counted by `words()`, which SCRUBS, and `detail`'s `trim`
    spends the allowance in RAW words -- so an allowance of `165 - core` is
    spent in raw words and then judged in scrubbed ones, and the block lands
    about 30 % short of what it was filled for.

    MEASURED, and this is why the correction is here rather than in the gate:
    episode 7's shot 0 was given a longer frame, a longer camera, a longer
    at_rest and two more motion clauses -- fifty words of authored prose -- and
    the measured block stayed at exactly 146 through every one of them, because
    each word added to `core` takes one out of `want` and each word added to a
    detail field is trimmed back to `want`.  The block was pinned below its own
    floor and nothing written could move it.

    Episodes 4 to 6 never hit it: their blocks carry dialogue and more beats, so
    `core` alone clears 150 and the fill never binds.  A LEAN block -- a silent
    insert, one short line -- is the case that cannot pass, and those are
    exactly the shots the rhythm work asks for.

    The ceiling is unchanged: OWNER 5.17's rule that a take is long because it
    has more shots, never because one shot is padded, is what `high` is for."""
    want = max(0, min(low + MARGIN, high) - core)
    return min(int(round(want / SCRUB_RATIO)), max(0, high - core))


REST_FLOOR = 24
"""The fewest raw words of at-rest geometry a block carries whatever its budget.
Episode 7's blocks carried 30 on average; episode 9's carried 4, because the
crowd caption was counted as core first and the geometry was what gave way."""


LIGHT_CAP = 10
"""Words of the light sentence: a direction and a black.

MEASURED (dq10/J.md §1, §4): ep05/07 carried a light sentence of 5.3/5.5
words in about half their blocks and looked right; ep10 carried 14.0 words in
33/34 blocks, and the second half of it ("... and leaves the right side of his
face in shadow") is inert in the take -- the light is honest in 30/30 because
the CELL carries it.  The first clause always lands whole: a direction cut in
half is no direction."""


def camera_parts(camera: str) -> tuple[str, str]:
    """The plan's `camera` is two sentences -- where the camera stands, then
    the light: "..., a 35mm lens. The low sun comes from the left ...".  Parted
    at the first full stop, so each is spent by its own cap."""
    where, _, light = " ".join((camera or "").split()).partition(". ")
    return where.strip(), light.strip()


LIGHT_TAIL = re.compile(r"\s+(?=(?:along|across|onto|over|into|toward|behind|between)\b)")
"""Where a first clause that overflows the cap may part: the phrase after the
direction ("... from the right | along the house front")."""


def under_cap(parts: list[str], cap: int) -> list[str]:
    """The leading parts that fit in `cap` words; the first always lands."""
    out: list[str] = []
    for part in parts:
        if out and len(" ".join(out + [part]).split()) > cap:
            break
        out.append(part)
    return out


def light_sentence(light: str) -> str:
    """The light in `LIGHT_CAP` words: the first clause, then clauses while
    they fit; a first clause over the cap parts at its trailing phrase.  T16's
    light was the one of 34 that never reached H3 -- cut off the end of a
    45-word camera field by `CAMERA_CAP` -- so the light is its own sentence
    now and never trimmed with the position."""
    text = calm(light).rstrip(".")
    if not text:
        return ""
    clauses = re.split(r"(?<=[;,])\s+|\s+(?=and\b)", text)
    if len(clauses[0].split()) > LIGHT_CAP:
        clauses[:1] = LIGHT_TAIL.split(clauses[0])
    return " ".join(under_cap(clauses, LIGHT_CAP)).strip(" ,;") + "."


def detail(seg: dict, want: int) -> list[str]:
    """D2c / D2d, REQUIRED: where the camera STANDS, the LIGHT, and what is at
    rest in the first frame, all authored per panel by the setup's own author.
    An unplaced camera is how a cab insert ended up on a different axis from
    its own wide; the at-rest clause is what keeps the drawer's still things
    still while the action runs.

    None of it is displaced by the budget: the camera position is whole (to
    `CAMERA_CAP`), the light is whole (to `LIGHT_CAP`), the at-rest runs to
    `REST_FLOOR` at least, and `want` only widens the at-rest.  When a block
    overflows, the crowd goes first (`life_for`), then at-rest clauses."""
    out = []
    position, light = camera_parts(seg.get("camera", ""))
    if where := trim(calm(position), CAMERA_CAP):
        out.append(f"The camera is {where}.")
        want -= len(where.split())
    if lit := light_sentence(light):
        out.append(lit)
        want -= len(lit.split())
    if rest := trim(calm(seg.get("at_rest", "")), max(REST_FLOOR, want)):
        out.append(f"At the first frame {lower_lead(rest)}.")
    return out


def block_parts(k: int, seg: dict, pic: int, ctx: dict) -> list[tuple[str, bool]]:
    """One `[Shot k]` block's CORE in the order §2.B emits it: the framing, the camera
    bound to its first action, the spoken line, the beats, then the closed mouth.
    Each part says whether the block's guarantees may WRITE into it: the spoken
    line is verbatim by grammar.  The life of the place is not core any more --
    counted here, it displaced the required detail (`life_for`)."""
    t0, t1, faces = int(round(seg["t"])), seg["end"], ctx["faces"]
    here = lines_under(ctx["lines"], ctx["at"], ctx["offset"], seg["t"], seg["t_to"])
    spoken = [l for l in here if l.kind == "dialogue"]
    end = int(round(sum(ctx["at"][spoken[0].index]) - ctx["offset"])) if spoken else None
    motion = tagged(limp_clause(seg["motion"]), faces)
    mouth = mouth_of(seg, faces, ctx["cast"])
    voice = lambda ls: voice_events(ls, ctx["at"], ctx["offset"], ctx["ids"], faces, ctx["physical"],
                                    mouth, mouth_action(motion, mouth), t0, t1, ctx["seen"])
    out = [(framing(k, seg, pic, faces, ctx.get("names", ())), True),
           (camera_sentence(motion, t0, t1, end), True), (voice(spoken), False)]
    out += [(s, True) for s in beat_sentences(motion, t0, t1, end)]
    out += [(voice([l for l in here if l.kind == "narration"]), False)]
    return [(text, writable) for text, writable in out if text]


def joined(parts: list[tuple[str, bool]]) -> int:
    """The scrubbed word count of a block's parts so far."""
    return words(" ".join(t for t, _ in parts))


def segment_text(k: int, seg: dict, pic: int, ctx: dict) -> str:
    """The block: the core, the REQUIRED detail, the take's one life sentence where
    it fits, the arrival; then made to keep its two block promises, a named pace
    and Watson's limp (L8, L9)."""
    parts = block_parts(k, seg, pic, ctx)
    # the detail says where the camera STANDS and what is at rest; the gait is never
    # its business, so the block's guarantees leave it alone
    parts[1:1] = [(s, False) for s in detail(seg, budget(joined(parts)))]
    # With no END PICTURE staged, the shot's destination is said in words instead --
    # otherwise nothing anywhere states where the shot gets to. It is appended AFTER
    # the budget is spent, like the head: a required statement is not detail, and
    # charging it to the detail allowance made blocks SHORTER than the 150 floor.
    tail = [(tagged(arrival_clause(seg, ctx.get("names", ())), ctx["faces"]), False)] \
        if ctx.get("no_ends") else []
    if life := life_for(k, seg, ctx, joined(parts + tail)):
        at = next((i for i, (t, _) in enumerate(parts) if "mouth is closed" in t), len(parts))
        parts.insert(at, (life, False))
    head = f"[Shot {k}] {span(int(round(seg['t'])), seg['end'])}."
    return " ".join([head] + guarantee(parts + tail, ctx["watson"]))


def describe(shots: list[Shot], placed: list[dict], lines: list[Line], at: dict, faces: list[str],
             physical: dict[str, str], narrator: str, frames: int, cells: dict,
             setup: Setup | None = None, fps: int = 24, no_ends: bool = False) -> tuple[str, dict]:
    """detailed_description and `{block -> the crowd clause it carries}`.  Line 0 is
    the style opening ref-en §5.2 asks for before `[Shot 1]`; every segment then
    gets its own block, and exactly one of them the take's life sentence."""
    by = {s["index"]: s for s in placed}
    offset = by[shots[0].index]["t_start"]
    segs = segments(shots, placed, offset, frames, setup, fps)
    cast = list(physical) or faces
    ctx = {"faces": faces, "physical": physical, "lines": lines, "at": at, "offset": offset,
           "ids": voice_id(lines, narrator), "seen": set(), "cast": cast, "names": names_of(cast),
           "watson": lead_tag(faces), "no_ends": no_ends, "crowd_at": crowd_block(segs), "life": {}}
    text = "\n".join([style_line(setup)] + [segment_text(k, seg, cells[k - 1], ctx)
                                            for k, seg in enumerate(segs, start=1)])
    return text, ctx["life"]


def description(*args, **kw) -> str:
    """The text half of `describe`."""
    return describe(*args, **kw)[0]


# ---- 1.2 / 1.5 / 1.6 -------------------------------------------------------

def summary(frames: int, segs: list[dict], cells: dict, described: str, faces: list[str],
            spoken, fps: int = 24, has_plate: bool = True) -> str:
    """1.2.  ref-en §3: the task types in play, joined with ` + `; base-en §2.1: the
    RENDERED length to two decimals, never the placed one (5.6).

    With no plate staged the place is named in WORDS: `<Subject n+1>` here would
    cite a subject `subject_definitions` never defined, and a cited-undefined
    reference is exactly what L11 refuses."""
    n = len(segs)
    plate = len(faces) + 1 if has_plate else None
    runs = "; ".join(f"[Shot {i + 1}] begins from <Picture {cells[i]}> and runs "
                     f"{during(int(round(s['t'])), s['end'])}" for i, s in enumerate(segs))
    where = f"<Subject {plate}>, {short_place(described)}" if plate else short_place(described)
    who = ", ".join(f"<Subject {k}>" for k in range(1, len(faces) + 1)) \
        or (f"<Subject {plate}>" if plate else f"<Picture {cells[0]}>")
    audio = ("<Audio 1> carries that spoken line and is the complete audio track." if spoken
             else "<Audio 1> is the complete audio track.")
    return (f"[reference generation + keyframe completion + audio reuse] One {frames / fps:.2f}-second "
            f"take of {n} shot{'s' if n > 1 else ''} in {where}. "
            f"{runs}. The take carries {who} through {shot_list(range(1, n + 1))} in that order. {audio}")


def soundscape(described: str, crowd: str = "", outdoors: bool = False) -> str:
    """1.5, base-en §4.6: ambience, physical action and non-verbal human sound, in one
    paragraph.  Dialogue 'already belongs in the multimodal description'."""
    body = (f"The ambience of {short_place(described)} runs under the whole take: its own air, the "
            f"surfaces underfoot and the fabric of the {place_word(described, outdoors)} around it.")
    if crowd:
        return (f"{body} Cloth, boots, wood and glass carry the physical action, and the movement and "
                f"low murmur of the people at work nearby carry under it throughout.")
    return (f"{body} Cloth, boots and the small sounds of hands on wood, glass and iron carry the "
            f"physical action throughout.")


# ---- 3.17  negation --------------------------------------------------------

NEGATIONS = re.compile(r"\b(no|not|never|nobody|nothing|none|neither|nor|without|barely|hardly|"
                       r"n't|don't|doesn't|isn't|cannot|can't)\b", re.I)


def scrub(text: str) -> str:
    """What a word rule scans: the spoken line is verbatim by grammar (ref-en §5.4) so
    everything between `<d>` and `</d>` is cut out, and the label tags carry no prose."""
    return re.sub(r"<[^>]+>|\bN/A\b", " ", re.sub(r"<d>.*?</d>", " ", text, flags=re.S))


def negations(text: str) -> list[str]:
    """Negated words in a prompt: MiniMax reads none of them (owner 2026-09-11), so the
    builder refuses to emit any."""
    return sorted({m.group(0).lower() for m in NEGATIONS.finditer(scrub(text))})


# ---- 4  the prompt lint ----------------------------------------------------

def sections(text: str) -> dict[str, str]:
    """The six named sections of a prompt, by name."""
    out, name = {}, None
    for line in text.split("\n"):
        if m := re.match(r"^(subject_definitions|summary|retention_analysis|detailed_description|"
                         r"overall_soundscape|non_diegetic_music):\s?(.*)$", line):
            name, out[name := m.group(1)] = m.group(1), m.group(2)
        elif name is not None:
            out[name] = (out[name] + "\n" + line).strip("\n")
    return out


def secs(text: str) -> int:
    m, s = text.split(":")
    return int(m) * 60 + int(s)


def blocks(text: str) -> list[tuple[int, int, int, str]]:
    """The `[Shot k] From A to B.` blocks of detailed_description, as (k, a, b, body)."""
    body = sections(text).get("detailed_description", text)
    found = list(re.finditer(r"\[Shot (\d+)\] From (\d\d:\d\d) to (\d\d:\d\d)\.", body))
    return [(int(m.group(1)), secs(m.group(2)), secs(m.group(3)),
             body[m.end():found[i + 1].start() if i + 1 < len(found) else len(body)])
            for i, m in enumerate(found)]


def words(text: str) -> int:
    return len(scrub(text).split())


STILL = re.compile(r"\b(still|stays?|remains?|motionless|frozen|pauses?|waits?|unchanged|unmoving|"
                   r"holds?|held)\b", re.I)
ACTS = ("walk", "limp", "climb", "step", "stride", "turn", "lift", "rais", "lower", "reach", "push",
        "pull", "open", "cross", "pass", "enter", "leave", "travel", "drink", "pour", "writ", "shrug",
        "plant", "spring", "roll", "sway", "drop", "follow", "arriv", "carry", "carrie", "swing",
        "advanc", "bend", "pump", "trot", "set down", "sets down", "setting down", "pick up",
        "picks up", "picking up", "take off", "takes off", "stand up", "stands up", "let go",
        "lets go", "come up", "comes up")
ACTION = re.compile(r"\b(" + "|".join(ACTS) + r")(e|es|ed|d|s|ing)?\b", re.I)
"""OWNER 5.18: every segment carries a BODY-SCALE action.  The gate is the verb's
class, never its ending -- the plan writes `both men advance`, `the two hands pump`
and `his shoulders turn round`, and an enumeration of third-person singulars called
those blocks static.  Eyes, brows, blinks, breath, jaw and fingers alone are still
out: `grips`, `narrow`, `draw together` and `sets` (as in a jaw) are absent on
purpose."""
PACE = ("walking pace", "at a normal pace", "the horse's trot", "at normal speed", "at a trot",
        "at a normal trot")


def l1_negation(text, facts):
    return [f"L1 NEGATION: {bad} outside <d>"] if (bad := negations(text)) else []


def l2_stillness(text, facts):
    """`holds a static shot` is the single allowed use of `hold` (base-en §4.3)."""
    bad = sorted({m.group(0).lower() for m in STILL.finditer(scrub(text).replace("holds a static shot", " "))})
    return [f"L2 STILLNESS: {bad}"] if bad else []


def l3_slow(text, facts):
    return ["L3 SLOW: this episode names no slow move; the limp carries the slowness"] \
        if SLOW.search(scrub(text)) else []


def affirmative(body: str) -> str:
    """What the block says HAPPENS.  A clause that denies its verb offers no action:
    `his head does not turn away` is the measured freeze, not a turn."""
    return " ".join(c for c in re.split(r"[.;,]", scrub(body)) if not NEGATIONS.search(c))


def l4_action(text, facts):
    """OWNER 5.18.  Eyes, brows, blinks, breath, jaw and fingers alone do not count."""
    return [f"L4 NO ACTION [Shot {k}]: the block carries no body-scale action"
            for k, a, b, body in blocks(text) if not ACTION.search(affirmative(body))]


def l5_coverage(text, facts):
    """OWNER 5.13: every second of the latent is inside some shot's range."""
    bs, out = blocks(text), []
    if not bs:
        return out
    if bs[0][1] != 0:
        out.append(f"L5 COVERAGE [Shot {bs[0][0]}]: the first range starts at {stamp(bs[0][1])}, not 00:00")
    out += [f"L5 COVERAGE [Shot {k}]: ends at {stamp(b)} where [Shot {k2}] starts at {stamp(a2)}"
            for (k, _, b, _), (k2, a2, _, _) in zip(bs, bs[1:]) if b != a2]
    out += [f"L5 COVERAGE [Shot {k}]: the range {stamp(a)}-{stamp(b)} spans nothing" for k, a, b, _ in bs if a >= b]
    if (frames := facts.get("frames")) and bs[-1][2] != (want := stated_end(frames, facts.get("fps", 24))):
        out.append(f"L5 COVERAGE [Shot {bs[-1][0]}]: the last range ends at {stamp(bs[-1][2])}, not {stamp(want)}")
    return out


def l6_stamps(text, facts):
    out = []
    for k, a, b, body in blocks(text):
        ats = [secs(s) for s in re.findall(r"\bAt (\d\d:\d\d)", body)]
        pairs = [secs(s) for x, y in re.findall(r"\b[Ff]rom (\d\d:\d\d) to (\d\d:\d\d)", body) for s in (x, y)]
        if loose := sorted({s for s in ats + pairs if not a <= s <= b}):
            out.append(f"L6 STAMP OUT OF RANGE [Shot {k}]: {[stamp(s) for s in loose]} outside "
                       f"{stamp(a)}-{stamp(b)}")
        if ats != sorted(set(ats)):
            out.append(f"L6 STAMP OUT OF RANGE [Shot {k}]: the At stamps do not ascend: {ats}")
    return out


def l7_pins(text, facts):
    """OWNER 5.14: whole-second stamps, capped at half a second from the pin."""
    at = {b[0]: b[1] for b in blocks(text)}
    return [f"L7 PIN DISAGREEMENT [Shot {k}]: the pin sits at {t:.2f} s, the text says {stamp(at[k])}"
            for k, t in facts.get("pins", []) if k > 1 and k in at and abs(t - at[k]) > 0.5]


def unquoted(text: str, spoken=()) -> str:
    """The block with its spoken lines removed: a gait the character SAYS is
    not a walk the picture makes (ep11: "We ride tonight" read as a ride with
    no pace).  The lines stand in the block bare, so they are cut by their text."""
    out = re.sub(r'"[^"]*"', "", text)
    for line in spoken or ():
        out = out.replace(str(line), "")
    return out


def l8_pace(text, facts):
    said = [s if isinstance(s, str) else s.get("text", "") for s in (facts.get("lines") or [])]
    return [f"L8 NO PACE [Shot {k}]: a walk, climb or ride with no pace named"
            for k, a, b, body in blocks(text)
            if gaits(unquoted(body, said)) and not any(p in body.lower() for p in PACE)]


def l9_limp(text, facts):
    who = facts.get("watson")
    return [f"L9 NO LIMP [Shot {k}]: {who} walks or climbs with no limp"
            for k, a, b, body in blocks(text)
            if who and who in body and gaits(body) and "limp" not in body.lower()]


def l10_life(text, facts):
    """§4 reads 'a BLOCK ... does not contain that setup's life clause'; the spec's own
    worked prompts vary the clause block by block, so `facts['life']` is
    `{block -> the crowd clause that block asked for}` and the gate is per block."""
    life = facts.get("life") or {}
    return [f"L10 NO LIFE [Shot {k}]: the block's background life is absent from the picture"
            for k, a, b, body in blocks(text) if life.get(k) and life[k] not in body]


def l11_pictures(text, facts):
    cited = {int(n) for n in re.findall(r"<Picture (\d+)>", text)}
    defined = {int(n) for n in re.findall(r"<Picture (\d+)> is ", text)} | \
              {int(n) for n in re.findall(r"in <Picture (\d+)>:", text)}
    out = [f"L11 PICTURES: <Picture {n}> is cited with no definition" for n in sorted(cited - defined)]
    out += [f"L11 PICTURES: <Picture {n}> is past the {MAX_PICTURES}-slot wall" for n in sorted(cited) if n > MAX_PICTURES]
    if (refs := facts.get("refs")) and len(defined) != refs:
        out.append(f"L11 PICTURES: {len(defined)} pictures defined against {refs} staged references")
    out += [f"L11 PICTURES: <Picture {n}> is the first frame of more than one shot"
            for n, body in re.findall(r"<Picture (\d+)> \(([^)]*)\)", text) if body.count("first frame") > 1]
    # THE OWNER'S RULE, 2026-09-16: no picture is a shot's LAST frame. `takes_r2v.NO_ENDS`
    # stops one being STAGED; this stops one being DECLARED, which is the same pin by
    # another route -- the model races to it and holds, so a near one freezes the segment
    # and a far one dissolves the background into it (docs/calibration/end_frames.md).
    # Episode 8 shipped 15 while the skill already said "no end pins", because the flag
    # was honoured in the anchor list and bypassed in the prompt text. The gate belongs
    # on the built artefact, which is what a lint reads.
    # Only a DECLARATION, never prose: "the lean continues to the last frame of the shot"
    # is the required continuation clause and must stay legal, so the pattern is the two
    # forms that bind a picture TO a shot's end -- the definition and the retention line.
    out += [f"L11 PICTURES: <Picture {n}> is declared the last frame of a shot"
            for n in re.findall(r"<Picture (\d+)> is the last frame", text)]
    out += [f"L11 PICTURES: <Picture {n}> is retained as a shot's last frame"
            for n, body in re.findall(r"<Picture (\d+)> \(([^)]*)\)", text) if "last frame" in body]
    if (plate := facts.get("plate")) and re.search(rf"<Picture {plate}>[^\n]*(first|last) frame", text):
        out.append(f"L11 PICTURES: the plate <Picture {plate}> is declared a frame")
    if (strip := facts.get("strip")) and (m := re.search(rf"<Picture {strip}> \([^)]*\): (\w+)", text)) \
            and m.group(1) != "weak_reference":
        out.append(f"L11 PICTURES: the strip is marked {m.group(1)}, not weak_reference")
    return out + l11_location(text, facts)


def l11_location(text, facts):
    """OWNER 5.16: the plate is a DEFINITION, so it never `appears in` a shot and it is
    never `fully_preserved` -- its wide empty composition is not retained."""
    plate = facts.get("plate")
    m = plate and re.search(rf"<Subject {plate}> \(([^)]*)\): (\w+)", text)
    if not m:
        return []
    out = ["L11 PICTURES: the location is marked " + m.group(2)] if m.group(2) != "partially_preserved" else []
    return out + (["L11 PICTURES: the location 'appears in' a shot"] if "appears in" in m.group(1) else [])


def l12_speakers(text, facts):
    out = ["L12 SPEAKERS: (Sx) in retention_analysis (ref-en §5.4)"] \
        if re.search(r"\(S\d+\)", sections(text).get("retention_analysis", "")) else []
    said = re.findall(r"\((S\d+)\)(.*?)says:\s*<d>\[English\] (.*?)</d>", text, re.S)
    known = {l["text"] for l in facts.get("lines", [])} if "lines" in facts else None
    order: list[str] = []
    for sid, mid, body in said:
        if sid not in order:
            order.append(sid)
            if not mid.strip(" ,"):
                out.append(f"L12 SPEAKERS: {sid} speaks first with no identity clause (base-en §4.4)")
        if known is not None and body not in known:
            out.append(f"L12 SPEAKERS: the spoken line is not the plan's line byte for byte: {body!r}")
    if order != [f"S{k}" for k in range(1, len(order) + 1)]:
        out.append(f"L12 SPEAKERS: the ids are not S1..Sn in vocal order: {order}")
    return out


TYPES = ("reference generation", "keyframe completion", "audio reuse")


def l13_task_type(text, facts):
    head = sections(text).get("summary", "").strip()
    if not head:
        return []
    if not (m := re.match(r"\[([^\]]*)\]", head)):
        return ["L13 TASK TYPE: summary does not open with its task types in [...]"]
    named = [t.strip() for t in m.group(1).split("+")]
    need = {t for t, on in ((TYPES[1], re.search(r"first frame|last frame", text)),
                            (TYPES[2], "fully_copy" in text),
                            (TYPES[0], re.search(r"<Picture \d+> is|storyboard reference", text))) if on}
    out = [f"L13 TASK TYPE: {t!r} is in play and unnamed" for t in sorted(need - set(named))]
    return out + (["L13 TASK TYPE: a task type is repeated"] if len(named) != len(set(named)) else [])


def take_floor(shots: int) -> int:
    """ref-en §5.2 asks 350-500 English words of `detailed_description`; the OWNER's
    gate is per block (5.17), and a ONE-shot take cannot reach 350 without breaking
    the 240-word block ceiling.  So the take's floor is its blocks' own floor until
    it has the shots to carry the guide's number."""
    return min(350, LOW_BLOCK * shots)


def l14_length(text, facts):
    """OWNER 5.17: the gate is PER BLOCK, so a long take is long because it has more
    shots, never because one shot is padded (ref-en §5.2 asks 350-500 a take)."""
    dd = sections(text).get("detailed_description")
    if dd is None:
        return []
    want = take_floor(len(blocks(text)))
    out = [f"L14 LENGTH: detailed_description is {n} words; the floor is {want}"] \
        if (n := words(dd)) < want else []
    return out + [f"L14 LENGTH [Shot {k}]: {n} words; the gate is "
                  f"{LOW_BLOCK}-{HIGH_BLOCK} a block"
                  for k, a, b, body in blocks(text) if not LOW_BLOCK <= (n := words(body)) <= HIGH_BLOCK]


def l15_summary_length(text, facts):
    m = re.search(r"One ([\d.]+)-second take", sections(text).get("summary", ""))
    if not (m and facts.get("frames")):
        return []
    want = facts["frames"] / facts.get("fps", 24)
    return [] if abs(float(m.group(1)) - want) <= 0.01 else \
        [f"L15 SUMMARY LENGTH: the summary says {m.group(1)} s; the latent is {want:.2f} s"]


def l16_dialogue_tail(text, facts):
    """Measured: 6 of 8 dialogue segments froze at the second their line ended."""
    out = []
    for line in facts.get("lines", []):
        found = [b for b in blocks(text) if b[0] == line["block"]]
        after = [secs(s) for b in found for s in re.findall(r"\bAt (\d\d:\d\d)", b[3])]
        if found and not any(s >= round(line["end"]) for s in after):
            out.append(f"L16 DIALOGUE TAIL [Shot {line['block']}]: no beat at or after {stamp(line['end'])}")
    return out


def l17_cross_cut(text, facts):
    """ref-en §5.1 / base-en §4.4.  No ep01 line crosses a cut; the rule is here so the
    first one that does cannot ship silently."""
    return [f"L17 CROSS-CUT LINE [Shot {l['block']}]: the line crosses a cut with no <scenetrans>"
            for l in facts.get("lines", []) if l.get("crosses") and "<scenetrans>" not in text]


def l18_banned_prop(text, facts):
    return [f"L18 BANNED PROP: {w!r} (the book gives bare hands)" for w in BANNED_PROPS if w in text.lower()]


# ---- L19-L23  take prompt hygiene (docs/analysis/ep08_ep09_why_worse.md §5) --

SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z<])")
LONG_SENTENCE = 20


def sentences(body: str) -> list[str]:
    return [s.strip() for s in SENTENCE.split(body.strip()) if s.strip()]


def l19_crowd(text, facts):
    """Episode 9's setup crowd caption went into 30 of 30 blocks verbatim, up to
    eight times over, ending `.,`.  One long sentence lives in one block."""
    seen: dict[str, list[int]] = {}
    out = [f"L19 CROWD [Shot {k}]: the block carries '.,'" for k, a, b, body in blocks(text) if ".," in body]
    for k, a, b, body in blocks(text):
        for said in {re.sub(r"\d\d:\d\d", "", s) for s in sentences(body)}:
            if len(said.split()) >= LONG_SENTENCE:
                seen.setdefault(said, []).append(k)
    out += [f"L19 CROWD: one {len(s.split())}-word sentence sits in {shot_list(ks)}: {s[:48]!r}..."
            for s, ks in seen.items() if len(ks) > 1]
    return out


STYLE_CAP = 16
STYLE_WORDS = ("warm", "cool", "hard", "soft", "deep", "bright", "dark", "pale", "muted", "natural", "golden",
               "gold", "cold", "hot", "dusty", "sunlit", "lamplit", "high", "low", "late", "early", "clear",
               "bleached", "bone", "alkali", "grey", "gray", "black", "white", "red", "green", "blue", "amber",
               "soot", "photoreal", "cinematic", "palette", "light", "shadow", "sunlight", "sun", "summer")
"""A style line's own vocabulary: none of these is a name, so capitalised
mid-sentence any of them is a pasted sentence head ("..., Warm high-summer")."""


def stray_capitals(line: str, text: str) -> list[str]:
    """Capitalised words after the first that are not names: in the style
    vocabulary, or used in lower case elsewhere in the prompt."""
    out = []
    for w in line.split()[1:]:
        word = w.strip(",.;:")
        if word[:1].isupper() and not word.isupper() and \
                (word.lower() in STYLE_WORDS or re.search(rf"\b{re.escape(word.lower())}\b", text)):
            out.append(word)
    return out


def l20_style(text, facts):
    """The style line is the first line of detailed_description: 13 words in
    episodes 5-8, 48 in episode 9 ("only., 35 mm")."""
    dd = sections(text).get("detailed_description")
    line = (dd or "").split("\n")[0].strip()
    if not line or line.startswith("[Shot"):
        return []
    out = [f"L20 STYLE: the style line is {n} words; the cap is {STYLE_CAP}"] \
        if (n := len(line.split())) > STYLE_CAP else []
    out += ["L20 STYLE: the style line carries '.,'"] if ".," in line else []
    if caps := stray_capitals(line, text):
        out.append(f"L20 STYLE: mid-sentence capital outside a name: {caps}")
    return out


MOVER = re.compile(r"\bthe camera\b|\bcontinues?\b|\b(?:is|are) \w+ing\b|"
                   r"\b(?:comes?|goes?|moves?|runs?|settles?|falls?|rises?)\b", re.I)
"""What a closing sentence may name as moving besides an `ACTION` verb: the camera,
a continuation, a progressive, or the plain verbs of a body in motion ("his head
comes further down over the buckle")."""


def l21_arrival(text, facts):
    """The last sentence of a block is the last thing the model hears about
    motion.  It names the camera or a moving body, never a layout: episode 9
    closed 29 of 30 blocks on "the log house stands twice its size along the
    left edge"."""
    out = []
    for k, a, b, body in blocks(text):
        last = (sentences(body) or [""])[-1]
        if m := LAYOUT.search(last):
            out.append(f"L21 ARRIVAL [Shot {k}]: the block ends on a layout, not a movement: {m.group(0)!r}")
        elif not (MOVER.search(last) or ACTION.search(last) or GAIT.search(last)):
            out.append(f"L21 ARRIVAL [Shot {k}]: the block's last sentence names nothing that moves")
    return out


ABSENT_MOUTH = re.compile(r"(?<![>\w])([A-Z][a-z]+(?: [A-Z][a-z]+)*)'s mouth is closed")


def l22_absent_mouth(text, facts):
    """A closed mouth belongs to a staged face, which the builder always writes as
    its `<Subject k>`; a bare name here is a man who is not in the shot."""
    return [f"L22 ABSENT MOUTH [Shot {k}]: {who}'s mouth is closed, and {who} is not a staged face"
            for k, a, b, body in blocks(text) for who in ABSENT_MOUTH.findall(body)]


PACE_MARK = re.compile(r"\bat (?:a normal (?:walking pace|pace|trot)|walking pace|normal speed|a trot|"
                       r"the horse's trot)\b")


def l23_pace_on_a_thing(text, facts):
    """A pace belongs to a clause whose subject can walk.  Episode 9 gave one to
    the sun and the wheat, episode 7 to a curtain and a gas flame."""
    out = []
    for k, a, b, body in blocks(text):
        for m in PACE_MARK.finditer(body):
            if not is_person(head := clause_head(body, m.start())):
                out.append(f"L23 PACE ON A THING [Shot {k}]: {head.strip()[:70]!r} moves at a walking pace")
    return out


RULES = (l1_negation, l2_stillness, l3_slow, l4_action, l5_coverage, l6_stamps, l7_pins, l8_pace,
         l9_limp, l10_life, l11_pictures, l12_speakers, l13_task_type, l14_length,
         l15_summary_length, l16_dialogue_tail, l17_cross_cut, l18_banned_prop,
         l19_crowd, l20_style, l21_arrival, l22_absent_mouth, l23_pace_on_a_thing)


def lint(text: str, facts: dict | None = None) -> list[str]:
    """Every rule of §4.  A fault reads `L{n} NAME [Shot k]: message`.  The lint is the
    PRE-RENDER gate: necessary, never sufficient -- it cannot predict a freeze caused
    by a pin, so `motion_scan` stays the post-render gate."""
    return [fault for rule in RULES for fault in rule(text, facts or {})]


def check(text: str, facts: dict | None = None) -> None:
    """Called by `build`, so a prompt that fails a rule can never reach the GPU."""
    if bad := lint(text, facts):
        raise ValueError(f"the prompt fails the lint ({len(bad)} faults): " + "; ".join(bad))


# ---- L24-L27  the wording H3 measurably ignores (ADVISORY, dq10/B.md §4, J.md §3-4) --
#
# Episode 10 measured four sentence shapes against the render: a kept-clause
# held 1 of 4 (the one a sharp static edge object under a small move); "turns
# his head toward the door" walked the man past the lens on 3/3 renders; a walk
# toward the lens or by a 50-px figure in a wide was ignored 2/2 while a walk
# away to a named thing in frame was obeyed 2/2.  None is a fault the render
# cannot survive, so these print and never refuse: `advise`, not `check`.

CAMERA_TRAVEL = re.compile(r"\bThe camera (?:pushes|pulls|tracks|pans|tilts|dollies|cranes|orbits|zooms|moves)\b")
KEPT_EDGE = re.compile(r"(?:[\w']+ ){1,3}keeps? the frame edges?\b", re.I)
HEAD_TARGET = re.compile(r"\bhead\b[^;.]*?\btoward the (?:[\w-]+ )?(?:doors?|windows?|gates?)\b", re.I)
KEPT_SCOPE = re.compile(r"\b(?:keeps?|kept)\b[^;.,]*?\b(?:inside the frame|whole face|sharp)\b|"
                        r"\bkeeps? sharp\b|\b(?:alone|only)\b[^;.]*?\bcomes? in\b|\bcomes? in\b[^;.]*?\b(?:alone|only)\b", re.I)
WALK_AT_LENS = re.compile(r"\b(?:walk|step|strid|climb)\w*\b[^;.]*?\btoward (?:the camera|the lens|it)\b", re.I)
WIDE_FRAMING = re.compile(r"^[^.]*\b(?:a wide|Wide )")


def kept_edge(body: str, travels: bool) -> str:
    """A kept frame edge under a camera travel: a 1.12x push removed the porch
    post (T20); a pull-back moved the gate posts inward (T03)."""
    hit = KEPT_EDGE.search(body)
    return hit.group(0).strip() if hit and travels else ""


def head_reposition(body: str) -> str:
    """A target noun in a head clause: obeyed as a reposition every time (T15
    x3, T28, T29 s2).  Name what the face keeps, never the thing looked at."""
    hit = HEAD_TARGET.search(body)
    return hit.group(0) if hit else ""


def kept_scope(body: str) -> str:
    """A kept-clause naming a scale, a blur or an absence: 0/3 obeyed (T05
    "whole face keeps inside", T15 "keeps sharp", T29 "the shoulder alone")."""
    hit = KEPT_SCOPE.search(body)
    return hit.group(0) if hit else ""


def walk_advice(body: str, wide: bool) -> str:
    """A walk at the lens (T04, 0/2) or by a figure in a wide (T20, 0/2)."""
    if hit := WALK_AT_LENS.search(body):
        return f"{hit.group(0)!r} walks at the lens; give the travel to the camera or walk away to a named thing"
    if wide and gaits(body):
        return "a walk by a figure in a wide is ignored (T20's 50-px figure never left the gate)"
    return ""


def l24_kept_edge(text, facts):
    return [f"ADVISORY L24 KEPT EDGE [Shot {k}]: {hit!r} under a camera travel -- a push removes the "
            f"edge, a pull-back moves it inward; keep a thing in the MIDDLE of the frame, or hold"
            for k, a, b, body in blocks(text) if (hit := kept_edge(body, bool(CAMERA_TRAVEL.search(body))))]


def l25_reposition(text, facts):
    return [f"ADVISORY L25 REPOSITION [Shot {k}]: {hit!r} names the thing looked at; obeyed as a "
            f"whole-body turn 3/3 -- say what the face keeps ('his eyes stay on the lens')"
            for k, a, b, body in blocks(text) if (hit := head_reposition(body))]


def l26_kept_scope(text, facts):
    return [f"ADVISORY L26 KEPT SCOPE [Shot {k}]: {hit!r} -- a kept-clause holds a sharp static edge "
            f"object, not a scale, a blur or an absence"
            for k, a, b, body in blocks(text) if (hit := kept_scope(body))]


def l27_walk(text, facts):
    return [f"ADVISORY L27 WALK [Shot {k}]: {why}"
            for k, a, b, body in blocks(text) if (why := walk_advice(body, bool(WIDE_FRAMING.match(body))))]


ADVISORIES = (l24_kept_edge, l25_reposition, l26_kept_scope, l27_walk)


def advise(text: str, facts: dict | None = None) -> list[str]:
    """Every advisory of L24-L27: printed beside the card, never a refusal."""
    return [note for rule in ADVISORIES for note in rule(text, facts or {})]


# ---- 3.16  the whole prompt ------------------------------------------------

def prompt_facts(frames, segs, faces, spoken, at, offset, setup, strip, refs, fps=24,
                 has_plate=True, life: dict | None = None) -> dict:
    """What the lint needs beyond the text itself.  `life` is what `describe`
    actually put in (one block, or none when it did not fit); without it the
    take's crowd block is assumed to carry the crowd."""
    at_block = crowd_block(segs)
    if life is None:
        life = {at_block + 1: crowd_of(segs[at_block])} if at_block is not None else {}
    lines = [{"block": 1 + next(i for i, s in enumerate(segs) if s["t"] - 1e-6 <= a < s["t_to"] - 1e-6),
              "text": l.text, "end": a + at[l.index][1],
              "crosses": a + at[l.index][1] > next(s["t_to"] for s in segs if s["t"] - 1e-6 <= a < s["t_to"] - 1e-6)}
             for l, a in spoken]
    return {"frames": frames, "fps": fps, "refs": refs,
            "plate": len(faces) + 1 if has_plate else None, "strip": strip,
            "pins": [(i + 1, s["t"]) for i, s in enumerate(segs)], "lines": lines,
            "life": life, "watson": lead_tag(faces)}


def six_sections(subs: str, summ: str, ret: str, dd: str, sound: str) -> str:
    """The six sections in ref-en's order, blank-line separated."""
    return "\n\n".join([f"subject_definitions:\n{subs}", f"summary:\n{summ}",
                        f"retention_analysis:\n{ret}", f"detailed_description:\n{dd}",
                        f"overall_soundscape: {sound}", "non_diegetic_music: N/A"])


def build(shots: list[Shot], placed: list[dict], lines: list[Line], at: dict, frames: int,
          faces: list[str], physical: dict[str, str], described: str, narrator: str,
          ends: list[int] | None = None, setup: Setup | None = None, refs: int | None = None,
          fps: int = 24, check_lint: bool = True, has_plate: bool = True) -> str:
    """The six sections, in order.  `frames` is the LATENT length: base-en §2.1 asks
    for the effective duration, and the placed length is 0.5 s short of it (5.6)."""
    offset = {s["index"]: s for s in placed}[shots[0].index]["t_start"]
    described = calm(described)     # the setup sheet is written for the drawer too (L2)
    outdoors = bool(getattr(setup, "outdoors", False))
    segs = segments(shots, placed, offset, frames, setup, fps)
    spoken = [(l, at[l.index][0] - offset) for l in sorted(lines, key=lambda l: l.index)
              if l.kind == "dialogue"]
    subs, cells, strip = subjects(faces, physical, described, segs, ends or [], spoken, has_plate, outdoors)
    dd, life = describe(shots, placed, lines, at, faces, physical, narrator, frames, cells, setup, fps,
                        not (ends or []))
    text = six_sections(subs, summary(frames, segs, cells, described, faces, spoken, fps, has_plate),
                        retention(faces, segs, cells, strip, ends or [], described, has_plate, outdoors),
                        dd, soundscape(described, getattr(setup, "crowd", ""), outdoors))
    if bad := negations(text):
        raise ValueError(f"the prompt carries negation MiniMax cannot read: {bad}")
    if check_lint:
        check(text, prompt_facts(frames, segs, faces, spoken, at, offset, setup, strip, refs, fps,
                                 has_plate, life))
    return text
