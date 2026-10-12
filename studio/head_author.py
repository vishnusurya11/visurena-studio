"""A dossier head authored from the book's quoted words (FINAL §1 Open, C1_L §3).

The profile writer reports what the book says, and Stevenson names no hair, beard
or hat for Jekyll, Hyde or Utterson: the look table refused all three ("head
unauthored") and their sheets came out three near-identical men.  A head is then
AUTHORED, once, in `analysis/heads.json`:

    {"<who>": {"words": "<body sentence>. <hair>; <facial hair>; <hat>.",
               "sources": [{"chapter": 3, "quote": "<verbatim>"}], "inferred": "<what the text does not say>"}}

and lands in the dossier's `profile.physical` -- where the look table reads a
head (`look_timeline.body_layer`) -- only when every quote is in its chapter at
SPAN_MATCH, the words name hair, facial hair AND a hat, and no two bound
characters share a face (hair family + facial hair: the unique-looks rule).
Deterministic; no model call.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio import look_table as lt

SPAN_MATCH = 0.85
"""A source quote must be in its chapter at this ratio (look_timeline.SPAN_MATCH)."""
SUPERSEDED = re.compile(r"\b(?:hair|face|facial|beard|hats?)\b", re.I)
"""A profile sentence that NEGATES one of these ('gives no ... hair, face') is the
writer's note of a silence the authored head now fills: it is dropped."""


def unquoted(sources: list[dict], chapter_text) -> list[str]:
    """Every source quote not found in its chapter at SPAN_MATCH, as 'chN: quote'."""
    from studio import plan_gates
    missing = []
    for s in sources:
        text = chapter_text(int(s["chapter"])) or ""
        if not text or plan_gates.span_match(s["quote"], text) < SPAN_MATCH:
            missing.append(f"ch{s['chapter']}: {s['quote']}")
    return missing


def marker(words: str, name: str) -> str:
    """One head layer's closed marker read off the words."""
    text = lt.layer_text(words, "", name)
    return lt.hair_colour(text) if name == "hair" else lt.first_of(lt.TABLES[name], text)


def missing_layers(words: str) -> list[str]:
    """The head layers (hair, face, headwear) the words leave without a marker."""
    return [name for name in lt.HEAD if not marker(words, name)]


def face_of(words: str) -> tuple[str, str]:
    """(hair family, facial hair): what tells two men apart once the hats are off."""
    return lt.HAIR_FAMILY.get(marker(words, "hair"), ""), marker(words, "face")


def clashes(faces: dict[str, tuple[str, str]], authored: set[str]) -> list[str]:
    """Every pair of characters, one of them authored, sharing one whole face."""
    names, out = list(faces), []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (a in authored or b in authored) and all(faces[a]) and faces[a] == faces[b]:
                out.append(f"{a} and {b} share {faces[a][0]} hair, {faces[a][1]}")
    return out


def with_head(physical: str, words: str, old: str) -> str:
    """The physical with its old authored head and its negated-head notes gone, the words appended."""
    text = physical.replace(old, " ") if old else physical
    kept = [s for s in lt.SENTENCE.split(text.strip())
            if s.strip() and not (lt.NEGATION.search(s) and SUPERSEDED.search(s))]
    return " ".join(kept + [words.strip()]).strip()


def refusals(book: Path, heads: dict, rows: list[dict]) -> list[str]:
    """Why heads.json may not land: an unfound quote, an incomplete head, a shared face."""
    from studio import plan_brief
    out = []
    for who, entry in heads.items():
        if not (Path(book) / "analysis" / "characters" / f"{who}.json").exists():
            out.append(f"{who}: no dossier")
        if bad := unquoted(entry.get("sources") or [], lambda n: plan_brief.chapter_text(book, n)):
            out.append(f"{who}: quote not in its chapter -- {'; '.join(bad)}")
        if not entry.get("sources"):
            out.append(f"{who}: no source quote")
        if gaps := missing_layers(entry["words"]):
            out.append(f"{who}: the words name no {', '.join(gaps)}")
    faces = {who: face_of(e["words"]) for who, e in heads.items()}
    faces |= {r["entity_id"]: face_of(r.get("physical", "")) for r in rows if r["entity_id"] not in heads}
    return out + clashes(faces, authored=set(heads))


def apply(book: Path, rows: list[dict]) -> list[str]:
    """Every head of heads.json written into its dossier; refuses before writing any."""
    heads = json.loads((Path(book) / "analysis" / "heads.json").read_text(encoding="utf-8"))
    if why := refusals(book, heads, rows):
        raise SystemExit("REFUSED:\n  " + "\n  ".join(why))
    for who, entry in heads.items():
        path = Path(book) / "analysis" / "characters" / f"{who}.json"
        card = json.loads(path.read_text(encoding="utf-8"))
        prof = card.setdefault("profile", {})
        old = (prof.get("head") or {}).get("words", "")
        prof["physical"], prof["head"] = with_head(prof.get("physical") or "", entry["words"], old), entry
        path.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    return list(heads)
