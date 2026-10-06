"""The plan cure table: every MECHANICAL battery fault repaired by template,
never by a WHOLE-PLAN writer call; one llm cure (studio/plan_llm_cures.py)
rewrites a single shot's position fields.

MEASURED (docs/audit/2026-10-01_plan_hours_debate.md): 97% of ep14-15's plan
hours were paid whole-plan rewrites refused by rules whose cures are template
arithmetic -- light directions, head fractions, pace words, catalog head
swaps, hold algebra, numbering remaps, registry filters, series pinning.  The
ep15 session executed every one of these by hand in seconds; this module is
that session, codified.  A fault with no cure here is CREATIVE (story,
coverage, invented content) and is the writer's -- one targeted call, never a
whole-plan rewrite.
"""
from __future__ import annotations

import re
from typing import Callable

from pydantic import BaseModel

# ---- the single repairs ----------------------------------------------------------

def renumber(doc: dict) -> dict:
    """Shots 0..n-1 in list order; lines' and beds' references remapped."""
    remap = {s["index"]: k for k, s in enumerate(doc.get("shots") or [])}
    for k, s in enumerate(doc.get("shots") or []):
        s["index"] = k
    for line in doc.get("lines") or []:
        if line.get("shot") in remap:
            line["shot"] = remap[line["shot"]]
    for bed in doc.get("beds") or []:
        if bed.get("from_shot") in remap:
            bed["from_shot"] = remap[bed["from_shot"]]
    return doc


LIGHT_SOURCES = re.compile(
    r"\b(lamps?|lamplight|gaslight|candles?|fire|firelight|hearth|lanterns?|windows?|"
    r"doorway|skylight|sun|sunlight|daylight|moon|moonlight|dawn|dusk|glow)\b", re.I)
DIRECTION_FOR = {
    "window": "through the {w} at the LEFT", "doorway": "through the {w} at the LEFT",
    "skylight": "through the {w} from above",
}


def has_light_direction(described: str) -> bool:
    from studio import house_style
    clause = house_style.lit_clause(described or "")
    return bool(house_style.source_of(clause)) and bool(
        house_style.DIRECTIONS.search(described or ""))


def light_directions(doc: dict) -> dict:
    """A setup whose `described` names no light source WITH a direction gets a
    terse clause built from its own words (G-LIGHT; the clause stays short so
    the style line keeps its 16-word cap -- ep15's long clauses fed L20)."""
    for name, s in (doc.get("setups") or {}).items():
        d = s.get("described") or ""
        if has_light_direction(d):
            continue
        found = LIGHT_SOURCES.search(d)
        w = (found.group(1).lower() if found else "daylight")
        if w in ("glow", "fire", "firelight", "hearth"):
            clause = " Low firelight from ahead, deep shadow."
        elif w in DIRECTION_FOR:
            clause = f" Grey daylight {DIRECTION_FOR[w].format(w=w)}, deep shadow."
        elif w in ("moon", "moonlight", "dusk"):
            clause = " Moonlight from the LEFT, black shadows."
        else:
            clause = " Raking grey daylight from the LEFT, deep shadow."
        s["described"] = d.rstrip() + clause
    return doc


FRACTION_OF = {"close": "half", "medium_close": "a third", "medium": "a quarter"}


def head_fractions(doc: dict) -> dict:
    """Every close-family at_rest names its head fraction (G-SIZE)."""
    from studio import picture_gates
    for s in doc.get("shots") or []:
        size = s.get("size") or ""
        if size in FRACTION_OF and not picture_gates.names_fraction(s.get("at_rest") or "", size):
            s["at_rest"] = (s.get("at_rest") or "").rstrip(". ") + \
                f", his head {FRACTION_OF[size]} of the frame's height."
    return doc


GAIT = re.compile(r"\b(walks?|walking|climbs?|climbing|rides?|riding|runs?|running|"
                  r"strides?|striding)\b(?![^.;]*\bpace\b)", re.I)


def pace_words(doc: dict) -> dict:
    """A walk, climb or ride names its pace (L8): 'at a walking pace' lands
    right after the gait's own clause, once."""
    def paced(text: str) -> str:
        out, last = [], 0
        for m in GAIT.finditer(text):
            seg_end = min([i for i in (text.find(";", m.end()), text.find(".", m.end()))
                           if i != -1] or [len(text)])
            if "pace" in text[m.start():seg_end].lower():
                continue
            out.append(text[last:m.end()] + " at a walking pace"
                       if text[m.end():m.end() + 18].find("at a walking") == -1 else text[last:m.end()])
            last = m.end()
        return "".join(out) + text[last:]

    for holder, f in _prose_fields(doc):
        if holder.get(f):
            holder[f] = paced(holder[f])
    return doc


def button_beat(doc: dict) -> dict:
    """The shot before the button keeps >= 1.0 s of silence (contract)."""
    shots = doc.get("shots") or []
    if len(shots) >= 2:
        pen = shots[-2]
        pen["beat_s"] = max(1.0, float(pen.get("beat_s") or 0.0))
    return doc


LOCKED = "The camera holds a locked-off frame"
PUSH = "The camera pushes in toward {aim} across the whole shot"
STOP = re.compile(r"\b(the|a|an|his|her|its|their|at|on|in|of|and|with|by|one)\b", re.I)


def cell_nouns(at_rest: str) -> list[str]:
    """Aimable nouns the cell already holds, longest first."""
    words = [w.strip(",.;") for w in (at_rest or "").split()]
    out = [w for w in words if len(w) > 3 and not STOP.fullmatch(w) and w[:1].isalpha()]
    return sorted(set(w.lower() for w in out), key=len, reverse=True)


def aim_of_head(head: str) -> list[str]:
    found = re.search(r"toward (?:the |a )?([\w' -]+?)(?: across| at|$)", head, re.I)
    return [found.group(1).strip().lower()] if found else []


def vary_heads(doc: dict, indices: list[int]) -> dict:
    """A repeated, still or mis-aimed head is swapped: a push toward a noun
    the cell holds, else a locked frame -- never the neighbour's move
    (G-MOVES, G-STILL, G-AIM; docs/calibration/camera_catalog.md)."""
    by = {s["index"]: s for s in doc.get("shots") or []}
    for i in indices:
        s = by.get(i)
        if not s:
            continue
        head, _, rest = (s.get("motion") or "").partition(";")
        nouns = cell_nouns(s.get("at_rest") or "")
        prev_head = (by.get(i - 1, {}).get("motion") or "").split(";")[0]
        pick = PUSH.format(aim=f"the {nouns[0]}") if nouns else LOCKED
        if pick.split()[2:4] == prev_head.split()[2:4]:          # would repeat: fall back
            pick = LOCKED if "locked" not in prev_head else PUSH.format(
                aim=f"the {nouns[1] if len(nouns) > 1 else nouns[0]}")
        s["motion"] = pick + ((";" + rest) if rest.strip() else "")
    return doc


def rebalance_heads(doc: dict, indices: list[int]) -> tuple[dict, list[int]]:
    """Catalog-wide head rebalancing (G-MOVES/G-STILL/G-AIM/G-ANCHOR/M2):
    delegated to `studio.move_rebalance`, which replays the REAL gate
    predicates on every candidate before writing it.  Pure and $0, so this
    table keeps its no-llm charter; the shots it cannot cure come back as
    `unfixed` for `move_llm`'s guarded escape (dispatched by plan_repair).
    Supersedes `vary_heads`, whose two-head vocabulary drove ep18's push_slow
    to share 0.30 while distinct moves stayed at 6 < MIN_MOVES 8."""
    from studio import move_rebalance
    return move_rebalance.rebalance(doc, indices)


def legal_props(doc: dict, legal: set[str]) -> dict:
    """Setup props filtered to the analysis registry; scenery nouns stay in
    the prose, where they belong (one picture per entity)."""
    for s in (doc.get("setups") or {}).values():
        s["props"] = [p for p in (s.get("props") or []) if p in legal]
    return doc


def pin_series(doc: dict, *, look: str, aspect: str, light: str | None = None,
               where: str | None = None) -> dict:
    """look/style/aspect (and light/where when given) are the SERIES', never
    the writer's (ep15: an invented 13-word look broke every style line and
    would have shipped a foreign-looking episode)."""
    doc["look"], doc["style"], doc["aspect"] = look, "", aspect
    if light is not None:
        doc["light"] = light
    if where is not None:
        doc["where"] = where
    return doc


DIRECTIONAL = re.compile(r"\b(left|right|top|bottom|centre|center)\b")


def edge_cases(doc: dict) -> dict:
    """G-FIRSTFRAME's frame-edge median counts UPPERCASE edge words; the
    at_rests assert placements in lowercase.  A case flip makes the geometry
    countable with zero content change (ep15)."""
    from studio import plan_gates
    for s in doc.get("shots") or []:
        at = s.get("at_rest") or ""
        if plan_gates.edge_tokens(at) < 3:
            s["at_rest"] = DIRECTIONAL.sub(lambda m: m.group(1).upper(), at)
    return doc


MAX_BEAT_S, MAX_CODA_S = 1.5, 4.0
HOLE_WALL_S, TAKE_BUDGET_S, SETUP_CAP_S = 6.0, 8.0, 50.0


HANDLE_S = 0.25
BREATH_S = 0.70
"""plan_check.projected's constants: 2 x HANDLE_S a shot, BREATH_S between its
lines.  The cure MEASURES LIKE THE CHECKER or it cures numbers nobody judges
(ep16: shot 16 at 8.05 s was invisible to a model that lacked these)."""


def _shot_secs(doc: dict, rate: float) -> dict[int, float]:
    words, lines = {}, {}
    for line in doc.get("lines") or []:
        words[line["shot"]] = words.get(line["shot"], 0) + len(str(line["text"]).split())
        lines[line["shot"]] = lines.get(line["shot"], 0) + 1
    return {s["index"]: 2 * HANDLE_S + words.get(s["index"], 0) / rate
            + BREATH_S * max(0, lines.get(s["index"], 0) - 1)
            + float(s.get("beat_s") or 0) + float(s.get("coda_s") or 0)
            for s in doc.get("shots") or []}


def _episode_shim(doc: dict):
    """Just enough of Episode for `episode_timeline.place`: shots in list
    order, lines indexed in playback order, no omits, no sub-shots -- the
    cure must still measure a draft the contract refuses mid-repair."""
    from types import SimpleNamespace
    shots = [SimpleNamespace(index=s["index"], beat_s=float(s.get("beat_s") or 0),
                             coda_s=float(s.get("coda_s") or 0), cuts=[])
             for s in doc.get("shots") or []]
    lines = [SimpleNamespace(index=k, kind=l.get("kind", "narration"),
                             speaker=l.get("speaker", ""), text=str(l.get("text") or ""),
                             shot=l["shot"],
                             words=lambda t=str(l.get("text") or ""): len(t.split()))
             for k, l in enumerate(doc.get("lines") or [])]
    ep = SimpleNamespace(shots=shots, lines=lines)
    ep.cut_shots = lambda: shots
    ep.lines_of = lambda i: [l for l in lines if l.shot == i]
    return ep


def _as_episode(doc: dict):
    """The doc as the placement function reads it: the contract's Episode when
    it validates, else the shim with the same timing fields."""
    from studio.episode_spec import Episode
    try:
        return Episode.model_validate(doc)
    except Exception:
        return _episode_shim(doc)


def _projection(doc: dict, rate: float) -> dict:
    """The placement step 05 would write for this draft, projected -- the
    G-HOLE gate's own numbers (the cure MEASURES LIKE THE CHECKER)."""
    from studio import plan_gates
    return plan_gates.projected_place(_as_episode(doc), rate)


def _floors(doc: dict) -> dict[tuple[int, str], float]:
    """The hold floor per (shot, key): a wordless shot keeps coda_s >= 0.5
    (the contract's no-line-no-beat rule and G-STORY's wordless tail; its
    beat_s carries the floor instead when it holds the shot alone), the shot
    before the button keeps beat_s >= 1.0 (contract), the button shot keeps
    coda_s >= 0.6 (BUTTON_REST advisory); a voiced shot floors at 0."""
    lines = doc.get("lines") or []
    voiced = {l["shot"] for l in lines}
    button = lines[-1]["shot"] if lines else None
    out: dict[tuple[int, str], float] = {}
    for s in doc.get("shots") or []:
        i, wordless = s["index"], s["index"] not in voiced
        beat = 1.0 if button is not None and i == button - 1 else 0.0
        if wordless and not float(s.get("coda_s") or 0):
            beat = max(beat, 0.5)                   # the beat holds the no-hole rule alone
        out[(i, "beat_s")] = beat
        out[(i, "coda_s")] = 0.5 if wordless else 0.6 if i == button else 0.0
    return out


def _hole_slots(doc: dict, shot_ids: list[int]) -> list[tuple[dict, str]]:
    """(shot, key) holds inside the hole: beat_s and coda_s of every plan shot
    the hole crosses -- never a shot outside it."""
    own = [s for s in doc.get("shots") or [] if s["index"] in set(shot_ids)]
    return [(s, key) for s in own for key in ("coda_s", "beat_s")]


def _shave(slots: list[tuple[dict, str]], over: float, floors: dict) -> int:
    """Cut `over` seconds from the largest holds first, never below a floor;
    cuts round UP to the cent so the on_frame ceiling cannot strand a hole a
    hair over the wall.  Returns how many holds were shaved."""
    import math
    cut_count = 0
    for s, key in sorted(slots, key=lambda sk: floors.get((sk[0]["index"], sk[1]), 0.0)
                         - float(sk[0].get(sk[1]) or 0)):
        if over <= 0:
            break
        room = float(s.get(key) or 0) - floors.get((s["index"], key), 0.0)
        cut = math.ceil(min(over, max(0.0, room)) * 100 - 1e-9) / 100
        if cut > 0:
            s[key] = round(float(s.get(key) or 0) - cut, 2)
            over -= cut
            cut_count += 1
    return cut_count


def _close_projected_holes(doc: dict, rate: float) -> dict:
    """Every projected hole in speech trimmed to MAX_GAP_S - HOLE_MARGIN_S by
    the checker's own placement, largest holds first, floors kept; <= 8
    passes, each re-measuring (replaces the approximate step 3b that missed
    beat_s, the 2xHANDLE seam, and voiced-to-voiced holes)."""
    from studio import speech_gap
    wall = speech_gap.MAX_GAP_S - speech_gap.HOLE_MARGIN_S
    floors = _floors(doc)
    for _ in range(8):
        holes = speech_gap.over_wall(_projection(doc, rate), wall)
        if not sum(_shave(_hole_slots(doc, ids), (end - start) - wall, floors)
                   for start, end, ids in holes):
            break
    return doc


def _headroom(doc: dict, rate: float, shot_index: int) -> float:
    """Seconds the hole this shot's trailing silence sits in may still grow
    before crossing MAX_GAP_S - HOLE_MARGIN_S, from the shared projection
    (recomputed by the caller after every write)."""
    from studio import speech_gap
    placed = _projection(doc, rate)
    shot = next((s for s in placed["shots"] if s["index"] == shot_index), None)
    if shot is None:
        return 0.0
    wall = speech_gap.MAX_GAP_S - speech_gap.HOLE_MARGIN_S
    t = shot["t_end"] - 1e-6
    for a, b in speech_gap.gaps(placed["lines"], placed.get("duration_s", 0.0)):
        if a <= t < b:
            return round(wall - (b - a), 2)
    return wall


def _grow_pair(doc: dict, rate: float, a: dict, b: dict, voiced: set,
               need: float) -> tuple[float, bool]:
    """One pair's growth, each add capped by its silence's hole headroom;
    (need left, True when zero headroom blocked an add)."""
    blocked = False
    for s in (a, b, a, b):
        if need <= 0:
            break
        for key, cap in (("coda_s", MAX_CODA_S), ("beat_s", MAX_BEAT_S)):
            room = cap - float(s.get(key) or 0)
            if need <= 0 or room <= 0.1 or s["index"] not in voiced:
                continue
            head = _headroom(doc, rate, s["index"])
            if head <= 0:
                blocked = True
                continue
            add = round(min(need, room, 1.2, head), 2)
            s[key] = round(float(s.get(key) or 0) + add, 2)
            need = round(need - add, 2)
    return need, blocked


def _grow_pairs(doc: dict, rate: float) -> list[tuple[int, int]]:
    """holds() step 1: consecutive same-setup pairs under the take budget grow
    their holds past it; the pairs no hole headroom lets split come back for
    the micro-line path (speech splits a take without opening silence)."""
    shots = doc.get("shots") or []
    voiced = {l["shot"] for l in doc.get("lines") or []}
    unsplit, secs = [], _shot_secs(doc, rate)
    for a, b in zip(shots, shots[1:]):
        if a.get("setup") != b.get("setup"):
            continue
        need = TAKE_BUDGET_S + 0.3 - (secs[a["index"]] + secs[b["index"]])
        if need <= 0:
            continue
        need, blocked = _grow_pair(doc, rate, a, b, voiced, need)
        secs = _shot_secs(doc, rate)
        if need > 0 and blocked:
            unsplit.append((a["index"], b["index"]))
    return unsplit


def holds(doc: dict, rate: float = 3.0) -> dict:
    """`holds_and_unsplit` for the callers that only want the doc (the cure
    table's dispatcher, the older tests): same cure, report dropped."""
    return holds_and_unsplit(doc, rate)[0]


def holds_and_unsplit(doc: dict, rate: float = 3.0) -> tuple[dict, list[tuple[int, int]]]:
    """The hold algebra, solved the way the ep15 session solved it by hand:
    the band floor is lifted with PRE-TURN codas (the turn ratio rises with
    them); a take-sharing pair grows past the budget (hole-aware: every add is
    capped by its silence's hole headroom); a setup past its cap is shaved
    from shots outside the pairs; every projected hole is closed by the
    checker's own placement.  The second value is the ONE PER TAKE pairs no
    headroom lets split -- plan_repair routes them to the micro-line path."""
    shots = doc.get("shots") or []
    if not shots:
        return doc, []
    turn_at = next((s["index"] for s in shots if s.get("section") == "turn"), len(shots) // 2)
    voiced = {line["shot"] for line in doc.get("lines") or []}

    # 1. ONE PER TAKE: consecutive pairs under the budget grow past it
    unsplit = _grow_pairs(doc, rate)

    # 2. the band floor: pre-turn codas rise until the projection clears 120
    def projection() -> float:
        return sum(_shot_secs(doc, rate).values())
    guard = 0
    while projection() < 120.5 and guard < 40:
        guard += 1
        for s in shots:
            if s["index"] >= turn_at or s["index"] not in voiced:
                continue
            if float(s.get("coda_s") or 0) < MAX_CODA_S - 0.4:
                s["coda_s"] = round(float(s.get("coda_s") or 0) + 0.4, 2)
                break
        else:
            break

    # 3. a setup past its cap is shaved from its longest codas
    per_setup: dict[str, float] = {}
    secs = _shot_secs(doc, rate)
    for s in shots:
        per_setup[s.get("setup") or ""] = per_setup.get(s.get("setup") or "", 0) + secs[s["index"]]
    for name, total in per_setup.items():
        over = total - SETUP_CAP_S
        own = sorted((s for s in shots if s.get("setup") == name),
                     key=lambda s: -float(s.get("coda_s") or 0))
        for s in own:
            if over <= 0:
                break
            cut = round(min(over, max(0.0, float(s.get("coda_s") or 0) - 0.2)), 2)
            if cut > 0:
                s["coda_s"] = round(float(s.get("coda_s") or 0) - cut, 2)
                over = round(over - cut, 2)

    # 4. no single shot past the take budget: the pair growth above may have
    # pushed one over (ep16 shot 16, 8.05 s); shave its own coda then beat.
    # A clamped shot keeps its pair split: the partner's handles alone hold
    # the pair's total over the budget.
    secs = _shot_secs(doc, rate)
    for s in shots:
        over = secs[s["index"]] - TAKE_BUDGET_S
        for key in ("coda_s", "beat_s"):
            if over <= 0:
                break
            cut = round(min(over + 0.05, float(s.get(key) or 0)), 2)
            if cut > 0:
                s[key] = round(float(s.get(key) or 0) - cut, 2)
                over = round(over - cut, 2)

    # 5. (was 3b) no projected hole in speech over the wall: closed LAST, by
    # the checker's own placement (G-HOLE's), largest holds first, floors
    # kept -- button_beat raises a hold, so it must run before the close or
    # it reopens the hole it sits in
    return _close_projected_holes(button_beat(doc), rate), unsplit


def trim_measured_holes(doc: dict, placed: dict) -> int:
    """Step 05's bounded measured-hole cure: the shave of
    `_close_projected_holes`, but hole boundaries and shot intersections come
    from the MEASURED placed.json.  Trims only, inserts nothing, touches no
    shot outside a hole, cuts at most hole - (MAX_GAP_S - HOLE_MARGIN_S) per
    hole (the margin below the 6.0 wall gives the once-only re-time headroom),
    respects every floor.  0 shaved = nothing trimmable: the step refuses."""
    from studio import speech_gap
    wall = speech_gap.MAX_GAP_S - speech_gap.HOLE_MARGIN_S
    floors = _floors(doc)
    return sum(_shave(_hole_slots(doc, ids), (end - start) - wall, floors)
               for start, end, ids in speech_gap.over_wall(placed, wall))


def insertion_shot(doc: dict, hole: tuple, rate: float) -> int | None:
    """The shot a micro-line should land on: inside the hole, under
    MAX_LINES_PER_SHOT, strictly before the button's shot (no line after the
    button), still inside the take budget with 14 more words, wordless
    preferred, splitting the hole most evenly.  None -> the row is creative."""
    from studio.episode_spec import BREATH, HANDLE, MAX_LINES_PER_SHOT
    from studio.episode_takes import BUDGET
    start, end, ids = hole
    lines = doc.get("lines") or []
    button = lines[-1]["shot"] if lines else -1
    placed = {s["index"]: s for s in _projection(doc, rate)["shots"]}
    best = None
    for s in doc.get("shots") or []:
        i, own = s["index"], [l for l in lines if l["shot"] == s["index"]]
        if i not in ids or i >= button or len(own) >= MAX_LINES_PER_SHOT or i not in placed:
            continue
        words = sum(len(str(l["text"]).split()) for l in own)
        secs = (2 * HANDLE + (words + 14) / rate + BREATH * len(own)
                + float(s.get("beat_s") or 0) + float(s.get("coda_s") or 0))
        if secs > BUDGET:
            continue
        at = placed[i]["t_start"] + HANDLE + words / rate + BREATH * len(own)
        score = (bool(own), max(at - start, end - at))
        if best is None or score < best[0]:
            best = (score, i)
    return best[1] if best else None


def pair_insertion_shot(doc: dict, pair: tuple[int, int], rate: float) -> tuple | None:
    """An unsplit ONE PER TAKE pair's micro-line target: its line-light shot
    and the hole its silence sits in -- a line there splits the take without
    opening silence.  None when both shots are full or at/past the button."""
    from studio import speech_gap
    from studio.episode_spec import MAX_LINES_PER_SHOT
    lines = doc.get("lines") or []
    button = lines[-1]["shot"] if lines else -1
    counts = {i: sum(1 for l in lines if l["shot"] == i) for i in pair}
    cands = [i for i in pair if i < button and counts[i] < MAX_LINES_PER_SHOT]
    if not cands:
        return None
    placed = _projection(doc, rate)
    i = min(cands, key=lambda k: counts[k])
    t = next(s["t_end"] for s in placed["shots"] if s["index"] == i) - 1e-6
    hole = next(((a, b) for a, b in speech_gap.gaps(placed["lines"],
                                                    placed.get("duration_s", 0.0))
                 if a <= t < b), (t, t + 1e-6))
    return i, (hole[0], hole[1], [i])


def narration_speaker(doc: dict) -> str | None:
    """Who a spliced micro-line speaks as: the first narration line's speaker;
    a plan with no narration anywhere refuses insertion."""
    return next((l["speaker"] for l in doc.get("lines") or []
                 if l.get("kind") == "narration"), None)


def _remap_answer(doc: dict, p: int) -> dict:
    """'line N' answers at or past the insertion point move by one; 'shot N'
    answers, omits and beds reference shots and are untouched."""
    from studio.episode_spec import ANSWER
    m = ANSWER.match(str(doc.get("answer") or ""))
    if m and m.group(1) == "line" and int(m.group(2)) >= p:
        doc["answer"] = f"line {int(m.group(2)) + 1}"
    return doc


def insert_line(doc: dict, shot_index: int, text: str, speaker: str) -> dict:
    """Splice one narration micro-line with the EXACT reindex: the new line
    lands after every existing line of its shot (lines are contract-sorted by
    shot, so G-SYNC's dialogue-first rule holds and the button stays last),
    indices renumber 0..n-1 in playback order, the answer is remapped."""
    from studio.episode_spec import MAX_LINES_PER_SHOT
    lines = doc.get("lines") or []
    button = lines[-1]["shot"] if lines else -1
    if shot_index >= button:
        raise ValueError(f"shot {shot_index} is not before the button shot {button}; "
                         f"no line lands on or after the button")
    if sum(1 for l in lines if l["shot"] == shot_index) >= MAX_LINES_PER_SHOT:
        raise ValueError(f"shot {shot_index} already carries {MAX_LINES_PER_SHOT} lines")
    p = next((k for k, l in enumerate(lines) if l["shot"] > shot_index), len(lines))
    lines.insert(p, {"index": -1, "kind": "narration", "speaker": speaker,
                     "text": text, "shot": shot_index, "delivery": ""})
    for k, l in enumerate(lines):
        l["index"] = k
    doc["lines"] = lines
    return _remap_answer(doc, p)


# ---- G-SOURCE and QUOTE: snap to the chapter's own words --------------------------

SNAP_FLOOR = 0.50
"""Below this `best_window` ratio a span is invention, not paraphrase, and is
DROPPED (plan_gates' SPAN_MATCH docstring: a paraphrase of the right sentence
reads 0.5-0.7; ep18 shot 16 read 0.75 and 0.78 -- snappable).  The drop IS the
escalation: the existing 'has no chapter span' fault fires next round."""
SNAP_WORDS = 40
"""A snap longer than this keeps only the single sentence containing the
matched window's midpoint, re-snapped -- a span is evidence, not a reprint."""


def snap_span(span: str, chapter: str) -> str | None:
    """A failing span replaced by the chapter window `best_window` already
    found, expanded to complete sentences -- the ep18 hand-fix, codified.  The
    final guard re-measures with the GATE'S own scorer: this cure can never
    write a span the gate would refuse next round.  $0."""
    from studio import plan_gates as pg
    ratio, start, n = pg.best_window(span, chapter)
    if ratio < SNAP_FLOOR or not n:
        return None
    offs = pg._word_offsets(chapter)
    out = pg.snap_sentences(chapter, offs[start][0], offs[min(start + n, len(offs)) - 1][1])
    if len(out.split()) > SNAP_WORDS:
        mid = offs[start + n // 2]
        out = pg.snap_sentences(chapter, mid[0], mid[1])
    return out if pg.span_match(out, chapter) >= pg.SPAN_MATCH else None


def source_spans(doc: dict, chapter: str) -> dict:
    """Every shot's `source` rebuilt against the doc itself, never the fault
    rows (they truncate spans at 60 chars): a passing span is kept as-is, a
    failing one snapped, an invention dropped; duplicates collapse keeping
    order (the ep18 'writer re-added it' case).  Idempotent: a verbatim span
    scores ~1.0 and is never touched."""
    from studio import plan_gates as pg
    for s in doc.get("shots") or []:
        out: list[str] = []
        for span in s.get("source") or []:
            kept = span if pg.span_match(span, chapter) >= pg.SPAN_MATCH \
                else snap_span(span, chapter)
            if kept is not None and kept not in out:
                out.append(kept)
        s["source"] = out
    return doc


def _trim_tail(text: str, spans: list[tuple[int, int]], b: int) -> str:
    """The run reaches the line's end: keep its first QUOTE_WALL words and
    re-attach the line's own terminal punctuation (the ep02 trim)."""
    from studio import episode_spec as es
    return text[:spans[es.QUOTE_WALL - 1][1]] + text[b:]


def _trim_head(text: str, spans: list[tuple[int, int]], n: int) -> str:
    """The run starts the line: drop its leading words down to QUOTE_WALL and
    capitalize the new first word."""
    from studio import episode_spec as es
    keep = text[spans[n - es.QUOTE_WALL][0]:]
    return keep[:1].upper() + keep[1:]


def _trim_line(text: str, source: str) -> str:
    """One narration line brought under the wall, at most 3 passes (a second,
    shorter run may remain).  A mid-line lift is CREATIVE and comes back
    byte-identical for the writer."""
    from studio import episode_spec as es
    for _ in range(3):
        if es.lifted_run(text, source) <= es.QUOTE_WALL:
            return text
        a, b, n = es.lifted_offsets(text, source)
        spans = [s for s in _word_spans(text) if a <= s[0] and s[1] <= b]
        if re.fullmatch(r"[\s.!?,;:\"'”’)]*", text[b:]):
            text = _trim_tail(text, spans, b)
        elif re.fullmatch(r"[\s\"'“‘(]*", text[:a]):
            text = _trim_head(text, spans, n)
        else:
            return text
    return text


def _word_spans(text: str) -> list[tuple[int, int]]:
    """Char (start, end) per word, `episode_spec._tokens`' own normalization
    (1:1 in char count, so the spans index the original line)."""
    low = text.replace("’", "'").replace("—", " ").replace("–", " ").lower()
    return [m.span() for m in re.finditer(r"[a-z']+", low)]


def quote_trim(doc: dict, source: str) -> dict:
    """QUOTE's mechanical cure: only the HARD lines (narration over the wall,
    by the gate's own `quoted_lines` split) are trimmed; dialogue is advisory
    and never touched.  Valid at the plan stage only -- narration text is
    downstream audio."""
    from studio import episode_spec as es
    hard, _ = es.quoted_lines(doc.get("lines") or [], source)
    over = {line["index"] for line in hard}
    for line in doc.get("lines") or []:
        if line.get("index") in over:
            line["text"] = _trim_line(line.get("text") or "", source)
    return doc


# ---- G-STAGE / G-FACE-KIND: machines by card name, creatures never staged ---------

SHOT_FIELDS = ("frame", "motion", "at_rest", "end")
SETUP_FIELDS = ("described", "crowd", "geometry")
CLAUSE_WORDS = 12
"""The physical clause the FIRST cured mention carries, capped (owner rule:
described in the shot); every later mention gets the card name alone -- the
full definition reaches every take via `pack_refs.props_named` anyway."""


def physical_clause(physical: str) -> str:
    """The card's first physical clause, <= CLAUSE_WORDS words, lowercase-led."""
    from studio.episode_spec import slow_word
    first = re.split(r"[,.;:]", physical or "", 1)[0].strip()
    said = " ".join(first.split()[:CLAUSE_WORDS])
    if slow_word(said):     # ep19: "the top turning slowly" broke the contract
        return ""
    return said[:1].lower() + said[1:] if said else ""


def _rename_first(text: str, term: str, name: str, card_names: list[str],
                  clause: str = "") -> tuple[str, bool]:
    """The first `(the|a|an)? term` phrase renamed to the card's `name` (plus
    ', clause' when given); existing card names are masked first so a word
    inside one is never renamed again.  (text, hit)."""
    from studio import pack_refs
    masked = pack_refs.mask_card_names(text or "", card_names)
    m = re.search(rf"(?:\b(?:the|a|an)\s+)?\b{re.escape(term)}s?\b", masked, re.I)
    if not m:
        return text, False
    said = name + (f", {clause}" if clause else "")
    return (text or "")[:m.start()] + said + (text or "")[m.end():], True


def _mentioned(doc: dict, name: str) -> bool:
    """Is the card's name already in some shot's prose?  The physical clause
    lands on the FIRST mention only."""
    return any(re.search(re.escape(name), " ".join(s.get(f) or "" for f in SHOT_FIELDS), re.I)
               for s in doc.get("shots") or [])


def _stage_pid(setup: dict, pid: str) -> None:
    props = setup.setdefault("props", [])
    if pid not in props:
        props.append(pid)


def _cure_fields(holder: dict, fields: tuple, card: dict, names: list[str], clause: str) -> bool:
    """The first bare term per field renamed to the card name; the clause is
    spent on the first field cured.  True when anything hit."""
    hit = False
    for f in fields:
        if not holder.get(f):
            continue
        for term in card["terms"]:
            out, done = _rename_first(holder[f], term, card["name"], names,
                                      "" if hit else clause)
            if done:
                holder[f], hit = out, True
                break
    return hit


def _candidates(s: dict, doc: dict, vocab: dict) -> list[str]:
    """The machine pids a bare creature word in this shot could mean: the
    setup's own staged machines, else the chapter's whole vocabulary."""
    setup = (doc.get("setups") or {}).get(s.get("setup")) or {}
    staged = [p for p in setup.get("props") or [] if p in vocab["machines"]]
    return staged or sorted(vocab["machines"])


def rename_creature(doc: dict, shot_index: int, term: str, pid: str, vocab: dict) -> dict:
    """One shot's creature phrase renamed to `pid`'s card name and the pid
    staged -- the mechanical rerun after an llm pick, and the one-candidate
    cure's workhorse.  The first mention carries the physical clause."""
    card = vocab["machines"][pid]
    names = [c["name"] for c in vocab["machines"].values()]
    s = next((x for x in doc.get("shots") or [] if x.get("index") == shot_index), None)
    if s is None:
        return doc
    clause = "" if _mentioned(doc, card["name"]) else physical_clause(card["physical"])
    _cure_fields(s, SHOT_FIELDS, {**card, "terms": [term]}, names, clause)
    _stage_pid((doc.get("setups") or {}).get(s.get("setup")) or {}, pid)
    return doc


def _cure_shot_creatures(doc: dict, vocab: dict, names: list[str]) -> list[tuple[int, str, list[str]]]:
    """Bare creature words in SHOT prose: renamed to the one candidate machine
    card; >= 2 candidates come back unresolved for the llm pick (ep17 shot 14:
    'a Martian wading' -> 'the Martian fighting-machine wading')."""
    from studio import pack_refs
    unresolved = []
    for s in doc.get("shots") or []:
        masked = pack_refs.mask_card_names(" ".join(s.get(f) or "" for f in SHOT_FIELDS), names)
        for terms in (vocab.get("creatures") or {}).values():
            term = pack_refs.first_term(masked, terms)
            if not term:
                continue
            cands = _candidates(s, doc, vocab)
            if len(cands) == 1:
                rename_creature(doc, s.get("index"), term, cands[0], vocab)
            elif cands:
                unresolved.append((s.get("index"), term, cands))
    return unresolved


def stage_machines(doc: dict, vocab: dict) -> tuple[dict, list[tuple[int, str, list[str]]]]:
    """G-STAGE's mechanical cure: every bare machine word becomes its card name
    with the pid staged in the setup's props; a bare creature word with one
    candidate is renamed the same way.  Returns (doc, unresolved creature rows
    for `stage_pick.pick_machine`).  $0."""
    from studio import pack_refs
    names = [c["name"] for c in vocab["machines"].values()]
    for s in doc.get("shots") or []:
        setup = (doc.get("setups") or {}).get(s.get("setup")) or {}
        for pid, card in vocab["machines"].items():
            prose = " ".join(s.get(f) or "" for f in SHOT_FIELDS)
            if not pack_refs.names_prop(prose, card["terms"]):
                continue
            if pack_refs.first_term(pack_refs.mask_card_names(prose, names), card["terms"]):
                clause = "" if _mentioned(doc, card["name"]) else physical_clause(card["physical"])
                _cure_fields(s, SHOT_FIELDS, card, names, clause)
            _stage_pid(setup, pid)
    for setup in (doc.get("setups") or {}).values():
        for pid, card in vocab["machines"].items():
            text = " ".join(setup.get(f) or "" for f in SETUP_FIELDS)
            if pack_refs.names_prop(text, card["terms"]):
                _cure_fields(setup, SETUP_FIELDS, card, names, "")
                _stage_pid(setup, pid)
    return doc, _cure_shot_creatures(doc, vocab, names)


def strip_creatures(doc: dict, vocab: dict) -> dict:
    """G-STAGE row (d) in SETUP text: every sentence naming a bare creature
    word is dropped -- a creature is never scenery of a place picture (ep17/18
    hand fix).  Card names are masked first, the gate's own exemption."""
    from studio import pack_refs
    names = [c["name"] for c in vocab["machines"].values()]
    terms = [t for ts in (vocab.get("creatures") or {}).values() for t in ts]
    for setup in (doc.get("setups") or {}).values():
        for f in SETUP_FIELDS:
            if not setup.get(f):
                continue
            kept = [sent for sent in split_sentences(setup[f])
                    if not pack_refs.first_term(pack_refs.mask_card_names(sent, names), terms)]
            setup[f] = " ".join(kept)
    return doc


def drop_creature_faces(doc: dict, creature_ids: set[str]) -> dict:
    """G-FACE-KIND's cure: creature ids filtered out of every shot's faces,
    every cut's faces and every setup's cast; human ids and extras untouched.
    Runs in the same round as stage_machines, so the shot that loses its
    creature face gains the machine card name in the same pass."""
    def kept(ids):
        return [i for i in ids or [] if i not in creature_ids]
    for s in doc.get("shots") or []:
        s["faces"] = kept(s.get("faces"))
        for cut in s.get("cuts") or []:
            cut["faces"] = kept(cut.get("faces"))
    for setup in (doc.get("setups") or {}).values():
        setup["cast"] = kept(setup.get("cast"))
    return doc


# ---- G-SOURCE: a cured prop claim copies its chapter sentence ---------------------

SPAN_WINDOW = 25
"""The longest span the cure copies: a verbatim window around the term -- a
span is evidence, not a reprint, and verbatim guarantees span_match >= 0.85."""


def _names_pid(text: str, pid: str) -> bool:
    """`plan_gates.staged_props`' pid-token test, on dicts."""
    low = (text or "").lower()
    return any(re.search(rf"\b{re.escape(t)}s?\b", low)
               for t in pid.lower().split("_") if len(t) > 3)


def _pid_terms(pid: str, vocab: dict) -> list[str]:
    """The pid's alias terms from the vocab, else its own id tokens."""
    said = (vocab.get("machines") or {}).get(pid) or {}
    return said.get("terms") or [t for t in pid.lower().split("_") if len(t) > 3]


def _unspanned_pids(s: dict, setup: dict, vocab: dict) -> list[str]:
    """The staged pids this shot's prose names whose `source` has no span
    naming any of the pid's terms (the 'has no chapter span' set)."""
    prose = " ".join(s.get(f) or "" for f in SHOT_FIELDS)
    spans = " ".join(s.get("source") or [])
    from studio import pack_refs
    return [pid for pid in setup.get("props") or []
            if _names_pid(prose, pid)
            and not pack_refs.first_term(spans, _pid_terms(pid, vocab))]


def _chapter_sentences(paragraphs: list[str]) -> list[tuple[int, str]]:
    """(1-based paragraph, sentence) for every chapter sentence --
    `span_paragraph`'s own numbering."""
    return [(k, sent) for k, para in enumerate(paragraphs, 1)
            for sent in split_sentences(para) if sent.strip()]


def _span_window(sentence: str, term: str) -> str:
    """The sentence verbatim, or its <= SPAN_WINDOW-word contiguous window
    centred on the term (still verbatim, so still ~1.0 on span_match)."""
    said = sentence.split()
    if len(said) <= SPAN_WINDOW:
        return sentence
    at = next((k for k, w in enumerate(said)
               if re.search(rf"\b{re.escape(term)}s?\b", w, re.I)), len(said) // 2)
    start = max(0, min(at - SPAN_WINDOW // 2, len(said) - SPAN_WINDOW))
    return " ".join(said[start:start + SPAN_WINDOW])


def _span_anchor(doc: dict, s: dict, paragraphs: list[str]) -> int:
    """The paragraph the shot's own spans sit in, else the nearest neighbour
    shot's, else 1."""
    from studio import plan_gates
    order = sorted(doc.get("shots") or [],
                   key=lambda x: abs((x.get("index") or 0) - (s.get("index") or 0)))
    for near in order:
        for span in near.get("source") or []:
            if (at := plan_gates.span_paragraph(span, paragraphs)) is not None:
                return at
    return 1


def prop_spans(doc: dict, paragraphs: list[str], vocab: dict) -> dict:
    """A staged pid claim with no chapter span gets a VERBATIM chapter sentence
    nearest the shot's own paragraph, appended to `source`; zero candidates
    leave the row uncured (creative, the writer's).  $0."""
    from studio import pack_refs
    for s in doc.get("shots") or []:
        setup = (doc.get("setups") or {}).get(s.get("setup")) or {}
        for pid in _unspanned_pids(s, setup, vocab):
            found = [(k, sent, t) for k, sent in _chapter_sentences(paragraphs)
                     if (t := pack_refs.first_term(sent, _pid_terms(pid, vocab)))]
            if not found:
                continue
            anchor = _span_anchor(doc, s, paragraphs)
            _, sent, term = min(found, key=lambda row: abs(row[0] - anchor))
            span = _span_window(sent, term)
            if span not in (s.get("source") or []):
                s.setdefault("source", []).append(span)
    return doc


# ---- G-GHOST: the ghost body-part clause is cut out, for free ---------------------

OVER_GHOST = re.compile(r"\bover\s+(?:the\s+)?([a-z][\w-]*)'s\s+shoulders?\b", re.I)
GHOST_STRIP_SHARE = 0.30
"""The largest share of a field's words the clause strip may delete; past it
the field is left for the llm rewrite (a strip that eats the field is a
rewrite wearing scissors)."""
GHOST_FLOOR_WORDS = 10
"""frame/at_rest keep at least this many words after a strip, or the strip
is refused the same way."""


def _ghost_owners(seg: str, faces: list, names: dict, prose: str) -> list[str]:
    """The ghost owners this segment stages: the GATE'S own test (ghost_hits +
    staged_elsewhere over the whole shot's prose) -- the cure measures like
    the checker."""
    from studio import plan_gates as pg
    return [owner for _, _, owner in pg.ghost_hits(seg, names)
            if owner not in faces and not pg.staged_elsewhere(prose, owner, names)]


def _swap_over_shoulder(text: str, faces: list, names: dict, prose: str) -> str:
    """'over the X's shoulder' -> 'from behind' when X is a ghost: the camera
    position stays, the body goes (the ep17 shot 11 hand fix)."""
    from studio import plan_gates as pg
    norm = (text or "").replace("’", "'")
    out, last = [], 0
    for m in OVER_GHOST.finditer(norm):
        owner = names.get(m.group(1).lower())
        if owner and owner not in faces and not pg.staged_elsewhere(prose, owner, names):
            out.append(text[last:m.start()] + "from behind")
            last = m.end()
    return "".join(out) + text[last:]


def _ghost_strip(text: str, faces: list, names: dict, prose: str) -> tuple[str, int, int]:
    """(stripped, dropped_words, total_words): every ;/.-delimited clause
    staging a ghost cut out whole, separators collapsed (the ep18 15/19/21
    hand surgery)."""
    kept, dropped = [], 0
    for seg in re.split(r"(?<=[;.])\s*", text or ""):
        if _ghost_owners(seg, faces, names, prose):
            dropped += len(seg.split())
        else:
            kept.append(seg)
    out = " ".join(s for s in kept if s.strip())
    out = re.sub(r"^[\s;.,]+", "", re.sub(r";\s*;", ";", out))
    return out, dropped, len((text or "").split())


def _ghost_cure(holder: dict, faces: list, names: dict, prose: str, rewrite, index) -> None:
    """One shot's (or cut's) fields through both passes, under the strip guard:
    a refused strip keeps the field and hands (shot_index, field) to `rewrite`."""
    from studio import plan_gates as pg
    for field in pg.GHOST_FIELDS:
        text = holder.get(field) or ""
        if not text:
            continue
        cured = _swap_over_shoulder(text, faces, names, prose)
        if cured != text:
            holder[field] = cured
        if _ghost_owners(cured, faces, names, prose):
            stripped, dropped, total = _ghost_strip(cured, faces, names, prose)
            floor = GHOST_FLOOR_WORDS if field in ("frame", "at_rest") else 0
            if dropped > GHOST_STRIP_SHARE * total or len(stripped.split()) < floor:
                if rewrite is not None:
                    rewrite(index, field)
            else:
                holder[field] = stripped


def _dict_prose(s: dict) -> str:
    """`plan_gates.shot_prose` on a plan DICT's shot."""
    from studio import plan_gates as pg
    fields = pg.GHOST_FIELDS + ("camera",)
    parts = [s.get(f) or "" for f in fields]
    for cut in s.get("cuts") or []:
        parts += [cut.get(f) or "" for f in fields]
    return " ".join(parts)


def ghost_limbs(doc: dict, names: dict, rewrite=None) -> dict:
    """G-GHOST's mechanical cure, the exact ep17/18 hand surgery, idempotent
    and $0: 'over the X's shoulder' -> 'from behind', any other ghost clause
    dropped whole.  A strip past GHOST_STRIP_SHARE of the field hands
    (shot_index, field) to `rewrite` when one is given, else leaves the field
    for the battery to re-flag.  names={} (a refs-less book) is a no-op."""
    if not names:
        return doc
    for s in doc.get("shots") or []:
        faces, prose = list(s.get("faces") or []), _dict_prose(s)
        _ghost_cure(s, faces, names, prose, rewrite, s.get("index"))
        for cut in s.get("cuts") or []:
            _ghost_cure(cut, faces + list(cut.get("faces") or []), names, prose, None, s.get("index"))
    return doc


# ---- G-TAKELINT: the take lint's word families, cured at the plan layer -----------

def _prose_fields(doc: dict):
    """Every (holder, field) prose slot a take prompt is built from: the
    shots' picture fields, their cuts', and the setups' injected texts."""
    for s in doc.get("shots") or []:
        for f in SHOT_FIELDS + ("changed",):
            yield s, f
        for cut in s.get("cuts") or []:
            for f in SHOT_FIELDS:
                yield cut, f
    for st in (doc.get("setups") or {}).values():
        for f in SETUP_FIELDS:
            yield st, f


def stillness_words(doc: dict) -> dict:
    """L2's plan-layer cure: the shared substitution table (studio.row_lint)
    over every prose field; `at_rest` alone may absorb motionless/frozen/
    unmoving as 'at rest' -- anywhere else those words are the llm cure's."""
    from studio import row_lint
    for holder, f in _prose_fields(doc):
        if holder.get(f):
            holder[f] = row_lint.substituted(holder[f], at_rest=(f == "at_rest"))
    return doc


FIGURATIVE = {"fire", "flame", "flames", "smoke", "fog", "mist", "shadow", "shadows",
              "light", "town", "road", "ivy", "water", "tide"}
"""Subject nouns whose 'gait' is figurative and safely swappable.  A non-person
gait OUTSIDE this list is left for the llm cure: `ro.is_person`'s capitalised
fallback is the known mis-router, so the swap never guesses."""

GAIT_SWAP = {"climb": "spread", "walk": "drift", "run": "stream", "ride": "roll"}


def _swapped_gait(word: str) -> str | None:
    low = word.lower()
    for gait, verb in GAIT_SWAP.items():
        if low in (gait, gait + "s"):
            return verb + ("s" if low.endswith("s") else "")
    return None


def _figurative(text: str) -> str:
    """Each gait verb whose clause fails the STRICT person test (ro.PERSON
    alone, never the capitalised fallback) and whose subject is on the
    allowlist, swapped for the thing's own motion verb."""
    from studio import episode_ref_official as ro
    body = ro.blank_measures(text)
    out, last = [], 0
    for m in ro.GAIT.finditer(body):
        head = ro.clause_head(body, m.start())
        verb = _swapped_gait(m.group(0))
        if verb is None or ro.PERSON.search(head) \
                or not any(w.strip(",.;:").lower() in FIGURATIVE for w in head.split()):
            continue
        out.append(text[last:m.start()] + verb)
        last = m.end()
    return "".join(out) + text[last:]


def figurative_gaits(doc: dict) -> dict:
    """L8 on a non-person subject: fire spreads, water streams -- a person's
    walk is never touched, so `pace_words` still handles it the same round."""
    for holder, f in _prose_fields(doc):
        if holder.get(f):
            holder[f] = _figurative(holder[f])
    return doc


def drop_thing_pace(doc: dict) -> dict:
    """L23: a pace phrase on a clause whose subject cannot walk is deleted --
    the exact inverse of `pace_words`, and like it idempotent."""
    from studio import episode_ref_official as ro

    def stripped(text: str) -> str:
        out, last = [], 0
        for m in ro.PACE_MARK.finditer(text):
            if not ro.is_person(ro.clause_head(text, m.start())):
                out.append(text[last:m.start()].rstrip())
                last = m.end()
        return re.sub(r" {2,}", " ", "".join(out) + text[last:])

    for holder, f in _prose_fields(doc):
        if holder.get(f):
            holder[f] = stripped(holder[f])
    return doc


SLOW_WORD = re.compile(r",?\s*\bslow(ly)?\b", re.I)


def strip_slow(doc: dict) -> dict:
    """L3: 'slow(ly)' deleted with its comma; the limp carries the slowness
    (`ro.limp_clause`'s own doctrine)."""
    for holder, f in _prose_fields(doc):
        if holder.get(f) and SLOW_WORD.search(holder[f]):
            out = re.sub(r" {2,}", " ", SLOW_WORD.sub("", holder[f]))
            holder[f] = re.sub(r"(^|[.;!?]\s*),\s*", r"\1", out).strip()
    return doc


def apply_limp(doc: dict, indices: list[int]) -> dict:
    """L9: the limp written at the first gait of the flagged shot (`ro.limp`,
    the function the owner's D12 rule already owns)."""
    from studio import episode_ref_official as ro
    by = {s["index"]: s for s in doc.get("shots") or []}
    for i in indices:
        s = by.get(i)
        for f in SHOT_FIELDS if s else ():
            if s.get(f) and ro.gaits(s[f]) and "limp" not in s[f].lower():
                s[f] = ro.limp(s[f])
                break
    return doc


def strip_banned_prop(doc: dict, cast_rows: str = "") -> dict:
    """L18: a banned-prop word deleted from plan prose when no bound cast row
    bears it (a row-borne word is the gate's own exemption); residue to llm."""
    from studio.episode_spec import BANNED_PROPS
    rows = (cast_rows or "").lower()
    for holder, f in _prose_fields(doc):
        text = holder.get(f) or ""
        cured = text
        for w in BANNED_PROPS:
            if w not in rows:
                cured = re.sub(rf"(?:\b(?:the|a|an|his|her|their)\s+)?\b{re.escape(w)}s?\b\s*",
                               " ", cured, flags=re.I)
        if cured != text:
            holder[f] = re.sub(r" {2,}", " ", cured).replace(" .", ".").replace(" ,", ",").strip()
    return doc


def _continuation(motion: str) -> str:
    """The legal L21 closing clause, built from the motion's own head;
    'continues' satisfies ro.MOVER and the L11 comment names it legal."""
    head = re.sub(r"^The camera\s*", "", (motion or "").partition(";")[0].strip(),
                  flags=re.I).strip(" .")
    if not head or "locked" in head.lower():
        return "The camera's move continues to the last frame of the shot."
    return f"The {head} continues to the last frame of the shot."


def arrival_ends(doc: dict, indices: list[int]) -> dict:
    """L21's cure: the layout-final sentence of `end` (else `at_rest`) is
    deleted when an earlier sentence already moves, else replaced with the
    motion head's own continuation clause."""
    from studio import episode_ref_official as ro
    by = {s["index"]: s for s in doc.get("shots") or []}
    for i in indices:
        s = by.get(i)
        if not s:
            continue
        field = "end" if s.get("end") else "at_rest"
        said = ro.sentences(s.get(field) or "")
        if not said or not ro.LAYOUT.search(said[-1]):
            continue
        if any(ro.MOVER.search(x) or ro.ACTION.search(x) for x in said[:-1]):
            s[field] = " ".join(said[:-1])
        else:
            s[field] = " ".join(said[:-1] + [_continuation(s.get("motion") or "")])
    return doc


# ---- G-CURE-VERIFY: the guarded llm field cures -----------------------------------

MAX_LLM_CURES = 24
"""The most llm field cures one plan_repair run may pay for: ~$0.0004 a call
on the workhorse tier, <= $0.01 an episode at the cap (guard_spend still walls
each call at the $3 episode ceiling)."""

BANNED_WORDS = re.compile(r"\b(still|stays?|remains?|motionless|frozen|pauses?|waits?|"
                          r"unchanged|unmoving|holds?|held|slow|slowly)\b", re.I)


class RewrittenField(BaseModel):
    """One rewritten plan/row/card field, nothing else."""
    text: str


RULE_HELP = {
    "L1": "state what IS in the frame, never what is not",
    "L2": "say the body's rest as placement and contact, never a stillness word",
    "L4": "give the block one body-scale action: a turn, a reach, a step at a normal walking pace",
    "L8": "any walk, climb or ride by a person ends its clause with 'at a normal walking pace'",
    "L14": "condense, keep every concrete visual fact",
    "L19": "split or shorten the sentence under 20 words",
    "L21": "end on the camera or a moving body, never a layout word",
    "L22": "remove the named absent person; describe the staged faces only",
}
"""One paragraph of canned help per rule family the llm cure may be handed."""


def verify_family(rule_id: str, text: str, old: str = "", need: int = 0) -> bool:
    """G-CURE-VERIFY: the lint family that ordered the rewrite re-passes on
    the rewritten text, and no banned word or negation was introduced -- the
    gates' own regexes, never the model's judgement of itself."""
    from studio import episode_ref_official as ro
    body = ro.scrub(text).replace("holds a static shot", " ")
    if BANNED_WORDS.search(body) or ro.NEGATIONS.search(body):
        return False
    if rule_id == "L2":
        return not ro.STILL.search(body)
    if rule_id == "L8":
        return not ro.gaits(body) or any(p in body.lower() for p in ro.PACE)
    if rule_id == "L21":
        last = (ro.sentences(text) or [""])[-1]
        return not ro.LAYOUT.search(last) and bool(
            ro.MOVER.search(last) or ro.ACTION.search(last) or ro.GAIT.search(last))
    if rule_id == "L14" and need:
        return len(text.split()) - len(old.split()) >= need
    return True


FIELD_PROMPT = """You are rewriting ONE field of a film-shot plan so it passes a mechanical lint. Change only what the fault requires; keep every concrete visual fact.
The fault: {fault_row}
The rule: {rule_help}
The field ({layer_said}) current text:
---
{text}
---
Hard constraints:
- never use: still, stays, remains, motionless, frozen, pauses, waits, unchanged, unmoving, holds, held, slow, slowly
- no negations (no, not, never, nobody, nothing, without, barely, hardly)
- any walk, climb or ride by a person ends its clause with 'at a normal walking pace'; a fire, road, town or light never walks or climbs - it spreads, runs or streams
- the final sentence names the camera or a moving body, never a layout word (edge, corner, twice, taller, smaller, larger, half)
- keep within {cap} words; invent nothing the plan does not already stage
Return the rewritten field text only."""

ENRICH_PROMPT = """You are enriching ONE field of a film-shot plan so its built take prompt reaches the length floor.
Shot {index}'s block is {n} words; the floor is {low} words.
The field is shots[{index}].at_rest. Current text:
---
{at_rest}
---
The shot's frame: {frame}
The setup: {described}
Add 1-3 sentences of VISIBLE at-rest state already implied by the frame and setup - posture, hands, light on surfaces, placement in the frame. Hard constraints:
- never use: still, stays, remains, motionless, frozen, pauses, waits, unchanged, unmoving, holds, held, slow, slowly
- no negations (no, not, never, without, barely, hardly)
- any walk, climb or ride by a person ends its clause with 'at a normal walking pace'
- the final sentence names the camera or a moving body, never a layout word (edge, corner, half, taller, smaller, larger)
- invent no object, person or light source the frame and setup do not name
Return the full enriched at_rest text."""


def _rule_of(row: str) -> str:
    m = re.search(r"\bL(\d+)\b", row)
    return f"L{m.group(1)}" if m else ""


def _layer_of(row: str) -> tuple[str, str]:
    """('plan'|'row'|'card', ident) off the fault row's layer tag."""
    m = re.search(r"\[(row|card) ([\w-]+)\]", row)
    return (m.group(1), m.group(2)) if m else ("plan", "")


def _flagged_words(row: str) -> list[str]:
    return [w.lower() for w in re.findall(r"'([^']+)'", row)]


def _plan_target(doc: dict, row: str) -> tuple[dict, str] | None:
    """The (shot, field) whose prose carries the fault's flagged word, on the
    shot the row names; a wordless family defaults to end/at_rest."""
    m = re.search(r"shot (\d+)", row)
    shot = next((s for s in doc.get("shots") or []
                 if m and s.get("index") == int(m.group(1))), None)
    if shot is None:
        return None
    for f in SHOT_FIELDS:
        text = (shot.get(f) or "").lower()
        if text and any(re.search(rf"\b{re.escape(w)}\b", text) for w in _flagged_words(row)):
            return shot, f
    default = {"L21": "end" if shot.get("end") else "at_rest"}.get(_rule_of(row), "at_rest")
    return shot, default


def _asked(tier: str, prompt: str, rule: str, old: str, need: int, _agent):
    """One structured rewrite, verified in code; ONE re-ask with the
    verifier's complaint, then None -- a failed cure never silently ships."""
    from studio import llm
    got = llm.structured(tier, prompt, RewrittenField, _agent=_agent)
    if verify_family(rule, got.text, old, need):
        return got.text
    got = llm.structured(tier, llm.re_ask(prompt, RuntimeError(
        f"the rewrite fails the {rule} lint family or reintroduces a banned word")),
        RewrittenField, _agent=_agent)
    return got.text if verify_family(rule, got.text, old, need) else None


def _target_text(book, doc: dict, row: str, layer: str, ident: str) -> str | None:
    if layer == "plan":
        found = _plan_target(doc, row)
        return found[0].get(found[1]) if found else None
    from studio import row_lint
    return row_lint.read_row_text(book, layer, ident)


def _write_target(book, doc: dict, row: str, layer: str, ident: str, text: str) -> dict:
    if layer == "plan":
        holder, field = _plan_target(doc, row)
        holder[field] = text
        return doc
    from studio import row_lint
    row_lint.write_row_text(book, layer, ident, text)
    return doc


def llm_field_cure(book, doc: dict, fault_row: str, tier: str = "workhorse",
                   _agent=None) -> tuple[dict, bool]:
    """One guarded workhorse rewrite of the ONE field the fault names, on its
    own layer (plan field / refs row / props card), accepted only through
    G-CURE-VERIFY.  `_agent` is the test seam; the real caller runs
    guard_spend before anything is sent (studio.llm)."""
    layer, ident = _layer_of(fault_row)
    rule = _rule_of(fault_row)
    old = _target_text(book, doc, fault_row, layer, ident)
    if old is None:
        return doc, False
    prompt = FIELD_PROMPT.format(fault_row=fault_row,
                                 rule_help=RULE_HELP.get(rule, "fix exactly the fault named"),
                                 layer_said=f"{layer} {ident}".strip(), text=old,
                                 cap=max(80, len(old.split()) + 40))
    text = _asked(tier, prompt, rule, old, 0, _agent)
    if text is None:
        return doc, False
    return _write_target(book, doc, fault_row, layer, ident, text), True


def enrich_at_rest(doc: dict, index: int, need_words: int, tier: str = "workhorse",
                   _agent=None) -> tuple[dict, bool]:
    """L14's plan-side lever: at_rest enriched with visible at-rest state, one
    structured call, accepted only when the word delta reaches the need and
    no banned word rode in (G-CURE-VERIFY's L14 arm)."""
    shot = next((s for s in doc.get("shots") or [] if s.get("index") == index), None)
    if shot is None:
        return doc, False
    setup = (doc.get("setups") or {}).get(shot.get("setup")) or {}
    old = shot.get("at_rest") or ""
    prompt = ENRICH_PROMPT.format(index=index, n=len(old.split()),
                                  low=len(old.split()) + need_words, at_rest=old,
                                  frame=shot.get("frame") or "",
                                  described=setup.get("described") or "")
    text = _asked(tier, prompt, "L14", old, need_words, _agent)
    if text is None:
        return doc, False
    shot["at_rest"] = text
    return doc, True


# ---- the dispatcher ---------------------------------------------------------------

CURES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"G-GHOST"), "ghost_limbs"),
    (re.compile(r"G-TWICE"), "one_position"),
    (re.compile(r"shots are numbered|lines are numbered|a line's shot never precedes"), "renumber"),
    (re.compile(r"G-LIGHT"), "light_directions"),
    (re.compile(r"G-SIZE"), "head_fractions"),
    (re.compile(r"bed span from_shot"), "clamp_beds"),
    # The G-TAKELINT families, most specific first.  A row tagged [row]/[card]
    # is cured in ITS OWN file, never the plan, so that route outranks every
    # word cure; figurative_gaits sits ABOVE the generic NO PACE row so a
    # thing's gait is swapped before a blind pace append can land on it.
    (re.compile(r"\[(?:row|card) [\w-]+\]"), "row_words"),
    (re.compile(r"L2 STILLNESS.*\[plan\]"), "stillness_words"),
    (re.compile(r"L8 NO PACE.*\[plan\]"), "figurative_gaits"),
    (re.compile(r"L21 ARRIVAL"), "arrival_ends"),
    (re.compile(r"L23 PACE ON A THING"), "drop_thing_pace"),
    (re.compile(r"L3 SLOW"), "strip_slow"),
    (re.compile(r"L9 NO LIMP"), "apply_limp"),
    (re.compile(r"L16 DIALOGUE TAIL"), "holds"),
    (re.compile(r"L18 BANNED PROP"), "strip_banned_prop"),
    (re.compile(r"NO PACE"), "pace_words"),
    (re.compile(r"beat of >= 1\.0 s of silence"), "button_beat"),
    (re.compile(r"G-MOVES|G-STILL|G-AIM|G-ANCHOR|\bM2 shot \d+:"), "rebalance_heads"),
    (re.compile(r"G-SOURCE shot \d+: span .* is not in the chapter"), "source_spans"),
    (re.compile(r"QUOTE\s+: \["), "quote_trim"),
    # The stage families sit ABOVE the legal_props catch-all: its bare 'prop '
    # alternative would otherwise swallow them into a no-op cure.
    (re.compile(r"G-STAGE setup \S+: bare creature word"), "strip_creatures"),
    (re.compile(r"G-STAGE"), "stage_machines"),
    (re.compile(r"G-FACE-KIND"), "drop_creature_faces"),
    (re.compile(r"prop '.+' has no chapter span"), "prop_spans"),
    (re.compile(r"props.*\.json|names setup .* not defined|prop (?!.*no chapter span)"), "legal_props"),
    (re.compile(r"G-CROWD-CLOSE"), "close_crowds"),
    (re.compile(r"G-PHANTOM"), "strip_phantoms"),
    (re.compile(r"projects to .* an episode is|ONE PER TAKE|TAKE LENGTH|G-SETUP|G-HOLE|hole in speech|of the runtime"), "holds"),
    (re.compile(r"median (?:frame-edge|at_rest)"), "edge_cases"),
    (re.compile(r"G-ASPECT|style line is \d+ words|look"), "pin_series"),
]
"""Fault-text patterns -> cure names, most specific first.  A row matching
nothing is CREATIVE and goes back to the writer, one field at a time."""


def clamp_beds(doc: dict) -> dict:
    """G-BED: keep only bed spans whose int `from_shot` names a shot with a
    CUT shot at or after it, sorted into story order; an emptied list is
    legal -- one plain span end to end (episode_bed.spans)."""
    shots = len(doc.get("shots") or [])
    omit = set(doc.get("omit") or [])
    cut = [i for i in range(shots) if i not in omit]
    kept = [b for b in doc.get("beds") or []
            if isinstance(b.get("from_shot"), int) and not isinstance(b.get("from_shot"), bool)
            and 0 <= b["from_shot"] < shots and any(i >= b["from_shot"] for i in cut)]
    doc["beds"] = sorted(kept, key=lambda b: b["from_shot"])
    return doc


def close_crowds(doc: dict) -> dict:
    """G-CROWD-CLOSE: a close or medium-close shot carries no crowd; wides keep theirs."""
    for s in doc.get("shots") or []:
        if s.get("size") in ("close", "medium_close", "big_close") and s.get("crowd"):
            s["crowd"] = ""
    return doc


def cure_for(fault_row: str) -> str | None:
    for pattern, name in CURES:
        if pattern.search(fault_row):
            return name
    return None


# ---- G-PHANTOM: the empty stage ---------------------------------------------------

MAX_SETUPS = 8
"""The most setups one repair run may pay to rewrite: one llm round per run,
<=~$0.01 a setup on the workhorse tier, under the $3 episode ceiling."""


def split_sentences(text: str) -> list[str]:
    """The gate's own sentence split (plan_gates.SENTENCE_SPLIT), kept-only."""
    from studio import plan_gates
    return [s for s in plan_gates.SENTENCE_SPLIT.split(text or "") if s.strip()]


def floor_for(field: str) -> int:
    """The G-FIRSTFRAME per-setup word floor a cured field must keep -- a
    conservative per-setup bound that guarantees the plan MEDIAN floor holds."""
    from studio import plan_gates
    return plan_gates.DESCRIBED_WORDS if field == "described" else plan_gates.GEOMETRY_WORDS


def strip_phantoms(doc: dict, names: dict, place_words: set) -> tuple[dict, list[str]]:
    """G-PHANTOM's mechanical cure: delete each offending sentence, found with
    the gate's own `phantom_hits` -- the cure MEASURES LIKE THE CHECKER.  A
    deletion that would drop the field under its floor is not committed; the
    setup comes back as residue for the llm cure.  $0."""
    from studio import plan_gates
    residue: list[str] = []
    for name, s in (doc.get("setups") or {}).items():
        for field in ("described", "geometry"):
            bad = {sent for sent, _ in plan_gates.phantom_hits(s.get(field) or "", names, place_words)}
            if not bad:
                continue
            kept = " ".join(sent for sent in split_sentences(s.get(field) or "") if sent not in bad)
            if len(kept.split()) >= floor_for(field):
                s[field] = kept
            elif name not in residue:
                residue.append(name)
    return doc, residue


class SetupRewrite(BaseModel):
    """One setup's two fields, rewritten people-free (G-PHANTOM's llm cure)."""
    described: str
    geometry: str


PHANTOM_PROMPT = """You are rewriting ONE setup description for a storyboard pipeline.
Every sentence below is pasted verbatim into every image prompt of this place, so any person or
creature it names is DRAWN into every frame of every shot as a phantom extra.

SETUP: {name}

DESCRIBED (current):
{described}

GEOMETRY (current):
{geometry}

Rewrite both fields under these rules:
1. Remove every mention of a person or creature. Banned names and their possessive forms: {banned}.
   Also banned as bare words: man, men, woman, women, people, person, figure, figures, child,
   children, boy, girl, crowd, onlooker, bystander.
   Keep what each such sentence says about the PLACE itself: 'The narrator and the curate approach
   along the dusted roadway' becomes 'The dusted roadway runs toward the gate, dust lying thick on it.'
2. Keep every object, surface, distance and frame-edge placement already present. Invent no new objects.
3. DESCRIBED must name one light source WITH a direction -- a practical (lamp, fire, window, doorway)
   or sky light plus where it falls from, e.g. 'Grey daylight comes from the LEFT, low from the west'
   or 'A low fire burns in the hearth, deep shadow beyond it.' A brightness alone ('hard morning
   sunlight') is refused, and an overhead sun is refused.
4. DESCRIBED stays at or above {described_floor} words and GEOMETRY at or above {geometry_floor} words;
   reach the floor by describing the place's fixed things, never by naming people.
5. Plain declarative present-tense sentences. No camera words, no story events, no sound.
Return both rewritten fields in full."""


def phantom_prompt(name: str, setup: dict, names: dict) -> str:
    from studio import plan_gates
    return PHANTOM_PROMPT.format(
        name=name, described=setup.get("described") or "", geometry=setup.get("geometry") or "",
        banned=", ".join(sorted(names)), described_floor=plan_gates.DESCRIBED_WORDS,
        geometry_floor=plan_gates.GEOMETRY_WORDS)


def rewrite_faults(got: SetupRewrite, names: dict, place_words: set) -> list[str]:
    """Why a rewrite is refused IN CODE: the gates' own measures, re-run on the
    answer -- never the model's own judgement of itself."""
    from studio import plan_gates
    out = [f"{field} still names {token!r}" for field in ("described", "geometry")
           for _, token in plan_gates.phantom_hits(getattr(got, field), names, place_words)]
    if not has_light_direction(got.described):
        out.append("described names no light source with a direction")
    for field in ("described", "geometry"):
        if len(getattr(got, field).split()) < floor_for(field):
            out.append(f"{field} is under {floor_for(field)} words")
    return out


def _rewritten(prompt: str, names: dict, place_words: set, caller) -> SetupRewrite | None:
    """One validated rewrite: a failing answer is re-asked ONCE with its
    refusal appended; a second failure returns None and the fault row stands
    (default ESCALATE for anything judgement could not settle)."""
    from studio import llm
    got = llm.structured("workhorse", prompt, SetupRewrite, _agent=caller)
    why = rewrite_faults(got, names, place_words)
    if not why:
        return got
    got = llm.structured("workhorse", llm.re_ask(prompt, RuntimeError("; ".join(why))),
                         SetupRewrite, _agent=caller)
    return got if not rewrite_faults(got, names, place_words) else None


def rewrite_setups(doc: dict, names: dict, place_words: set, setup_names: list[str],
                   caller=None) -> tuple[dict, list[str]]:
    """The workhorse-tier rewrite for setups the strip could not cure: one
    `studio.llm.structured` call per setup, at most MAX_SETUPS of them.
    `caller` is the `_agent` test seam; the real caller it defaults to runs
    `guard_spend` against the episode ceiling before anything is sent."""
    uncured = list(setup_names[MAX_SETUPS:])
    for name in setup_names[:MAX_SETUPS]:
        s = (doc.get("setups") or {}).get(name)
        if s is None:
            continue
        got = _rewritten(phantom_prompt(name, s, names), names, place_words, caller)
        if got is None:
            uncured.append(name)
        else:
            s["described"], s["geometry"] = got.described, got.geometry
    return doc, uncured
