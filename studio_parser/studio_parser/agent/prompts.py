MERGE_PROMPT = """You are a text quality analyst comparing two parsed versions of the same literary work.

Work title: {work_title}

## Candidate A ({format_a})
- Word count: {words_a}
- Paragraph count: {paras_a}
- Chapter count: {chapters_a}
- First 3 chapter titles: {chapter_titles_a}

## Candidate B ({format_b})
- Word count: {words_b}
- Paragraph count: {paras_b}
- Chapter count: {chapters_b}
- First 3 chapter titles: {chapter_titles_b}

Which candidate is the better, more complete parse? Consider:
1. Higher word/paragraph count suggests more complete extraction
2. More chapters suggests better structure detection
3. Meaningful chapter titles suggest better parsing

Respond with ONLY "A" or "B" followed by a brief reason."""


QUALITY_PROMPT = """You are a text quality analyst. Score the following parsed story on a scale of 0-100.

Title: {title}
Author: {author}
Word count: {word_count}
Paragraph count: {paragraph_count}
Chapter count: {chapter_count}

First paragraph: {first_paragraph}

Last paragraph: {last_paragraph}

Consider:
- Does the word count seem reasonable for a short story/novella? (typically 1,000-50,000 words)
- Does the first paragraph look like a proper story opening (not metadata/boilerplate)?
- Does the last paragraph look like a proper ending (not truncated/boilerplate)?
- Are the word and paragraph counts consistent (not suspiciously low)?

Respond with ONLY a number 0-100."""
