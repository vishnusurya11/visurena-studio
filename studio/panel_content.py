"""What is actually IN a picture, read by the local vision model and judged here.

Every other gate in this pipeline measures a statistic -- edge strength, face
count, frozen share, mux lag. None of them looks at the frame. So a doll in a
pink dress, a horse cropped to its head, three men drawn as one man three
times, hills on a flat Surrey horizon and a Sherlock Holmes title card on a
War of the Worlds episode all passed DQ, and were caught by eye or by the
owner (2026-09-21: "you have to do a lot of dq on these prompts and videos").

THE MODEL IS NEVER ASKED WHETHER THE PICTURE IS RIGHT. A VLM says yes. It is
asked to LIST what it sees in a closed vocabulary and the judging is done in
this file, against the shot's own words -- the rule `studio/describe.py`
established for trait cards, applied to content.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LANDFORMS = ("flat", "gentle rise", "hills", "mountains", "cliffs", "indoors")
"""What the ground may read as. The book's own country decides which of these
is a fault: Horsell, Woking and Maybury are flat heath and river terrace, and
ep05's T06 and ep07's shot 0 both grew hills the prompt never asked for."""

RAISED = ("hills", "mountains", "cliffs")

HOURS = ("day", "dusk", "night")


@dataclass(frozen=True)
class Seen:
    """One picture as the reader saw it, in the closed vocabulary."""
    landform: str = "flat"
    people: int = 0
    lookalikes: int = 0
    text: bool = False
    hour: str = "night"
    subjects: list[str] = field(default_factory=list)


ASK = (
    "Describe this picture by ANSWERING EACH QUESTION with one of the allowed "
    "answers and nothing else. Output strict JSON with these keys.\n"
    '"landform": the shape of the ground, one of ' + ", ".join(LANDFORMS) + ".\n"
    '"people": how many human figures you can see, as a number.\n'
    '"lookalikes": how many of those figures look like copies of another one '
    "(same face, same build, same clothes), as a number.\n"
    '"text": true if any letters, words, numbers or captions appear anywhere, '
    "else false.\n"
    '"hour": the time of day the LIGHT says, one of ' + ", ".join(HOURS) + ".\n"
    '"subjects": a list of the things in the picture, each a short plain noun '
    "phrase, everything you can name, including anything unexpected."
)


def forbidden_landform(seen: Seen, flat: bool) -> bool:
    """Ground that rises where the book's country does not."""
    return flat and seen.landform in RAISED


def reads_as_night(seen: Seen) -> bool:
    return seen.hour != "day"


WORD = re.compile(r"[a-z]+")


def unasked_subject(seen: Seen, frame: str) -> list[str]:
    """Subjects the reader saw that the shot's own words never mention.

    A subject counts as asked for when ANY of its words is in the shot's
    prose: "pine trees" answers "bare pine trunks", and "a child's doll"
    answers nothing at all.
    """
    said = {stem(w) for w in WORD.findall((frame or "").lower())}
    out = []
    for subject in seen.subjects:
        words = [stem(w) for w in WORD.findall(subject.lower()) if len(w) > 2]
        if words and not (set(words) & said):
            out.append(subject)
    return out


def stem(word: str) -> str:
    """Enough of a word to match its plural: the reader says "pine trees" where
    the shot says "bare pine trunks ... among the pines", and those agree."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    # ONLY the plural s. Stripping "es" turned "pines" into "pin" and "trees"
    # into "tre", so a picture of pine trees read as unasked-for in a shot
    # about pines.
    if word.endswith("s") and len(word) > 3:
        return word[:-1]
    return word


def people_fault(seen: Seen, planned: int, crowd: bool) -> bool:
    """More faces than the shot casts, or a crowd made of one repeated person."""
    # Lookalikes are counted AMONG the people. ep10 shot 13 read 0 people and
    # 2 lookalikes: two tripods the book asks for, not a copied person.
    if min(seen.lookalikes, seen.people):
        return True
    return not crowd and seen.people > planned

BEARDS = ("beard", "moustache", "mustache", "whiskers", "goatee", "stubble")
"""Facial hair a reader may name. A cast row that says clean-shaven and a
picture that shows a moustache are two different men, and the take that
follows the picture carries the wrong face into the cut."""

CLEAN = re.compile(r"\bclean[- ]shaven\b", re.I)


def contradictions(seen: Seen, physical: str) -> list[str]:
    """What the picture shows that the cast row rules out.

    MEASURED on ep07: the reader named a moustache on the narrator in six
    panels and his row reads "a lean clean-shaven man of thirty-five".
    Nothing in this pipeline compared the two.
    """
    out = []
    said = " ".join(seen.subjects).lower()
    if CLEAN.search(physical or "") and (hair := [b for b in BEARDS if b in said]):
        out.append(f"{hair[0]} on a clean-shaven character")
    return out


def banned_subject(seen: Seen, banned) -> list[str]:
    """Subjects an episode has said must never appear -- the doll's list.

    A WHOLE WORD. MEASURED: the reader said "carafe" on three panels of a
    dining room and a substring test reported a CAR in each of them.
    """
    said = " ".join(seen.subjects).lower()
    # BY STEM: "mountains", "cliffs" and "dolls" passed a list that bans the
    # singulars (VLM-gate audit, 2026-09-23).
    words = {stem(w) for w in WORD.findall(said)}
    return [b for b in (banned or ())
            if (want := {stem(w) for w in WORD.findall(b.lower())}) and want <= words]


def faults(seen: Seen, frame: str, planned: int, crowd: bool,
           flat: bool, night: bool, banned=(), physical: str = "",
           size: str = "", extras: int = 0) -> list[str]:
    """Every way this picture disagrees with the shot that asked for it.

    `frame` is kept for the caller's own reporting; it is NOT used to decide
    whether a detail belongs, because shot prose is a composition and not an
    inventory, and judging against it failed 27 of 27.
    """
    out = []
    if forbidden_landform(seen, flat):
        out.append(f"landform {seen.landform!r}: this place is flat")
    if strangers := banned_subject(seen, banned):
        out.append(f"banned from this book: {', '.join(strangers)}")
    out += contradictions(seen, physical)
    # who may be here is DECLARED: faces + extras, or the setup's crowd. The
    # one prose exemption left is an INSERT on something worn -- a collar stud
    # at a throat holds a person by necessity -- and it reads whole words now.
    worn = not planned and size == "insert" and worn_by_someone(frame)
    if people_fault(seen, planned + extras, crowd or worn):
        out.append(f"{seen.people} figure(s) for {planned + extras} declared ({planned} cast + "
                   f"{extras} extras), {seen.lookalikes} of them copies of another")
    if missing_cast(seen, planned, size, frame):
        out.append(f"{seen.people} figure(s) for {planned} named: someone the shot casts is missing")
    if seen.text and not lettering_expected(frame, size):
        out.append("text or lettering in the picture")
    # AN INTERIOR HAS NO HOUR TO READ. A lamplit dining room came back 'day'
    # and was called a night fault; the reader cannot see the sky from inside.
    if night and seen.landform != "indoors" and not reads_as_night(seen):
        out.append(f"the hour reads {seen.hour!r} and the shot is at night")
    return out


def missing_cast(seen: "Seen", planned: int, size: str, frame: str) -> bool:
    """Fewer people than the shot NAMES. Only too many used to fail: ep09's
    two-person tea panel read 0 and passed. An insert or a back view the plan
    asks for may hold fewer faces."""
    from studio.panel_dq import back_view
    return seen.people < planned and size != "insert" and not back_view(frame)


def truthy(value) -> bool:
    """bool("false") is True: the reader's "false" as a string read as lettering."""
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1")
    return bool(value)


def subject_list(value) -> list[str]:
    """A subjects STRING was iterated into single letters, which silently blinded
    the beard, banned and hair checks."""
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return [str(s).strip() for s in (value or [])]


def salvage(text: str):
    """A reply cut off inside `subjects`, the LAST key: the five judged fields are
    already complete, so the list is closed at its last whole item. ep09 T21 read
    'unread: no JSON' at seed 6 and failed on that alone (VLM-gate audit)."""
    import json
    start, key = text.find("{"), text.find('"subjects"')
    if start < 0 or key < 0:
        return None
    body = text[start:]
    cut = body.rfind('",')
    head = body[:cut + 1] if cut > body.find('"subjects"') else body[:body.find("[", body.find('"subjects"')) + 1]
    try:
        return json.loads(head + "]}")
    except json.JSONDecodeError:
        return None


class Unreadable(ValueError):
    """The reader said something this vocabulary cannot hold.

    IT RAISES, IT DOES NOT DEFAULT. The first version returned an empty `Seen`
    when the parse failed, and every panel of ep07 came back 'flat, 0 people,
    night' -- a gate that silently passes everything.
    """


REQUIRED = ("landform", "people", "lookalikes", "text", "hour")


def parse(said: str) -> Seen:
    """The reader's answer, however the workflow wrapped it.

    `image_qwen3vl_caption` returns a JSON ARRAY whose one element is a STRING
    of JSON, so the object has to be unwrapped once before it will load.
    """
    import json

    got = _loads(said)
    if isinstance(got, list) and got:
        got = _loads(got[0]) if isinstance(got[0], str) else got[0]
    if not isinstance(got, dict):
        raise Unreadable(f"no object in {said[:80]!r}")
    # A MISSING FIELD IS AN UNREADABLE ANSWER, never a default: no "people"
    # read as 0 people, no "hour" as night, no "text" as clean -- a malformed
    # answer passed as a clean picture (audit 2026-09-22).
    if absent := [k for k in REQUIRED if k not in got]:
        raise Unreadable(f"the reader's answer has no {', '.join(absent)}")
    try:
        return Seen(
            landform=str(got["landform"]).lower().strip(),
            people=int(got["people"] or 0),
            lookalikes=int(got["lookalikes"] or 0),
            text=truthy(got["text"]),
            hour=str(got["hour"]).lower().strip(),
            subjects=subject_list(got.get("subjects")),
        )
    except (TypeError, ValueError) as bad:
        raise Unreadable(str(bad)) from bad


def _loads(text: str):
    import json
    import re as _re

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    found = _re.search(r"\{.*\}", text, _re.S)
    if not found:
        if (saved := salvage(text)) is not None:
            return saved
        raise Unreadable(f"no JSON in {text[:80]!r}")
    try:
        return json.loads(found.group(0))
    except json.JSONDecodeError as bad:
        raise Unreadable(str(bad)) from bad

WORN = re.compile(
    r"\b(?:throat|collar|lapel|cuffs?|sleeves?|shoulders?|"
    r"hands?|wrists?|fingers?|face|cheeks?|jaw|mouth|eyes|hair|boots?|foot|feet)\b",
    re.I)
"""WHOLE WORDS (audit 2026-09-22): without boundaries "surface" was a face,
"chair" was hair and "footpath" a foot, and a match stood the people check
down."""
"""Parts of a person, and the things worn on them. An INSERT naming one of
these holds a figure by necessity: ep07's shot 20 is a burst collar stud at a
man's throat and it is cast for nobody. The other direction of the same rule
is `storyboard_grid.whole_subject`: a horse's head cannot exist on its own."""


def worn_by_someone(frame: str) -> bool:
    """Does this shot's prose put the subject ON a person?"""
    return bool(WORN.search(frame or ""))

PRINTED = re.compile(
    r"\b(?:newspapers?|papers?|pages?|placards?|posters?|signboards?|boards?|signs?|"
    r"timetables?|bookstalls?|letters?|telegrams?|books?|labels?|tickets?|headlines?)\b",
    re.I)
"""WHOLE WORDS: "boot print" is not a page, and with a boundary "cupboard" is no
longer a board. Without boundaries "papered wall" was paper."""

LETTERING_SIZES = ("insert", "close", "extreme_close", "medium_close")


def lettering_expected(frame: str, size: str) -> bool:
    """Is type EXPECTED in this picture -- because the printed thing is its
    subject, seen close enough to read?

    A printed noun anywhere in the prose used to excuse lettering anywhere in
    the picture: five ep07 dining-room wides say "papered wall" and the gate
    never looked at them, in the room that had a lettered engraving. A poster
    on the far wall of a wide is set dressing, not a page to read."""
    return size in LETTERING_SIZES and bool(PRINTED.search(frame or ""))
"""Things that carry words because that is what they are. ep08's shot 6 is an
insert on the front page of an evening paper and the lettering check called
it a fault; a page without type is not a page."""


def prints_words(frame: str) -> bool:
    return bool(PRINTED.search(frame or ""))


# ---- the rules live with the book, not in the runners -----------------------

def flat_place(book, location: str) -> bool:
    """Does this place's own row say it is flat? A row that does not say is
    not assumed flat: a hill called flat fails every panel of the hill."""
    from pathlib import Path
    import json
    if not location:
        return False
    path = Path(book) / "analysis" / "locations" / f"{location}.json"
    if not path.exists():
        return False
    return json.loads(path.read_text(encoding="utf-8")).get("landform") == "flat"


def banned_subjects(book) -> tuple:
    """Subjects this book never shows, from analysis/dq_rules.json. The two
    runners each kept their own list and they drifted: the take checker still
    banned "car", so a railway carriage failed (audit 2026-09-22, item 7)."""
    from pathlib import Path
    import json
    path = Path(book) / "analysis" / "dq_rules.json"
    if not path.exists():
        return ()
    return tuple(json.loads(path.read_text(encoding="utf-8")).get("banned_subjects", ()))
