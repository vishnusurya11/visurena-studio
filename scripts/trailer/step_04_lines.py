"""Step 04 -- lines: rank the pools, label Function once, order, write lines.json.

Everything measurable is code: the four pools (`studio.trailer_story`), the
line value graded on a held-out corpus (`studio.trailer_dialogue`), what
Wikiquote kept (`studio.iconicity`), the order and the slot fit.  The one
judged thing is each candidate's Function, and two gates stand over it.  The
CONTRACT refuses a sheet that yields no hook, or no threat or stakes.  The
STORY rules refuse a slate that is not a trailer: too few voices for its
length, a hook that arrives after twelve seconds, a last word that answers the
question.  Each refusal is quoted back and ten more candidates join the sheet;
the third rung drops the story rules rather than ship silence, and only a
slate that cannot satisfy the contract ends as `music_only`.

What the labeller SEES is the other half of the fix.  Run 10 handed it the top
24 by score, 17 of them Wikiquote aphorisms off the page for the character
Sherlock Holmes, and the book's own threat ranked #663.  The window is now
quota-filled by function: the figure's confrontation whole and in order, four
seats for what the culture kept, two per role.  Nothing here asks a question.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

from scripts.analysis.iconicity_coverage import book_identity
from studio import iconicity, llm
from studio.ladder import Ladder, Rung, climb
from studio.line_windows import beat_for, load_plan, windows_for
from studio.trailer_dialogue import (line_value, names_figure, order_lines, speech_seconds,
                                     story_refusal, wanted_speech)
from studio.trailer_stage_spec import (MAX_LINES, Function, LineSlate, Metre, SlateLine,
                                       StorySpec)
from studio.trailer_story import identity_scenes, line_pools

STEP_ID = "04"
NAME = "lines"
TIER = "reasoning"
TOP_N = 30
RELABEL = 10
KEPT_BONUS, BOLD_BONUS = 2.0, 1.0
"""What the culture kept is a modifier, not the ranking.  At 6.0/2.0 over a
line value spanning about -10..+4 it WAS the ranking: 17 of run 10's 24
candidates were brain-attic aphorisms, and the book's own threat -- "Now,
Enoch Drebber, who am I?" -- ranked #663 and was never offered."""

WHERE_WEIGHT = {"book": 1.0, "author": 0.5, "character": 0.25}
"""Whose page the quotations came from.  Run 10's iconicity resolved to the
Wikiquote page for the CHARACTER Sherlock Holmes -- a century of Holmes
across every adaptation, aphorisms rather than this book's scenes.  A
character page ranks below the book's own text."""

VO_LINES = 3
"""How many of the narrator's own sentences he may speak.  `narration_pool`
marks them speakerless, so every one of them was a card."""

ROLE_QUOTA = 2
KEPT_QUOTA = 4
CONFRONTATION = 14
"""Reservations, not bonuses.  What the culture kept gets four guaranteed
seats instead of a score that swamps every other signal, each role gets two,
and the figure's confrontation joins whole and in the order he speaks it --
a confrontation is a SEQUENCE, and ranking its sentences against each other
by lexical value is what buried "Choose and eat." at #664."""

SECOND_PERSON = re.compile(r"\b(you|your|yours|thou|thy|thee)\b", re.I)
STAKES_MARK = re.compile(r"\b(die|dead|death|kill|murder|blood|danger|lose|lost"
                         r"|never|no one|nothing|life|hang|revenge)\b", re.I)
PROMISE_MARK = re.compile(r"\b(will|shall|going to|promise|before)\b", re.I)
ROLE_MARKS = {"hook": lambda t: t.rstrip().endswith("?"),
              "threat": lambda t: SECOND_PERSON.search(t) is not None,
              "stakes": lambda t: STAKES_MARK.search(t) is not None,
              "promise": lambda t: PROMISE_MARK.search(t) is not None,
              "button": lambda t: len(t.split()) <= 6}
"""The marks a role leaves in the TEXT.  The labeller still decides the
function; these only make sure it has something of each kind to decide
between, which run 10's score ranking did not (R12)."""
SLOT_STRETCH = 2.0
"""A line predicted longer than twice the longest slot is not a candidate:
the prediction is loose, the measurement decides, but this one cannot fit."""
FETCH = iconicity.default_fetch
"""The only network seam of the step; tests point it at an outage."""
LADDER = Ladder([Rung("relabel_next_10", cost_seconds=60, tries=2),
                 Rung("drop_story_rules", cost_seconds=60, tries=1)],
                terminal="music_only")
"""R1: `music_only` is a REFUSAL, not an outcome.  Two labellings are gated
on the story rules -- enough voices, an early hook, an open last word -- and
the third drops those rules rather than shipping a silent trailer.  Only a
slate that cannot satisfy the CONTRACT ends in silence."""


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


def kept_quotes(ctx) -> dict:
    """Wikiquote's record for this book: the kept quotations AND whose page
    they came from, because a character page is worth a quarter of the
    book's own (`WHERE_WEIGHT`)."""
    title, author, names = book_identity(ctx.book_dir)
    doc = iconicity.fetch_wikiquote(title, author, names, book_dir=ctx.book_dir, fetch=FETCH)
    if doc.get("offline"):
        ctx.tracker.log("wikiquote unreachable; iconicity from cache", step_id=STEP_ID,
                        level="WARNING")
    return doc


def candidates(book_dir: Path, story: StorySpec) -> list[dict]:
    """The pools, less the resolution and any line that names the figure."""
    restricted = set(story.restricted_scenes)
    return [line for line in line_pools(book_dir, narrator=story.narrator)
            if line["scene"] not in restricted and not names_figure(line["text"], story.figure)]


def rank(lines: list[dict], kept: list[dict], leads: tuple[str, ...],
         longest_slot: float, where: str | None = "book") -> list[dict]:
    """Line value plus what the culture kept, best first.

    `order` travels with every line, because a confrontation is read in the
    order it is spoken and a score sort destroys that order.
    """
    weight = WHERE_WEIGHT.get(where or "", 1.0)
    ranked: list[dict] = []
    for order, line in enumerate(lines):
        if speech_seconds(line["text"]) > SLOT_STRETCH * longest_slot:
            continue
        hit = iconicity.match_kept(line["text"], kept) if kept else None
        score = line_value(line["text"], None, line["speaker"] or "", leads)
        if hit:
            score += weight * (KEPT_BONUS + BOLD_BONUS * bool(hit["bold"]))
        ranked.append({**line, "order": order, "score": round(score, 4),
                       "kept": hit is not None, "bold": bool(hit and hit["bold"])})
    return sorted(ranked, key=lambda l: -l["score"])


def climax_scenes(scenes: list[dict], story: StorySpec) -> set[int]:
    """The scenes a trailer's threat and last word come from: where the
    figure is finally tied to what he did, plus the story's own turn."""
    found = {story.turn_scene} | identity_scenes(scenes, story.lead, story.figure)
    return found - set(story.restricted_scenes)


def confrontation(ranked: list[dict], figure: str, climax: set[int]) -> list[dict]:
    """Where the figure's climax LANDS: his last lines of it, in spoken order.

    This is R12's core.  Hope's "Now, Enoch Drebber, who am I?" and "Choose
    and eat." score 0.6 apiece against a brain-attic aphorism's 10.0, because
    lexical value measures how well a sentence reads ALONE and these two are
    the halves of a murder.  No ranking reaches them; a quota does.

    The TAIL rather than the head: the opening of a confrontation is still
    setup, and a trailer's threat and last word come from where it lands.
    """
    found = [l for l in ranked if l["speaker"] == figure and l["scene"] in climax]
    return sorted(found, key=lambda l: l["order"])[-CONFRONTATION:]


def kept_seeds(ranked: list[dict]) -> list[dict]:
    """The lines the culture kept, as a QUOTA rather than as a bonus.

    Wikiquote is real evidence and it is not a ranking: at 6.0 over a line
    value spanning -10..+4 it decided the whole order.  Four reserved seats,
    editor-bolded first, keeps the signal and hands the rest of the window
    back to the book.
    """
    return sorted([l for l in ranked if l["kept"]],
                  key=lambda l: (not l["bold"], -l["score"]))[:KEPT_QUOTA]


def role_seeds(ranked: list[dict]) -> list[dict]:
    """Two candidates per trailer role, by the marks a role leaves in the
    text.  A labeller cannot label a threat it was never shown."""
    seeds: list[dict] = []
    for mark in ROLE_MARKS.values():
        seeds += [l for l in ranked if mark(l["text"])][:ROLE_QUOTA]
    return seeds


def quota_fill(ranked: list[dict], count: int, figure: str,
               climax: set[int]) -> list[dict]:
    """What the labeller actually sees: the best `count`, with room reserved.

    Run 10 handed it the top 24 by score, 17 of them Wikiquote aphorisms off
    the Sherlock Holmes character page, and the sheet came back hook 1 /
    threat 2 / stakes 0 / button 0.  The model did not choose wrong; it was
    never offered the right lines.
    """
    reserved, seen = [], set()
    for line in ([l for l in ranked if l["pool"] == "thesis"]
                 + confrontation(ranked, figure, climax) + kept_seeds(ranked)
                 + role_seeds(ranked)):
        if line["text"] not in seen:
            seen.add(line["text"])
            reserved.append(line)
    best = [l for l in ranked if l["text"] not in seen][:max(count - len(reserved), 0)]
    return sorted(reserved + best, key=lambda l: -l["score"])


def voiced(ranked: list[dict], narrator: str | None, cap: int = VO_LINES) -> list[dict]:
    """Let the narrator SPEAK a few of his own sentences.

    `narration_pool` marks them speakerless, which makes every one a card,
    and a card is eight words (R9) -- so the framing the narrator exists for
    could only ever ship as prose on screen.  He never plays the hook or the
    last word (`trailer_dialogue.playable`).
    """
    if not narrator or narrator == "omniscient":
        return ranked
    spent, out = 0, []
    for line in ranked:
        if line["pool"] == "narration" and not line["speaker"] and spent < cap:
            line, spent = {**line, "speaker": narrator}, spent + 1
        out.append(line)
    return out


def thesis_card(story: StorySpec) -> list[dict]:
    """R11: the refrain reaches the screen, as a card or in a voice."""
    if not story.thesis:
        return []
    return [{"text": story.thesis[:1].upper() + story.thesis[1:].rstrip(".") + ".",
             "speaker": None, "pool": "thesis", "scene": None}]


def runtime_of(ctx, metre: Metre) -> float:
    """How long the picture will actually run.

    Step 06 folds the cue's spans to the takes the budget affords, so the
    cue's own length is an upper bound and not the trailer.  A recut reads the plan's
    end; the first pass has only the cue.
    """
    path = ctx.out_dir / "plan.json"
    if path.exists():
        shots = json.loads(path.read_text(encoding="utf-8")).get("shots") or []
        if shots:
            return shots[-1]["start"] + shots[-1]["seconds"]
    return metre.title_hit or metre.seconds


def iconicity_level(ranked: list[dict], kept: list[dict]) -> str:
    """`none` with no record, `thin` when fewer than two kept lines reached
    the pool: the run is then flying on text signals (research 7.3)."""
    if not kept:
        return "none"
    return "full" if sum(l["kept"] for l in ranked) >= 2 else "thin"


def prompt_for(ranked: list[dict], story: StorySpec, violation: str | None,
               wanted: int = 3) -> str:
    functions = ", ".join(Function.__args__)  # type: ignore[attr-defined]
    listed = "\n".join(f"[{i}] {l['speaker'] or 'CARD'}: {l['text']}" for i, l in enumerate(ranked))
    quoted = (f"\n\nYour previous sheet was refused: {violation}. Relabel with that in mind."
              if violation else "")
    return (f"Setting: {story.setting or 'unknown'}. Lead: {story.lead}. The figure whose "
            f"identity the trailer withholds: {story.figure}.\n\nLabel each candidate line "
            f"with its trailer function, one of: {functions}.\nhook: a question or claim "
            f"the audience must have answered. stakes: what is at risk. threat: the danger, "
            f"in the figure's voice where possible. promise: what the story will deliver. "
            f"button: a short last word, a question or a threat. exposition: everything "
            f"else.\n\nThis trailer must SPEAK at least {wanted} of these lines, so label "
            f"at least that many with a role other than exposition.\n\n{listed}" + quoted)


def labelled(ranked: list[dict], sheet: LabelSheet) -> list[SlateLine]:
    """The sheet applied to the ranking, in rank order, first label per index."""
    functions: dict[int, str] = {}
    for label in sheet.labels:
        functions.setdefault(label.index, label.function)
    return [SlateLine(text=l["text"], speaker=l["speaker"], function=functions[i],
                      kept=l["kept"], bold=l["bold"], pool=l["pool"], score=l["score"])
            for i, l in enumerate(ranked) if i in functions]


def write_sheet(out_dir: Path, attempt: int, lines: list[SlateLine]) -> None:
    """work/labels-N.json: the sheet as applied, for the retrospect."""
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    rows = [{"text": l.text, "speaker": l.speaker, "function": l.function} for l in lines]
    (work / f"labels-{attempt}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False),
                                                 encoding="utf-8")


def try_order(lines: list[SlateLine], slots: list, figure: str, beat: float | None,
              level: str, violation: dict, runtime: float | None = None) -> tuple[bool, object, str]:
    """The ladder's gate: the ordered slate, or the refusal to quote back.

    Two kinds of refusal, and they are not the same kind of thing.  The
    CONTRACT refuses a slate that is not a slate.  The STORY rules refuse a
    slate that is not a TRAILER -- one voice in a hundred seconds, a hook at
    38.9 s, a last word that answers the question.  `runtime` is None on the
    last rung, where the story rules are dropped rather than ship silence.
    """
    try:
        slate = order_lines(lines, slots, figure, beat=beat, iconicity=level)
    except ValueError as exc:
        violation["text"] = str(exc)
        return False, violation["text"], "LineSlate"
    said = story_refusal(slate, runtime, MAX_LINES) if runtime else None
    if said:
        violation["text"] = said
        return False, said, "a trailer that speaks"
    return True, slate, "LineSlate"


def line_windows(ctx, metre: Metre) -> tuple[list, float | None]:
    """Where a line may sit, and the beat it is measured in.

    BUILD 50: with step 03's plan the windows are its troughs and sustains,
    each a beat short of the span, so a line ends before the cut and never
    under it.  A production cut before the plan existed keeps the metre's
    windows; which path was taken is on the log.
    """
    plan = load_plan(ctx.out_dir)
    source = "music/plan.json (troughs and sustains)" if plan else "music/metre.json (slots and phrases)"
    ctx.tracker.log(f"line windows from {source}", step_id=STEP_ID)
    return windows_for(metre, plan), beat_for(metre, plan)


def label(ranked: list[dict], story: StorySpec, windows: list, beat: float | None, level: str,
          ctx, runtime: float = 0.0, climax: set | None = None) -> tuple[LineSlate, list[SlateLine]]:
    """Climb the labelling ladder: each refusal is quoted back, ten more
    candidates join the sheet, and the last rung drops the story rules.
    Returns the slate and every labelled line, so step 05 can fall back to a
    spare."""
    violation: dict = {"text": None}
    seen: list[SlateLine] = []
    state = {"n": 0, "strict": True}
    wanted = wanted_speech(runtime, MAX_LINES)

    def attempt(rung, i):
        state["strict"] = rung.name != "drop_story_rules"
        top = quota_fill(ranked, TOP_N + state["n"] * RELABEL, story.figure, climax or set())
        sheet = llm.structured(TIER, prompt_for(top, story, violation["text"], wanted), LabelSheet)
        seen[:] = labelled(top, sheet)
        write_sheet(ctx.out_dir, state["n"], seen)
        state["n"] += 1
        return seen

    def gate(lines):
        return try_order(lines, windows, story.figure, beat, level, violation,
                         runtime if state["strict"] else None)

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


def scenes_of(book_dir: Path) -> list[dict]:
    path = book_dir / "screenplay/feature/screenplay.json"
    return json.loads(path.read_text(encoding="utf-8"))["scenes"]


def run(codex_id: str, ctx) -> None:
    story, metre = load_inputs(ctx.out_dir)
    doc = kept_quotes(ctx)
    kept = doc.get("kept", [])
    windows, beat = line_windows(ctx, metre)
    longest = max([s.seconds for s in windows] or [0.0])
    scenes = scenes_of(ctx.book_dir)
    pool = thesis_card(story) + candidates(ctx.book_dir, story)
    ranked = voiced(rank(pool, kept, (story.lead,), longest, doc.get("where")), story.narrator)
    level = iconicity_level(ranked, kept)
    runtime = runtime_of(ctx, metre)
    slate, spare = label(ranked, story, windows, beat, level, ctx, runtime,
                         climax_scenes(scenes, story))
    write_slate(ctx.out_dir, slate, spare)
    print(f"[{STEP_ID}] {len(ranked)} candidates, {len(windows)} windows, "
          f"{runtime:.0f} s picture, needs {wanted_speech(runtime, MAX_LINES)} spoken, "
          f"iconicity {level}, " + ("music only" if slate.music_only else
                                    " -> ".join(f"{l.function}:{l.speaker or 'CARD'}"
                                                for l in slate.lines)))
