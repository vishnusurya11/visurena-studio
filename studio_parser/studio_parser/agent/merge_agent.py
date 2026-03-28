from __future__ import annotations

from studio_parser.agent.llm_provider import get_llm
from studio_parser.agent.prompts import MERGE_PROMPT
from studio_parser.config import ParserConfig
from studio_parser.models import Work


def reconcile_pair(
    candidate_a: tuple[str, Work],
    candidate_b: tuple[str, Work],
    config: ParserConfig,
) -> tuple[str, Work] | None:
    """Use LLM to pick the better parse between two close candidates.

    Returns the winning (format_type, Work) or None if LLM fails.
    """
    format_a, work_a = candidate_a
    format_b, work_b = candidate_b

    paras_a = sum(len(c.paragraphs) for c in work_a.chapters)
    paras_b = sum(len(c.paragraphs) for c in work_b.chapters)

    titles_a = [c.title for c in work_a.chapters[:3] if c.title]
    titles_b = [c.title for c in work_b.chapters[:3] if c.title]

    prompt = MERGE_PROMPT.format(
        work_title=work_a.title,
        format_a=format_a,
        words_a=work_a.total_word_count,
        paras_a=paras_a,
        chapters_a=len(work_a.chapters),
        chapter_titles_a=", ".join(titles_a) or "(none)",
        format_b=format_b,
        words_b=work_b.total_word_count,
        paras_b=paras_b,
        chapters_b=len(work_b.chapters),
        chapter_titles_b=", ".join(titles_b) or "(none)",
    )

    try:
        llm = get_llm(config)
        response = llm.invoke(prompt)
        answer = response.content.strip().upper()

        if answer.startswith("A"):
            print(f"    LLM chose {format_a} for '{work_a.title}'")
            return candidate_a
        elif answer.startswith("B"):
            print(f"    LLM chose {format_b} for '{work_b.title}'")
            return candidate_b
        else:
            print(f"    LLM gave ambiguous answer: {answer[:50]}")
            return None
    except Exception as e:
        print(f"    LLM merge failed: {e}")
        return None
