"""Deriving a trailer's dramatic structure from a screenplay.

The previous selector spread eleven scenes evenly across the story and cycled
each three times.  That is a sampler, not a trailer: it had no protagonist
logic, no turn, and it answered its own logline halfway through.

Everything here is derived from screenplay.json alone -- no model, no spend --
and every function is a pure function of that data so it can be tested against
fixtures.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

CONNECTIVES = (" until ", " whose ", " before ", " only to ", " and discovers ",
               " to reveal ", " while ", " when he ", " when she ")
"""A logline's hinge.  Everything AFTER it is the thing the trailer sells by
withholding, so it marks the forbidden zone."""

STOPWORDS = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "at", "by",
             "for", "with", "his", "her", "their", "its", "that", "this", "is",
             "are", "was", "were", "be", "been", "from", "as", "it", "he", "she"}


def people_in(scene: dict) -> set[str]:
    """Everyone present or speaking in a scene."""
    return set(scene.get("cast") or []) | set(scene.get("speaking") or [])


GENERIC_TOKENS = {"group", "unnamed", "the", "and", "two", "three", "four", "mr",
                  "mrs", "miss", "sir", "man", "men", "woman", "women"}
"""Parts of a cast id that name no one: a count, a title, a class."""


def name_tokens(person: str) -> list[str]:
    """The words of a cast id that could name them in prose, in order."""
    return [t for t in re.split(r"[\s_]+", person.lower())
            if len(t) >= 3 and t not in GENERIC_TOKENS]


def consume_full_names(prose: str, cast: list[str], tokens: dict) -> tuple[str, set[str]]:
    """Whole names credited and struck: 'Lucy Ferrier' is one person, and
    her surname there is not also her father."""
    named: set[str] = set()
    for person in cast:
        full = " ".join(tokens[person])
        if full and f" {full} " in f" {prose} ":
            named.add(person)
            prose = f" {prose} ".replace(f" {full} ", "  ").strip()
    return prose, named


def subjects_of(text: str, cast) -> list[str]:
    """Who a shot's own prose puts in frame, from the scene's cast.

    A surname two people share is credited to whichever of them the prose
    does not name by their own token -- 'Lucy looking up at Ferrier' is her
    and her father -- and to all of them when it names neither.  The scene
    cast is the universe: a name from elsewhere in the book binds nothing.
    """
    cast = sorted(cast)
    tokens = {p: name_tokens(p) for p in cast}
    prose, named = consume_full_names(" ".join(re.findall(r"[A-Za-z]+", text.lower())),
                                      cast, tokens)
    words = set(prose.split())
    owners = Counter(t for ts in tokens.values() for t in ts)
    named |= {p for p in cast if {t for t in tokens[p] if owners[t] == 1} & words}
    shared = {p for p in cast if {t for t in tokens[p] if owners[t] > 1} & words}
    return sorted(named | shared)


def lead_of(scenes: list[dict]) -> str | None:
    """The character present in the most scenes -- the story's centre."""
    counts: dict[str, int] = {}
    for scene in scenes:
        for who in people_in(scene):
            counts[who] = counts.get(who, 0) + 1
    return max(counts, key=lambda w: (counts[w], w)) if counts else None


def figure_of(scenes: list[dict], lead: str | None) -> str | None:
    """The opposition: whoever owns the most story mass OUTSIDE the lead's view.

    Not "the second most present character" -- that is usually a companion.
    The antagonist is the one the protagonist keeps missing.
    """
    shadow: dict[str, int] = {}
    for scene in scenes:
        present = people_in(scene)
        if lead in present:
            continue
        for who in present:
            if who != lead:
                shadow[who] = shadow.get(who, 0) + 1
    return max(shadow, key=lambda w: (shadow[w], w)) if shadow else None


def turn_of(scenes: list[dict], lead: str | None) -> dict | None:
    """The first scene of the longest run in which the lead is absent.

    For an adaptation the turn is not a plot reveal -- it is the moment the
    narration changes hands.  Run on these two books it lands on Part II of
    A Study in Scarlet and on Henry Jekyll's Full Statement, which are exactly
    where each book breaks.
    """
    best_len = best_start = current = 0
    start = 0
    for index, scene in enumerate(scenes):
        if lead in people_in(scene):
            current = 0
            continue
        if current == 0:
            start = index
        current += 1
        if current > best_len:
            best_len, best_start = current, start
    return scenes[best_start] if best_len else None


def forbidden_words(logline: str, scenes: list[dict],
                    max_share: float = 0.30) -> set[str]:
    """Content words from the logline's final clause that actually discriminate.

    A logline reads "When <A>, <B> until <C>".  <A> and <B> are the promise;
    <C> is the payoff, and a trailer that shows <C> has answered its own
    question.  Both shipped trailers did exactly that, in both cases with the
    forbidden material arriving as a spoken line.

    Rarity matters as much as membership.  Taking the tail's words verbatim put
    "jekyll" in the forbidden set, which appears in 39 of 50 scenes and would
    ban the book -- so a word present in more than `max_share` of scenes is
    dropped as too common to mean anything.
    """
    lowered = logline.lower()
    tail = ""
    for connective in CONNECTIVES:
        if connective in lowered:
            tail = lowered.split(connective, 1)[1]
            break
    if not tail:
        return set()
    candidates = {w for w in re.findall(r"[a-z']{4,}", tail) if w not in STOPWORDS}
    texts = [" ".join(e.get("text", "") for e in sc.get("elements", [])).lower()
             for sc in scenes]
    limit = max_share * max(len(texts), 1)
    return {w for w in candidates if sum(w in t for t in texts) <= limit}


def scene_is_forbidden(scene: dict, forbidden: set[str], threshold: int = 2) -> bool:
    """True when a scene depicts the logline's withheld payoff."""
    if not forbidden:
        return False
    text = " ".join(e.get("text", "") for e in scene.get("elements", [])).lower()
    return sum(1 for word in forbidden if word in text) >= threshold


def action_elements(scenes: list[dict], min_words: int = 4) -> list[dict]:
    """Every action line in the book, as an individual shot candidate.

    THIS is the fix for repetition.  The scene is not the trailer's atom -- a
    scene is ninety seconds of story and a trailer shot is two.  Selecting
    scenes gave 11 candidates for 33 shots, so every setup repeated three
    times; selecting ELEMENTS gives 268 candidates for the same 33 shots.
    """
    found: list[dict] = []
    for scene in scenes:
        for index, element in enumerate(scene.get("elements", [])):
            if element.get("kind") != "action":
                continue
            text = (element.get("text") or "").strip()
            if len(text.split()) < min_words:
                continue
            found.append({"scene": scene["number"], "index": index, "text": text,
                          "location_id": scene.get("slug", {}).get("location_id"),
                          "int_ext": scene.get("slug", {}).get("int_ext"),
                          "time": scene.get("slug", {}).get("time"),
                          "cast": list(people_in(scene))})
    return found


def resolution_scenes(scenes: list[dict], lead: str | None, figure: str | None,
                      tail_share: float = 0.15) -> set[int]:
    """Scene numbers that give the story away, by STRUCTURE not by vocabulary.

    Matching the logline's words against scene text does not work: a logline is
    abstract ("whose solution exposes a decades-old revenge") and action lines
    are concrete ("Hope releases the bridle"), so the words never meet.  Two
    structural facts identify the payoff instead, and both are exact:

    * the story's last stretch IS the resolution, in any book;
    * the scene where the lead and the opposition finally stand in the same
      room is the answer to the question the whole trailer is asking.

    These may still be SHOWN -- an image gives nothing away on its own -- but
    only briefly and never carrying a line.  You may show it; you may not
    caption it.
    """
    if not scenes:
        return set()
    cutoff = len(scenes) - max(1, int(len(scenes) * tail_share))
    banned = {sc["number"] for sc in scenes[cutoff:]}
    if lead and figure:
        # The LAST time they stand together, not every time.  In Jekyll and
        # Hyde the two meet early and often -- that is the premise, not the
        # payoff -- and banning every meeting would ban the first third.
        meetings = [sc["number"] for sc in scenes if {lead, figure} <= people_in(sc)]
        if meetings:
            banned.add(meetings[-1])
    return banned


CONCRETE = ("door", "hand", "face", "window", "light", "candle", "lamp", "knife",
            "blood", "letter", "paper", "key", "glass", "fire", "street", "stair",
            "mirror", "coat", "cab", "horse", "gun", "pistol", "body", "eyes",
            "watch", "ring", "box", "bottle", "table", "floor", "wall", "smoke")
ABSTRACT = ("realis", "understand", "consider", "remember", "decide", "wonder",
            "seem", "appear to", "later", "meanwhile", "we learn", "it becomes")


def element_value(element: dict, lead: str | None, figure: str | None) -> float:
    """How much trailer one action line is worth.

    Concreteness dominates.  A shot is a photograph, so a line naming a thing a
    camera can point at is worth more than one describing a state of mind --
    "A great blue anchor marks the back of the man's hand" is a shot;
    "Holmes considers the problem" is not.
    """
    text = element["text"].lower()
    score = 0.0
    score += 2.0 * sum(word in text for word in CONCRETE)
    score -= 3.0 * sum(word in text for word in ABSTRACT)
    if lead and lead in element["cast"]:
        score += 1.5
    if figure and figure in element["cast"]:
        score += 1.2
    words = len(text.split())
    score += 1.5 if 6 <= words <= 22 else -1.0
    if element.get("int_ext") == "EXT":
        score += 0.5
    return score


def select_setups(scenes: list[dict], refs: set[str], count: int,
                  iconicity: dict | None = None,
                  max_share: float = 0.35) -> list[dict]:
    """`count` DISTINCT authored setups, ranked by value and spread by scene.

    The rule this replaces took one element per scene and capped each location
    at two.  For A Study in Scarlet that made NINE the arithmetic maximum --
    twelve eligible scenes over six locations -- and thirty-one shots were then
    cut out of those nine, so 23% of the delivered picture was frames already
    on screen.  Two of them were pixel-identical nineteen seconds apart.

    Selection now draws on `scene["shots"]`: 411 framings the screenplay itself
    authored, each with an element span, which no trailer code had ever read.
    """
    iconicity = iconicity or {}
    pool = [c for c in authored_setups(scenes)
            if is_bindable(c, refs) and photographable_setup(c)]
    if not pool:
        return []
    first, last = appearance_scenes(scenes)
    ranked = sorted(pool, key=lambda c: (-setup_value(c, first, last, refs,
                                                      iconicity),
                                         c["scene"], c["index"]))
    return _take_spread(ranked, scene_quota(pool, count), count, max_share)


def _take_spread(ranked: list[dict], quota: dict[int, int], count: int,
                 max_share: float) -> list[dict]:
    """Best first, but never more than a scene's quota or a place's share."""
    from collections import Counter

    taken: list[dict] = []
    per_scene: Counter = Counter()
    per_place: Counter = Counter()
    ceiling = max(1, int(count * max_share))
    for candidate in ranked:
        if len(taken) >= count:
            break
        if per_scene[candidate["scene"]] >= quota.get(candidate["scene"], 1):
            continue
        if per_place[candidate["location_id"]] >= ceiling:
            continue
        taken.append(candidate)
        per_scene[candidate["scene"]] += 1
        per_place[candidate["location_id"]] += 1
    return _backfill(taken, ranked, count, per_place, ceiling)


def _backfill(taken: list[dict], ranked: list[dict], count: int,
              per_place, ceiling: int) -> list[dict]:
    """Quotas underfill.  The old selector returned nine for a request of
    eighteen and printed a success line; take the next best globally instead."""
    chosen = {(c["scene"], c["index"]) for c in taken}
    for candidate in ranked:
        if len(taken) >= count:
            break
        key = (candidate["scene"], candidate["index"])
        if key in chosen or per_place[candidate["location_id"]] >= ceiling:
            continue
        taken.append(candidate)
        chosen.add(key)
        per_place[candidate["location_id"]] += 1
    return taken


def is_bindable(candidate: dict, refs: set[str]) -> bool:
    """A location plate exists for this setup's place.

    Worth naming, because it is invisible from inside a score: seven of
    thirteen locations have no plate, which deletes every Utah setup -- Lucy,
    the farm, the riders, the alkali plain.  No ranking can rescue a place with
    no picture to bind to; that is a reference gap, not a selection one.
    """
    return f"loc-{candidate['location_id']}" in refs


def photographable_setup(candidate: dict) -> bool:
    """Is there a thing here a camera could point at.

    Gated on the setup prose AND the action it covers: setup prose is camera
    language, and the objects live in the lines underneath it.
    """
    return bool(IMAGE_GATE.search(action_text(candidate)))


def scene_quota(pool: list[dict], count: int) -> dict[int, int]:
    """How many setups each scene may contribute, by its share of the pool.

    A quota lets one ninety-second scene carry five setups -- the body, the
    ring, the writing on the wall, the objects on the stair, the cab -- which is
    what a scene that long is worth.  The rule it replaces took exactly one and
    moved on, which is how the most-remembered image in the book was
    unreachable.
    """
    from collections import Counter

    available = Counter(c["scene"] for c in pool)
    total = sum(available.values()) or 1
    return {scene: min(max(1, round(count * n / total)), n)
            for scene, n in available.items()}


IMAGE_GATE = re.compile(
    r"\b(door|hand|face|window|light|candle|lamp|knife|blood|letter|paper|key"
    r"|glass|fire|street|stair|mirror|coat|cab|horse|gun|pistol|body|eye|eyes"
    r"|watch|ring|box|bottle|table|floor|wall|smoke|flame|match|dust|lens|wall"
    r"|room|road|sky|water|snow|rain|fog|boot|hat|chair|bed|book|knife|axe"
    r"|stick|salt|phial|jar|tube|card|note|sign|lock|gate|bell|clock|corpse)\b",
    re.I)
"""Is there a THING here at all -- a gate, not a score.

Counting matches was measured at 1.10x lift once paragraph length is
controlled, and below 1.0 in two of four books: it was ranking by LENGTH, since
longer lines contain more nouns.  The cost was concrete -- "The flame reveals
RACHE, scrawled in red across the plaster", the title image of A Study in
Scarlet, scored 3.5 and ranked 165 of 268, because `match`, `flame`, `plaster`
and `scrawled` were not on the hand-written list.  A word list can gate; it
cannot rank."""


def distinctiveness(text: str, corpus_counts: dict[str, int], total: int) -> float:
    """How unusual this line's vocabulary is for THIS book.

    An iconic image is an anomaly -- the only word written on a wall in a
    wordless book, the only white whale.  Rarity is not iconicity on its own
    (it likes "the commissionaire clicks his heels"), but it is a real signal
    where a fixed noun list is none, and it needs no model.
    """
    import math
    words = {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOPWORDS}
    if not words:
        return 0.0
    rarest = sorted(math.log(total / (1 + corpus_counts.get(w, 0))) for w in words)
    return sum(rarest[-3:]) / 3.0


def corpus_frequency(scenes: list[dict]) -> tuple[dict[str, int], int]:
    """How often each word appears across the book's action lines."""
    counts: dict[str, int] = {}
    total = 0
    for scene in scenes:
        for element in scene.get("elements", []):
            if element.get("kind") != "action":
                continue
            total += 1
            for word in {w for w in re.findall(r"[a-z]{4,}",
                                               (element.get("text") or "").lower())}:
                counts[word] = counts.get(word, 0) + 1
    return counts, max(total, 1)


def quotable_elements(scenes: list[dict], min_words: int = 3) -> list[dict]:
    """Dialogue lines as SHOT candidates, not just as speech.

    `action_elements()` filters on kind == "action", which made the most
    recognisable beat in A Study in Scarlet structurally unreachable: "You have
    been in Afghanistan, I perceive." can never be selected, because it is
    dialogue and the image channel never looks at dialogue.

    Recognition is bimodal -- readers remember aphorisms, illustrators draw
    tableaux, and they are rarely the same moment.  Sampling one mode loses
    half the material.
    """
    found: list[dict] = []
    for scene in scenes:
        for index, element in enumerate(scene.get("elements", [])):
            if element.get("kind") != "dialogue" or not element.get("character"):
                continue
            text = (element.get("text") or "").strip()
            if len(text.split()) < min_words:
                continue
            found.append({"scene": scene["number"], "index": index, "text": text,
                          "speaker": element.get("character"),
                          "provenance": element.get("provenance"),
                          "emotion": element.get("emotion"),
                          "location_id": scene.get("slug", {}).get("location_id"),
                          "cast": list(people_in(scene))})
    return found


def deduplicate(elements: list[dict], head: int = 60) -> list[dict]:
    """Drop near-identical lines that live in DIFFERENT scenes.

    One-element-per-scene does not catch these.  Real pairs from the corpus:
    Jekyll sc 28 and sc 32 both read "measured heaps of white salt wait on
    glass saucers"; Metamorphosis sc 7 and sc 8 both "Grete lays the violin
    across her mother's lap".  A trailer built from them shows one frame twice
    and calls it two shots.
    """
    seen: set[str] = set()
    kept: list[dict] = []
    for element in elements:
        key = re.sub(r"[^a-z]", "", element["text"].lower())[:head]
        if key in seen:
            continue
        seen.add(key)
        kept.append(element)
    return kept


def load_iconicity(book: "Path") -> dict[int, float]:
    """Per-scene memorability, from evidence outside the text.

    Text statistics cannot reach this.  Lexical concreteness measures paragraph
    length; rarity likes "the commissionaire clicks his heels".  What makes a
    moment iconic is its reproduction history -- whether illustrators drew it,
    whether readers quote it, whether the culture kept it -- and none of that is
    in the book.

    So it arrives as DATA, gathered once per book and cached, never recomputed
    per run.  Shape:

        {"scenes": {"5": {"score": 0.93, "why": "RACHE by matchlight",
                          "sources": ["illustration index", "reader reviews"]}}}

    A missing file returns {} and selection falls back to the text signals.
    That fallback is deliberate: a book nobody has written about should still
    get a trailer, just a less well-aimed one.
    """
    import json as _json
    path = book / "analysis" / "iconicity.json"
    if not path.exists():
        return {}
    doc = _json.loads(path.read_text(encoding="utf-8"))
    return {int(k): float(v.get("score", 0.0))
            for k, v in doc.get("scenes", {}).items()}


def with_iconicity(elements: list[dict], iconicity: dict[int, float],
                   weight: float = 6.0) -> list[dict]:
    """Attach the cached memorability of each element's scene.

    Weighted heavily on purpose.  When we know a moment is one readers carry,
    that should outrank every text feature -- those were measured at roughly
    noise, and this is the only signal with evidence behind it.
    """
    for element in elements:
        element["iconicity"] = iconicity.get(element["scene"], 0.0) * weight
    return elements


def principal_of(scene_cast: list[str], refs: set[str], lead: str | None,
                 figure: str | None) -> str | None:
    """The one character this shot is about, chosen from WHO IS THERE.

    The rule it replaces read `[lead, figure] + scene_cast` and took the first
    with a sheet, so the lead won every beat by construction and the scene's own
    cast was decoration.  A Study in Scarlet shipped Holmes in all nine beats,
    Utah included -- a book he leaves for four chapters.

    Preference among people actually present is fine and is not the same thing:
    the lead carries a scene when he is IN it, the opposition carries the scenes
    he is absent from, and that alternation is the structure the trailer is
    supposed to be showing.
    """
    present = [c for c in scene_cast if f"char-{c}" in refs]
    if not present:
        return None
    return min(present, key=lambda c: (c != lead, c != figure, c))


# ---------------------------------------------------------------- authored setups

CAMERA_WORDS = {"Locked", "Dolly", "Handheld", "Rack", "Pan", "Tilt", "Close",
                "Medium", "Wide", "Insert", "Extreme", "Two", "The", "He", "She",
                "His", "Her", "It", "They", "Inside", "Outside", "Early", "Later"}
"""Words that appear capitalised in setup prose without naming anything."""


def authored_setups(scenes: list[dict]):
    """Every framing the screenplay already wrote, as a shot candidate.

    411 of them for A Study in Scarlet, against 268 raw action lines -- and each
    is a camera position with an element span rather than a sentence that
    happens to contain a photographable noun.  `scene["shots"]` has been in the
    file since the screenplay stage and no trailer code had ever read it.

    The selector it replaces took at most ONE element per scene and capped each
    location at two, which made nine setups the arithmetic maximum for this
    book.  Thirty-one shots were then cut out of those nine.
    """
    for scene in scenes:
        for shot in scene.get("shots") or []:
            setup = {"scene": scene["number"], "index": shot["index"],
                     "setup": shot["setup"], "term": shot.get("term", "locked-off"),
                     "location_id": scene["slug"]["location_id"],
                     "duration_s": scene.get("duration_s", 0.0),
                     "cast": people_in(scene),
                     "covers": covered_elements(scene, shot)}
            yield setup | {"subjects": subjects_of(action_text(setup), setup["cast"])}


def covered_elements(scene: dict, shot: dict) -> list[dict]:
    """The elements one authored setup puts on screen.

    This join is what makes dialogue reachable from the image channel:
    `action_elements` filtered `kind == "action"`, so "You have been in
    Afghanistan, I perceive." could never be chosen as a picture.
    """
    start = shot.get("covers_start", 0)
    end = shot.get("covers_end", start)
    return scene.get("elements", [])[start:end + 1]


def action_text(candidate: dict) -> str:
    """Setup prose plus the action it covers.

    Gating on the setup prose alone drops most candidates, because setup prose
    is camera language and the objects live in the lines it covers.
    """
    covered = " ".join(e.get("text", "") for e in candidate.get("covers", [])
                       if e.get("kind") == "action")
    return f"{candidate.get('setup', '')} {covered}".strip()


def is_emphasised(candidate: dict) -> bool:
    """The adapter spent a camera move here.

    43 of 411 setups carry one, and read as a highlight reel: the dolly toward
    Watson as Holmes names Afghanistan, the aneurism, the handcuffs, the tilt to
    the buzzards over Lucy, the two pills.  It is the only signal in the file
    whose author was deciding EMPHASIS rather than coverage.
    """
    return candidate.get("term", "locked-off") != "locked-off"


def _density(candidate: dict, mark: str) -> float:
    covered = candidate.get("covers") or []
    if not covered:
        return 0.0
    return sum(e.get("provenance") == mark for e in covered) / len(covered)


def verbatim_density(candidate: dict) -> float:
    """Share of covered elements the adaptation refused to paraphrase.

    259 of 541 elements are verbatim Doyle.  That is a per-line memorability
    judgment already made and cached; a ratio rather than a count, so it cannot
    become a proxy for length.
    """
    return _density(candidate, "verbatim")


def invented_density(candidate: dict) -> float:
    """Share invented for the adaptation.  A reader cannot remember these."""
    return _density(candidate, "invented")


def named_things(text: str, cap: int = 3) -> int:
    """Proper nouns and shouted words, minus the camera vocabulary.

    Catches the icons that carry no camera move -- RACHE, Drebber, Lucy, Baker
    Street.  Capped so a long setup cannot outrank a sharp one.
    """
    found = set(re.findall(r"\b([A-Z][a-z]{2,}|[A-Z]{4,})\b", text)) - CAMERA_WORDS
    return min(len(found), cap)


def shouted_things(text: str, cap: int = 2) -> int:
    """Words the screenplay set in capitals.

    Screenplay convention capitalises what the audience must notice.  In this
    book that is thirteen tokens across 268 action lines -- RACHE, RING, CLICK,
    THROBBING, MURDER, HOPE -- which is a list of its beats written by the
    adapter and never read by anything.  Rare enough to be a signal and
    deliberate enough to trust; capped so volume cannot substitute for weight.
    """
    import re as _re
    found = {w for w in _re.findall(r'[A-Z]{4,}', text)} - CAMERA_WORDS
    return min(len(found), cap)


def appearance_scenes(scenes: list[dict]) -> tuple[dict, dict]:
    """First and last scene number for every character."""
    first: dict[str, int] = {}
    last: dict[str, int] = {}
    for scene in scenes:
        for who in people_in(scene):
            first.setdefault(who, scene["number"])
            last[who] = scene["number"]
    return first, last


def is_entrance_or_exit(candidate: dict, first: dict, last: dict,
                        refs: set[str]) -> bool:
    """Someone the trailer can bind arrives or leaves in this scene.

    Entrances and exits are what a viewer can follow.  The previous cut had no
    face the eye could track because nothing in selection knew who was new.
    """
    return any(f"char-{who}" in refs
               and candidate["scene"] in (first.get(who), last.get(who))
               for who in candidate.get("cast", []))


def bound_convergence(candidate: dict, refs: set[str], cap: int = 3) -> float:
    """How much of the frame can actually be identity-bound, 0..1."""
    bound = sum(1 for who in candidate.get("cast", []) if f"char-{who}" in refs)
    return min(bound, cap) / cap


def setup_value(candidate: dict, first: dict, last: dict, refs: set[str],
                iconicity: dict) -> float:
    """How much trailer one authored setup is worth.

    Replaces `distinctiveness`, which averaged the three highest IDF values in a
    line and SATURATED: 75 of 268 lines tied at the ceiling, so the sort fell
    back to document order.  RACHE lost to wet grass because wet grass appears
    earlier in the JSON.  A metric that ties a quarter of its corpus at the top
    is not ranking anything.
    """
    text = action_text(candidate)
    return (3.0 * is_emphasised(candidate)
            + 2.5 * verbatim_density(candidate)
            + 1.0 * named_things(text)
            + 2.0 * shouted_things(text)
            + 1.5 * is_entrance_or_exit(candidate, first, last, refs)
            + 1.0 * bound_convergence(candidate, refs)
            - 1.5 * invented_density(candidate)
            + 6.0 * iconicity.get(candidate["scene"], 0.0))


# ---------------------------------------------------------------- line pools

REFUSED = "refused"
SIBLING_FLOOR = 0.85
QUOTED = re.compile("[“\"]([^“”\"]+)[”\"]")
"""Double marks only: a curly single quote is an apostrophe in most of the
corpus, and treating it as a mark cut "I’ll" in half."""
SENTENCE_END = re.compile(r"(?<=[.!?…])(?<!Mr\.)(?<!Dr\.)(?<!Mrs\.)(?<!St\.)\s+")
POOL_ORDER = ("screenplay", "quotes", "source", "narration")


def sentences(text: str, min_words: int = 2) -> list[str]:
    """Split on sentence ends: the famous clause is often the child of a
    dull parent, and a slot holds one sentence."""
    return [s.strip() for s in SENTENCE_END.split(text.strip())
            if len(s.split()) >= min_words]


def _line(text: str, speaker: str | None, pool: str, scene: int | None) -> dict:
    return {"text": text, "speaker": speaker, "pool": pool, "scene": scene}


def screenplay_pool(scenes: list[dict]) -> list[dict]:
    """Every spoken sentence of the screenplay, with its scene number."""
    out: list[dict] = []
    for scene in scenes:
        for element in scene.get("elements", []):
            if element.get("kind") != "dialogue" or not element.get("character"):
                continue
            out += [_line(s, element["character"], "screenplay", scene["number"])
                    for s in sentences(element.get("text") or "")]
    return out


def character_quotes(book_dir: Path) -> dict[str, list[str]]:
    """The analysis stage's judged quotes per character, cleaned to speech."""
    from studio.quotes import clean
    found: dict[str, list[str]] = {}
    for path in sorted((Path(book_dir) / "analysis" / "characters").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        spoken = [clean(q.get("quote", "")) for q in doc.get("quotes", [])]
        found[doc.get("id", path.stem)] = [s for s in spoken if s]
    return found


def quote_pool(quotes: dict[str, list[str]]) -> list[dict]:
    return [_line(s, who, "quotes", None)
            for who, spoken in quotes.items() for raw in spoken for s in sentences(raw)]


def alias_index(characters: list[dict]) -> dict:
    """Registry names, aliases and unambiguous surnames -> id."""
    from studio.names import build_index, build_surname_index
    return {**build_index(characters), **build_surname_index(characters)}


def known_speech(scenes: list[dict], quotes: dict[str, list[str]]) -> list[tuple[set, str]]:
    """What we already know somebody said, as word sets: screenplay dialogue
    and the character quotes, each whole and sentence by sentence."""
    from studio.iconicity import tokens
    known: list[tuple[set, str]] = []
    for line in screenplay_pool(scenes) + quote_pool(quotes):
        known.append((tokens(line["text"]), line["speaker"]))
    for scene in scenes:
        for element in scene.get("elements", []):
            if element.get("kind") == "dialogue" and element.get("character"):
                known.append((tokens(element.get("text") or ""), element["character"]))
    return known


def sibling_speaker(spoken: list[str], known: list[tuple[set, str]],
                    floor: float = SIBLING_FLOOR) -> str | None:
    """The speaker of any sentence in the paragraph we already know a line
    of: that is how "the scarlet thread" reaches Holmes."""
    from studio.iconicity import tokens
    for sentence in spoken:
        mine = tokens(sentence)
        if not mine:
            continue
        for theirs, speaker in known:
            if theirs and len(mine & theirs) / len(mine | theirs) >= floor:
                return speaker
    return None


def tag_speakers(paragraph: str, index: dict) -> set[str]:
    """Every character the paragraph's own speech tag names.

    The tag is the prose OUTSIDE the quotation marks, and only when it carries
    a speech verb.  A one-word alias must appear capitalised there ("Stamford",
    "I"), so "me" in "he said to me" does not claim the addressee.
    """
    from studio.names import run_starts_at
    from studio.quotes import _SAID
    outside = QUOTED.sub(" ", paragraph)
    if not re.search(rf"\b(?:{_SAID})\b", outside, re.I):
        return set()
    words = re.sub(r"[^a-z0-9 ]+", "", outside.lower()).split()
    proper = {p.lower() for p in re.findall(r"\b[A-Z][a-z]*\b", outside)}
    found = set()
    for alias, who in index.items():
        parts = alias.split()
        if (len(parts) >= 2 and run_starts_at(words, parts)) or \
                (len(parts) == 1 and alias in proper):
            found.add(who)
    return found


def attribute(paragraph: str, spoken: list[str], index: dict,
              known: list[tuple[set, str]]) -> str | None:
    """Who said the quoted speech: both rules must agree where both fire.

    A tag naming two people, or a tag and a sibling that disagree, is
    REFUSED -- the paragraph yields no line.  Neither firing is a card.
    """
    by_sibling = sibling_speaker(spoken, known)
    by_tag = tag_speakers(paragraph, index)
    if len(by_tag) > 1:
        return REFUSED
    tagged = next(iter(by_tag), None)
    if by_sibling and tagged and by_sibling != tagged:
        return REFUSED
    return by_sibling or tagged


def chapters(book_dir: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((Path(book_dir) / "source" / "chapters").glob("ch_*.json"))]


def source_pool(book_dir: Path, index: dict, known: list[tuple[set, str]]) -> list[dict]:
    """Quoted speech in the source text, attributed or a card."""
    out: list[dict] = []
    for chapter in chapters(book_dir):
        for paragraph in chapter.get("paragraphs", []):
            spans = QUOTED.findall(paragraph.get("text") or "")
            spoken = [s for span in spans for s in sentences(span)]
            if not spoken:
                continue
            speaker = attribute(paragraph["text"], spoken, index, known)
            if speaker == REFUSED:
                continue
            out += [_line(s, speaker, "source", None) for s in spoken]
    return out


def narration_pool(book_dir: Path, min_words: int = 4) -> list[dict]:
    """Sentences of paragraphs with no speech in them.  A card, never a
    voice: the narrator has a card and reads nothing here."""
    out: list[dict] = []
    for chapter in chapters(book_dir):
        for paragraph in chapter.get("paragraphs", []):
            text = paragraph.get("text") or ""
            if QUOTED.search(text):
                continue
            out += [_line(s, None, "narration", None) for s in sentences(text, min_words)]
    return out


def dedupe_lines(lines: list[dict], head: int = 60) -> list[dict]:
    """First pool wins: a screenplay line keeps its scene, the same words
    found again in the source add nothing."""
    seen: set[str] = set()
    kept: list[dict] = []
    for line in sorted(lines, key=lambda l: POOL_ORDER.index(l["pool"])):
        key = re.sub(r"[^a-z]", "", line["text"].lower())[:head]
        if not key or key in seen:
            continue
        seen.add(key)
        kept.append(line)
    return kept


def line_pools(book_dir: Path, narrator: str | None = None) -> list[dict]:
    """The four pools a trailer line can come from, merged and deduplicated.

    Wikiquote lists 19 quotations for A Study in Scarlet and four survive into
    the screenplay; the title sentence is in the source text and nowhere else.
    Narration joins only for a book told by a character (StorySpec.narrator).
    """
    book = Path(book_dir)
    screenplay = json.loads((book / "screenplay/feature/screenplay.json")
                            .read_text(encoding="utf-8"))
    registry = json.loads((book / "analysis/registry.json").read_text(encoding="utf-8"))
    quotes = character_quotes(book)
    known = known_speech(screenplay["scenes"], quotes)
    pools = screenplay_pool(screenplay["scenes"]) + quote_pool(quotes)
    pools += source_pool(book, alias_index(registry["characters"]), known)
    if narrator and narrator != "omniscient":
        pools += narration_pool(book)
    return dedupe_lines(pools)


# ---------------------------------------------------------------- the spine

MOVEMENTS = ("M1", "M2", "M3")
"""World & hook, problem & turn, threat & climax.  The order IS the trailer:
`trailer_order.one_each` plays the beats in the order it is handed them, so a
list that is not ordered by movement is a playlist, which is what run 10
shipped -- the killer's face at 8.75 s and the handcuffs at 17 s."""

QUOTA_SHARES = {"M1": 0.25, "M2": 0.45, "M3": 0.30}
"""How much of the picture each movement is worth.  Shares, not counts, so
twelve shots and forty-one shots get the same shape."""

LATE_SHARE = 0.75
"""R4: the answer may not be photographed before three quarters of the cut."""

PLACE_SHARE = 0.30
"""R6: no location past this share of the shots.  Run 10 spent 39% of its
seconds in 221B Baker Street and never photographed London at all."""

PRINCIPAL_SHARE = 0.45
"""R10: no one face owns the trailer.  Run 10 gave Holmes 26 of 51 shots and
nine of his twelve setups were the same three-quarter deerstalker face with
an orange lamp behind it -- the ensemble the ref sheets paid for never
arrived, and Lucy, Drebber and Stangerson were never cast at all."""


def late_floor(count: int) -> int:
    """The first shot index an identity-revealing frame may occupy."""
    return int(LATE_SHARE * count)


def introduction_end(scenes: list[dict]) -> int:
    """The last scene of the lead's introduction: the prefix that holds
    nobody the first scene did not already have.

    A trailer's first movement is the world before the story happens to it,
    and the screenplay marks that boundary by who WALKS IN.  In Scarlet the
    bar and the hospital are Watson, Holmes and Stamford; scene 3 brings
    Lestrade, and Lestrade is the problem arriving.
    """
    if not scenes:
        return 0
    opening = people_in(scenes[0])
    end = scenes[0]["number"]
    for scene in scenes[1:]:
        if not people_in(scene) <= opening:
            break
        end = scene["number"]
    return end


def movement_bounds(scenes: list[dict], lead: str | None) -> tuple[int, int]:
    """(last scene of M1, last scene of M2), from the story's own two marks.

    The second mark is `turn_of` -- where the narration changes hands.  The
    first is the end of the lead's introduction.  Where the two would collide
    they are pulled apart, because a movement with no scene in it cannot be
    ordered and its quota would have nowhere to spend.
    """
    if not scenes:
        return (0, 0)
    first, last = scenes[0]["number"], scenes[-1]["number"]
    turn = turn_of(scenes, lead)
    m2_end = turn["number"] if turn else (first + last) // 2
    m2_end = max(first + 1, min(m2_end, last - 1))
    m1_end = max(first, min(introduction_end(scenes), m2_end - 1))
    return (m1_end, m2_end)


def movement_of(scene_number: int, bounds: tuple[int, int]) -> str:
    """Which movement a scene plays in."""
    if scene_number <= bounds[0]:
        return "M1"
    return "M2" if scene_number <= bounds[1] else "M3"


def movement_quota(count: int) -> dict[str, int]:
    """How many shots each movement gets, always summing to `count`."""
    if count <= 0:
        return {m: 0 for m in MOVEMENTS}
    exact = {m: count * QUOTA_SHARES[m] for m in MOVEMENTS}
    quota = {m: int(exact[m]) for m in MOVEMENTS}
    if count >= len(MOVEMENTS):
        quota = {m: max(1, n) for m, n in quota.items()}
    return _settle(quota, exact, count)


def _settle(quota: dict, exact: dict, count: int) -> dict:
    """Hand the remainder to the movement the rounding shortchanged most."""
    while sum(quota.values()) > count:
        quota[max(MOVEMENTS, key=lambda m: quota[m] - exact[m])] -= 1
    while sum(quota.values()) < count:
        quota[max(MOVEMENTS, key=lambda m: exact[m] - quota[m])] += 1
    return quota


def identity_scenes(scenes: list[dict], lead: str | None,
                    figure: str | None) -> set[int]:
    """Scenes whose picture answers the question the trailer is selling.

    Not a vocabulary match and not the story's tail: the answer to "who did
    it" is the FIGURE standing where the LEAD stands -- the same room, or the
    same company.  Both halves are already in the screenplay, so this needs
    no model and no list of spoiler words.

    In Scarlet it names the police-station chamber, 3 Lauriston Gardens by
    night and Halliday's Hotel, and leaves Utah alone: Utah is the figure
    before anyone is looking for him, and it is most of the second half.
    """
    if not lead or not figure:
        return set()
    places, people = set(), set()
    for scene in scenes:
        if lead in people_in(scene):
            places.add(scene.get("slug", {}).get("location_id"))
            people |= people_in(scene)
    people -= {figure}
    return {sc["number"] for sc in scenes if figure in people_in(sc)
            and (sc.get("slug", {}).get("location_id") in places
                 or bool(people_in(sc) & people))}


def _ranked_pool(scenes: list[dict], refs: set[str], iconicity: dict,
                 banned: set[int]) -> list[dict]:
    """Every bindable, photographable setup outside the banned scenes, best
    first -- the ranking `select_setups` uses, before the spine reorders it."""
    pool = [c for c in authored_setups(scenes) if c["scene"] not in banned
            and is_bindable(c, refs) and photographable_setup(c)]
    first, last = appearance_scenes(scenes)
    return sorted(pool, key=lambda c: (-setup_value(c, first, last, refs, iconicity),
                                       c["scene"], c["index"]))


def _fill(ranked: list[dict], want: int, max_share: float = 0.5) -> list[dict]:
    """The best `want` of one movement, spread over its scenes and places."""
    if want <= 0 or not ranked:
        return []
    return _take_spread(ranked, scene_quota(ranked, want), want, max_share)


def _in_scene_order(chosen: list[dict]) -> list[dict]:
    return sorted(chosen, key=lambda c: (c["scene"], c["index"]))


def _third_movement(ranked: list[dict], reveal: set[int], want: int,
                    room: int) -> list[dict]:
    """The climax: what may be shown, then -- last of all -- the answer.

    The reveal is the point of the third movement and the reason R4 exists,
    so it is spent, but only into the slots after `late_floor`.
    """
    answers = [c for c in ranked if c["scene"] in reveal]
    rest = [c for c in ranked if c["scene"] not in reveal]
    late = _in_scene_order(_fill(answers, min(room, want)))
    return _in_scene_order(_fill(rest, want - len(late))) + late


def face_of(candidate: dict, refs: set[str], lead: str | None,
            figure: str | None) -> str | None:
    """The character a setup would be bound to, before it becomes a beat.

    Exactly what `build_plan.beat_of` will decide: the setup's OWN subjects,
    the scene cast only where the prose named nobody.  A quota that counted
    faces differently from the thing that casts them counts the wrong faces.
    """
    return principal_of(sorted(candidate.get("subjects", candidate.get("cast") or [])),
                        refs, lead, figure)


def _swappable(candidate: dict, instead_of: dict, taken: set, bounds: tuple[int, int],
               reveal: set[int]) -> bool:
    """A setup that could stand in this slot: unused, the same movement, and
    the same side of the reveal line -- so a quota can never reorder the
    story or move the answer earlier."""
    if (candidate["scene"], candidate["index"]) in taken:
        return False
    if movement_of(candidate["scene"], bounds) != movement_of(instead_of["scene"], bounds):
        return False
    return (candidate["scene"] in reveal) == (instead_of["scene"] in reveal)


def _another_face(ranked: list[dict], instead_of: dict, taken: set, refs: set[str],
                  lead: str | None, figure: str | None, bounds: tuple[int, int],
                  reveal: set[int], seen, places, caps: tuple[int, int]) -> dict | None:
    """The best unused setup of the same movement showing somebody else, in a
    place the trailer has not already spent (R6)."""
    faces_cap, place_cap = caps
    for candidate in ranked:
        if not _swappable(candidate, instead_of, taken, bounds, reveal):
            continue
        if places[candidate["location_id"]] >= place_cap:
            continue
        face = face_of(candidate, refs, lead, figure)
        if face is not None and seen[face] < faces_cap:
            return candidate
    return None


def _relief(ranked: list[dict], candidate: dict, books: dict, refs: set[str],
            lead: str | None, figure: str | None, bounds: tuple[int, int],
            reveal: set[int], caps: tuple[int, int]) -> dict | None:
    """A setup to stand in for one whose face is over its share.

    A face over its share is the louder fault -- run 10 was half Holmes, nine
    of his twelve setups the same lamp-lit three-quarter face -- so where no
    other face is free inside R6's place ceiling, the ceiling gives by one
    rather than the trailer showing one man.
    """
    wider = (caps[0], caps[1] + 1)
    return (_another_face(ranked, candidate, books["taken"], refs, lead, figure, bounds,
                          reveal, books["seen"], books["places"], caps)
            or _another_face(ranked, candidate, books["taken"], refs, lead, figure, bounds,
                             reveal, books["seen"], books["places"], wider))


def _book_swap(books: dict, out_face: str | None, out_place: str, swap: dict,
               in_face: str | None) -> None:
    """Move one setup's face, place and identity off the books and another on."""
    books["seen"][out_face] -= 1
    books["places"][out_place] -= 1
    books["seen"][in_face] += 1
    books["places"][swap["location_id"]] += 1
    books["taken"].add((swap["scene"], swap["index"]))


def _cap_faces(chosen: list[dict], ranked: list[dict], refs: set[str], lead: str | None,
               figure: str | None, bounds: tuple[int, int], reveal: set[int]) -> list[dict]:
    """R10: no principal past `PRINCIPAL_SHARE` of the shots.

    The EARLIEST appearances of a face are kept -- they are the ones that
    introduce him -- and the ones past the ceiling are swapped for a setup of
    the same movement showing somebody else.  Where the book offers no other
    face the setup stays: a quota may not invent an actor.

    Faces count UP as the walk proceeds, so the earliest appearances survive;
    places are counted for the WHOLE list from the start, because a swap must
    not push a location past its share of a trailer it cannot see yet.
    """
    caps = (max(1, int(PRINCIPAL_SHARE * len(chosen))),
            max(1, int(PLACE_SHARE * len(chosen))))
    books = {"taken": {(c["scene"], c["index"]) for c in chosen}, "seen": Counter(),
             "places": Counter(c["location_id"] for c in chosen)}
    out: list[dict] = []
    for candidate in chosen:
        face = face_of(candidate, refs, lead, figure)
        books["seen"][face] += 1
        swap = (None if face is None or books["seen"][face] <= caps[0] else
                _relief(ranked, candidate, books, refs, lead, figure, bounds, reveal, caps))
        if swap is not None:
            _book_swap(books, face, candidate["location_id"], swap,
                       face_of(swap, refs, lead, figure))
        out.append(swap if swap is not None else candidate)
    return out


def _regroup(chosen: list[dict], bounds: tuple[int, int], reveal: set[int]) -> list[dict]:
    """Movement order, scene order inside it, the answer last of all."""
    grouped: list[dict] = []
    for movement in MOVEMENTS:
        here = [c for c in chosen if movement_of(c["scene"], bounds) == movement]
        answers = [c for c in here if c["scene"] in reveal]
        grouped += _in_scene_order([c for c in here if c["scene"] not in reveal]) + answers
    return grouped


def select_by_movement(scenes: list[dict], refs: set[str], count: int,
                       iconicity: dict | None = None, lead: str | None = None,
                       figure: str | None = None, banned=()) -> list[dict]:
    """`count` setups in TRAILER order: M1 -> M2 -> M3, scene order inside.

    This is the change run 10 needed most.  Selection was a score ranking and
    ordering was `best_scatter`, whose only objective is "do not bring an
    image back soon" -- it has no notion of before and after, so the trailer
    had none either.  Here the movement decides the slot, the scene decides
    the place inside it, and the identity-revealing frames are held back to
    the last quarter.
    """
    banned, reveal = set(banned), identity_scenes(scenes, lead, figure)
    bounds = movement_bounds(scenes, lead)
    quota, ranked = movement_quota(count), _ranked_pool(scenes, refs, iconicity or {}, banned)
    room = count - late_floor(count)
    chosen: list[dict] = []
    for movement in MOVEMENTS:
        here = [c for c in ranked if movement_of(c["scene"], bounds) == movement]
        if movement == "M3":
            chosen += _third_movement(here, reveal, quota[movement], room)
        else:
            chosen += _in_scene_order(_fill([c for c in here if c["scene"] not in reveal],
                                            quota[movement]))
    filled = _top_up(chosen, ranked, bounds, reveal, count)
    return _regroup(_cap_faces(filled, ranked, refs, lead, figure, bounds, reveal),
                    bounds, reveal)


def _spare(ranked: list[dict], taken: set, reveal: set[int], places,
           ceiling: int, want: int) -> list[dict]:
    """The best unused setups that do not push a location past `ceiling`."""
    found: list[dict] = []
    for candidate in ranked:
        if len(found) >= want:
            break
        if (candidate["scene"], candidate["index"]) in taken or candidate["scene"] in reveal:
            continue
        if places[candidate["location_id"]] >= ceiling:
            continue
        places[candidate["location_id"]] += 1
        taken.add((candidate["scene"], candidate["index"]))
        found.append(candidate)
    return found


def _top_up(chosen: list[dict], ranked: list[dict], bounds: tuple[int, int],
            reveal: set[int], count: int) -> list[dict]:
    """A quota a movement could not fill is spent in the OTHER movements,
    each in its own place -- never by lengthening the trailer's answer.

    Two passes.  The first holds R6's ceiling on how much of the trailer one
    place may own; the second lets it slip by ONE rather than hand a rendered
    take back, because run 10's other lesson is that an unspent take is a
    shot the trailer does not have.
    """
    if len(chosen) >= count:
        return chosen[:count]
    taken = {(c["scene"], c["index"]) for c in chosen}
    places = Counter(c["location_id"] for c in chosen)
    ceiling = max(1, int(PLACE_SHARE * count))
    spare = _spare(ranked, taken, reveal, places, ceiling, count - len(chosen))
    if len(chosen) + len(spare) < count:
        spare += _spare(ranked, taken, reveal, places, ceiling + 1,
                        count - len(chosen) - len(spare))
    return _regroup(chosen + spare, bounds, reveal)
