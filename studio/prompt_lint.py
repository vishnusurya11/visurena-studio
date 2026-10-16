"""Deterministic lints on an H3 take prompt, the plan behind it and the files on
disk: P1-P13, P14 (take side), P15, P17, P18 of the Jekyll ep01 prompt audit
(docs/audit/2026-10-15_jekyll_ep01_ref_audit/02_prompts.md, "Deterministic
lints").  Regex and set logic only: $0, no model, no GPU.  The grid-side
P14-P16 live in studio/grid_lint.py.

Every fault is one line, "P<n> <short name>: <evidence>".  Lint what is on
disk, not what the code would write now: a fix in code does not fix the plan
field or the prompt an older build wrote (audit LESSONS 2).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio import cast_alias

PERSON = r"tramp|child|girl|boy|woman|man|family|doctor|crowd|beggar|constable|policeman"
BAIT = r"cheques?|letters?|signs?|placards?|plates?|newspapers?|cards?|notes?|ledgers?"
META = r"associated with|described as|access to|residence|dossier|presented as|identifies"
TITLES = {"Mr.", "Mrs.", "Dr.", "Miss", "Mr", "Mrs", "Dr", "The", "the"}
DETERMINERS = {"the", "a", "an", "his", "her", "its", "their", "this", "that"}
SUBJECT_NOUNS = {"man", "men", "hand", "hands", "he", "she", "they", "woman", "women",
                 "girl", "boy", "child", "figure", "two"}
FINITE = {"turns", "holds", "keeps", "stands", "walks", "opens", "closes", "lifts", "points",
          "grips", "pushes", "strikes", "thrusts", "swings", "sways", "nods", "falls",
          "steps", "looks", "leans", "rises", "reaches", "takes", "watches"}
BARE = {"face", "turn", "hold", "stand", "walk", "open", "lift", "point", "look", "lean", "watch"}
ADJ_CUT = {"near", "far", "little", "small", "great", "old", "black", "brown", "grey", "dark",
           "pale", "bright", "narrow", "wide", "long", "open", "closed", "two", "three"}
VERTICAL = {"TOP", "CENTRE", "BOTTOM"}
POS = re.compile(r"\b((?:TOP|BOTTOM|CENTRE)(?: (?:LEFT|RIGHT))?|LEFT|RIGHT)\b")
SENT = re.compile(r"(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bSt)(?<=[.!?])\s+")
PLAN_FIELDS = ("frame", "motion", "at_rest", "end", "camera")
RENDER_CEILING = 7200
"""Seconds a graph may precede its mp4: takes_r2v writes the graph BEFORE the
render, so the mp4 lands one render later (ep01: up to 37 min).  T06's stale
graph was 20 h older than its mp4 (audit T22)."""


# ---- text helpers ---------------------------------------------------------------
def section(prompt: str, name: str) -> str:
    """One `name:` block of a take prompt, up to the next `word:` header."""
    m = re.search(rf"(?ms)^{re.escape(name)}:[ \t]*(.*?)(?=^[a-z_]+:|\Z)", prompt or "")
    return m.group(1) if m else ""


def sentences(text: str) -> list[str]:
    """Sentences, not split after Mr./Mrs./Dr./St."""
    return [s for s in SENT.split(text or "") if s.strip()]


def fault(rule: str, name: str, evidence: str) -> str:
    """One fault line; the evidence clipped to stay readable."""
    ev = " ".join(evidence.split())
    return f"{rule} {name}: {ev[:160]}"


def _has(alias: str, text: str) -> bool:
    return re.search(rf"(?i)\b{re.escape(alias)}\b", text) is not None


def definitions(prompt: str) -> dict[int, tuple[str, str]]:
    """{k: (name, text)} from the `<Subject k> is NAME in <Picture j>: TEXT` lines."""
    out = {}
    for line in section(prompt, "subject_definitions").splitlines():
        m = re.match(r"<Subject (\d+)> is (.+?) in <Picture \d+>: (.*)$", line.strip())
        if m:
            out[int(m.group(1))] = (m.group(2), m.group(3))
    return out


# ---- P1 / P2 / P3 ---------------------------------------------------------------------
def p1_case(text: str) -> list[str]:
    """A lowered first letter on an upper-case word: "tHE FOCUS"."""
    return [fault("P1", "case garble", m.group(0)) for m in re.finditer(r"\b[a-z][A-Z]{2,}\b", text)]


def p2_camera_is(text: str) -> list[str]:
    """"The camera is On the ..." -- a capital preposition mid-sentence."""
    return [fault("P2", "capital preposition", m.group(0)) for m in re.finditer(r"The camera is [A-Z]\w*", text)]


def p3_cure_lead(text: str) -> list[str]:
    """A ladder cure sentence read by the take builder as the opening noun phrase."""
    pat = r"The shot opens on (only the named|the named subject|the frame is cut|each person in the picture)[^.]*"
    return [fault("P3", "cure lead as noun phrase", m.group(0)) for m in re.finditer(pat, text)]


def cure_led(frame: str) -> list[str]:
    """A plan frame that starts with a panel_ladder cure sentence."""
    from studio.panel_ladder import CURES
    heads = {v.split("{")[0] for v in CURES.values()}
    lead = (frame or "").strip()
    return [fault("P3", "frame led by a cure", lead[:80]) for h in sorted(heads) if lead.startswith(h)][:1]


# ---- P4 / P5 --------------------------------------------------------------------------
def p4_binding(prompt: str, facts: dict) -> list[str]:
    """Every staged <Subject k> is cited in the shot text; no staged epithet stays free."""
    detail, faces = section(prompt, "detailed_description"), facts.get("faces") or []
    out = [fault("P4", "uncited subject", f"<Subject {k}> ({who}) never cited in detailed_description")
           for k, who in enumerate(faces, 1) if f"<Subject {k}>" not in detail]
    for k, who in enumerate(faces, 1):
        out += [fault("P4", "free alias", f"'{a}' left free; {who} is <Subject {k}>")
                for a in (facts.get("aliases") or {}).get(who, []) if _has(a, detail)]
    return out


def p5_parenthetical(text: str, facts: dict) -> list[str]:
    """A staged person described a second time in parentheses."""
    out = [fault("P5", "second description", m.group(0))
           for m in re.finditer(r"<Subject \d+> \((?!S\d+\))[^()]*\)", text)]
    for who in facts.get("faces") or []:
        for a in (facts.get("aliases") or {}).get(who, []):
            out += [fault("P5", "second description", m.group(0))
                    for m in re.finditer(rf"(?i)\b{re.escape(a)}\s*\([^()]*\)", text)]
    return out


# ---- P6 -------------------------------------------------------------------------------
def other_names(k: int, header: str, facts: dict) -> list[str]:
    """Capitalised cast names that are not this Subject's own person."""
    names, own = facts.get("cast_names") or {}, (facts.get("own") or {}).get(k)
    pool = [n for who, ns in names.items() if who != own for n in ns] if isinstance(names, dict) else list(names)
    mine = set(re.findall(r"[\w'-]+", header))
    return [n for n in pool if n[:1].isupper() and not set(re.findall(r"[\w'-]+", n)) <= mine]


def debris(s: str) -> str | None:
    """Why one definition sentence is debris, or None."""
    if len(re.findall(r"[\w'-]+", s)) < 4:
        return "short sentence"
    if re.search(r"\b(?:a long|a|an|the|to|of|with)\W*$", s, re.I):
        return "cut sentence"
    if m := re.search(rf"\b(?:{META})\b", s, re.I):
        return f"dossier meta '{m.group(0)}'"
    return None


def p6_definition(k: int, header: str, text: str, facts: dict) -> list[str]:
    """Each sentence of a Subject definition is whole, about this person, not dossier meta."""
    out, others = [], other_names(k, header, facts)
    for s in sentences(text):
        if why := debris(s):
            out.append(fault("P6", f"<Subject {k}> {why}", s))
        if hit := next((n for n in others if re.search(rf"\b{re.escape(n)}\b", s)), None):
            out.append(fault("P6", f"<Subject {k}> names {hit}", s))
    return out


# ---- P7 / P8 / P9 / P10 ---------------------------------------------------------------------
def p7_speaker(text: str) -> list[str]:
    """A speaker identity of three words or fewer, or one cut at an initial "A compact,"."""
    out = []
    for m in re.finditer(r"\(S\d+\), on screen, (?P<who>.*?),? with (?:a|an) [^.]*?voice", text):
        who = m.group("who")
        if len(re.findall(r"[\w'-]+", who)) <= 3 or re.search(r"(?:^|[.;] )A [\w-]+$", who):
            out.append(fault("P7", "stub speaker", m.group(0)))
    return out


def p8_line_ends(text: str) -> list[str]:
    """"as the line ends" and then "as he speaks" in the same segment."""
    out = []
    for s in sentences(text):
        i = s.find("as the line ends")
        if i >= 0 and re.search(r"\b(?:as|while) (?:he|she) speaks\b", s[i:]):
            out.append(fault("P8", "line ended yet speaking", s))
    return out


def p9_continues(text: str) -> list[str]:
    """"the lean continues" with no verb lean before it; "the opening" is always a noun
    (an aperture, in a door scene) whatever verb came before."""
    out = []
    for s in sentences(text):
        for m in re.finditer(r"\b[Tt]he (lean|opening) continues", s):
            before = s[:m.start()]
            verb = re.search(r"\bleans\b|\blean(?:ing)? (?:in|forward|back|over|toward|out|against)\b", before)
            if m.group(1) == "opening" or not verb:
                out.append(fault("P9", f"'{m.group(0)}' without its verb", s))
    return out


def finite_in(words: list[str]) -> bool:
    """A finite verb inside an end noun phrase ("the hand turns the key", "the two men face")."""
    for prev, w in zip(words, words[1:]):
        if w in FINITE and prev not in DETERMINERS:
            return True
        if w in BARE and prev in SUBJECT_NOUNS:
            return True
    return False


def p9_end_noun(text: str) -> list[str]:
    """"with the now in frame" and end noun phrases that hold a clause."""
    out = []
    for m in re.finditer(r"\bwith ((?:(?!\bwith\b)[^,.;])*?)\s*now in frame", text):
        words = m.group(1).lower().replace("face to face", "face-to-face").split()
        if len(words) <= 1 or finite_in(words):
            out.append(fault("P9", "garbled end noun", m.group(0)))
    return out


def p10_mouth(text: str) -> list[str]:
    """X's closed mouth tied to an action aimed "toward X" (the speaker's, not X's)."""
    out = []
    pat = r"(<Subject \d+>|\b\w+\.? \w+)'s mouth is closed[^.]*?\bwhile\b([^.]*)"
    for m in re.finditer(pat, text):
        if re.search(rf"\btoward {re.escape(m.group(1))}", m.group(2)):
            out.append(fault("P10", "closed mouth on the wrong person", m.group(0)))
    return out


# ---- P11 ------------------------------------------------------------------------------
def cut_word(w: str) -> bool:
    """An adjective or possessive standing where an aim's noun should be."""
    return w.endswith("'s") or (w.endswith("ed") and len(w) > 4) or w.lower() in ADJ_CUT


def p11_dangling(text: str) -> list[str]:
    """A camera clause that stops on an article, preposition or a cut noun phrase."""
    # not "her": an object pronoun may end a clause ("past her;")
    hits = [m.group(0) for m in re.finditer(r"\b(?:the|a|an|to|of|his|its|with)\s*[;,.]", text)]
    hits += [m.group(0) for m in re.finditer(r"[\w-]+'s\s*[;,.]", text)]
    hits += [m.group(0) for m in re.finditer(r"\bto the ([\w'-]+)(?=;|\s+as\b)", text) if cut_word(m.group(1))]
    return [fault("P11", "dangling aim", h) for h in hits]


def camera_text(detail: str) -> str:
    """The camera sentences of a shot text: those led by "The camera"."""
    return " ".join(s for s in sentences(detail) if s.strip().startswith("The camera"))


# ---- P13 / P14 / P15 ----------------------------------------------------------------------
def unbound(text: str, facts: dict) -> str:
    """The text with staged labels, staged epithets and past relative clauses removed."""
    text = re.sub(r"<Subject \d+>|<d>.*?</d>", " ", text)
    staged = set(facts.get("faces") or [])
    for who, names in (facts.get("aliases") or {}).items():
        for a in sorted(names, key=len, reverse=True) if who in staged else []:
            text = re.sub(rf"(?i)\b{re.escape(a)}\b(?:\s*\([^()]*\))?", " ", text)
    return re.sub(rf"(?i)\b(?:the|a|an)\s+(?:[\w-]+\s+)?(?:{PERSON})\s+who\b[^,.;:]*", " ", text)


def covered(noun: str, facts: dict) -> bool:
    """A person-noun that a staged face's own epithet or name already holds."""
    faces, aliases = facts.get("faces") or [], facts.get("aliases") or {}
    names = facts.get("cast_names") if isinstance(facts.get("cast_names"), dict) else {}
    words = {w.lower() for who in faces for n in aliases.get(who, []) + names.get(who, []) for w in n.split()}
    return noun.lower() in words


def aimless(text: str) -> str:
    """The text without "toward <someone>": a person aimed at off the frame's edge is not
    in the picture (the take builder aims such a move at the edge, `ro.offscreen`)."""
    return re.sub(r"(?i)\btoward (?:the |mr\. |mrs\. )?[\w'-]+(?: [\w'-]+)?", " ", text)


def p13_people(text: str, facts: dict) -> list[str]:
    """A person in the words who is neither staged, an extra, nor the setup's crowd."""
    staged = set(facts.get("faces") or [])
    out = [fault("P13", "unstaged person", f"'{a}' ({who}) is not staged")
           for who, names in (facts.get("aliases") or {}).items() if who not in staged
           for a in names if _has(a, aimless(text))]
    if int(facts.get("extras") or 0) > 0 or (facts.get("crowd") or "").strip():
        return out
    rest = unbound(text, facts)
    nouns = {m.group(1).lower() for m in re.finditer(rf"(?i)\b({PERSON})\b(?!')", rest)}
    return out + [fault("P13", "unstaged person", n) for n in sorted(nouns) if not covered(n, facts)]


def p14_lettering(detail: str, prompt: str) -> list[str]:
    """A noun that invites lettering, with no wordless/unlettered sentence."""
    if re.search(r"\b(?:unlettered|wordless)\b", prompt, re.I):
        return []
    found = sorted({m.group(0).lower() for m in re.finditer(rf"(?i)\b(?:{BAIT})\b", detail)})
    return [fault("P14", "lettering bait", ", ".join(found))] if found else []


def p15_lens(text: str, photoreal: bool) -> list[str]:
    """A lens length in a drawn book's prompt."""
    if photoreal:
        return []
    return [fault("P15", "lens in a drawn book", m.group(0)) for m in re.finditer(r"\b\d{2,3}mm\b", text)]


# ---- P17 -------------------------------------------------------------------------------
def p17_shoulder(text: str) -> list[str]:
    """Behind his X side puts his shoulder at the OTHER edge (behind RIGHT -> LEFT edge)."""
    who = r"(?:his|her|<Subject \d+>'s|the \w+'s|[A-Z][\w.]*(?: \w+)?'s)"
    out = []
    for m in re.finditer(rf"behind {who} (LEFT|RIGHT) (?:side|shoulder)", text):
        for e in re.finditer(r"\bshoulders?\b[^.]*?\b(?:(?:BOTTOM|TOP) )?(LEFT|RIGHT) (?:edge|corner)", text):
            if e.group(1) == m.group(1):
                out.append(fault("P17", "shoulder on the camera's side", f"{m.group(0)} / {e.group(0)}"))
    return out


def head(phrase: str) -> str:
    """The head noun of an aim: the last word before a trailing prepositional phrase."""
    core = re.split(r"\s(?:at|in|on|of|along|across|toward|beside|near|under|over)\s", phrase.strip())[0]
    words = re.findall(r"[\w-]+", core)
    return words[-1] if words else ""


def position(noun: str, phrase: str, text: str, skip: str) -> str | None:
    """Where the text places a noun: inline in its phrase, else the first sentence naming it."""
    if m := POS.search(phrase):
        return m.group(1)
    for s in sentences(text):
        i = re.search(rf"\b{re.escape(noun)}\b", s) if noun and s != skip else None
        clause = s[i.end():].split(";")[0] if i else ""
        if m := POS.search(clause):
            return m.group(1)
    return None


def p17_pan(text: str) -> list[str]:
    """A "pans from A to B" whose A and B sit one above the other is a tilt."""
    out = []
    for s in sentences(text):
        m = re.search(r"\bpans from (?P<a>.+?)\s+(?:(?:across|up|down|over|back)\s+)*to (?P<b>[^,;.]+)", s)
        if not m:
            continue
        pa = position(head(m.group("a")), m.group("a"), text, s)
        pb = position(head(m.group("b")), m.group("b"), text, s)
        if pa in VERTICAL and pb in VERTICAL and pa != pb:
            out.append(fault("P17", f"pan is a tilt ({pa} -> {pb})", m.group(0)))
    return out


# ---- P18 density ----------------------------------------------------------------------
def shot_blocks(detail: str) -> list[tuple[float, str]]:
    """[(seconds, block text)] per "[Shot n] From mm:ss to mm:ss." block."""
    pat = r"\[Shot \d+\] From (\d+):(\d+) to (\d+):(\d+)\."
    marks = list(re.finditer(pat, detail))
    out = []
    for i, m in enumerate(marks):
        a, b = int(m.group(1)) * 60 + int(m.group(2)), int(m.group(3)) * 60 + int(m.group(4))
        stop = marks[i + 1].start() if i + 1 < len(marks) else len(detail)
        out.append((float(max(1, b - a)), detail[m.start():stop]))
    return out


def actions(text: str) -> int:
    """Action clauses: camera moves, "At mm:ss" beats, "Then" sentences, ", then" joins."""
    n = sum(1 for s in sentences(text)
            if re.match(r"(?:The camera (?!is\b)\w+|At \d+:\d+|Then\b)", s.strip()))
    return n + len(re.findall(r"(?:[,;] then|\band then)\b", text))


def p18_density(block: str, frames: int | None = None, fps: int = 24) -> list[str]:
    """More than one action clause per 1.2 s of take time."""
    blocks = shot_blocks(block)
    seconds = frames / fps if frames else (blocks[0][0] if blocks else 0.0)
    n = actions(block)
    if seconds and n > max(1.0, seconds / 1.2):
        return [fault("P18", "too dense", f"{n} actions in {seconds:.2f} s")]
    return []


# ---- one take -------------------------------------------------------------------------
def take_text_faults(prompt: str, detail: str, facts: dict) -> list[str]:
    """The rules that read the whole prompt or the shot text alone."""
    return (p1_case(prompt) + p2_camera_is(prompt) + p3_cure_lead(detail) + p4_binding(prompt, facts)
            + p5_parenthetical(detail, facts) + p7_speaker(detail) + p8_line_ends(detail)
            + p9_continues(detail) + p9_end_noun(detail) + p10_mouth(detail))


def take_faults(prompt: str, facts: dict) -> list[str]:
    """Every P-rule fault in one H3 take prompt."""
    detail = section(prompt, "detailed_description")
    out = take_text_faults(prompt, detail, facts)
    for k, (name, text) in sorted(definitions(prompt).items()):
        out += p6_definition(k, name, text, facts)
    out += p11_dangling(camera_text(detail)) + p13_people(detail, facts)
    out += p14_lettering(detail, prompt) + p15_lens(detail, bool(facts.get("photoreal")))
    out += p17_shoulder(detail) + p17_pan(detail)
    blocks = shot_blocks(detail)
    for _, block in blocks:
        out += p18_density(block, facts.get("frames") if len(blocks) == 1 else None)
    return out


# ---- the plan (P12 and the plan-side P3/P11/P13/P17) ----------------------------------------
def p12_tags(text: str, rows: dict[str, str]) -> list[str]:
    """Each fragment a tag quotes from a person's row is still in that row, word for word."""
    out = []
    for said, frags in cast_alias.tags_in(text):
        who = cast_alias.owner_of(frags, rows)
        missing = [f for f in frags if who and cast_alias._words(f) not in cast_alias._words(rows[who])]
        if missing:
            out.append(fault("P12", f"stale tag on {who}", f"{said} ({', '.join(missing)})"))
    return out


def plan_texts(plan: dict) -> list[str]:
    """Every person-bearing text field of every shot."""
    return [s.get(f) or "" for s in plan.get("shots") or [] for f in PLAN_FIELDS]


def shot_facts(plan: dict, shot: dict, table: dict) -> dict:
    """What P13 needs for one plan shot."""
    setup = (plan.get("setups") or {}).get(shot.get("setup"), {}) or {}
    return {"faces": shot.get("faces") or [], "aliases": table, "extras": shot.get("extras") or 0,
            "crowd": f"{shot.get('crowd') or ''} {setup.get('crowd') or ''}"}


def shot_plan_faults(plan: dict, shot: dict, rows: dict, table: dict) -> list[str]:
    """P3, P11, P12, P13, P17 on one plan shot."""
    out = []      # a cure-led frame is the drawer's; P3 judges the take text (iter5)
    for f in PLAN_FIELDS:
        out += p12_tags(shot.get(f) or "", rows)
    out += p11_dangling(f"{shot.get('motion') or ''} {shot.get('camera') or ''}")
    words = " ".join(shot.get(f) or "" for f in ("frame", "motion", "at_rest", "end"))
    out += p13_people(words, shot_facts(plan, shot, table))
    return out + p17_shoulder(" ".join(shot.get(f) or "" for f in ("camera", "at_rest", "end")))


def plan_faults(plan: dict, rows: dict[str, str]) -> list[str]:
    """Every plan-side fault, its evidence led by the shot ("P13 ...: shot 22 tramp")."""
    table = cast_alias.aliases(plan_texts(plan), rows)
    out = []
    for n, shot in enumerate(plan.get("shots") or []):
        out += [f.replace(": ", f": shot {shot.get('index', n):02d} ", 1)
                for f in shot_plan_faults(plan, shot, rows, table)]
    return out


# ---- files (P18) ------------------------------------------------------------------------
def graph_prompt(graph: dict) -> str | None:
    """The render node's prompt: the *ToVideo node first, else any prompt input."""
    nodes = [n for n in (graph or {}).values() if isinstance(n, dict)]
    nodes.sort(key=lambda n: "ToVideo" not in str(n.get("class_type", "")))
    for n in nodes:
        if isinstance(p := (n.get("inputs") or {}).get("prompt"), str):
            return p
    return None


def file_faults(take_dir: Path) -> list[str]:
    """Each T<NN>.mp4's graph says the prompts.json prompt and is not older than the mp4."""
    take_dir = Path(take_dir)
    path = take_dir / "prompts.json"
    prompts = {r.get("index"): r.get("prompt") for r in json.loads(path.read_text(encoding="utf-8"))} if path.exists() else {}
    out = []
    for mp4 in sorted(take_dir.glob("T[0-9][0-9].mp4")):
        graph = mp4.with_name(f"{mp4.stem}.graph.json")
        if not graph.exists():
            continue
        if prompts.get(int(mp4.stem[1:])) not in (None, graph_prompt(json.loads(graph.read_text(encoding="utf-8")))):
            out.append(fault("P18", "stale graph", f"{graph.name} prompt differs from prompts.json"))
        if (lag := mp4.stat().st_mtime - graph.stat().st_mtime) > RENDER_CEILING:
            out.append(fault("P18", "stale graph", f"{graph.name} is {lag:.0f} s older than {mp4.name}"))
    return out


# ---- an episode ------------------------------------------------------------------------
def _read(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def characters(book: Path) -> list[dict]:
    """The book's character rows from refs/refs.json."""
    refs = _read(Path(book) / "refs" / "refs.json", {}).get("refs") or []
    return [r for r in refs if r.get("kind", "character") == "character" and r.get("entity_id")]


def row_words(r: dict) -> str:
    """A row's words, as cast_refs.tag reads them: physical plus every wardrobe state."""
    worn = r.get("wardrobe") or {}
    return " ".join([r.get("physical") or ""] + (list(worn.values()) if isinstance(worn, dict) else [str(worn)]))


def names_of(r: dict) -> list[str]:
    """A row's display and name, and each capitalised word of them that is not a title."""
    full = [n for n in (r.get("display"), r.get("name")) if n]
    words = [w for n in full for w in n.split() if w[:1].isupper() and w not in TITLES and len(w) > 2]
    return list(dict.fromkeys(full + words))


def facts_for(book: Path, rec: dict, plan: dict) -> dict:
    """What take_faults needs beyond the text, from the record, plan, rows and look."""
    rows = {r["entity_id"]: row_words(r) for r in characters(book)}
    shots = [s for n, s in enumerate(plan.get("shots") or []) if s.get("index", n) in (rec.get("shots") or [])]
    setups = plan.get("setups") or {}
    faces = rec.get("faces") or []
    return {"faces": faces, "own": {k: who for k, who in enumerate(faces, 1)},
            "aliases": cast_alias.aliases(plan_texts(plan), rows),
            "cast_names": {r["entity_id"]: names_of(r) for r in characters(book)},
            "photoreal": _read(Path(book) / "refs" / "look.json", {"look": "photoreal"}).get("look") == "photoreal",
            "extras": sum(int(s.get("extras") or 0) for s in shots),
            "crowd": " ".join(f"{s.get('crowd') or ''} {(setups.get(s.get('setup')) or {}).get('crowd') or ''}" for s in shots).strip(),
            "frames": rec.get("frames")}


def lint_episode(book: Path, number: int) -> dict:
    """{"takes": {idx: [faults]}, "plan": [faults], "files": [faults]} for one episode."""
    book = Path(book)
    ep = book / "episodes" / f"ep{int(number):02d}"
    take_dir = ep / "takes" / "r2v"
    plan = _read(ep / "plan.json", {})
    rows = {r["entity_id"]: row_words(r) for r in characters(book)}
    takes = {r["index"]: take_faults(r.get("prompt") or "", facts_for(book, r, plan))
             for r in _read(take_dir / "prompts.json", [])}
    return {"takes": takes, "plan": plan_faults(plan, rows), "files": file_faults(take_dir)}
