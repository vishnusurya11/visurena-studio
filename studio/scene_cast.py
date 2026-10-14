"""Who is in a scene, shot by shot -- the cast a picture must show and stage.

OWNER 2026-10-14 (Jekyll ep01 HEL): "the first shot doesn't have the actual
characters in the scene, so in the second shot the character magically appears
... Every shot needs to have all characters involved in the references."

A SCENE is a run of consecutive shots on one setup: the same place at the same
hour, cut without leaving it.  Whoever is in the picture anywhere in a scene is
present from its first shot, unless a shot marks his arrival (`Shot.enters`);
once present he stays until a shot marks his leaving (`Shot.exits`).  A wide or
full shot frames the whole place, so it shows everyone present (advised, not
refused: no field says where a wide points); a medium or a close-up may single
one person out.  What a picture STAGES is what it holds (`in_frame`), at every
size -- a wide no longer draws its people from words (grids.py, 2026-10-14).

Pure functions over duck-typed shots (`faces`, `cuts`, `frame`, `at_rest`, `end`,
`size`, `setup`, `motion`, `enters`, `exits`); `names` is a {token: entity_id}
map such as `plan_gates.names_from_refs`."""
from __future__ import annotations

import re

WHOLE_PLACE = ("wide", "full")
"""Sizes that frame the whole place: every present person is in them."""

PICTURE_FIELDS = ("frame", "at_rest", "end")
"""The words that say what is IN the picture.  `camera` says where the camera
stands ("from Holmes's chair") and `motion` what moves; neither puts a man in."""

SIZE_RANK = {"extreme_close": 7, "close": 6, "medium_close": 5, "medium": 4,
             "full": 3, "wide": 2, "insert": 1}
"""How much of a face a size shows: the closer the face, the more its sheet binds."""

ARRIVAL = re.compile(
    r"\b(?:enters?|entering|arriv\w*|comes?|coming|emerg\w*|appears?|rounds?|"
    r"(?:steps?|walks?|runs?|strides?|hurr(?:y|ies)|stumps?|drives?|rides?)\s+"
    r"(?:in|into|up|out|through|toward|towards|down|across)|in from|"
    r"into (?:the )?(?:frame|picture|view|shot))\b", re.I)
"""A motion that shows a person arriving: what makes a marked entrance true."""

LEAVING = re.compile(
    r"\b(?:leav\w*|exits?|departs?|(?:walks?|goes?|runs?|strides?|hurr(?:y|ies)|drives?|rides?)\s+"
    r"(?:away|off|out)|out of (?:the )?(?:frame|picture|view|shot))\b", re.I)
"""A motion that shows a person leaving: what makes a marked exit true."""


def _unique(people) -> list[str]:
    return list(dict.fromkeys(p for p in people if p))


COMMON = frozenset({"unnamed", "first", "person", "people", "man", "men", "woman", "women", "boy", "girl",
                    "child", "wife", "husband", "brother", "sister", "miss", "mrs", "lord", "lady",
                    "police", "inspector", "sergeant", "captain", "retired", "marine", "newspaper",
                    "young", "old", "incident", "driver", "waiter", "housemaid", "housekeeper"})
"""Row tokens that are common nouns, never a name: the WotW narrator's id claims
"first" and "person", and "Each person in the picture" would put him in a shot."""


def named(text: str, names: dict[str, str]) -> list[str]:
    """Whoever the words name by a proper-name token of his row, in the map's order."""
    return _unique(who for token, who in names.items()
                   if token.lower() not in COMMON and re.search(rf"\b{re.escape(token)}\b", text or "", re.I))


def in_frame(shot, names: dict[str, str] | None = None) -> list[str]:
    """Everyone this shot's picture holds: its faces, its cuts' faces, and whoever
    its picture words name -- an over-the-shoulder holds the shoulder's owner."""
    cuts = list(getattr(shot, "cuts", None) or [])
    people = list(getattr(shot, "faces", None) or []) + [w for c in cuts for w in getattr(c, "faces", None) or []]
    words = " ".join(str(getattr(seg, f, "") or "") for seg in [shot] + cuts for f in PICTURE_FIELDS)
    return _unique(people + named(words, names or {}))


def scenes(shots: list) -> list[list]:
    """Runs of consecutive shots (in index order) on one setup."""
    runs: list[list] = []
    for s in sorted(shots, key=lambda s: s.index):
        if runs and runs[-1][-1].setup == s.setup:
            runs[-1].append(s)
        else:
            runs.append([s])
    return runs


def visibility(who: str, shots: list) -> tuple[int, int]:
    """(closest size his face READS at, shots he is a face in) across these shots."""
    mine = [s for s in shots if who in in_frame(s)]
    return max((SIZE_RANK.get(str(s.size), 0) for s in mine), default=0), len(mine)


def pick(people: list[str], shots: list, slots: int) -> list[str]:
    """At most `slots` people for the reference ceiling: the closest readable faces
    first, then the most panels; kept in first-appearance order."""
    if len(people) <= slots:
        return list(people)
    ranked = sorted(people, key=lambda w: (-visibility(w, shots)[0], -visibility(w, shots)[1], people.index(w)))
    keep = set(ranked[:max(slots, 0)])
    return [w for w in people if w in keep]
