from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from studio_parser.config import ParserConfig

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS parsed_stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id TEXT NOT NULL,
    story_title TEXT NOT NULL,
    book_title TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    word_count INTEGER NOT NULL DEFAULT 0,
    paragraph_count INTEGER NOT NULL DEFAULT 0,
    chapter_count INTEGER NOT NULL DEFAULT 0,
    format_source TEXT NOT NULL,
    json_path TEXT NOT NULL,
    genre TEXT DEFAULT NULL,
    publish_year TEXT DEFAULT NULL,
    language TEXT DEFAULT NULL,
    description TEXT DEFAULT NULL,
    pg_metadata TEXT DEFAULT NULL,
    parse_quality_score INTEGER DEFAULT NULL,
    llm_assisted INTEGER NOT NULL DEFAULT 0,
    parse_warnings TEXT DEFAULT NULL,
    parsed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(book_id, story_title)
);
"""

# Migration for existing tables that lack new columns
MIGRATION_COLUMNS = [
    ("genre", "TEXT DEFAULT NULL"),
    ("publish_year", "TEXT DEFAULT NULL"),
    ("language", "TEXT DEFAULT NULL"),
    ("description", "TEXT DEFAULT NULL"),
    ("pg_metadata", "TEXT DEFAULT NULL"),
]


def get_connection(config: ParserConfig) -> sqlite3.Connection:
    db_path = Path(config.database.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ensure_table(config: ParserConfig) -> None:
    conn = get_connection(config)
    try:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()

        # Migrate existing table: add new columns if missing
        for col_name, col_type in MIGRATION_COLUMNS:
            try:
                conn.execute(f"ALTER TABLE parsed_stories ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists
    finally:
        conn.close()


def upsert_story(
    config: ParserConfig,
    *,
    book_id: str,
    story_title: str,
    book_title: str,
    author: str,
    word_count: int,
    paragraph_count: int,
    chapter_count: int,
    format_source: str,
    json_path: str,
    genre: str | None = None,
    publish_year: str | None = None,
    language: str | None = None,
    description: str | None = None,
    pg_metadata: dict | None = None,
    parse_quality_score: int | None = None,
    llm_assisted: bool = False,
    parse_warnings: list[str] | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    warnings_json = json.dumps(parse_warnings) if parse_warnings else None
    pg_metadata_json = json.dumps(pg_metadata) if pg_metadata else None

    conn = get_connection(config)
    try:
        conn.execute(
            """
            INSERT INTO parsed_stories
                (book_id, story_title, book_title, author, word_count, paragraph_count,
                 chapter_count, format_source, json_path, genre, publish_year, language,
                 description, pg_metadata, parse_quality_score,
                 llm_assisted, parse_warnings, parsed_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(book_id, story_title) DO UPDATE SET
                book_title = excluded.book_title,
                author = excluded.author,
                word_count = excluded.word_count,
                paragraph_count = excluded.paragraph_count,
                chapter_count = excluded.chapter_count,
                format_source = excluded.format_source,
                json_path = excluded.json_path,
                genre = excluded.genre,
                publish_year = excluded.publish_year,
                language = excluded.language,
                description = excluded.description,
                pg_metadata = excluded.pg_metadata,
                parse_quality_score = excluded.parse_quality_score,
                llm_assisted = excluded.llm_assisted,
                parse_warnings = excluded.parse_warnings,
                updated_at = excluded.updated_at
            """,
            (
                book_id, story_title, book_title, author, word_count, paragraph_count,
                chapter_count, format_source, json_path, genre, publish_year, language,
                description, pg_metadata_json, parse_quality_score,
                int(llm_assisted), warnings_json, now, now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_book_stories(config: ParserConfig, book_id: str) -> int:
    """Delete all parsed stories for a book. Returns number of rows deleted."""
    conn = get_connection(config)
    try:
        cursor = conn.execute(
            "DELETE FROM parsed_stories WHERE book_id = ?", (book_id,)
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def get_parsed_stories(config: ParserConfig, book_id: str) -> list[dict]:
    conn = get_connection(config)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM parsed_stories WHERE book_id = ?", (book_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
