"""One structured pick when a bare creature word maps to >= 2 drawn machine
cards, and one sheet-prompt writer for a card the designer never gave one
(G-STAGE / step 03_02).  Both ride `studio.llm.structured` on the workhorse
tier: every paid path passes `guard_spend` against money.episode_ceiling_usd
before anything is sent, and spend is recorded by `_record_spend`.  The
`_structured` kwarg is the FakeModel test seam, mirroring llm.structured's
`_agent` seam -- no test may spend."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

TIER = "workhorse"


class MachinePick(BaseModel):
    """The one pid among the candidates this shot is actually showing."""
    pid: str


def pick_model(candidates: list[str]):
    """A MachinePick whose pid must be one of `candidates`: the refusal raises
    INSIDE the schema, so llm.structured's StructuredOutputException re-ask
    ladder fires with the candidate list quoted back."""
    class _Pick(MachinePick):
        @field_validator("pid")
        @classmethod
        def _known(cls, v: str) -> str:
            if v not in candidates:
                raise ValueError(f"pid {v!r} is none of the candidates {sorted(candidates)}")
            return v
    return _Pick


PICK_PROMPT = """A storyboard shot of a silent film of {book_title} reads:

  "{shot_prose}"

The bare word {term!r} must be replaced by exactly one drawn card. The candidates, from the book's prop registry:

{rows}
Pick the single pid whose card is the thing this shot is actually showing, judged from the shot's own verbs and scale (a thing that wades, strides or towers is the fighting-machine class; a thing that digs or handles is the handling class; a thing afloat is a vessel). Return only the pid."""


def candidate_rows(candidates: list[dict]) -> str:
    """One block per candidate: pid, name, two sentences of what it is, and
    what else the book calls it."""
    out = []
    for c in candidates:
        physical = ". ".join(s for s in (c.get("physical") or "").split(". ")[:2] if s)
        also = ", ".join(c.get("aliases") or c.get("terms") or [])
        out.append(f"- pid: {c['pid']}\n  name: {c.get('name') or c['pid']}\n"
                   f"  what it is: {physical}\n  the book also calls it: {also}")
    return "\n".join(out) + "\n"


def pick_prompt(prose: str, candidates: list[dict], term: str, book_title: str) -> str:
    return PICK_PROMPT.format(book_title=book_title or "the book", shot_prose=prose,
                              term=term, rows=candidate_rows(candidates))


def pick_machine(prose: str, candidates: list[dict], term: str = "", book_title: str = "",
                 *, _structured=None) -> str:
    """The picked pid, validated against the candidates twice: in the schema
    (for the real re-ask ladder) and on whatever comes back (so a fake that
    bypasses the schema still refuses)."""
    from strands.types.exceptions import StructuredOutputException
    from studio import llm
    pids = [c["pid"] for c in candidates]
    got = (_structured or llm.structured)(TIER, pick_prompt(prose, candidates, term, book_title),
                                          pick_model(pids), retries=3)
    if got.pid not in pids:
        raise StructuredOutputException(f"pid {got.pid!r} is none of the candidates {pids}")
    return got.pid


class SheetPrompt(BaseModel):
    """One reference-sheet prompt in the house form."""
    prompt: str = Field(min_length=40, max_length=600)


SHEET_PROMPT = """Write the one-image reference-sheet prompt for a prop card. The card:
  id: {pid}
  name: {name}
  kind: {kind}
  physical: {physical}
  scale: {scale}

Two sheet prompts from this book's other cards, as the form to match exactly (one object centered on a plain neutral ground, every surface and mechanism stated, no scene, no people, no text):

1. {example_1}
2. {example_2}

Return the prompt text alone: the object exactly as `physical` states it, its material and color, its one most identifying silhouette feature first, at most 90 words. Never invent a feature `physical` does not give."""


def sheet_prompt_of(card: dict, example_prompts: list[str]) -> str:
    prof = card.get("profile") or {}
    examples = (list(example_prompts) + ["", ""])[:2]
    return SHEET_PROMPT.format(pid=card.get("id") or "", name=card.get("name") or "",
                               kind=card.get("kind") or "", physical=prof.get("physical") or "",
                               scale=prof.get("scale") or "",
                               example_1=examples[0], example_2=examples[1])


def write_sheet_prompt(card: dict, example_prompts: list[str], *, _structured=None) -> str:
    """A missing design.sheet_prompt written on the workhorse tier; the house
    form travels by example from the same book's cards (the code tree names
    no book)."""
    from studio import llm
    return (_structured or llm.structured)(TIER, sheet_prompt_of(card, example_prompts),
                                           SheetPrompt, retries=3).prompt