"""The plan cure table: every MECHANICAL battery fault repaired by template,
never by a writer call.

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

    for s in doc.get("shots") or []:
        for f in ("frame", "at_rest", "end", "motion"):
            if s.get(f):
                s[f] = paced(s[f])
    for st in (doc.get("setups") or {}).values():
        for f in ("described", "crowd", "geometry"):
            if st.get(f):
                st[f] = paced(st[f])
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


def holds(doc: dict, rate: float = 3.0) -> dict:
    """The hold algebra, solved the way the ep15 session solved it by hand:
    the band floor is lifted with PRE-TURN codas (the turn ratio rises with
    them); a take-sharing pair grows past the budget; a setup past its cap is
    shaved from shots outside the pairs.  Every move stays inside MAX_BEAT /
    MAX_CODA and leaves the button's breath alone."""
    shots = doc.get("shots") or []
    if not shots:
        return doc
    by = {s["index"]: s for s in shots}
    turn_at = next((s["index"] for s in shots if s.get("section") == "turn"), len(shots) // 2)
    voiced = {line["shot"] for line in doc.get("lines") or []}

    # 1. ONE PER TAKE: consecutive pairs under the budget grow past it
    secs = _shot_secs(doc, rate)
    for a, b in zip(shots, shots[1:]):
        i, j = a["index"], b["index"]
        if a.get("setup") != b.get("setup"):
            continue
        need = TAKE_BUDGET_S + 0.3 - (secs[i] + secs[j])
        for s in (a, b, a, b):
            if need <= 0:
                break
            for key, cap in (("coda_s", MAX_CODA_S), ("beat_s", MAX_BEAT_S)):
                room = cap - float(s.get(key) or 0)
                if need > 0 and room > 0.1 and s["index"] in voiced:
                    add = round(min(need, room, 1.2), 2)
                    s[key] = round(float(s.get(key) or 0) + add, 2)
                    need = round(need - add, 2)
        secs = _shot_secs(doc, rate)

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

    # 3b. no speech hole after a line's last word: ep16's 6.14 s hole at shot
    # 23 was the VOICED shot's own coda plus its silent successor, found only
    # at the MEASURED timeline.  A hole starts where speech ENDS, so each cap
    # covers the preceding voiced shot's coda plus every unvoiced shot after
    # it, at HOLE_WALL_S - 0.5, shaved from the largest holds first.
    secs = _shot_secs(doc, rate)
    tail: list[tuple[dict, str]] = []   # (shot, key) pairs that make the hole
    hole = 0.0
    for s in shots + [None]:
        if s is not None and s["index"] not in voiced:
            tail += [(s, "coda_s"), (s, "beat_s")]
            hole += secs[s["index"]]
            continue
        over = hole - (HOLE_WALL_S - 0.5)
        for r, key in sorted(tail, key=lambda rk: -float(rk[0].get(rk[1]) or 0)):
            if over <= 0:
                break
            cut = round(min(over, float(r.get(key) or 0)), 2)
            if cut > 0:
                r[key] = round(float(r.get(key) or 0) - cut, 2)
                over = round(over - cut, 2)
        if s is not None:   # this voiced shot's coda opens the next hole
            tail, hole = [(s, "coda_s")], float(s.get("coda_s") or 0)

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
    return button_beat(doc)


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
    first = re.split(r"[,.;:]", physical or "", 1)[0].strip()
    said = " ".join(first.split()[:CLAUSE_WORDS])
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


# ---- the dispatcher ---------------------------------------------------------------

CURES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"shots are numbered|lines are numbered|a line's shot never precedes"), "renumber"),
    (re.compile(r"G-LIGHT"), "light_directions"),
    (re.compile(r"G-SIZE"), "head_fractions"),
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
    (re.compile(r"projects to .* an episode is|ONE PER TAKE|TAKE LENGTH|G-SETUP|hole in speech|of the runtime"), "holds"),
    (re.compile(r"median (?:frame-edge|at_rest)"), "edge_cases"),
    (re.compile(r"G-ASPECT|style line is \d+ words|look"), "pin_series"),
]
"""Fault-text patterns -> cure names, most specific first.  A row matching
nothing is CREATIVE and goes back to the writer, one field at a time."""


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
