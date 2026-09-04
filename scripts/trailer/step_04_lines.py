"""Step 04 -- lines: rank the pools, label Function once, order, write lines.json.

Everything measurable is code: the four pools (`studio.trailer_story`), the
line value graded on a held-out corpus (`studio.trailer_dialogue`), what
Wikiquote kept (`studio.iconicity`), the order and the slot fit.  The one
judged thing is each candidate's Function, and the contract is the gate: a
sheet that yields no hook, or no threat or stakes, is refused; the next ten
candidates join a second sheet; a second refusal ships `music_only` and
writes why.  Nothing here asks a question.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from scripts.analysis.iconicity_coverage import book_identity
from studio import iconicity, llm
from studio.ladder import Ladder, Rung, climb
from studio.trailer_dialogue import line_value, names_figure, order_lines, speech_seconds
from studio.trailer_stage_spec import Function, LineSlate, Metre, SlateLine, StorySpec
from studio.trailer_story import line_pools

STEP_ID = "04"
NAME = "lines"
TIER = "reasoning"
TOP_N = 24
RELABEL = 10
KEPT_BONUS, BOLD_BONUS = 6.0, 2.0
SLOT_STRETCH = 2.0
"""A line predicted longer than twice the longest slot is not a candidate:
the prediction is loose, the measurement decides, but this one cannot fit."""
FETCH = iconicity.default_fetch
"""The only network seam of the step; tests point it at an outage."""
LADDER = Ladder([Rung("relabel_next_10", cost_seconds=60, tries=2)], terminal="music_only")


class Label(BaseModel):
    index: int = Field(ge=0)
    function: Function


class LabelSheet(BaseModel):
    """What the model decides: one Function per candidate index."""

    labels: list[Label]


def load_inputs(out_dir: Path) -> tuple[StorySpec, Metre]:
    story = StorySpec.model_validate_json((out_dir / "story.json").read_text(encoding="utf-8"))
    metre = Metre.model_validate_json((out_dir / "music/metre.json").read_text(encoding="utf-8"))
    return story, metre


def kept_quotes(ctx) -> list[dict]:
    """Wikiquote's kept quotations for the book, from the cache unless the
    page moved on; offline the cache is the record."""
    title, author, names = book_identity(ctx.book_dir)
    doc = iconicity.fetch_wikiquote(title, author, names, book_dir=ctx.book_dir, fetch=FETCH)
    if doc.get("offline"):
        ctx.tracker.log("wikiquote unreachable; iconicity from cache", step_id=STEP_ID,
                        level="WARNING")
    return doc.get("kept", [])


def candidates(book_dir: Path, story: StorySpec) -> list[dict]:
    """The pools, less the resolution and any line that names the figure."""
    restricted = set(story.restricted_scenes)
    return [line for line in line_pools(book_dir, narrator=story.narrator)
            if line["scene"] not in restricted and not names_figure(line["text"], story.figure)]


def rank(lines: list[dict], kept: list[dict], leads: tuple[str, ...],
         longest_slot: float) -> list[dict]:
    """Line value plus what the culture kept, best first."""
    ranked: list[dict] = []
    for line in lines:
        if speech_seconds(line["text"]) > SLOT_STRETCH * longest_slot:
            continue
        hit = iconicity.match_kept(line["text"], kept) if kept else None
        score = line_value(line["text"], None, line["speaker"] or "", leads)
        score += (KEPT_BONUS + BOLD_BONUS * bool(hit["bold"])) if hit else 0.0
        ranked.append({**line, "score": round(score, 4), "kept": hit is not None,
                       "bold": bool(hit and hit["bold"])})
    return sorted(ranked, key=lambda l: -l["score"])


def iconicity_level(ranked: list[dict], kept: list[dict]) -> str:
    """`none` with no record, `thin` when fewer than two kept lines reached
    the pool: the run is then flying on text signals (research 7.3)."""
    if not kept:
        return "none"
    return "full" if sum(l["kept"] for l in ranked) >= 2 else "thin"


def prompt_for(ranked: list[dict], story: StorySpec, violation: str | None) -> str:
    functions = ", ".join(Function.__args__)  # type: ignore[attr-defined]
    listed = "\n".join(f"[{i}] {l['speaker'] or 'CARD'}: {l['text']}" for i, l in enumerate(ranked))
    quoted = (f"\n\nYour previous sheet was refused: {violation}. Relabel with that in mind."
              if violation else "")
    return (f"Setting: {story.setting or 'unknown'}. Lead: {story.lead}. The figure whose "
            f"identity the trailer withholds: {story.figure}.\n\nLabel each candidate line "
            f"with its trailer function, one of: {functions}.\nhook: a question or claim "
            f"the audience must have answered. stakes: what is at risk. threat: the danger, "
            f"in the figure's voice where possible. promise: what the story will deliver. "
            f"button: a short last word. exposition: everything else.\n\n{listed}" + quoted)


def labelled(ranked: list[dict], sheet: LabelSheet) -> list[SlateLine]:
    """The sheet applied to the ranking, in rank order, first label per index."""
    functions: dict[int, str] = {}
    for label in sheet.labels:
        functions.setdefault(label.index, label.function)
    return [SlateLine(text=l["text"], speaker=l["speaker"], function=functions[i],
                      kept=l["kept"], bold=l["bold"], pool=l["pool"], score=l["score"])
            for i, l in enumerate(ranked) if i in functions]


def try_order(lines: list[SlateLine], slots: list, figure: str, beat: float | None,
              level: str, violation: dict) -> tuple[bool, object, str]:
    """The ladder's gate: the ordered slate, or the refusal to quote back."""
    try:
        return True, order_lines(lines, slots, figure, beat=beat, iconicity=level), "LineSlate"
    except ValueError as exc:
        violation["text"] = str(exc)
        return False, violation["text"], "LineSlate"


def label(ranked: list[dict], story: StorySpec, metre: Metre, level: str,
          ctx) -> tuple[LineSlate, list[SlateLine]]:
    """Climb the labelling ladder: each refusal is quoted back, ten more
    candidates join the sheet, and the terminal rung is music only.  Returns
    the slate and every labelled line, so step 05 can fall back to a spare."""
    beat = metre.beat if metre.grid == "metre" else None
    violation: dict = {"text": None}
    seen: list[SlateLine] = []

    def attempt(rung, i):
        top = ranked[:TOP_N + i * RELABEL]
        sheet = llm.structured(TIER, prompt_for(top, story, violation["text"]), LabelSheet)
        seen[:] = labelled(top, sheet)
        return seen

    def gate(lines):
        return try_order(lines, metre.slots, story.figure, beat, level, violation)

    outcome = climb(LADDER, STEP_ID, attempt, gate, ctx.budget, ctx.learn, gate_name="slate")
    if outcome.terminal:
        return LineSlate(lines=[], iconicity=level, music_only=True), seen
    return gate(outcome.result)[1], seen


def write_slate(out_dir: Path, slate: LineSlate, spare: list[SlateLine]) -> None:
    """lines.json: the slate, plus the labelled lines it did not use as
    `pool`, so step 05 can swap in the next line of the same function."""
    used = {l.text for l in slate.lines}
    doc = json.loads(slate.model_dump_json(by_alias=True))
    doc["pool"] = [json.loads(l.model_dump_json()) for l in spare if l.text not in used]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lines.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                                        encoding="utf-8")


def run(codex_id: str, ctx) -> None:
    story, metre = load_inputs(ctx.out_dir)
    kept = kept_quotes(ctx)
    longest = max((s.seconds for s in metre.slots), default=0.0)
    ranked = rank(candidates(ctx.book_dir, story), kept, (story.lead,), longest)
    level = iconicity_level(ranked, kept)
    slate, spare = label(ranked, story, metre, level, ctx)
    write_slate(ctx.out_dir, slate, spare)
    print(f"[{STEP_ID}] {len(ranked)} candidates, {len(metre.slots)} slots, iconicity {level}, "
          + ("music only" if slate.music_only else
             " -> ".join(f"{l.function}:{l.speaker or 'CARD'}" for l in slate.lines)))
