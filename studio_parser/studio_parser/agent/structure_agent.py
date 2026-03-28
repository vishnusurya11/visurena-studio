from __future__ import annotations

import json

from studio_parser.agent.llm_provider import get_llm
from studio_parser.config import ParserConfig
from studio_parser.models import ParseResult
from studio_parser.parsers.base import make_chapter, make_work

STRUCTURE_PROMPT = """You are analyzing the structure of an ebook to identify individual stories/works.

Book title: {book_title}
Author: {author}

Here are the first ~3000 characters of the book content (HTML stripped to text):

---
{content_sample}
---

Here are all the heading elements found in the document:
{headings}

Here is the TOC (table of contents) if available:
{toc}

Your task:
1. Identify what tag/pattern separates individual stories or chapters (e.g., h2, h3, section, hr, etc.)
2. List all story/work titles you can identify
3. Describe the structural pattern

Respond in JSON format:
{{
  "separator_tag": "h2",
  "separator_pattern": "description of how stories are separated",
  "works": [
    {{"title": "Story Title 1"}},
    {{"title": "Story Title 2"}}
  ]
}}"""


def analyze_structure(
    combined_soup,
    book_title: str,
    author: str,
    toc_entries: list,
    config: ParserConfig,
) -> list[dict] | None:
    """Use LLM to analyze ebook structure and identify story boundaries.

    Returns list of {title, separator_tag, separator_pattern} or None if LLM fails.
    """
    # Extract text sample (first ~3000 chars)
    body = combined_soup.find("body")
    if not body:
        return None
    full_text = body.get_text(" ", strip=True)
    content_sample = full_text[:3000]

    # Gather all headings
    headings_info = []
    for tag_name in ("h1", "h2", "h3", "h4", "h5"):
        for el in combined_soup.find_all(tag_name):
            text = el.get_text(strip=True)[:80]
            cls = el.get("class", [])
            el_id = el.get("id", "")
            headings_info.append(f"<{tag_name} class='{cls}' id='{el_id}'>{text}</{tag_name}>")

    # Format TOC
    toc_str = "No TOC available"
    if toc_entries:
        toc_lines = []
        for lbl, anchor, depth, children in toc_entries:
            indent = "  " * (depth - 1)
            toc_lines.append(f"{indent}- {lbl} (#{anchor}, children={children})")
        toc_str = "\n".join(toc_lines)

    prompt = STRUCTURE_PROMPT.format(
        book_title=book_title,
        author=author,
        content_sample=content_sample,
        headings="\n".join(headings_info) if headings_info else "No headings found",
        toc=toc_str,
    )

    try:
        llm = get_llm(config)
        response = llm.invoke(prompt)
        content = response.content.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]

        result = json.loads(content)
        return result.get("works", [])
    except Exception as e:
        print(f"    Structure analysis failed: {e}")
        return None


def parse_with_llm_structure(
    combined_soup,
    book_title: str,
    author: str,
    toc_entries: list,
    config: ParserConfig,
    source_file: str,
) -> ParseResult:
    """Fallback parser: use LLM to understand structure, then extract content.

    Called when standard parsers return 0 works.
    """
    warnings: list[str] = ["Used LLM-based structure detection (fallback)"]

    # Ask LLM to analyze structure
    works_info = analyze_structure(combined_soup, book_title, author, toc_entries, config)
    if not works_info:
        warnings.append("LLM structure analysis returned no results")
        return ParseResult(
            source_file=source_file,
            format_type="llm_fallback",
            book_title=book_title,
            author=author,
            works=[],
            total_word_count=0,
            total_paragraphs=0,
            parse_warnings=warnings,
        )

    # Try to find content for each identified work using heading text matching
    works = []
    work_titles = [w.get("title", "") for w in works_info if w.get("title")]

    # Find heading elements that match work titles
    all_headings = []
    for tag_name in ("h1", "h2", "h3", "h4"):
        for el in combined_soup.find_all(tag_name):
            text = el.get_text(strip=True)
            all_headings.append((tag_name, text, el))

    for i, title in enumerate(work_titles):
        title_upper = title.upper().strip()
        # Find matching heading
        heading_el = None
        for tag_name, text, el in all_headings:
            if text.upper().strip() == title_upper:
                heading_el = el
                break

        if not heading_el:
            # Try partial match
            for tag_name, text, el in all_headings:
                if title_upper in text.upper() or text.upper() in title_upper:
                    heading_el = el
                    break

        if not heading_el:
            warnings.append(f"Could not find heading for: {title}")
            continue

        # Collect paragraphs from this heading to the next work's heading
        paras = []
        next_title_upper = work_titles[i + 1].upper().strip() if i + 1 < len(work_titles) else None

        for el in heading_el.find_all_next():
            if not hasattr(el, "name"):
                continue
            # Stop at next work heading
            if next_title_upper and el.name in ("h1", "h2", "h3", "h4"):
                el_text = el.get_text(strip=True).upper().strip()
                if el_text == next_title_upper or next_title_upper in el_text:
                    break
            # Stop at PG footer
            el_id = el.get("id", "") if hasattr(el, "get") else ""
            if el_id in ("pg-footer", "pg-footer-heading"):
                break
            if el.name == "p":
                text = el.get_text(" ", strip=True)
                if text and len(text) >= 10:
                    paras.append(text)

        if paras:
            chapter = make_chapter(title, paras)
            works.append(make_work(title, [chapter]))

    total_words = sum(w.total_word_count for w in works)
    total_paras = sum(len(c.paragraphs) for w in works for c in w.chapters)

    return ParseResult(
        source_file=source_file,
        format_type="llm_fallback",
        book_title=book_title,
        author=author,
        works=works,
        total_word_count=total_words,
        total_paragraphs=total_paras,
        parse_warnings=warnings,
    )
