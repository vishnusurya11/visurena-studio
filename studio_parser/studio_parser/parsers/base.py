from __future__ import annotations

import re
from typing import Protocol

from bs4 import Tag

from studio_parser.models import Chapter, ParseResult, Work


class Parser(Protocol):
    def parse(self, filepath: ...) -> ParseResult: ...


def clean_text(text: str) -> str:
    text = re.sub(r"\[Pg\s*\d+\]", "", text)
    text = re.sub(r"\{[a-z0-9]+\}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def wc(text: str) -> int:
    return len(text.split())


def is_boilerplate(tag: Tag) -> bool:
    for parent in tag.parents:
        if not hasattr(parent, "get"):
            continue
        pid = parent.get("id", "")
        if pid in ("pg-header", "pg-footer"):
            return True
        cls = " ".join(parent.get("class", []))
        if any(bp in cls for bp in ("pg-boilerplate", "pgheader", "pgfooter")):
            return True
    return False


def make_chapter(title: str, paragraphs: list[str], min_length: int = 10) -> Chapter:
    cleaned = [clean_text(p) for p in paragraphs]
    cleaned = [p for p in cleaned if len(p) >= min_length]
    total = sum(wc(p) for p in cleaned)
    return Chapter(title=title, paragraphs=cleaned, word_count=total)


def make_work(title: str, chapters: list[Chapter]) -> Work:
    total = sum(c.word_count for c in chapters)
    return Work(title=title, chapters=chapters, total_word_count=total)


def parse_div_chapters(soup, warnings: list[str]) -> list[Work]:
    """Extract works from div.chapter > h2 > h3 structure."""
    chapter_divs = soup.find_all("div", class_="chapter")
    works = []

    for div in chapter_divs:
        h2 = div.find("h2")
        if not h2:
            warnings.append("div.chapter without h2 found")
            continue

        work_title = clean_text(h2.get_text(" ", strip=True))

        if "GUTENBERG" in work_title.upper() or "LICENSE" in work_title.upper():
            continue

        h3_tags = div.find_all("h3")

        if not h3_tags:
            paras = [
                p.get_text(" ", strip=True)
                for p in div.find_all("p")
                if not is_boilerplate(p)
            ]
            works.append(make_work(work_title, [make_chapter("", paras)]))
        else:
            chapters = []
            for i, h3 in enumerate(h3_tags):
                h3_title = h3.get_text(strip=True)
                paras = []
                next_h3 = h3_tags[i + 1] if i + 1 < len(h3_tags) else None

                sibling = h3.find_next_sibling()
                while sibling:
                    if sibling == next_h3:
                        break
                    if sibling.name == "p" and not is_boilerplate(sibling):
                        paras.append(sibling.get_text(" ", strip=True))
                    elif isinstance(sibling, Tag) and sibling.name != "h3":
                        for p in sibling.find_all("p"):
                            if not is_boilerplate(p):
                                paras.append(p.get_text(" ", strip=True))
                    sibling = sibling.find_next_sibling()

                chapters.append(make_chapter(h3_title, paras))
            works.append(make_work(work_title, chapters))

    return works
