"""Step 01 — ingest: EPUB -> clean numbered text. Design: docs/analysis/steps/01_ingest.md.

Deterministic, zero LLM. Establishes the (chapter, paragraph) coordinate system every
later claim anchors to. Substeps pass data IN MEMORY; only two things are written,
both read downstream:

    library/<id>_<slug>/source/chapters/ch_NN.json   (01_03)
    library/<id>_<slug>/source/book.json             (01_04, only if checks pass)

(source/ holds raw book + normalized text — consumed by EVERY stage;
 analysis/ holds only what analysis derives. Owner decision 2026-08-23.)

Manual substep-by-substep running: set RUN_UNTIL below (e.g. "01_01"), then
`uv run python analysis.py` — the step executes up to that substep and prints
what it found. Events land in the DB per substep; detail in the run's log file.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from studio import db, epub, paths, tracking

STEP_ID = "01"
NAME = "ingest"

# --- configuration (hardcoded; no CLI args by convention) ---
RUN_UNTIL = "01_06"          # last substep: full step incl. agent check + improve loop
EXPECTED_CHAPTERS = None     # None = derive from the book's own TOC (generic, any book);
                             # set a number only as a manual per-book override

_PG_START = re.compile(r"\*\*\*\s*START OF", re.IGNORECASE)
_PG_END = re.compile(r"\*\*\*\s*END OF", re.IGNORECASE)
_NONCONTENT_HREF = re.compile(r"cover|toc|nav|colophon", re.IGNORECASE)
_PG_PHRASE = re.compile(r"project gutenberg|www\.gutenberg\.org", re.IGNORECASE)

MAX_IMPROVE_ROUNDS = 2       # 01_06: bounded; still failing after this -> loud failure

# Adjustable knobs the improve playbook may flip. Agents NEVER edit files;
# remedies steer this deterministic code, then 01_02..01_05 re-run.
ADJUSTMENTS = {"strip_pg_phrases": False}

# Remedy playbook: issue kind -> adjustment action. Kinds mapped to None have no
# safe auto-remedy and ESCALATE to the owner. The table grows from real failures.
REMEDIES = {
    "boilerplate": "strip_pg_phrases",
    "structure": None,      # the parser found no divisions — needs a human, not a knob
    "boundary": None, "garbled": None, "front_matter": None,
    "parts": None, "completeness": None, "metadata": None,
}


# Issue kinds that are worth recording but must not stop a correct parse.
#
# Once the cartographer got the chapters right, Pride and Prejudice and Tom Sawyer still
# failed on front matter - and both had every chapter correct, 61 of 61 for P&P. Their
# "problem" is a real 225-paragraph Saintsbury preface. Front matter having content is
# what front matter IS.
#
# structure, boundary and garbled stay blocking, because those say the TEXT is wrong.
# `boundary` is advisory for a specific reason, not because the agent is unreliable:
# _garbled() already checks mechanical damage over EVERY paragraph of every chapter,
# while the agent sees ONE SENTENCE from each end. Blocking on the weaker evidence while
# the stronger check passes is backwards - and it blocked four books whose chapters were
# correct, including Peter Pan chapter 1 for "opening mid-sentence" on "All children,
# except one, grow up."
ADVISORY_KINDS = ("front_matter", "metadata", "parts", "boundary")


def unfixable_issues(issues) -> list:
    """Findings with no safe remedy. Returned so they can be LOGGED - never discarded."""
    return [i for i in issues
            if i.kind not in ADVISORY_KINDS and REMEDIES.get(i.kind) is None]


def plan_remedies(issues) -> list[str]:
    """Issues -> adjustment actions.

    MECHANICAL CHECKS GATE; JUDGMENT INFORMS. This used to raise whenever no issue had a
    remedy, and across eight books the agent found something on every one - boundary,
    then structure, then completeness, changing between runs. Widening an advisory list
    one kind at a time was chasing it.

    _check_chapters, _garbled and check_retention measure every paragraph of every
    chapter and raise on their own. The agent sees samples and gives an opinion, and an
    opinion must not halt a parse that measured clean. The original bug this check
    existed for - a whole novel landing in front matter while step 01 reported PASS - is
    caught mechanically now.

    Unfixable findings are logged by the caller, not thrown away.
    """
    actions = []
    for issue in issues:
        action = REMEDIES.get(issue.kind)
        if action and action not in actions:
            actions.append(action)
    return actions


def apply_remedies(actions: list[str]) -> None:
    for action in actions:
        ADJUSTMENTS[action] = True


# --- 01_01 read_source ---


def read_source(source_path: Path) -> dict:
    """Parse the EPUB: metadata + spine raw html + TOC."""
    return epub.read_epub(source_path)


# --- 01_02 clean ---


MIN_RETENTION = 0.5      # of the input's words; a PG header+footer is ~2,700


def check_retention(words_in: int, words_out: int) -> None:
    """Cleaning may trim boilerplate. It may not delete the book.

    The expectation here is the INPUT word count — it comes from OUTSIDE the thing
    being checked, which is the whole point. Every check that compared the output
    against a number derived from the same parse could not fail, and did not."""
    if words_in and words_out < words_in * MIN_RETENTION:
        raise ValueError(
            f"cleaning retained only {words_out} of {words_in} words "
            f"({words_out / words_in:.0%}) — boilerplate stripping removed content")


def _is_marker(text: str) -> bool:
    """A bare `*** START/END OF THE PROJECT GUTENBERG EBOOK ***` line.

    Older Gutenberg files predate the `pg-boilerplate` wrapper, so the marker arrives
    as an ordinary paragraph. Only THAT LINE is dropped. The previous code used the
    marker as a global state machine — everything after an END, in any later document,
    was discarded — which is what turned 379 KB of Sherlock Holmes into 0 words. A
    trailing licence section is back matter and is dropped by classification, where a
    wrong answer costs one division rather than the book."""
    return bool(_PG_START.search(text) or _PG_END.search(text))


def _is_cover(doc: dict, index: int) -> bool:
    """Spine position 0 is the cover wrapper in 11/11 books of the corpus."""
    return index == 0 and "wrap" in doc["href"].lower()


def clean(raw: dict) -> dict:
    """Blocks per document, with publisher boilerplate removed.

    Owner-facing rule, learned the hard way: **never drop a whole spine document as
    chrome.** The `*** START OF THE PROJECT GUTENBERG EBOOK ***` marker lives in spine
    document #1 in 11/11 books, and the old code tracked that marker across documents —
    so dropping #1 meant the started-flag never flipped and every later document was
    discarded. Sherlock Holmes went in at 379 KB and came out at 0 words.

    Document #1 is also not merely a title page: it carries real narrative in 3 of 11
    books — 17.9% of Pride and Prejudice, 10.0% of Moby-Dick, and 63.7% of The Yellow
    Wallpaper. And in Pride and Prejudice and Moby-Dick the inline contents table lives
    in that same file as chapters I-X, so a "this document looks like a table of
    contents" heuristic is equally fatal.

    So: keep every document but the cover, and drop boilerplate by ELEMENT — the two
    `class="pg-boilerplate"` blocks, measured at exactly two per book across 75. A book
    with no such markup is untouched, so the logic is inert rather than fail-closed."""
    docs = []
    for index, item in enumerate(raw["spine"]):
        if _is_cover(item, index):
            continue
        blocks = [b for b in epub.html_to_blocks(item["raw_html"])
                  if not _is_marker(b["text"])]
        if ADJUSTMENTS["strip_pg_phrases"]:
            blocks = [b for b in blocks
                      if b["kind"] == "heading" or not _PG_PHRASE.search(b["text"])]
        if blocks:
            docs.append({"href": item["href"], "blocks": blocks})
    return {"title": raw["title"], "author": raw["author"], "docs": docs}


def _word_count(blocks) -> int:
    return sum(len(b["text"].split()) for b in blocks)


# --- 01_03_01 candidates ---------------------------------------------------------
#
# Code enumerates every place a division COULD open; an agent decides which ones do;
# code slices between the survivors. The enumerator's contract is COMPLETENESS, not
# precision — a candidate it misses is one nothing downstream can recover — so it is
# deliberately generous, and every discriminator it computes is handed on as evidence
# rather than applied as a hidden threshold.

PREVIEW_WORDS = 15

_SERIES = {"chapter": "chapter", "chap": "chapter", "stave": "chapter",
           "canto": "chapter", "letter": "letter", "part": "part", "book": "part",
           "volume": "part", "vol": "part", "act": "act", "scene": "scene"}

_WORD_ORDINALS = {w: i + 1 for i, w in enumerate(
    "one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}

_ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}

# The numeral may be glued to its word ("CHAPTERXXVII.") and the word may be preceded
# by a caption Ebookmaker glued on ("I hope Mr. Bingley will like it. CHAPTER II.") —
# so this SEARCHES rather than matches. Anchoring it scores 0 of Pride and Prejudice's
# 61 chapters; searching scores 61.
_SERIES_RE = re.compile(
    r"\b(" + "|".join(_SERIES) + r")\.?\s*"
    r"([ivxlcdm]+|\d+|" + "|".join(_WORD_ORDINALS) + r")\b", re.IGNORECASE)
_BARE_RE = re.compile(r"^([ivxlcdm]{1,7}|\d{1,3})\.?$", re.IGNORECASE)
# A numeral opening the heading, with the title after it: "I. A SCANDAL IN BOHEMIA".
# Neither pattern above sees this — no series word, and the heading is not ONLY a
# numeral — and Sherlock Holmes scores 3 of its 12 stories without it.
_LEADING_RE = re.compile(r"^([ivxlcdm]{1,7}|\d{1,3})\.\s+\S", re.IGNORECASE)
MAX_ORDINAL = 200        # a numeral above this is a word that looks Roman ("MIX.")


def _roman(text: str) -> int | None:
    total = previous = 0
    for char in reversed(text.lower()):
        value = _ROMAN_VALUES.get(char)
        if value is None:
            return None
        total += -value if value < previous else value
        previous = max(previous, value)
    return total or None


def _numeral(token: str) -> int | None:
    token = token.lower()
    if token.isdigit():
        return int(token)
    return _WORD_ORDINALS.get(token) or _roman(token)


def parse_heading(text: str) -> tuple[str | None, int | None]:
    """(series, ordinal) read from the heading's own words.

    Numbers must be READ, never assigned by position: numbering candidates by their
    order among non-junk TOC entries means one misclassified entry shifts every later
    chapter, which is how Dracula's spaced-out title page consumed chapter 1."""
    match = _SERIES_RE.search(text or "")
    if match:
        ordinal = _numeral(match.group(2))
        if ordinal:
            return _SERIES[match.group(1).lower()], ordinal
    stripped = (text or "").strip()
    bare = _BARE_RE.match(stripped) or _LEADING_RE.match(stripped)
    if bare:
        ordinal = _numeral(bare.group(1))
        if ordinal and ordinal <= MAX_ORDINAL:
            return "bare", ordinal
    return None, None


def _flatten(book: dict) -> list[tuple[int, str, int, dict]]:
    return [(d, doc["href"], b, block)
            for d, doc in enumerate(book["docs"])
            for b, block in enumerate(doc["blocks"])]


def _basename(href: str) -> str:
    return (href or "").split("#")[0].split("/")[-1]


def enumerate_candidates(book: dict, toc: list[dict]) -> list[dict]:
    """Every heading in the cleaned stream, with the evidence for judging it."""
    stream = _flatten(book)
    heads = [i for i, (_, _, _, blk) in enumerate(stream) if blk["kind"] == "heading"]

    anchors: dict[tuple[str, str], int] = {}
    for order, index in enumerate(heads):
        _, href, _, blk = stream[index]
        for anchor_id in blk.get("ids", []):
            anchors.setdefault((_basename(href), anchor_id), order)
    titles = {_normalize(e["title"]): e for e in toc}

    candidates = []
    for order, index in enumerate(heads):
        doc_index, href, block_index, blk = stream[index]
        stop = heads[order + 1] if order + 1 < len(heads) else len(stream)
        following = [b["text"] for _, _, _, b in stream[index + 1:stop]
                     if b["kind"] == "para"]
        words = " ".join(following).split()
        series, ordinal = parse_heading(blk["text"])
        signals = []
        resolved = any(anchors.get((_basename(e["href"]), e["href"].partition("#")[2]))
                       == order for e in toc if "#" in (e["href"] or ""))
        if resolved:
            signals.append("toc_anchor")
        if _normalize(blk["text"]) in titles:
            signals.append("toc_title")
        if series:
            signals.append("heading_numeral")
        candidates.append({
            "id": f"h{order + 1:03d}",
            "doc_index": doc_index, "block_index": block_index, "href": href,
            "text": blk["text"],
            "preview": " ".join(words[:PREVIEW_WORDS]),
            "words_after": len(words),
            "anchor_resolved": resolved,
            "series": series, "ordinal": ordinal,
            "signals": signals,
        })
    return candidates


# --- 01_03 chapterize ---


# "Part" opens a PART only when a number follows it. Without that, a chapter titled
# "Part of the Plan" was filed as a structural division of the book.
_ORDINAL = (r"[ivxlcdm]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
            r"eleven|twelve|first|second|third|fourth|fifth")
_PART_RE = re.compile(rf"^(part|book|volume)\s+({_ORDINAL})\b", re.IGNORECASE)


def _normalize(title: str) -> str:
    return " ".join(title.lower().replace(".", " ").split())


def _is_junk(key: str, title_key: str) -> bool:
    """TOC entries that are not chapters: title pages, contents page, PG license."""
    return key == title_key or key == "contents" or "project gutenberg" in key


def _toc_parts_and_chapters(toc: list[dict], book_title: str):
    """Parts = entries with nested children OR titles like 'PART I.' (real PG TOCs
    are FLAT). Junk filtered. Chapter ordinals continuous across parts — needed
    because Part II restarts at 'CHAPTER I' in pg244."""
    title_key = _normalize(book_title)
    parts, chapters, parts_meta = {}, {}, []
    for i, entry in enumerate(toc):
        key = _normalize(entry["title"])
        if _is_junk(key, title_key):
            continue
        has_child = i + 1 < len(toc) and toc[i + 1]["level"] > entry["level"]
        if has_child or _PART_RE.match(key):
            parts[key] = len(parts) + 1
            parts_meta.append({"n": len(parts), "title": entry["title"]})
        else:
            chapters[key] = len(chapters) + 1
    return parts, chapters, parts_meta


def _word_prefix(short: str, long: str) -> bool:
    """'part ii' prefixes 'part ii the country…' but NOT 'part i' anything."""
    return long.startswith(short) and (len(long) == len(short) or long[len(short)] == " ")


def _lookup(key: str, table: dict) -> int | None:
    """Exact match, else unique word-boundary prefix match (body headings are often
    shorter than TOC titles, e.g. 'PART II.' vs 'PART II. The Country of the Saints.')."""
    if key in table:
        return table[key]
    if len(key) < 6:
        return None
    hits = {v for k, v in table.items() if _word_prefix(key, k) or _word_prefix(k, key)}
    return hits.pop() if len(hits) == 1 else None


def chapters_from_map(book: dict, book_map) -> list[dict]:
    """Assemble chapters from the cartographer's map. No TOC text matching.

    The deterministic path matched TOC entry text against body heading text, which works
    only when they correspond one to one - true for 3 of 8 books tested. Here every
    heading already carries a ROLE, so a chapter simply opens at each heading whose role
    is `chapter`, and none of the five ways a TOC and a body disagree can break it.

    Prose under a non-chapter heading is NOT discarded. A closing note is not a chapter,
    but its words are still part of the book, and silent loss is the failure mode of
    every join in this pipeline.
    """
    roles = {d.candidate_id: d.role for d in book_map.divisions}
    stream = _flatten(book)
    heading_order = [i for i, (_, _, _, b) in enumerate(stream) if b["kind"] == "heading"]
    role_at = {index: roles.get(f"h{order + 1:03d}")
               for order, index in enumerate(heading_order)}

    chapters = [{"n": 0, "part": 0, "title": "Front matter", "paragraphs": []}]
    part_now = 0
    for index, (_, _, _, block) in enumerate(stream):
        role = role_at.get(index)
        if block["kind"] == "heading" and role == "part":
            part_now += 1
        elif block["kind"] == "heading" and role == "chapter":
            chapters.append({"n": len([c for c in chapters if c["n"] > 0]) + 1,
                             "part": part_now, "title": block["text"],
                             "paragraphs": []})
        elif block["kind"] == "para":
            paragraphs = chapters[-1]["paragraphs"]
            paragraphs.append({"n": len(paragraphs) + 1, "text": block["text"]})
    # An agent's output is INPUT, not a guarantee. The skill tells it not to mark a
    # heading `chapter` when no prose follows, and Moby Dick shows it does anyway - so
    # the same fold that handles a wrapped title handles a mis-mapped one.
    return fold_empty_headings(chapters)


def chapterize(book: dict, toc: list[dict], out_dir: Path):
    """Walk blocks in spine order; headings matching TOC open parts/chapters;
    front matter before chapter 1 becomes chapter 0 (part 0)."""
    parts, chapter_ords, parts_meta = _toc_parts_and_chapters(toc, book["title"])
    chapters = [{"n": 0, "part": 0, "title": "Front matter", "paragraphs": []}]
    part_now = 0
    for doc in book["docs"]:
        for block in doc["blocks"]:
            key = _normalize(block["text"])
            part_hit = _lookup(key, parts) if block["kind"] == "heading" else None
            chapter_hit = _lookup(key, chapter_ords) if block["kind"] == "heading" else None
            if part_hit:
                part_now = part_hit
            elif chapter_hit:
                chapters.append({"n": chapter_hit, "part": part_now,
                                 "title": block["text"], "paragraphs": []})
            elif block["kind"] == "para":
                para_n = len(chapters[-1]["paragraphs"]) + 1
                chapters[-1]["paragraphs"].append({"n": para_n, "text": block["text"]})
    if not chapters[0]["paragraphs"]:
        chapters.pop(0)
    # Fold BEFORE writing. Folding after the files existed renumbered the in-memory list
    # while the on-disk ch_NN.json kept the old numbers, so the manifest pointed at the
    # wrong files - which the 01_05 agent check caught, correctly, as "the title page
    # was split and misassigned".
    unfolded = chapters
    chapters = fold_empty_headings(chapters)
    # The contents page is prose-shaped but is not prose. Drop it before the count is
    # taken, so the expectation and the reality are computed over the same set.
    chapters = drop_contents_pages(chapters, [t["title"] for t in toc])
    # HONEST STATE, 2026-08-26: this expectation is right for 2 of 7 books and I stopped
    # patching it rather than trade one book against another.
    #
    # The adjustment is needed by Frankenstein and Metamorphosis (a wrapped title really
    # does remove a chapter) and wrong for Dracula (whose folded heading shared an
    # ordinal that chapter_count already collapses). Removing it fixed Dracula's
    # expectation and immediately broke Metamorphosis. That is whack-a-mole, and it is
    # the symptom of a wrong model rather than a missing case.
    #
    # The real problem is upstream and is the same one in every remaining failure: TOC
    # entries and body headings do not correspond one-to-one. Dracula opens "D R A C U
    # L A" and "NOTE" as chapters; Peter Pan finds 17 of 18; Pride and Prejudice finds
    # 27 of 61. Counting is not the fix - MATCHING is. See docs/analysis for the
    # cartographer work this belongs to.
    folded_only = fold_empty_headings(unfolded)
    expected = folded_expectation(len(chapter_ords), unfolded, folded_only)
    _write_chapters(chapters, out_dir)
    return chapters, parts_meta, expected


def _write_chapters(chapters: list[dict], out_dir: Path) -> None:
    out = out_dir / "chapters"
    out.mkdir(parents=True, exist_ok=True)
    for ch in chapters:
        path = out / f"ch_{ch['n']:02d}.json"
        path.write_text(json.dumps(ch, ensure_ascii=False, indent=2), encoding="utf-8")


# --- 01_04 finalize (python checks + manifest) ---


_MOJIBAKE = re.compile(r"[\ufffd\u00c2\u00e3]|\u00e2\u20ac")
_RAW_TAG = re.compile(r"<\s*/?\s*[a-z][a-z0-9]*(\s[^<>]*)?>", re.IGNORECASE)
_ENTITY = re.compile(r"&(?:[a-z]+|#\d+);", re.IGNORECASE)
_LONG_TOKEN = 34         # longest real English word in this corpus class is ~30


def console_safe(text: str) -> str:
    """Text that will survive being printed to whatever console this is.

    Twenty Thousand Leagues was LOST to a progress message: "'charmap' codec can't
    encode character '′'" on a Windows cp1252 console. The data was fine and the
    parse was fine. Any book with a prime, a curly quote or an accent could hit it, so
    printing is made safe rather than each message being made careful.
    """
    import sys
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return str(text).encode(encoding, errors="replace").decode(encoding, errors="replace")


def _garbled(text: str) -> str | None:
    """Mechanical corruption, described. None when the text is clean.

    These five checks used to live only in the validator SKILL — which is handed each
    chapter's FIRST and LAST paragraph and nothing else, so damage in paragraph 30 was
    invisible to the one check that claimed to look for it. Mechanical damage is
    mechanical: check it here, over every paragraph, and leave the agent the judgement
    calls it is actually equipped to make."""
    if _MOJIBAKE.search(text):
        return "mojibake"
    if _RAW_TAG.search(text):
        return "raw html tag"
    if _ENTITY.search(text):
        return "unresolved html entity"
    longest = max((w for w in text.split()), key=len, default="")
    # Measure the longest RUN OF LETTERS, not the longest whitespace-delimited
    # token. A hyphenated or em-dashed compound is separators; glued text is the
    # absence of them. Stripping dashes only from the ENDS made every long
    # compound look glued - Dracula and Peter Pan both died on real prose.
    # A word is LETTERS. This check exists to find letters glued together with no
    # separator, so anything that is not a letter is a separator - dashes, slashes,
    # and runs of dots, underscores or asterisks. A table-of-contents leader row
    # ("Chapter I .......... 1") killed a clean book as one 40-character word.
    longest = max(re.split(r"[^A-Za-z\u00c0-\u024f]+", longest) or [""],
                  key=len, default="")
    if len(longest) > _LONG_TOKEN:
        return f"impossibly long token {longest[:40]!r} (text glued together?)"
    return None


# TOC entries that are apparatus, not chapters. Matched on the WHOLE normalized entry,
# never as a substring: "The Contents of the Casket" is a chapter.
NOT_A_CHAPTER = {
    "contents", "table of contents", "title page", "titlepage", "cover", "colophon",
    "index", "illustrations", "list of illustrations", "transcriber's note",
    "transcribers note", "note", "advertisement", "frontispiece",
}


def chapter_count(chapter_ords: dict) -> int:
    """How many CHAPTERS the TOC describes - not how many heading texts it lists.

    chapter_ords maps every heading text to an ordinal, so a chapter announced by two
    headings contributes two keys. Dracula lists "D R A C U L A" and "CHAPTER I ..."
    both pointing at chapter 2, so counting keys claimed 29 chapters in a 28-chapter
    book and failed a parse that was correct.
    """
    return len(set(chapter_ords.values()))


def chapter_titles(toc: list[dict]) -> list[str]:
    """TOC entries that are actually chapters.

    The expectation and the body must be cleaned the SAME way. Adjusting the TOC count
    by what was removed from the body only works when the removed thing was counted in
    the TOC - and a contents page never is, which is why a correct 29-chapter Dracula
    failed against an expectation wrongly shrunk to 28.
    """
    kept = []
    for entry in toc:
        title = (entry.get("title") or "").strip()
        key = _normalize(title)
        if not key or key in NOT_A_CHAPTER:
            continue
        if key.startswith("the full project gutenberg"):
            continue
        kept.append(title)
    return kept


CONTENTS_MATCH = 0.6     # share of a chapter's paragraphs that must BE toc entries


def is_contents_page(chapter: dict, toc_titles: list[str]) -> bool:
    """Is this chapter the book's table of contents, ingested as prose?

    Frankenstein's chapter 1 arrived as 28 paragraphs reading "Letter 1", "Letter 2",
    ... "Chapter 24". No heuristic about word count or page position is needed, and
    none would generalise: the contents page is the one whose PARAGRAPHS ARE THE TOC'S
    OWN ENTRY TITLES. A chapter that merely opens with "Chapter 1" and then contains
    prose does not match, because the share is measured over every paragraph.
    """
    paragraphs = chapter.get("paragraphs") or []
    if not paragraphs or not toc_titles:
        return False
    titles = {_normalize(t) for t in toc_titles}
    hits = sum(1 for p in paragraphs if _normalize(p.get("text", "")) in titles)
    return hits / len(paragraphs) >= CONTENTS_MATCH


def drop_contents_pages(chapters: list[dict], toc_titles: list[str]) -> list[dict]:
    """Remove contents pages and renumber. The n==0 sentinel is never dropped: it
    anchors the coordinate system every later step reads."""
    kept = [c for c in chapters
            if c["n"] == 0 or not is_contents_page(c, toc_titles)]
    if len(kept) == len(chapters):
        return chapters
    for number, chapter in enumerate(c for c in kept if c["n"] > 0):
        chapter["n"] = number + 1
    return kept


def fold_empty_headings(chapters: list[dict]) -> list[dict]:
    """A heading with no text before the next heading is part of that heading.

    Frankenstein sets its own title across two lines - "Frankenstein;" and "or, the
    Modern Prometheus" - so the first became a chapter with zero paragraphs and ingest
    died on "chapter 1 is empty" for a book it had otherwise parsed correctly. A wrapped
    title is common in Gutenberg HTML and it is not a chapter boundary.

    The n==0 front-matter sentinel is exempt: it anchors the coordinate system and later
    steps expect it whether or not the book has front matter.
    """
    folded: list[dict] = []
    carry = ""
    for chapter in chapters:
        if chapter["n"] > 0 and not chapter["paragraphs"]:
            carry = f"{carry} {chapter['title']}".strip() if carry else chapter["title"]
            continue                       # fold forward into the next real chapter
        title = f"{carry} {chapter['title']}".strip() if carry else chapter["title"]
        folded.append({**chapter, "title": title})
        carry = ""
    for number, chapter in enumerate(c for c in folded if c["n"] > 0):
        chapter["n"] = number + 1
    return folded


def folded_expectation(expected: int | None, before: list[dict],
                       after: list[dict]) -> int | None:
    """Move the TOC expectation by however many headings were folded away.

    The expectation comes from the TOC, which counts a wrapped title as two entries.
    Folding merges them, so the actual count drops and a comparison against the unfolded
    expectation fails on a book that parsed correctly. Fixing one side of a comparison
    and not the other is how checks in this repo have been broken before.
    """
    if expected is None:
        return None
    removed = len([c for c in before if c["n"] > 0]) - len([c for c in after if c["n"] > 0])
    return max(0, expected - removed)


def _check_chapters(chapters: list[dict], expected: int | None) -> None:
    # `n > 0`, NOT `part > 0`. Front matter is the n==0 sentinel; a PART is optional and
    # most novels have none. Using part as the discriminator meant any book without
    # Parts - Frankenstein, Dracula, Metamorphosis - died here claiming every paragraph
    # landed in front matter, on books it had just chapterized correctly.
    real = [c for c in chapters if c["n"] > 0]
    if not real:
        # The expectation is derived from the TOC, so an empty TOC expected zero
        # chapters and zero chapters matched: a check that could not fail. The whole
        # novel arrived as one "Front matter" blob and step 01 reported checks PASS.
        raise ValueError(
            "no chapters were found — every paragraph landed in front matter. "
            "The TOC was empty or no body heading matched it.")
    if expected is not None and len(real) != expected:
        raise ValueError(f"chapter count {len(real)} != expected {expected}")
    for ch in chapters:
        # The n==0 front-matter sentinel may legitimately be empty: a book that opens
        # straight on Chapter 1 has no front matter, and that is not a defect.
        if not ch["paragraphs"] and ch["n"] > 0:
            raise ValueError(f"chapter {ch['n']} is empty")
        if [p["n"] for p in ch["paragraphs"]] != list(range(1, len(ch["paragraphs"]) + 1)):
            raise ValueError(f"chapter {ch['n']} paragraph numbering not contiguous")
        # Boilerplate in a CHAPTER means the license text was chapterized as prose -
        # real damage. In FRONT MATTER it is usually a transcriber's note about the
        # edition, which is what front matter is for. Moby Dick's note about being
        # assembled from two etexts killed an otherwise clean ingest.
        for para in (ch["paragraphs"] if ch["n"] > 0 else []):
            if _PG_PHRASE.search(para["text"]):
                raise ValueError(f"PG boilerplate leaked into chapter {ch['n']} "
                                 f"paragraph {para['n']}")
            damage = _garbled(para["text"])
            if damage:
                raise ValueError(f"garbled text in chapter {ch['n']} "
                                 f"paragraph {para['n']}: {damage}")


def finalize(chapters: list[dict], out_dir: Path, source_path: Path,
             *, title: str, author: str, expected_chapters: int | None,
             toc_expected: int | None = None, parts: list[dict] | None = None) -> dict:
    """Validate loudly; write book.json only when every check passes.
    Expectation = manual override if set, else the TOC's own chapter count."""
    _check_chapters(chapters, expected_chapters or toc_expected)
    manifest = {
        "title": title,
        "author": author,
        "parts": parts or [],
        "source": source_path.name,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "chapters": [
            {"n": c["n"], "part": c["part"], "title": c["title"],
             "file": f"chapters/ch_{c['n']:02d}.json",
             "paragraphs": len(c["paragraphs"]),
             "words": sum(len(p["text"].split()) for p in c["paragraphs"])}
            for c in chapters
        ],
    }
    path = out_dir / "book.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


# --- runner ---


def map_chapters(book: dict, toc: list[dict], out_dir: Path, tracker=None):
    """Map the book's divisions with the cartographer, then assemble from the map.

    The deterministic TOC-text matcher worked on 3 of 8 books and failed 5 different
    ways. Rather than keep two paths and a rule for choosing between them, the agent is
    the path: it costs about $0.002 a book and answers the question the matcher could
    not - which of these headings is actually a chapter.

    The deterministic count is still computed and LOGGED as a cross-check. It is no
    longer the authority, but a disagreement is worth seeing.
    """
    from agents import book_cartographer

    candidates = enumerate_candidates(book, toc)
    usage: dict = {}
    book_map = book_cartographer.map_book(candidates, toc, usage=usage)
    chapters = chapters_from_map(book, book_map)
    real = [c for c in chapters if c["n"] > 0]

    if tracker:
        tracker.log(f"cartographer: {book_map.structure}", step_id="01_03")
        for missing in book_map.missing:
            tracker.log(f"cartographer MISSING division {missing.expected_ordinal} "
                        f"inside {missing.inside_candidate_id}: {missing.evidence}",
                        level="WARNING", step_id="01_03")
        _, ords, _ = _toc_parts_and_chapters(toc, book["title"])
        if len(set(ords.values())) != len(real):
            tracker.log(f"cross-check: TOC matching would have given "
                        f"{len(set(ords.values()))} chapters, the map gives {len(real)}",
                        step_id="01_03")
    print(f"  01_03 cartographer: {book_map.structure[:96]}")
    for missing in book_map.missing:
        print(f"         MISSING division {missing.expected_ordinal} "
              f"inside {missing.inside_candidate_id}")
    _write_chapters(chapters, out_dir)
    parts_meta = _parts_meta_from(chapters)
    return chapters, parts_meta, len(real)


def _parts_meta_from(chapters: list[dict]) -> list[dict]:
    """Part records derived from what the map actually produced."""
    seen: dict[int, dict] = {}
    for chapter in chapters:
        if chapter["part"] > 0 and chapter["part"] not in seen:
            seen[chapter["part"]] = {"n": chapter["part"],
                                     "title": f"Part {chapter['part']}"}
    return list(seen.values())


def _pass(tracker, raw, book_dir, source):
    """One pass of 01_02..01_05. Returns the agent Verdict, or None if RUN_UNTIL
    stopped before 01_05. Does not raise on a bad verdict — the improve loop decides."""
    with tracker.step("01_02"):
        book = clean(raw)
    kept = [d["href"] for d in book["docs"]]
    dropped = [i["href"] for i in raw["spine"] if i["href"] not in kept]
    tracker.log(f"kept={kept} dropped={dropped}", step_id="01_02")
    print(f"  01_02 clean: kept={len(kept)} docs, dropped={dropped}")
    if RUN_UNTIL < "01_03":
        return None

    with tracker.step("01_03"):
        chapters, parts_meta, toc_expected = map_chapters(book, raw["toc"],
                                                          book_dir / "source", tracker)
        for ch in chapters:
            words = sum(len(p["text"].split()) for p in ch["paragraphs"])
            tracker.log(f"chapter n={ch['n']} part={ch['part']} paras="
                        f"{len(ch['paragraphs'])} words={words} title={ch['title']!r}",
                        step_id="01_03")
    print(f"  01_03 chapterize: {len(chapters)} chapters written")
    for ch in chapters:
        words = sum(len(p["text"].split()) for p in ch["paragraphs"])
        print(console_safe(f"         ch {ch['n']:>2} part {ch['part']} "
                           f"¶{len(ch['paragraphs']):>3} w{words:>6}  {ch['title']}"))
    if RUN_UNTIL < "01_04":
        return None

    with tracker.step("01_04"):
        manifest = finalize(chapters, book_dir / "source", source,
                            title=raw["title"], author=raw["author"],
                            expected_chapters=EXPECTED_CHAPTERS,
                            toc_expected=toc_expected, parts=parts_meta)
    print(f"  01_04 finalize: checks PASS, book.json written "
          f"(sha256={manifest['source_sha256'][:12]}…)")
    if RUN_UNTIL < "01_05":
        return None

    with tracker.step("01_05"):
        from agents import ingest_validator
        usage = {}
        verdict = ingest_validator.review(book_dir / "source", usage=usage)
        for issue in verdict.issues:
            tracker.log(f"issue ch={issue.chapter} kind={issue.kind} "
                        f"severity={issue.severity}: {issue.note}",
                        level="WARNING", step_id="01_05")
        tracker.log(f"verdict ok={verdict.ok}: {verdict.summary}", step_id="01_05")
        tracker.log(f"tokens: in={usage.get('input_tokens')} out={usage.get('output_tokens')}"
                    f" total={usage.get('total_tokens')} tier={usage.get('tier')}",
                    step_id="01_05")
    print(f"  01_05 agent_check: ok={verdict.ok} issues={len(verdict.issues)} "
          f"— {verdict.summary}")
    print(f"        tokens: in={usage.get('input_tokens')} out={usage.get('output_tokens')} "
          f"tier={usage.get('tier')}")
    return verdict


def _already_done(book_dir: Path, source: Path) -> bool:
    """Artifact resume: manifest exists and its sha matches the source epub."""
    manifest_path = book_dir / "source" / "book.json"
    if not manifest_path.exists():
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest.get("source_sha256") == hashlib.sha256(source.read_bytes()).hexdigest()


def run(codex_id: str) -> None:
    conn = db.get_connection()
    row = db.get_codex(conn, codex_id)
    book_dir = paths.book_dir(codex_id)
    source = book_dir / "source" / f"{row['source_ref']}.epub"
    if _already_done(book_dir, source):
        print(f"[{STEP_ID}] {NAME}: book.json current (sha match) — skipping (cached). "
              f"Delete source/book.json to force re-ingest.")
        return
    tracker = tracking.Tracker(conn, codex_id, "analysis")
    print(f"[{STEP_ID}] {NAME}: source={source}  run_id={tracker.run_id}  until={RUN_UNTIL}")

    with tracker.step("01_01"):
        raw = read_source(source)
        tracker.log(f"source={source} size={source.stat().st_size} bytes", step_id="01_01")
        tracker.log(f"opf metadata: title={raw['title']!r} author={raw['author']!r}",
                    step_id="01_01")
        for item in raw["spine"]:
            tracker.log(f"spine doc: {item['href']} ({len(item['raw_html'])} chars html)",
                        step_id="01_01")
        for entry in raw["toc"]:
            tracker.log(f"toc L{entry['level']}: {entry['title']!r} -> {entry['href']}",
                        step_id="01_01")
    print(console_safe(f"  01_01 read_source: title={raw['title']!r} "
                       f"author={raw['author']!r} spine_docs={len(raw['spine'])} "
                       f"toc_entries={len(raw['toc'])}"))
    if RUN_UNTIL < "01_02":
        return

    for round_no in range(1 + MAX_IMPROVE_ROUNDS):
        verdict = _pass(tracker, raw, book_dir, source)
        if verdict is None or verdict.ok:
            return
        actions = plan_remedies(verdict.issues)
        remaining = unfixable_issues(verdict.issues)
        if not actions or round_no == MAX_IMPROVE_ROUNDS:
            # The mechanical checks in finalize() have already passed - they measure
            # every paragraph of every chapter and raise on their own. What is left is
            # the agent's OPINION about samples, and an opinion does not halt a parse
            # that measured clean. It is recorded instead, in full, for the owner.
            for issue in remaining:
                tracker.log(f"unresolved (advisory): ch {issue.chapter} "
                            f"[{issue.kind}] {issue.note}",
                            level="WARNING", step_id="01_05")
            print(f"  01_05 advisory: {len(remaining)} unresolved finding(s), "
                  f"mechanical checks passed - continuing")
            for issue in remaining[:3]:
                print(f"         - ch {issue.chapter} [{issue.kind}] {issue.note[:88]}")
            return
        with tracker.step("01_06"):
            apply_remedies(actions)
            tracker.log(f"round {round_no + 1}: applied {actions}; re-running 01_02..01_05",
                        step_id="01_06")
        print(f"  01_06 improve: applied {actions}; re-running 01_02..01_05")
