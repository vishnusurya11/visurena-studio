"""Plan gates that read a shot against its CELL -- what the panel will hold.

Every rule here cost ep09 GPU renders to discover (2026-09-23), and each was
prototyped by the plan-gate audit against ep01-ep09's plan.json before it
came in (docs in the tests):

G-AIM     a camera head names a thing as the move's start or aim; at_rest must
          hold it. ep09 shots 14 ("ruin"), 15 ("broken tiles") and 18
          ("railway bridge") repeated their fault on fresh seeds.
G-HAT     one first picture wears a hat and holds it off or in hand. ep09
          shots 11 and 20 drew two hats.
G-PLACE   a frame names a major landmark the setup's place lacks. ep09 shot 18
          "under the brick railway bridge" on the lawn.
G-ANCHOR  a sideways truck on a medium-or-closer person anchored to scenery.
          ep09 T02, owner: "he walked with the fence ... ai slop, dq missed it".
          Fires on 7 shots of ep05-09, 5 of them visible faults (T02, T10, T20;
          ep07 T13, ep08 T14); silent on the walker ep08 T05.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio.episode_spec import NOISE, Episode, Shot, head_noun, named_at_rest

# ---- G-AIM -----------------------------------------------------------------------
INTRO = re.compile(r"\b(?:until|to|from|on|toward|towards|across|at|past)\s+(?:the|his|her|their)\s+", re.I)
ALREADY = re.compile(r"\balready in the (?:picture|frame)\b", re.I)
STARTS = re.compile(r"\b(?:tilts?|pans?|swings?)\b[^;]*?\bfrom (?:the |his |her |their )([\w' -]{1,60}?)"
                    r"(?=\s+(?:to|across|along|up|down|until|with)\b|,|$)", re.I)
ENDS = re.compile(r"\b(?:tilts?|pans?)\b[^;]*?\bfrom [^;]*?\b(?:across )?to (?:the |his |her |their )([\w' -]{1,60}?)"
                  r"(?=\s+(?:already|until|travelling)\b|,|$)", re.I)
PERSON = re.compile(r"^(?:man|men|woman|women|boy|boys|girl|girls|child|children|figure|figures|rider|riders|"
                    r"soldier|soldiers|people|face|faces|head|eyes|him|her|them)$", re.I)
SAME = {"face": ("face", "head"), "head": ("head", "face"), "man": ("man", "men"), "men": ("men", "man"),
        "woman": ("woman", "women"), "women": ("women", "woman")}


def aimed_at(head: str) -> list[tuple[str, str]]:
    """(role, phrase) for every noun phrase the camera head starts on or aims at.
    'rises from X' names the camera's floor, not a target, so it is not read."""
    out = []
    for m in ALREADY.finditer(head):
        before = head[:m.start()]
        cut = list(INTRO.finditer(before))
        out.append(("already", before[cut[-1].end():].strip() if cut else before.strip()))
    out += [("from", m.group(1)) for m in STARTS.finditer(head)]
    out += [("to", m.group(1)) for m in ENDS.finditer(head) if not ALREADY.search(head[m.end():m.end() + 30])]
    return out


def heads(phrase: str) -> list[str]:
    """The phrase's head noun, and the noun before 'of' ('heap of fragments' -> heap too)."""
    out = [head_noun(phrase)]
    if (m := re.search(r"([A-Za-z']+)\s+of\b", phrase)) and m.group(1).lower() not in NOISE:
        out.append(m.group(1).lower())
    return [h for h in out if h]


def in_cell(phrase: str, shot: Shot) -> bool:
    """A thing must stand in at_rest; a person may stand in the frame sentence instead.
    Only at_rest predicts the panel: 14's ruin, 15's tiles and 18's bridge were all
    in the frame sentence, and the drawer did not draw them."""
    for h in heads(phrase):
        where = shot.at_rest + (" " + shot.frame if PERSON.match(h) else "")
        if any(named_at_rest(w, where) for w in SAME.get(h, (h,))):
            return True
    return False


def aim_faults(episode: Episode) -> list[str]:
    out = []
    for s in episode.shots:
        for role, phrase in aimed_at(s.motion.split(";")[0]):
            if not in_cell(phrase, s):
                out.append(f"G-AIM shot {s.index}: the camera {'starts on' if role == 'from' else 'aims at'} "
                           f"{phrase!r}, which the cell (at_rest) does not hold; a move toward what is not "
                           f"drawn invents it. Name it in at_rest, or aim at what at_rest holds")
    return out


# ---- G-HAT -------------------------------------------------------------------------
HEADWEAR = (r"hat|boater|bowler|cap|toque|bonnet|helmet|topper|pillbox|deerstalker|busby|shako|"
            r"billycock|wideawake|panama|kepi")
OFF = re.compile(
    rf"\b(?:(?:his|her|its|a|the|own)\s+)?(?:[\w-]+\s+){{0,3}}?({HEADWEAR})s?\b\s*(?:\w+\s+){{0,3}}?"
    rf"(?:in (?:his|her|one|both|the other) hands?|in (?:his|her) fist|off\b(?!\s+(?:his|her)\s+(?:\w+\s+)?(?:forehead|brow|face|eyes))"
    rf"|held\b|against (?:his|her) chest|under (?:his|her) arm|by (?:its|the) brim|set on the|lying)"
    rf"|\b(?:holding|holds|carrying|carries|turning|doffs?)\s+(?:his|her|the|a)\s+(?:own\s+)?(?:[\w-]+\s+){{0,3}}?({HEADWEAR})s?\b(?!\s+on\b)",
    re.I)
BARE = re.compile(r"\b(?:bareheaded|bare-headed|hatless|bare head)\b", re.I)
WORN = re.compile(rf"\b({HEADWEAR})s?\b", re.I)


def hat_clash(text: str) -> tuple[set, set]:
    """(worn, off) headwear nouns that name the same hat, in one first picture."""
    offs = {next(g for g in m.groups() if g).lower() for m in OFF.finditer(text)}
    worn = {m.group(1).lower() for m in WORN.finditer(OFF.sub(" ", text))}
    if not offs:
        return set(), offs
    same = {w for w in worn if w in offs or "hat" in offs or w == "hat"}
    return same, offs


def hat_faults(episode: Episode) -> tuple[list[str], list[str]]:
    """(hard, advisory). Hard: the same hat worn and off, and nothing says
    bareheaded. Advisory: the same, but the picture also says bareheaded."""
    hard, soft = [], []
    for s in episode.shots:
        text = f"{s.frame} {s.at_rest}"
        same, offs = hat_clash(text)
        if not same:
            continue
        line = (f"G-HAT shot {s.index}: {sorted(same)} is worn and also {sorted(offs)} off or in hand in one "
                f"first picture; the panel draws both. Tag the person without the hat and say 'bareheaded'")
        (soft if BARE.search(text) else hard).append(line)
    return hard, soft


# ---- G-PLACE -------------------------------------------------------------------------
MAJOR = ("bridge arch viaduct tower spire steeple church chapel college windmill station platform canal "
         "river railway embankment gasworks gasholder mast lighthouse pier cathedral castle mill barn "
         "pond lake summerhouse observatory").split()
KIN = {"bridge": {"arch", "viaduct"}, "arch": {"bridge", "viaduct"}, "viaduct": {"bridge", "arch"},
       "gasworks": {"gasholder"}, "gasholder": {"gasworks"}, "church": {"chapel", "spire", "steeple"},
       "railway": {"embankment", "station", "platform"}}
LANDMARK = re.compile(r"\b(" + "|".join(MAJOR) + r")(?:es|s)?\b", re.I)
NOT_DRAWN = re.compile(r"\b(?:like|as) an? [^,;.]*|\btoward(?:s)? the [^,;.]*", re.I)
"""A simile ('bright as a lighthouse reflector') or a direction ('toward the
railway') names no object in the picture."""


def landmarks(text: str) -> set[str]:
    return {m.group(1).lower() for m in LANDMARK.finditer(NOT_DRAWN.sub(" ", text or ""))}


def place_text(setup, pictures: dict[str, str]) -> str:
    """Everything the place is: its words, geometry, landmark, and the prompt of
    the picture it opens on."""
    drawn = pictures.get(f"{setup.location}/{setup.view}", "") if setup.view else ""
    return " ".join([setup.described, setup.geometry, setup.landmark, drawn])


def place_faults(episode: Episode, pictures: dict[str, str]) -> list[str]:
    out = []
    for s in episode.shots:
        have = landmarks(place_text(episode.setups[s.setup], pictures)) | landmarks(s.at_rest)
        missing = sorted(w for w in landmarks(s.frame) - have if not KIN.get(w, set()) & have)
        if missing:
            out.append(f"G-PLACE shot {s.index}: the frame names {missing}, which neither setup "
                       f"{s.setup!r} nor its picture nor the cell holds; the drawer drops it or invents it")
    return out


def pack_prompts(book: Path) -> dict[str, str]:
    """{'<location>/<view>': the prompt that drew it}, from refs/pack.jsonl."""
    out, pack = {}, Path(book) / "refs" / "pack.jsonl"
    for line in (pack.read_text(encoding="utf-8").splitlines() if pack.exists() else []):
        row = json.loads(line) if line.strip() else {}
        parts = Path(row.get("path", "")).parts
        if len(parts) == 4 and parts[1] == "locations":
            out[f"{parts[2]}/{Path(parts[3]).stem}"] = row.get("prompt", "")
    return out


# ---- G-ANCHOR --------------------------------------------------------------------------
TRUCK = re.compile(r"\b(?:tracks? sideways|truck|dolly sideways|crab)\b", re.I)
WITH_SUBJECT = re.compile(r"\bwith (?:him|her|them)\b|\bat (?:his|her|their) own pace\b|\balongside (?:him|her|them)\b"
                          r"|\bkeeping (?:him|her|them)\b", re.I)
ANCHOR = re.compile(
    r"\b(?:lean(?:s|ing|ed)?|rest(?:s|ing)?|sit(?:s|ting)?|seated|perched|kneel(?:s|ing)?|knelt|lying|lies|"
    r"crouch(?:es|ed|ing)?|squatting|propped|hooked|braced)\s+(?:\w+\s+){0,3}?(?:on|over|against|along|at|in|across)\b"
    r"|\b(?:hands?|forearms?|elbows?)\s+(?:\w+\s+){0,2}?(?:on|over) the\s+(?:\w+\s+){0,2}?"
    r"(?:counter|rail|fence|paling|table|wall|parapet|gate|sill|bar)\b"
    r"|\bstand(?:s|ing)?\s+(?:\w+\s+){0,2}?(?:at|behind) the\s+(?:\w+\s+){0,2}?(?:counter|rail|fence|paling|gate|table|bar)\b",
    re.I)
PEOPLE = re.compile(r"\b(?:man|men|woman|women|boys?|girls?|child(?:ren)?|people|soldiers?|figures?|he|she)\b", re.I)
CLOSE_ENOUGH = ("full", "medium", "medium_close", "close", "extreme_close")


def peopled(s: Shot) -> bool:
    return bool(s.faces or s.extras or PEOPLE.search(s.frame))


def anchored_truck(s: Shot) -> str:
    """The anchoring phrase when a sideways truck crosses a person held to scenery, else ''."""
    head = s.motion.split(";")[0]
    if s.size not in CLOSE_ENOUGH or not TRUCK.search(head) or WITH_SUBJECT.search(head) or not peopled(s):
        return ""
    hit = ANCHOR.search(f"{s.frame} {s.at_rest}")
    return hit.group(0) if hit else ""


def anchor_faults(episode: Episode) -> list[str]:
    return [f"G-ANCHOR shot {s.index}: a sideways truck on a {s.size} of a person {why!r}; H3 keeps the "
            f"person where the cell put them and slides the scenery through them (ep09 T02, the fence "
            f"through the neighbour). Push in, crane, or hold"
            for s in episode.shots if (why := anchored_truck(s))]


# ---- G-LAID ----------------------------------------------------------------------------
LAID = re.compile(r"\b(?:lying|lies|lay|laid|sprawled|prone|supine)\b", re.I)
SEEN_LAID = re.compile(r"\blooking down\b|\bfrom above\b|\boverhead\b|\bstraight down\b"
                       r"|\blevel with (?:his|her|their) (?:face|head|eyes)\b|\bon the ground\b", re.I)


def laid_unseen(s: Shot) -> bool:
    """A close on one person lying down whose camera neither looks down on the
    face nor lies level with it. ep10 shot 18 said "low over him"; the drawer
    stood the landlord up against the lane, and H3 turned the world round his
    face to lay him on the sand."""
    if s.size not in ("close", "medium_close", "extreme_close") or len(s.faces or []) != 1:
        return False
    return bool(LAID.search(f"{s.frame} {s.at_rest}")) and not SEEN_LAID.search(s.camera or "")


def laid_faults(episode: Episode) -> list[str]:
    return [f"G-LAID shot {s.index}: a {s.size} of a person lying down, and the camera {s.camera.split(',')[0]!r} "
            f"neither looks down on the face nor lies level with it; the drawer stands them up (ep10 T18). "
            f"Say 'above him looking down' or 'on the ground level with his face'"
            for s in episode.shots if laid_unseen(s)]


# ---- the verdict -------------------------------------------------------------------------

def faults(episode: Episode, pictures: dict[str, str]) -> list[str]:
    """Every cell reason this plan should not be drawn: hard."""
    return (aim_faults(episode) + hat_faults(episode)[0] + place_faults(episode, pictures)
            + anchor_faults(episode) + laid_faults(episode))


def advisories(episode: Episode) -> list[str]:
    return hat_faults(episode)[1]
