"""G-WHO: two figures of one frame that each read as the same cast member (owner 2026-10-28, a hard check).

Jekyll ep05 shipped Utterson twice (T22: his back and his face beside Guest) and Poole drawn in
Utterson's grey hair and black coat (T02).  Every gate passed it: the faces were too small for a
face vector, the figure count matched the panel's, and the twin ask wants the same face AND the
same dress.  A viewer tells two men apart by hair, facial hair and coat colour, so the reader LISTS
those per figure (never judges) and code resolves each figure to the one staged cast member it
agrees with while contradicting every other.  The reader calls a bowler a top hat (ep05, 6 of 6
frames), so headwear is not read.  A figure that agrees with two members, or with none, resolves
to nobody: the check fires only on a figure the rows place beyond doubt."""
from __future__ import annotations

import re

from studio import look_table as lt
from studio import panel_content as pc

ASK_VERSION = "2"
ASK = (
    "List EVERY person you can see in this picture, whether facing the camera, in profile, or seen "
    "from behind. Output strict JSON: {\"figures\": [ ... ]}, one object per person with keys:\n"
    "\"headwear\": one of none, bowler, top_hat, felt_hat, cap, bonnet, helmet, hood, other_hat, not_visible.\n"
    "\"hair\": the hair colour, one of grey, white, black, brown, blond, red, bald, not_visible.\n"
    "\"facial_hair\": one of none, beard, moustache, sideburns, stubble, not_visible.\n"
    "\"coat\": the colour of the outer coat or jacket, one of black, grey, brown, green, blue, red, "
    "white, other, not_visible.\n"
    f"(who ask v{ASK_VERSION})")

SEEN_HAIR = {"black": "dark", "brown": "dark", "blond": "fair"}
"""The reader's hair words onto look_table's HAIR_FAMILY keys."""
COATS = (("green", r"green"), ("blue", r"blue|navy"), ("red", r"red|crimson|scarlet|maroon"),
         ("brown", r"brown|tan|fawn|buff|camel|tweed"), ("white", r"white"),
         ("dark", r"black|dark|charcoal|grey|gray|sable"))
COAT_FAMILY = {"black": "dark", "grey": "dark"}
"""A black and a grey coat are one family at night; the reader names either."""
UNSEEN = {"", "not_visible", "other"}
KEYS = ("hair_colour", "facial_hair", "coat")


def coat_of(top: str) -> str:
    """The coat colour family the look's top layer names first (its first clause is the coat:
    'black overcoat with six white buttons' is a dark coat)."""
    first = (top or "").split(",")[0]
    found = [(m.start(), c) for c, pat in COATS if (m := re.search(rf"\b(?:{pat})", first, re.I))]
    return min(found)[1] if found else ""


def staged_marks(markers: dict, top: str) -> dict:
    """One staged look as the who-read compares it, every value in its family ('' = unsaid)."""
    hair = (markers or {}).get("hair_colour", "")
    return {"hair_colour": lt.family("hair_colour", hair) if hair else "",
            "facial_hair": lt.family("facial_hair", (markers or {}).get("facial_hair", "")), "coat": coat_of(top)}


def seen_of(fig: dict) -> dict:
    """One listed figure in the same families; an unseen value stays ''."""
    hair, face, coat = (str(fig.get(k, "") or "") for k in ("hair", "facial_hair", "coat"))
    return {"hair_colour": "" if hair in UNSEEN else lt.family("hair_colour", SEEN_HAIR.get(hair, hair)),
            "facial_hair": "" if face in UNSEEN else lt.family("facial_hair", face),
            "coat": "" if coat in UNSEEN else COAT_FAMILY.get(coat, coat)}


def clashes(fig: dict, marks: dict) -> int:
    """How many keys the figure shows that the look says otherwise."""
    seen = seen_of(fig)
    return sum(1 for k in KEYS if seen[k] and marks.get(k) and seen[k] != marks[k])


def resolve(fig: dict, staged: dict) -> str | None:
    """The one staged member this figure agrees with while clashing with every other, else None."""
    agree = [who for who, marks in staged.items() if not clashes(fig, marks)]
    return agree[0] if len(agree) == 1 else None


def fault(figures: list[dict], staged: dict) -> str | None:
    """The 'who: ...' line when two or more figures resolve to one cast member."""
    who = [resolve(f, staged) for f in figures]
    twice = sorted({w for w in who if w and who.count(w) >= 2})
    if not twice:
        return None
    return f"who: {who.count(twice[0])} figures read as {twice[0]!r} by hair, facial hair and coat; the shot casts one"


def parse(said: str) -> list[dict]:
    """The reader's figure list; an answer with no `figures` list is Unreadable, never empty."""
    got = pc._loads(said)
    if isinstance(got, list) and got:
        got = pc._loads(got[0]) if isinstance(got[0], str) else got[0]
    if not isinstance(got, dict) or not isinstance(got.get("figures"), list):
        raise pc.Unreadable(f"no figures list in {str(said)[:80]!r}")
    return [f for f in got["figures"] if isinstance(f, dict)]


def readable(said: str) -> bool:
    """Whether `parse` can read this answer; the vlm cache keeps only these."""
    try:
        parse(said)
    except pc.Unreadable:
        return False
    return True


def applies(planned: int, size: str, people: int) -> bool:
    """Two or more cast at a face size, two or more figures seen: the twin ask's guard, for two cast."""
    return planned >= 2 and pc.twin_applies(planned, size, people)
