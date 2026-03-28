from __future__ import annotations

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    title: str = ""
    paragraphs: list[str] = Field(default_factory=list)
    word_count: int = 0


class Work(BaseModel):
    title: str = ""
    chapters: list[Chapter] = Field(default_factory=list)
    total_word_count: int = 0


class ParseResult(BaseModel):
    source_file: str = ""
    format_type: str = ""
    book_title: str = ""
    author: str = ""
    works: list[Work] = Field(default_factory=list)
    total_word_count: int = 0
    total_paragraphs: int = 0
    parse_warnings: list[str] = Field(default_factory=list)


class BookMetadata(BaseModel):
    title: str = ""
    author: str = ""
    author_raw: str = ""
    author_birth_year: str = ""
    author_death_year: str = ""
    author_wikipedia: str = ""
    genre: str = ""
    subjects: list[str] = Field(default_factory=list)
    bookshelves: list[str] = Field(default_factory=list)
    publish_year: str = ""
    pg_issued_date: str = ""
    language: str = ""
    description: str = ""
    wikipedia_link: str = ""
    reading_ease: str = ""
    download_count: int = 0
    table_of_contents: str = ""


class StoryOutput(BaseModel):
    story_title: str = ""
    author: str = ""
    book_title: str = ""
    book_id: str = ""
    word_count: int = 0
    paragraph_count: int = 0
    chapter_count: int = 0
    format_source: str = ""
    genre: str = ""
    publish_year: str = ""
    language: str = ""
    description: str = ""
    chapters: list[Chapter] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
