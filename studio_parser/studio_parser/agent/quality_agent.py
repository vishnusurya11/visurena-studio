from __future__ import annotations

from studio_parser.agent.llm_provider import get_llm
from studio_parser.agent.prompts import QUALITY_PROMPT
from studio_parser.config import ParserConfig
from studio_parser.models import StoryOutput


def score_story(story: StoryOutput, config: ParserConfig) -> int | None:
    """Score a single story's parse quality 0-100 using LLM."""
    all_paras = []
    for ch in story.chapters:
        all_paras.extend(ch.paragraphs)

    first_para = all_paras[0][:200] if all_paras else "(empty)"
    last_para = all_paras[-1][:200] if all_paras else "(empty)"

    prompt = QUALITY_PROMPT.format(
        title=story.story_title,
        author=story.author,
        word_count=story.word_count,
        paragraph_count=story.paragraph_count,
        chapter_count=story.chapter_count,
        first_paragraph=first_para,
        last_paragraph=last_para,
    )

    try:
        llm = get_llm(config)
        response = llm.invoke(prompt)
        score_text = response.content.strip()
        # Extract first number from response
        for token in score_text.split():
            token = token.strip(".,;:!?")
            if token.isdigit():
                score = int(token)
                if 0 <= score <= 100:
                    return score
        return None
    except Exception:
        return None


def score_stories(stories: list[StoryOutput], config: ParserConfig) -> list[StoryOutput]:
    """Score all stories and update their metadata with quality scores."""
    for story in stories:
        score = score_story(story, config)
        if score is not None:
            story.metadata["parse_quality_score"] = score
            print(f"    {story.story_title}: {score}/100")
        else:
            print(f"    {story.story_title}: scoring failed")
    return stories
