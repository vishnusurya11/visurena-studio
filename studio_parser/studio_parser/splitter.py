from __future__ import annotations

from studio_parser.models import Chapter, StoryOutput, Work


def split_into_stories(
    reconciled_works: list[tuple[str, Work]],
    *,
    book_id: str,
    book_title: str,
    author: str,
) -> list[StoryOutput]:
    """Split reconciled works into individual StoryOutput objects."""
    stories: list[StoryOutput] = []

    for format_source, work in reconciled_works:
        total_paras = sum(len(c.paragraphs) for c in work.chapters)

        # For single-chapter works where chapter has no title, the work IS the story
        chapters = work.chapters
        if len(chapters) == 1 and not chapters[0].title:
            chapters = [Chapter(
                title=work.title,
                paragraphs=chapters[0].paragraphs,
                word_count=chapters[0].word_count,
            )]

        story = StoryOutput(
            story_title=work.title,
            author=author,
            book_title=book_title,
            book_id=book_id,
            word_count=work.total_word_count,
            paragraph_count=total_paras,
            chapter_count=len(work.chapters),
            format_source=format_source,
            chapters=chapters,
            metadata={
                "book_id": book_id,
                "original_book_title": book_title,
            },
        )
        stories.append(story)

    return stories
