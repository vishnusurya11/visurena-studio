from __future__ import annotations

import argparse
import sys
from pathlib import Path

from studio_parser.config import load_config
from studio_parser.db import ensure_table
from studio_parser.downloader import download_book
from studio_parser.models import ParseResult
from studio_parser.output import write_stories
from studio_parser.parsers.epub_divchapter import parse_epub_divchapter
from studio_parser.parsers.epub_toc import parse_epub_toc
from studio_parser.parsers.html_parser import parse_html
from studio_parser.reconciler import reconcile
from studio_parser.splitter import split_into_stories


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="studio_parser",
        description="Parse Project Gutenberg books into individual story JSONs",
    )
    parser.add_argument(
        "book_id",
        help="Project Gutenberg book ID (e.g., pg160, pg174)",
    )
    parser.add_argument(
        "--provider",
        choices=["ollama", "openrouter"],
        default=None,
        help="LLM provider override",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="LLM model override",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.yaml",
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    book_id: str = args.book_id

    # Normalize book_id: ensure it has "pg" prefix
    if not book_id.startswith("pg"):
        book_id = f"pg{book_id}"

    config = load_config(
        config_path=args.config,
        provider_override=args.provider,
        model_override=args.model,
    )

    print(f"=== Studio Parser: {book_id} ===\n")

    # Ensure DB table exists
    print("Ensuring database table...")
    ensure_table(config)

    # Fetch PG metadata (genre, author, publish year, etc.)
    print("\nFetching PG metadata...")
    from studio_parser.metadata_fetcher import fetch_pg_metadata

    book_meta = fetch_pg_metadata(book_id)
    if book_meta:
        print(f"  Title: {book_meta.title}")
        print(f"  Author: {book_meta.author}")
        print(f"  Genre: {book_meta.genre}")
        print(f"  Year: {book_meta.publish_year}")
        print(f"  Language: {book_meta.language}")
    else:
        print("  WARNING: Could not fetch PG metadata")

    # Download
    print(f"\nDownloading {book_id}...")
    downloaded = download_book(book_id, config)
    if not downloaded:
        print("ERROR: No files downloaded. Exiting.")
        sys.exit(1)

    # Parse all formats with all strategies
    print("\nParsing all formats...")
    results: list[ParseResult] = []
    all_warnings: list[str] = []

    # HTML
    if "html" in downloaded:
        print(f"  Parsing HTML: {downloaded['html'].name}")
        result = parse_html(downloaded["html"])
        _report(result)
        results.append(result)

    # EPUBs: both div.chapter and TOC-based
    for label in ["epub2", "epub2_images", "epub3_images"]:
        if label not in downloaded:
            continue
        filepath = downloaded[label]

        print(f"  Parsing {label} (div.chapter): {filepath.name}")
        result_div = parse_epub_divchapter(filepath, label)
        _report(result_div)
        results.append(result_div)

        print(f"  Parsing {label} (TOC-based): {filepath.name}")
        result_toc = parse_epub_toc(filepath, label)
        _report(result_toc)
        results.append(result_toc)

    # Collect all warnings
    for r in results:
        all_warnings.extend(r.parse_warnings)

    # If ALL parsers returned 0 works, use LLM fallback on EPUB3
    total_works_found = sum(len(r.works) for r in results)
    if total_works_found == 0:
        print("\n  All standard parsers returned 0 works — trying LLM structure analysis...")
        # Prefer EPUB3, fallback to any EPUB
        epub_path = (
            downloaded.get("epub3_images")
            or downloaded.get("epub2_images")
            or downloaded.get("epub2")
        )
        if epub_path:
            try:
                from studio_parser.agent.structure_agent import parse_with_llm_structure
                from studio_parser.parsers.epub_reader import read_epub

                title, author_epub, toc_entries, combined_soup, epub_warnings = read_epub(epub_path)
                fallback_result = parse_with_llm_structure(
                    combined_soup, title, author_epub, toc_entries, config, epub_path.name
                )
                _report(fallback_result)
                results.append(fallback_result)
                all_warnings.extend(fallback_result.parse_warnings)
            except Exception as e:
                print(f"    LLM fallback failed: {e}")

    # Reconcile
    print(f"\nReconciling {len(results)} parse results...")
    best_works = reconcile(results, config)
    print(f"  Found {len(best_works)} unique works")

    # Get metadata — prefer PG metadata (clean author name, etc.) over parser-extracted
    book_title = ""
    author = ""
    for r in results:
        if r.book_title:
            book_title = r.book_title
        if r.author:
            author = r.author
        if book_title and author:
            break

    # Override with PG metadata if available
    if book_meta:
        if book_meta.author:
            author = book_meta.author
        if book_meta.title:
            book_title = book_meta.title

    # Split into stories
    stories = split_into_stories(
        best_works,
        book_id=book_id,
        book_title=book_title,
        author=author,
    )
    print(f"\nSplit into {len(stories)} stories")

    # Enrich stories with PG metadata
    if book_meta:
        pg_extra = {
            "author_raw": book_meta.author_raw,
            "author_birth_year": book_meta.author_birth_year,
            "author_death_year": book_meta.author_death_year,
            "author_wikipedia": book_meta.author_wikipedia,
            "wikipedia_link": book_meta.wikipedia_link,
            "reading_ease": book_meta.reading_ease,
            "download_count": book_meta.download_count,
            "pg_issued_date": book_meta.pg_issued_date,
            "subjects": book_meta.subjects,
            "bookshelves": book_meta.bookshelves,
            "table_of_contents": book_meta.table_of_contents,
        }
        for story in stories:
            story.genre = book_meta.genre
            story.publish_year = book_meta.publish_year
            story.language = book_meta.language
            story.description = book_meta.description
            story.metadata.update(pg_extra)

    # Quality scoring (optional, LLM)
    llm_assisted = False
    try:
        from studio_parser.agent.quality_agent import score_stories

        print("\nScoring story quality with LLM...")
        stories = score_stories(stories, config)
        llm_assisted = True
    except Exception as e:
        print(f"\nLLM quality scoring skipped: {e}")

    # Write output
    print("\nWriting stories...")
    written = write_stories(
        stories, config, parse_warnings=all_warnings, llm_assisted=llm_assisted
    )

    print(f"\nDone! {len(written)} stories written for {book_id}")
    print(f"  Stories: {config.paths.stories_dir / book_id}")
    print(f"  Database: {config.database.path}")


def _report(result: ParseResult) -> None:
    print(
        f"    -> {len(result.works)} works, {result.total_paragraphs} paragraphs, "
        f"{result.total_word_count} words"
    )
    for w in result.parse_warnings:
        print(f"    WARNING: {w}")
