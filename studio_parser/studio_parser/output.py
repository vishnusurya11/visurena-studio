from __future__ import annotations

import json
import re
from pathlib import Path

from studio_parser.config import ParserConfig
from studio_parser.db import delete_book_stories, upsert_story
from studio_parser.models import StoryOutput


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "_", slug)
    return slug[:80]


def write_stories(
    stories: list[StoryOutput],
    config: ParserConfig,
    *,
    parse_warnings: list[str] | None = None,
    llm_assisted: bool = False,
) -> list[Path]:
    """Write each story as JSON and upsert into DB. Returns list of written file paths."""
    written: list[Path] = []

    # Clean slate: delete old rows for this book before inserting fresh
    if stories:
        deleted = delete_book_stories(config, stories[0].book_id)
        if deleted:
            print(f"  Cleared {deleted} old DB rows for {stories[0].book_id}")

    for story in stories:
        # Write JSON to {stories_dir}/{book_id}/{slug}.json
        book_dir = config.paths.stories_dir / story.book_id
        book_dir.mkdir(parents=True, exist_ok=True)

        slug = _slugify(story.story_title) or "untitled"
        json_filename = f"{slug}.json"
        json_path = book_dir / json_filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(story.model_dump(), f, indent=2, ensure_ascii=False)

        print(f"  Written: {json_path}")
        written.append(json_path)

        # Upsert into DB
        quality_score = story.metadata.get("parse_quality_score")
        pg_meta = {
            k: v for k, v in story.metadata.items()
            if k != "parse_quality_score"
        } or None
        upsert_story(
            config,
            book_id=story.book_id,
            story_title=story.story_title,
            book_title=story.book_title,
            author=story.author,
            word_count=story.word_count,
            paragraph_count=story.paragraph_count,
            chapter_count=story.chapter_count,
            format_source=story.format_source,
            json_path=str(json_path),
            genre=story.genre or None,
            publish_year=story.publish_year or None,
            language=story.language or None,
            description=story.description or None,
            pg_metadata=pg_meta,
            parse_quality_score=quality_score,
            llm_assisted=llm_assisted,
            parse_warnings=parse_warnings,
        )

    return written
