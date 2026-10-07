"""The micro-line writer: ONE grounded narration sentence bridging a residual
hole in speech that trimming to the floors could not close (or splitting an
unsplit ONE PER TAKE pair -- speech splits a take without opening silence).

Book-neutral: typed inputs in (the shot's own fields, the chapter's paragraph,
the lines either side), a string out.  The call runs on the 'local' tier
through `studio.llm.structured`, so `guard_spend` fires inside the real caller
before anything is sent; `_agent` is the test seam and no test may call a paid
API.  Schema rules live in MicroLine; the checks that need the book
(lifted_run, slow_word) live in `refusals` and re-ask exactly once."""
from __future__ import annotations

from pydantic import BaseModel, model_validator

from studio import episode_spec as spec

TIER = "local"
"""The writer tier: a micro-line is written by the same voice as the plan."""

PROMPT = """You write one line of first-person narration for a short film of a public-domain novel.
A {gap_s:.1f} second stretch of picture has no voice over it and needs exactly one sentence.

THE SHOT it will play on (shot {shot_index}, {size}):
frame: {frame}
motion: {motion}
why this shot is in the episode: {why}

THE CHAPTER'S OWN WORDS for this moment (ground truth -- paraphrase, never copy):
{source_paragraph}

The spoken line BEFORE this stretch: {prev_line_text}
The spoken line AFTER this stretch: {next_line_text}

Write ONE narration sentence of 8 to 14 words, first person, past tense, in the narrator's voice, bridging those two lines over this picture.
Rules:
- never copy a run of more than {quote_wall} consecutive words from the chapter text above
- no parentheses, no camera or stage words, no character descriptions
- add what the picture cannot show (a thought, a sound off, a fear, a smell) -- never caption what the frame already draws
- do not end the sentence with an exclamation mark"""


class MicroLine(BaseModel):
    """One narration bridge sentence; every rule its own validator so the
    re-ask ladder in llm.structured hears exactly what was refused."""
    text: str

    @model_validator(mode="after")
    def _eight_to_fourteen_words(self) -> "MicroLine":
        n = len(self.text.split())
        if not 8 <= n <= 14:
            raise ValueError(f"the line is {n} words; a micro-line is 8 to 14")
        if n > spec.MAX_WORDS:
            raise ValueError(f"{n} words is over the contract's {spec.MAX_WORDS}")
        return self

    @model_validator(mode="after")
    def _nothing_bracketed_is_spoken(self) -> "MicroLine":
        if "(" in self.text or ")" in self.text:
            raise ValueError("a parenthesis rides in spoken text, which is read aloud whole")
        return self

    @model_validator(mode="after")
    def _no_narration_shout(self) -> "MicroLine":
        if self.text.rstrip(" \"'’”").endswith("!"):
            raise ValueError("a narration shout is refused (G-SHOUT); end without '!'")
        return self


def prompt_for(shot: dict, source_paragraph: str, prev_text: str,
               next_text: str, gap_s: float) -> str:
    return PROMPT.format(
        gap_s=gap_s, shot_index=shot.get("index"), size=shot.get("size") or "",
        frame=shot.get("frame") or "", motion=shot.get("motion") or "",
        why=shot.get("why") or "", source_paragraph=source_paragraph,
        prev_line_text=prev_text, next_line_text=next_text, quote_wall=spec.QUOTE_WALL)


def refusals(text: str, book_words: str) -> list[str]:
    """The post-checks that need the book, so they live outside the schema:
    the gates' own measures, re-run on the answer."""
    out = []
    if spec.lifted_run(text, book_words) > spec.QUOTE_WALL:
        out.append(f"the line copies a run of more than {spec.QUOTE_WALL} "
                   f"consecutive words from the chapter; paraphrase it")
    if word := spec.slow_word(text):
        out.append(f"the line carries the pace word {word!r}; no slow shots")
    return out


def fill(shot: dict, source_paragraph: str, prev_text: str, next_text: str,
         gap_s: float, book_words: str, _agent=None) -> str | None:
    """One grounded micro-line, or None (the fault row stays creative): a
    breach of the book-grounded checks is re-asked ONCE with the refusal
    quoted, then given up -- default ESCALATE for what judgement cannot settle."""
    from studio import llm
    prompt = prompt_for(shot, source_paragraph, prev_text, next_text, gap_s)
    got = llm.structured(TIER, prompt, MicroLine, _agent=_agent)
    bad = refusals(got.text, book_words)
    if not bad:
        return got.text
    got = llm.structured(TIER, llm.re_ask(prompt, RuntimeError("; ".join(bad))),
                         MicroLine, _agent=_agent)
    return got.text if not refusals(got.text, book_words) else None
