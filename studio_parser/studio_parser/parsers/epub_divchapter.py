from __future__ import annotations

from pathlib import Path

from studio_parser.models import ParseResult
from studio_parser.parsers.base import parse_div_chapters
from studio_parser.parsers.epub_reader import read_epub


def parse_epub_divchapter(filepath: Path, label: str) -> ParseResult:
    book_title, author, _, combined_soup, warnings = read_epub(filepath)

    works = parse_div_chapters(combined_soup, warnings)

    total_words = sum(w.total_word_count for w in works)
    total_paras = sum(len(c.paragraphs) for w in works for c in w.chapters)

    return ParseResult(
        source_file=filepath.name,
        format_type=f"{label}_divchapter",
        book_title=book_title,
        author=author,
        works=works,
        total_word_count=total_words,
        total_paragraphs=total_paras,
        parse_warnings=warnings,
    )
