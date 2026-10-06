#!/usr/bin/env python
"""episodes/epNN/youtube.json, generated: a mechanical frame around ONE paid call.

    uv run python scripts/publish/metadata.py <codex_id> <n> [--force]
    uv run python scripts/publish/metadata.py <codex_id> --seed

The last hand-written artifact on the publish path was this file.  Now every
part that is a FACT is composed from the book's own records -- source/book.json
+ the plan's chapter name make the title (series_of refuses a book that does
not name its series; nothing is ever hardcoded here), the cut's own sha8 and
take count make the _synthetic_note, and the AI-disclosure block is a code
constant with only the author's surname read in -- and ONE llm.structured call
writes the prose: synopsis, attribution, tags, grounded in the plan's lines
and shots with the two newest prior episodes' youtube.json of THIS book as the
voice to match (the code tree names no book; the voice lives in the library).

G-META checks every round: the exact series title, the disclosure verbatim,
every proper noun the synopsis claims present in the plan or a prior episode's
description, yp.spec's own walls, and the `_for.plan_sha8` binding that makes
a stale file regenerate.  Two grounding re-asks quoting the exact failed
checks, then the mechanical narration-lines fallback -- the pipeline never
blocks on prose.  guard_spend fires inside the call whenever a spend context
is open, which is why step 13 imports and calls this IN-PROCESS: a subprocess
has an empty spend context and would walk past the $3 wall.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic import BaseModel  # noqa: E402

from scripts.publish.youtube_retitle import series_of  # noqa: E402
from studio import episode_home, llm, plan_verdict, publish_lock  # noqa: E402
from studio import youtube_publish as yp  # noqa: E402

TIER = "reasoning"
RE_ASKS = 2
"""Grounding re-asks after the first answer; past them, the fallback."""
FEW_SHOT = 2
"""Prior episodes quoted whole in the brief: the newest two of this book."""

AI_DISCLOSURE = ("AI DISCLOSURE: the picture and the voices in this video are generated. "
                 "The words\nare {author}'s story, adapted; the performances are synthetic.")
"""The owner's statement to the platform, fixed in code: only the author's
surname varies, and it is read from the book's own record, never typed."""

PROMPT = """You are writing the YouTube description and tags for one episode of a serialized public-domain book adaptation. The ONLY facts you may use are in this brief; name no character, place or event that is not named here.

BOOK: {display_title} by {author}; series label "{series}"; this is episode {number} of {total}.
CHAPTER: "{chapter_title}"

THE EPISODE'S LINES, in order (every word actually heard):
{lines_block}

THE EPISODE'S SHOTS (frame + motion, abridged to one line each):
{shots_block}

PRIOR EPISODES OF THIS SERIES, for voice and format — match their tone, tense, paragraph rhythm and tag style; do not copy their events:
{few_shot_block}

Return exactly:
- synopsis_paragraphs: 2 to 4 short present-tense paragraphs telling what happens in THIS episode using only the lines and shots above; the last paragraph may land on the episode's closing beat and may quote one short line of dialogue from the lines block. No URLs, no hashtags, no channel name, no AI-disclosure text (it is appended separately).
- attribution_line: one sentence naming the chapter exactly as "{chapter_title}", the book, the author, its year if a prior episode's attribution names one, and that it is in the public domain — same shape as the priors.
- tags: 18 to 24 lowercase search tags, each 30 characters or fewer, no '#': start from the series' recurring tags {series_tags} (the intersection of the priors' tag lists, computed by the caller) and add this episode's own people, places and things from the brief."""


class ShortMetadata(BaseModel):
    """What the ONE call returns: the prose, and nothing mechanical."""
    synopsis_paragraphs: list[str]
    attribution_line: str
    tags: list[str]


# ---- the mechanical parts ------------------------------------------------------

def disclosure(author: str) -> str:
    """The fixed disclosure block for this book's author."""
    surname = str(author).split()[-1] if str(author).strip() else "the author"
    return AI_DISCLOSURE.format(author=surname)


def book_said(book) -> dict:
    """The book's own record; series_of has already refused a thin one."""
    return episode_home.read_json(Path(book) / "source" / "book.json")


ORDINALS = ("One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten")


def chapter_marker(book, number: int) -> tuple[str, str, int]:
    """(roman, title, part) of the book's own chapter `number` from book.json:
    'I. UNDER FOOT.' in part 2 -> ('I', 'Under Foot', 2)."""
    chapter = book_said(book)["chapters"][number]
    roman, _, rest = str(chapter.get("title", "")).partition(". ")
    title = rest.rstrip(". ").replace("“", "").replace("”", "")
    return roman.strip(), headline(title), int(chapter.get("part") or 1)


SMALL = {"a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"}


def headline(text: str) -> str:
    """Title case with the small words lower, the first always up:
    'WHAT WE SAW FROM THE RUINED HOUSE' -> 'What We Saw from the Ruined House'."""
    words = text.lower().split()
    return " ".join(w if (i and w in SMALL) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def house_style(prior_docs: list[dict]) -> tuple[str, str]:
    """(division word, year) from the series' own prior attributions:
    'Chapter XVI of Book One of ... (1898)' -> ('Book', '1898')."""
    said = " ".join(str(d.get("description", "")) for d in prior_docs)
    division = re.search(r"Chapter [IVXLC]+ of (\w+) ", said)
    year = re.search(r"\((\d{4})\)", said)
    return (division.group(1) if division else "Part"), (year.group(1) if year else "")


def attribution(book, number: int, prior_docs: list[dict]) -> str:
    """The attribution line, composed: a chapter number is a fact, never prose
    (ep18 dry run: the model wrote 'Chapter XVIII of Book One')."""
    roman, title, part = chapter_marker(book, number)
    division, year = house_style(prior_docs)
    said = book_said(book)
    work = said.get("display_title") or said.get("title", "")
    dated = f" ({year})" if year else ""
    return (f"Chapter {roman} of {division} {ORDINALS[part - 1]} of {said.get('author', '')}'s "
            f"{work}{dated}, \"{title}\", in the public domain.")


def composed_attribution(book, number: int, prior_docs: list[dict]) -> str | None:
    """The composed line when the book records its chapters, else None (the
    model's line stands, G-META still checks it)."""
    chapters = book_said(book).get("chapters") or []
    return attribution(book, number, prior_docs) if 0 <= number < len(chapters) else None


def title_for(book, number: int, plan: dict) -> str:
    """G-META check 1: composed from the book's own words, never typed."""
    series, display_title, total = series_of(book)
    return yp.series_title(display_title, number, total, plan["title"], series=series)


def publish_dir(book) -> Path:
    return Path(book) / "publish"


def _required(path: Path, what: str) -> str:
    """A per-book publish artifact, or the refusal that says how to seed it."""
    if not path.exists():
        raise SystemExit(f"{path} is missing: {what}; seed it once with "
                         f"`metadata.py <codex_id> --seed` or write it by hand")
    return path.read_text(encoding="utf-8").strip()


def footer(book) -> str:
    """The channel block between the attribution and the disclosure."""
    return _required(publish_dir(book) / "footer.txt",
                     "the channel banner every description carries")


def pipeline_note(book) -> str:
    """The book's model stack, the constant half of _synthetic_note."""
    return _required(publish_dir(book) / "pipeline_note.txt", "the book's model stack")


def cut_facts(home) -> tuple[str, int, int]:
    """(cut sha8, takes recorded, judge-cleared terminals), measured off disk."""
    engine, master, _qc = yp.deliverable(Path(home), "")
    sheet = episode_home.takes_under(Path(home), engine) / "shots.json"
    takes = len(episode_home.read_json(sheet)) if sheet.exists() else 0
    return yp.sha8(master), takes, len(publish_lock.judge_waivers(Path(home)))


def synthetic_note(book, home) -> str:
    """The model stack + this cut's own measured facts.  `deliverable` only
    returns a pair whose QC passed, so 'QC passed' is a measurement."""
    sha8, takes, cleared = cut_facts(home)
    return (f"{pipeline_note(book)} Cut {sha8}: QC passed, {takes}/{takes} takes, "
            f"{cleared} judge-signed terminal(s) auto-cleared.")


# ---- the priors: this book's own published voice --------------------------------

def priors(book, number: int) -> list[dict]:
    """Every OTHER episode's youtube.json under THIS book, newest first."""
    out = []
    for path in Path(book).glob("episodes/ep*/youtube.json"):
        tail = path.parent.name[2:]
        if tail.isdigit() and int(tail) != number:
            out.append({"episode": int(tail), **episode_home.read_json(path)})
    return sorted(out, key=lambda doc: doc["episode"], reverse=True)


def series_tags(prior_docs: list[dict]) -> list[str]:
    """The tags every prior shares, in the newest prior's own order."""
    if not prior_docs:
        return []
    rest = [set(doc.get("tags", [])) for doc in prior_docs[1:]]
    return [tag for tag in prior_docs[0].get("tags", []) if all(tag in s for s in rest)]


def few_shot_block(prior_docs: list[dict]) -> str:
    """The newest priors quoted whole: the voice, never the events."""
    parts = [f"--- Episode {doc.get('episode')} ---\n{doc.get('description', '')}\n"
             f"tags: {', '.join(doc.get('tags', []))}" for doc in prior_docs[:FEW_SHOT]]
    return "\n\n".join(parts) or "(none yet: this is the first episode of the book)"


# ---- the brief -------------------------------------------------------------------

def lines_block(plan: dict) -> str:
    """Every word actually heard, in playback order."""
    return "\n".join(f"L{line['index']:02d} [{line.get('kind', '')}] "
                     f"{line.get('speaker', '')}: {line['text']}"
                     for line in plan.get("lines", []))


def first_sentence(text: str) -> str:
    return str(text).split(". ")[0].strip().rstrip(".")


def shots_block(plan: dict) -> str:
    """One line per shot: the frame's first sentence and the motion's."""
    return "\n".join(f"S{shot['index']:02d} [{shot.get('size', '')}] "
                     f"{first_sentence(shot.get('frame', ''))}; "
                     f"{first_sentence(shot.get('motion', ''))}"
                     for shot in plan.get("shots", []))


def brief(book, number: int, plan: dict, prior_docs: list[dict]) -> str:
    """The whole prompt: every fact the model may use, and nothing else."""
    series, display_title, total = series_of(book)
    return PROMPT.format(
        display_title=display_title, author=book_said(book).get("author", ""),
        series=series, number=number, total=total, chapter_title=plan["title"],
        lines_block=lines_block(plan), shots_block=shots_block(plan),
        few_shot_block=few_shot_block(prior_docs),
        series_tags=", ".join(series_tags(prior_docs)))


# ---- G-META ----------------------------------------------------------------------

def cap_words(text: str) -> set[str]:
    """Every capitalized word -- the KNOWN side, where over-inclusion is safe."""
    return {word for word in re.findall(r"[A-Za-z][A-Za-z']+", text) if word[0].isupper()}


def candidate_nouns(text: str) -> set[str]:
    """Capitalized words past the first of each sentence: the names a synopsis
    actually claims (a sentence-leading 'The' is not a claim)."""
    out: set[str] = set()
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        words = re.findall(r"[A-Za-z][A-Za-z']+", sentence)
        out |= {word for word in words[1:] if word[0].isupper()}
    return out


def stem(word: str) -> str:
    """'Martians' matches 'Martian' (known risk: legitimate inflections)."""
    return word.removesuffix("'s").lower().rstrip("s")


def grounding_faults(meta: ShortMetadata, plan: dict, prior_docs: list[dict]) -> list[str]:
    """G-META check 3: every proper noun the synopsis claims is in the plan or
    a prior episode's description -- no invented people or places."""
    known = {stem(word) for word in cap_words(json.dumps(plan, ensure_ascii=False))}
    for doc in prior_docs:
        known |= {stem(word) for word in cap_words(str(doc.get("description", "")))}
    loose = sorted(word for word in candidate_nouns(" ".join(meta.synopsis_paragraphs))
                   if stem(word) not in known)
    return [f"synopsis names {word!r}, which is in neither the plan nor a prior episode"
            for word in loose]


def claim_faults(meta: ShortMetadata, doc: dict, book) -> list[str]:
    """G-META check 2: the disclosure verbatim, the attribution honest."""
    out = []
    if disclosure(book_said(book).get("author", "")) not in doc["description"]:
        out.append("description must carry the AI-disclosure block verbatim")
    _series, display_title, _total = series_of(book)
    low = meta.attribution_line.lower()
    if display_title.lower() not in low:
        out.append(f"attribution_line must name the book: {display_title}")
    if "public domain" not in low:
        out.append("attribution_line must say 'public domain'")
    return out


def wall_faults(doc: dict) -> list[str]:
    """G-META checks 4 and 5: the API's own walls, and the plan binding."""
    out = []
    try:
        yp.spec(doc.get("title", ""), doc.get("description", ""), doc.get("tags", []),
                synthetic=bool(doc.get("synthetic")), privacy=doc.get("privacy", "private"))
    except ValueError as why:
        out.append(str(why))
    if not (doc.get("_for") or {}).get("plan_sha8"):
        out.append("youtube.json must carry _for.plan_sha8")
    return out


def check(doc: dict, meta: ShortMetadata, book, number: int, plan: dict,
          prior_docs: list[dict]) -> list[str]:
    """G-META, HARD: every reason this metadata may not be written."""
    out = []
    if doc["title"] != title_for(book, number, plan):
        out.append(f"title must be exactly {title_for(book, number, plan)!r}")
    return out + claim_faults(meta, doc, book) + grounding_faults(meta, plan, prior_docs) \
        + wall_faults(doc)


# ---- generate --------------------------------------------------------------------

def description_of(meta: ShortMetadata, book) -> str:
    """Synopsis, attribution, the channel banner, the disclosure -- in order."""
    return "\n\n".join([*meta.synopsis_paragraphs, meta.attribution_line, footer(book),
                        disclosure(book_said(book).get("author", ""))])


def assemble(book, home, number: int, plan: dict, meta: ShortMetadata) -> dict:
    """The youtube.json document: mechanical frame + the call's prose."""
    return {"title": title_for(book, number, plan),
            "description": description_of(meta, book), "tags": list(meta.tags),
            "privacy": "private", "synthetic": True,
            "_synthetic_note": synthetic_note(book, home),
            "_for": {"plan_sha8": plan_verdict.plan_sha8(Path(home) / "plan.json")}}


def fallback(book, home, number: int, plan: dict, prior_docs: list[dict]) -> dict:
    """The terminal rung: a description with no prose call in it at all -- the
    plan's narration lines in order -- marked so a reader knows what it is."""
    narration = " ".join(line["text"] for line in plan.get("lines", [])
                         if line.get("kind") == "narration")
    _series, display_title, _total = series_of(book)
    author = book_said(book).get("author", "")
    attribution = f'"{plan["title"]}", from {display_title} by {author}, in the public domain.'
    return {"title": title_for(book, number, plan),
            "description": "\n\n".join([narration, attribution, footer(book),
                                        disclosure(author)]),
            "tags": series_tags(prior_docs), "privacy": "private", "synthetic": True,
            "_synthetic_note": synthetic_note(book, home),
            "_for": {"plan_sha8": plan_verdict.plan_sha8(Path(home) / "plan.json")},
            "_fallback": True}


def generate(book, home, number: int, *, _agent=None) -> dict:
    """ONE structured call inside the mechanical frame; G-META after each
    round; cap-2 grounding re-asks quoting the exact failed checks; then the
    narration-lines fallback -- the pipeline never blocks on prose."""
    home = Path(home)
    plan = episode_home.read_json(home / "plan.json")
    prior_docs = priors(book, number)
    prompt = brief(book, number, plan, prior_docs)
    asked = prompt
    for _ in range(RE_ASKS + 1):
        meta = llm.structured(TIER, asked, ShortMetadata, _agent=_agent)
        if composed := composed_attribution(book, number, prior_docs):
            meta = meta.model_copy(update={"attribution_line": composed})
        doc = assemble(book, home, number, plan, meta)
        if not (faults := check(doc, meta, book, number, plan, prior_docs)):
            return doc
        asked = llm.re_ask(prompt, RuntimeError("; ".join(faults)))
    return fallback(book, home, number, plan, prior_docs)


def recheck(home, book, number: int) -> list[str]:
    """What G-META can re-verify on a youtube.json already on disk (step 13
    asks before the upload; the prose checks ran when it was written)."""
    path = Path(home) / "youtube.json"
    if not path.exists():
        return [f"{path} does not exist"]
    doc = episode_home.read_json(path)
    plan = episode_home.read_json(Path(home) / "plan.json")
    out = []
    if doc.get("title") != title_for(book, number, plan):
        out.append("title is not the series format for this plan")
    if disclosure(book_said(book).get("author", "")) not in str(doc.get("description", "")):
        out.append("description lacks the AI-disclosure block")
    out += wall_faults(doc)
    if (doc.get("_for") or {}).get("plan_sha8") != plan_verdict.plan_sha8(Path(home) / "plan.json"):
        out.append("_for.plan_sha8 is stale: the plan moved since this was written")
    return out


def ensure(home, book, number: int, *, force: bool = False, _agent=None) -> Path:
    """youtube.json for the CURRENT plan: kept while G-META still accepts it,
    regenerated when absent, stale or over a wall.  Zero calls when kept."""
    path = Path(home) / "youtube.json"
    if not force and not recheck(home, book, number):
        return path
    doc = generate(book, home, number, _agent=_agent)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# ---- seeding the per-book publish artifacts ---------------------------------------

def footer_of(description: str) -> str:
    """The channel banner out of a prior description: the em-dash paragraph."""
    kept = [p for p in str(description).split("\n\n")
            if p.startswith("—") and "AI DISCLOSURE" not in p]
    if not kept:
        raise SystemExit("the newest prior description carries no channel banner "
                         "to seed from; write publish/footer.txt by hand")
    return "\n\n".join(kept)


def note_of(note: str) -> str:
    """The model stack out of a prior _synthetic_note, cut-specific tail off."""
    kept = re.split(r"\s+Cut [0-9a-f]{8}:", str(note))[0].strip()
    if not kept:
        raise SystemExit("the newest prior _synthetic_note says nothing; "
                         "write publish/pipeline_note.txt by hand")
    return kept


def seed(book) -> list[Path]:
    """publish/footer.txt + pipeline_note.txt, once, from the newest prior."""
    docs = priors(book, 0)
    if not docs:
        raise SystemExit(f"no episodes/ep*/youtube.json under {book} to seed from")
    room = publish_dir(book)
    room.mkdir(parents=True, exist_ok=True)
    wrote = []
    for name, text in (("footer.txt", footer_of(docs[0].get("description", ""))),
                       ("pipeline_note.txt", note_of(docs[0].get("_synthetic_note", "")))):
        if not (room / name).exists():
            (room / name).write_text(text + "\n", encoding="utf-8")
            wrote.append(room / name)
    return wrote


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    book = episode_home.book_dir(args[0])
    if "--seed" in argv:
        for path in seed(book):
            print(path)
        return 0
    number = episode_home.episode_arg(argv)
    home = episode_home.home(book, number)
    print(ensure(home, book, number, force="--force" in argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
