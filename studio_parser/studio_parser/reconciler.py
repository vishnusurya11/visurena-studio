from __future__ import annotations

from studio_parser.config import ParserConfig
from studio_parser.models import ParseResult, Work


def _score_result(result: ParseResult) -> tuple[int, int, int, int]:
    """Score a full ParseResult. Higher is better.

    Priority: total word count, total paragraphs, number of works, negative warnings.
    """
    return (
        result.total_word_count,
        result.total_paragraphs,
        len(result.works),
        -len(result.parse_warnings),
    )


def _pick_best_source(results: list[ParseResult], config: ParserConfig) -> ParseResult:
    """Pick ONE best format source for the entire book.

    Prefers epub3_images_toc > epub3_images_divchapter > other formats.
    Among equal word counts, prefers EPUB3 > EPUB2 > HTML.
    """
    if not results:
        raise ValueError("No parse results to reconcile")

    # Format preference order (higher = better)
    format_preference = {
        "epub3_images_toc": 10,
        "epub3_images_divchapter": 9,
        "epub2_images_toc": 8,
        "epub2_images_divchapter": 7,
        "epub2_toc": 6,
        "epub2_divchapter": 5,
        "html": 4,
        "llm_fallback": 3,
    }

    # Filter out results with 0 works
    valid = [r for r in results if len(r.works) > 0 and r.total_word_count > 0]
    if not valid:
        return results[0]

    # Find the max word count across all results
    max_words = max(r.total_word_count for r in valid)

    # Among results within 5% of max word count, pick by format preference
    top_tier = [r for r in valid if r.total_word_count >= max_words * 0.95]

    best = max(
        top_tier,
        key=lambda r: (format_preference.get(r.format_type, 0), _score_result(r)),
    )

    return best


def reconcile(
    results: list[ParseResult],
    config: ParserConfig,
) -> list[tuple[str, Work]]:
    """Pick the single best format source, then return all its works.

    Filters out works with 0 words (section headers, metadata entries).
    Returns list of (format_source, Work) tuples.
    """
    if not results:
        return []

    best = _pick_best_source(results, config)
    print(f"  Best source: {best.format_type} ({best.total_word_count} words, "
          f"{len(best.works)} works, {len(best.parse_warnings)} warnings)")

    # Filter out 0-word works (section headers, year entries, etc.)
    works = [
        (best.format_type, work)
        for work in best.works
        if work.total_word_count > 0
    ]

    return works
