from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup

from studio_parser.models import ParseResult
from studio_parser.parsers.base import parse_div_chapters


def parse_html(filepath: Path) -> ParseResult:
    warnings: list[str] = []
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Metadata
    title_tag = soup.find("title")
    raw_title = title_tag.get_text(strip=True) if title_tag else ""
    book_title = re.sub(r"^.*?eBook of\s*", "", raw_title)
    book_title = re.sub(r",\s*by\s+.*$", "", book_title).strip()

    author = ""
    for attr in ("author", "dc.creator"):
        meta = soup.find("meta", attrs={"name": attr})
        if meta and meta.get("content"):
            author = meta["content"]
            break

    works = parse_div_chapters(soup, warnings)

    total_words = sum(w.total_word_count for w in works)
    total_paras = sum(len(c.paragraphs) for w in works for c in w.chapters)

    return ParseResult(
        source_file=filepath.name,
        format_type="html",
        book_title=book_title,
        author=author,
        works=works,
        total_word_count=total_words,
        total_paragraphs=total_paras,
        parse_warnings=warnings,
    )
