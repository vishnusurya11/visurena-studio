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
    "boundary": None, "garbled": None, "front_matter": None,
    "parts": None, "completeness": None, "metadata": None,
}


def plan_remedies(issues) -> list[str]:
    """Issues -> adjustment actions. Applies every fixable remedy and lets the
    re-run's agent verdict re-judge (fixing one cause often clears several issues).
    Escalates ONLY when no issue has any safe remedy."""
    actions, unfixable = [], []
    for issue in issues:
        action = REMEDIES.get(issue.kind)
        if action and action not in actions:
            actions.append(action)
        elif action is None:
            unfixable.append(issue)
    if not actions and unfixable:
        issue = unfixable[0]
        raise ValueError(
            f"no safe auto-remedy for issue kind {issue.kind!r} "
            f"(ch {issue.chapter}: {issue.note}) — owner attention needed")
    return actions


def apply_remedies(actions: list[str]) -> None:
    for action in actions:
        ADJUSTMENTS[action] = True


# --- 01_01 read_source ---


def read_source(source_path: Path) -> dict:
    """Parse the EPUB: metadata + spine raw html + TOC."""
    return epub.read_epub(source_path)


# --- 01_02 clean ---


def clean(raw: dict) -> dict:
    """Content docs only: drop cover/toc/colophon; keep only text between the PG
    *** START *** and *** END *** markers — tracked GLOBALLY across docs, because
    the license usually lives in its own doc after the END marker."""
    parsed = [(item, epub.html_to_blocks(item["raw_html"])) for item in raw["spine"]]
    started = not any(_PG_START.search(b["text"]) for _, blocks in parsed for b in blocks)
    ended = False
    docs = []
    for item, blocks in parsed:
        if ended or _NONCONTENT_HREF.search(item["href"]) or _is_chrome_doc(blocks):
            continue
        kept, started, ended = _keep_content(blocks, started, ended)
        if ADJUSTMENTS["strip_pg_phrases"]:
            kept = [b for b in kept if not _PG_PHRASE.search(b["text"])]
        if kept:
            docs.append({"href": item["href"], "blocks": kept})
    return {"title": raw["title"], "author": raw["author"], "docs": docs}


def _is_chrome_doc(blocks: list[dict]) -> bool:
    """A doc that is navigation chrome, not story: its headings say CONTENTS
    (the PG contents page's link table would otherwise glob into front matter)."""
    return any(b["kind"] == "heading" and _normalize(b["text"]) == "contents"
               for b in blocks)


def _keep_content(blocks: list[dict], started: bool, ended: bool):
    """One doc's blocks filtered by the global START/END marker state."""
    kept = []
    for block in blocks:
        if not started:
            started = bool(_PG_START.search(block["text"]))
        elif _PG_END.search(block["text"]):
            ended = True
            break
        else:
            kept.append(block)
    return kept, started, ended


# --- 01_03 chapterize ---


_PART_RE = re.compile(r"^(part|book|volume)\b", re.IGNORECASE)


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
    _write_chapters(chapters, out_dir)
    return chapters, parts_meta, len(chapter_ords)  # TOC's own chapter count = expectation


def _write_chapters(chapters: list[dict], out_dir: Path) -> None:
    out = out_dir / "chapters"
    out.mkdir(parents=True, exist_ok=True)
    for ch in chapters:
        path = out / f"ch_{ch['n']:02d}.json"
        path.write_text(json.dumps(ch, ensure_ascii=False, indent=2), encoding="utf-8")


# --- 01_04 finalize (python checks + manifest) ---


def _check_chapters(chapters: list[dict], expected: int | None) -> None:
    real = [c for c in chapters if c["part"] > 0]
    if expected is not None and len(real) != expected:
        raise ValueError(f"chapter count {len(real)} != expected {expected}")
    for ch in chapters:
        if not ch["paragraphs"]:
            raise ValueError(f"chapter {ch['n']} is empty")
        if [p["n"] for p in ch["paragraphs"]] != list(range(1, len(ch["paragraphs"]) + 1)):
            raise ValueError(f"chapter {ch['n']} paragraph numbering not contiguous")
        if any(_PG_PHRASE.search(p["text"]) for p in ch["paragraphs"]):
            raise ValueError(f"PG boilerplate leaked into chapter {ch['n']}")


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
        chapters, parts_meta, toc_expected = chapterize(book, raw["toc"], book_dir / "source")
        for ch in chapters:
            words = sum(len(p["text"].split()) for p in ch["paragraphs"])
            tracker.log(f"chapter n={ch['n']} part={ch['part']} paras="
                        f"{len(ch['paragraphs'])} words={words} title={ch['title']!r}",
                        step_id="01_03")
    print(f"  01_03 chapterize: {len(chapters)} chapters written")
    for ch in chapters:
        words = sum(len(p["text"].split()) for p in ch["paragraphs"])
        print(f"         ch {ch['n']:>2} part {ch['part']} ¶{len(ch['paragraphs']):>3} "
              f"w{words:>6}  {ch['title']}")
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
    print(f"  01_01 read_source: title={raw['title']!r} author={raw['author']!r} "
          f"spine_docs={len(raw['spine'])} toc_entries={len(raw['toc'])}")
    if RUN_UNTIL < "01_02":
        return

    for round_no in range(1 + MAX_IMPROVE_ROUNDS):
        verdict = _pass(tracker, raw, book_dir, source)
        if verdict is None or verdict.ok:
            return
        if round_no == MAX_IMPROVE_ROUNDS:
            raise ValueError(f"agent_check still failing after {MAX_IMPROVE_ROUNDS} "
                             f"improve rounds: {verdict.summary}")
        with tracker.step("01_06"):
            actions = plan_remedies(verdict.issues)  # unknown kind -> raises = escalation
            apply_remedies(actions)
            tracker.log(f"round {round_no + 1}: applied {actions}; re-running 01_02..01_05",
                        step_id="01_06")
        print(f"  01_06 improve: applied {actions}; re-running 01_02..01_05")
