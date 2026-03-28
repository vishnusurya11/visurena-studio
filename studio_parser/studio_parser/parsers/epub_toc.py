from __future__ import annotations

import re
from pathlib import Path

from bs4 import Tag

from studio_parser.models import Chapter, ParseResult
from studio_parser.parsers.base import is_boilerplate, make_chapter, make_work
from studio_parser.parsers.epub_reader import read_epub


def parse_epub_toc(filepath: Path, label: str) -> ParseResult:
    book_title, author, toc_entries, combined_soup, warnings = read_epub(filepath)

    if not toc_entries:
        warnings.append("No TOC found")
        return ParseResult(
            source_file=filepath.name,
            format_type=f"{label}_toc",
            book_title=book_title,
            author=author,
            works=[],
            total_word_count=0,
            total_paragraphs=0,
            parse_warnings=warnings,
        )

    # Filter boilerplate TOC entries
    skip_labels = {"contents", "the full project gutenberg", "cover"}

    def _normalize(s: str) -> str:
        return re.sub(r"[^a-z\s]", "", s.lower()).strip()

    book_title_norm = _normalize(book_title)

    filtered = []
    for lbl, anchor, depth, children in toc_entries:
        lbl_lower = lbl.lower().strip()
        if any(lbl_lower.startswith(s) for s in skip_labels):
            continue
        if depth == 1 and _normalize(lbl) == book_title_norm:
            continue
        filtered.append((lbl, anchor, depth, children))

    # Build flat list of leaf entries (actual content sections)
    leaf_entries = []
    for lbl, anchor, depth, children in filtered:
        if children > 0:
            continue
        leaf_entries.append((lbl, anchor, depth))

    # Collect paragraphs between consecutive leaf-level anchors
    def _paras_between_anchors(start_anchor: str, end_anchor: str) -> list[str]:
        paras = []
        start_el = combined_soup.find(id=start_anchor) if start_anchor else None
        if not start_el:
            warnings.append(f"Anchor not found: {start_anchor}")
            return paras

        for el in start_el.find_all_next():
            if not isinstance(el, Tag):
                continue
            if end_anchor and el.get("id") == end_anchor:
                break
            if el.name == "p" and not is_boilerplate(el):
                if not el.find_parent("p"):
                    paras.append(el.get_text(" ", strip=True))

        return paras

    # Build chapter data for each leaf entry
    chapter_data = []
    for i, (lbl, anchor, depth) in enumerate(leaf_entries):
        next_anchor = leaf_entries[i + 1][1] if i + 1 < len(leaf_entries) else ""
        paras = _paras_between_anchors(anchor, next_anchor)
        chapter_data.append((lbl, anchor, depth, make_chapter(lbl, paras)))

    # Group into works using the filtered TOC
    works = []
    ch_idx = 0
    fi = 0
    while fi < len(filtered):
        lbl, anchor, depth, children = filtered[fi]
        if depth == 1:
            if children > 0:
                work_chapters = []
                for _ in range(children):
                    if ch_idx < len(chapter_data):
                        work_chapters.append(chapter_data[ch_idx][3])
                        ch_idx += 1
                works.append(make_work(lbl, work_chapters))
                fi += 1 + children
            else:
                if ch_idx < len(chapter_data):
                    ch = chapter_data[ch_idx][3]
                    ch_idx += 1
                    works.append(
                        make_work(
                            lbl,
                            [Chapter(title="", paragraphs=ch.paragraphs, word_count=ch.word_count)],
                        )
                    )
                fi += 1
        else:
            fi += 1

    total_words = sum(w.total_word_count for w in works)
    total_paras = sum(len(c.paragraphs) for w in works for c in w.chapters)

    return ParseResult(
        source_file=filepath.name,
        format_type=f"{label}_toc",
        book_title=book_title,
        author=author,
        works=works,
        total_word_count=total_words,
        total_paragraphs=total_paras,
        parse_warnings=warnings,
    )
