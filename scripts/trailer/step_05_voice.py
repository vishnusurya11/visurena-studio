"""Step 05 -- voice: one designed voice per speaker, every spoken line cloned
from it, gated on speaker similarity, written to voice.json.

The gate is the only judgment here and it is a number: a resemblyzer cosine
between the line and its reference, against `SIMILARITY_FLOOR`.  A miss
climbs: three seeds on the same line, then the next unused line with the same
FUNCTION from the slate's pool, then the card -- the line shown as text, which
always exists.  A line nobody speaks, or whose speaker has no cast card, is a
card without a render.  Rung costs are what the render took, not a guess.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from pydantic import TypeAdapter

from studio import voice
from studio.ladder import Ladder, Outcome, Rung, climb
from studio.learnings import Learning
from studio.trailer_stage_spec import LineSlate, SlateLine, VoiceLine

STEP_ID = "05"
NAME = "voice"
FIRST_RENDER_GUESS = 15.0
"""Until a render has been measured, what a reroll is assumed to cost."""
LADDER = Ladder([Rung("reroll_seed", cost_seconds=FIRST_RENDER_GUESS, tries=3),
                 Rung("next_line_same_function", cost_seconds=FIRST_RENDER_GUESS)],
                terminal="card")
VOICE_LINES = TypeAdapter(list[VoiceLine])


def fresh_ladder() -> Ladder:
    """A ladder per line: rung costs are updated from measured renders, and one
    line's slow render must not gate the next line's first reroll unfairly."""
    return Ladder([Rung(r.name, r.cost_seconds, r.tries) for r in LADDER.rungs], LADDER.terminal)


def load_pool(raw: dict) -> list[SlateLine]:
    """The slate's unused candidates (`pool` in lines.json), if step 04 kept them."""
    return [SlateLine.model_validate(p) for p in raw.get("pool", [])]


def load_card(book_dir: Path, speaker: str) -> dict | None:
    path = book_dir / "analysis" / "characters" / f"{speaker}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def design_refs(slate: LineSlate, ctx) -> dict[str, Path]:
    """One reference per speaker who has a cast card, cached under voice/refs/."""
    refs: dict[str, Path] = {}
    for line in slate.spoken():
        if line.speaker in refs:
            continue
        who = load_card(ctx.book_dir, line.speaker)
        if who is None:
            continue
        refs[line.speaker] = voice.design_reference(who, ctx.out_dir / "voice" / "refs")
        ctx.tracker.log(f"voice reference for {line.speaker}", step_id=STEP_ID)
    return refs


def card_line(line: SlateLine, index: int) -> VoiceLine:
    return VoiceLine(index=index, text=line.text, speaker=line.speaker, card=True)


def next_candidate(pool: list[SlateLine], function: str, used: set[str],
                   speakers: set[str]) -> SlateLine | None:
    """The next unused spoken line with the same function and a designed speaker."""
    for line in pool:
        if line.function == function and line.speaker in speakers and line.text not in used:
            return line
    return None


def next_castable(pool: list[SlateLine], function: str, used: set[str],
                  refs: dict[str, Path], ctx) -> SlateLine | None:
    """The next unused line of this function whose speaker the book can CARD --
    designed already, or with a cast card to design from.  Wider than
    `next_candidate` on purpose: this runs when the slate's own speaker turned
    out to be uncastable, so there is no designed voice for that function yet."""
    for line in pool:
        if line.function != function or line.text in used or not line.speaker:
            continue
        if line.speaker in refs or load_card(ctx.book_dir, line.speaker) is not None:
            return line
    return None


def reference_for(speaker: str, refs: dict[str, Path], ctx) -> Path:
    """The speaker's designed reference, designed now if this is the first line
    of theirs the step has reached."""
    if speaker not in refs:
        refs[speaker] = voice.design_reference(load_card(ctx.book_dir, speaker),
                                               ctx.out_dir / "voice" / "refs")
        ctx.tracker.log(f"voice reference for {speaker}", step_id=STEP_ID)
    return refs[speaker]


def attempt_line(rung: Rung, i: int, line: SlateLine, index: int, refs: dict[str, Path],
                 out_dir: Path) -> VoiceLine:
    """Render one try, measure its similarity, and charge the rung what it took."""
    seed = voice.seed_for(line.speaker, i)
    out = out_dir / "voice" / "lines" / f"{index:02d}-{i}.wav"
    started = time.monotonic()
    result = voice.clone_line(refs[line.speaker], line.text, seed, out,
                              index=index, speaker=line.speaker)
    rung.cost_seconds = max(time.monotonic() - started, 1.0)
    result.similarity = round(voice.similarity(out, refs[line.speaker]), 4)
    return result


def gate(result: VoiceLine | None) -> tuple[bool, float | None, float]:
    if result is None:
        return False, None, voice.SIMILARITY_FLOOR
    return result.similarity >= voice.SIMILARITY_FLOOR, result.similarity, voice.SIMILARITY_FLOOR


def climb_line(line: SlateLine, index: int, refs: dict[str, Path], pool: list[SlateLine],
               used: set[str], ctx) -> Outcome:
    """Seeds on this line, then the pool's next line of the same function."""
    current = {"line": line}

    def attempt(rung: Rung, i: int):
        if rung.name == "next_line_same_function":
            alt = next_candidate(pool, line.function, used | {line.text}, set(refs))
            if alt is None:
                return None
            current["line"] = alt
        return attempt_line(rung, i, current["line"], index, refs, ctx.out_dir)

    return climb(fresh_ladder(), STEP_ID, attempt, gate, ctx.budget, ctx.learn,
                 gate_name="similarity")


def voice_line(line: SlateLine, index: int, refs: dict[str, Path], pool: list[SlateLine],
               used: set[str], ctx) -> VoiceLine:
    """A card without trying when nobody designed can say it; else climb."""
    if line.card:
        return card_line(line, index)
    if line.speaker not in refs:
        # MEASURED, run 19: the slate's stakes line was spoken by "Police
        # Inspector", who has no cast card, and the trailer SPOKE 4 OF 5 while
        # four castable stakes spares sat in the same pool.  A speaker nobody
        # designed is the same problem as a take nobody can use: draw the next
        # line of that function, the rung the ladder already knows.
        spare = next_castable(pool, line.function, used | {line.text}, refs, ctx)
        ctx.learn(Learning(step=STEP_ID, gate="speaker_card", measured=line.speaker,
                           threshold="cast card", terminal=spare is None,
                           action="spare_drawn" if spare else "card",
                           note=spare.speaker if spare else ""))
        if spare is None:
            return card_line(line, index)
        reference_for(spare.speaker, refs, ctx)
        line = spare
    outcome = climb_line(line, index, refs, pool, used, ctx)
    if outcome.terminal:
        return card_line(line, index)
    used.add(outcome.result.text)
    return outcome.result


def run(codex_id: str, ctx) -> None:
    raw = json.loads((ctx.out_dir / "lines.json").read_text(encoding="utf-8"))
    slate = LineSlate.model_validate(raw)
    out = ctx.out_dir / "voice.json"
    if slate.music_only or not slate.spoken():
        out.write_text("[]", encoding="utf-8")
        print(f"[{STEP_ID}] nothing spoken; voice.json is empty")
        return
    refs = design_refs(slate, ctx)
    used = {line.text for line in slate.lines}
    lines = [voice_line(line, i, refs, load_pool(raw), used, ctx)
             for i, line in enumerate(slate.lines)]
    out.write_bytes(VOICE_LINES.dump_json(lines, indent=2, by_alias=True))
    spoken = [l for l in lines if not l.card]
    print(f"[{STEP_ID}] {len(refs)} voice(s), {len(spoken)} of {len(lines)} lines spoken, "
          f"{len(lines) - len(spoken)} card(s)")
