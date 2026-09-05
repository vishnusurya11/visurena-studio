"""Step 02 -- refs: the sheets that bind identity, judged by a vision model.

`build_refs.py` rendered sheets and hoped; a cast that measured as the same
man shipped once (Watson/Holmes at 0.420).  A face recogniser then gated the
sheets, but a cosine says only THAT two sheets read alike, so its rungs were
another seed and another pose -- and Lestrade collided five times in a row on
the same words.  Here every sheet is READ BACK by the local Qwen3-VL into a
trait card (`studio.describe`) and compared with the cast already bound:
fewer than DISTINCT_AT traits apart is a collision -- and a render that
DISOBEYED its card on a trait the channel expresses (`studio.distinguish`)
fails first, since it would condition every clip against its own words.
The ladder is the first render, then three `distinguish` rungs: a collision
rewrites exactly the traits the two sheets share, a disobedient render goes
again as written on a new seed; a character that still fails is UNBOUND:
listed in refs.json, absent from `refs`, so no setup downstream can carry
it.  The palette is derived from story.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from scripts.trailer.build_refs import describe_location, generate, refs_needed
from studio.canon import canons_for, known_look
from studio.cast_card import POOLS, cards_for, infer_gender, render_card
from studio.describe import (DISTINCT_AT, TIMEOUT, TraitCard, closest, describe, distance,
                             patiently, same_look, shared, verifiable)
from studio.distinguish import adopt, disobeyed, distinguish, movable
from studio.ladder import Ladder, Rung, climb
from studio.learnings import Learning
from studio.portrait import physical_text, portraits_for, stated
from studio.trailer_refs import (character_prompt, load_json, location_prompt, palette_for,
                                 physical_of, ref_id_for)
from studio.trailer_stage_spec import StorySpec

STEP_ID = "02"
NAME = "refs"
SEED_BASE = 40000
RENDER_SECONDS = 180
DESCRIBE_SECONDS = 110
"""Run 7 timed a sheet attempt at 286, 237, 212 and 371 s (691 s with the
model load); the rung had been priced at 90, and the budget let the ladder
start climbs it could not finish."""
LADDER = Ladder([Rung("reroll_seed", RENDER_SECONDS + DESCRIBE_SECONDS, tries=1),
                 Rung("distinguish", RENDER_SECONDS + DESCRIBE_SECONDS, tries=3)],
                terminal="unbound")


def seed_for(index: int, rung: Rung, i: int) -> int:
    """First try keeps build_refs' seed (an existing sheet is reused); every
    later try on every rung is a seed no earlier try used."""
    rung_offset = 5000 * LADDER.rungs.index(rung) if rung in LADDER.rungs else 0
    return SEED_BASE + index + rung_offset + 1000 * i


def cast_cards(book: Path, characters: list[str]) -> dict[str, dict]:
    """One distinct card per character, from the analysis the book has.

    Authority order: the book's own words, then the look the world already
    knows the character by, then the card's own invention.  Scarlet run 7:
    the book silent on Holmes's face, the rotation gave him a walrus
    moustache, a bowler and forty years, and every clip followed."""
    docs = {c: load_json(book / "analysis/characters" / f"{c}.json") for c in characters}
    portraits = portraits_for(book, docs)
    looks = canons_for(book, docs)
    physical = {c: physical_text(portraits[c], physical_of(d)) for c, d in docs.items()}
    genders = {c: infer_gender(d.get("name", c), d.get("aliases", []), physical[c])
               for c, d in docs.items()}
    roles = {c: (d.get("role") or "").lower() for c, d in docs.items()}
    return cards_for(characters, physical, genders, roles,
                     {c: {**known_look(looks[c]), **stated(portraits[c])} for c in docs},
                     known={c for c in docs if looks[c].known})


def render_sheet(book: Path, char_id: str, card: dict, palette: str, seed: int,
                 fresh: bool) -> tuple[Path, str]:
    physical = render_card(card)
    prompt = character_prompt(physical, palette)
    dest = book / "refs/characters" / f"{ref_id_for('character', char_id)}.png"
    if fresh and dest.exists():
        dest.unlink()
    return generate(prompt, f"REF-{ref_id_for('character', char_id)}", seed, dest), physical


def character_record(char_id: str, name: str, physical: str, prompt: str, path: Path,
                     book: Path, identity: dict) -> dict:
    return {"ref_id": ref_id_for("character", char_id), "kind": "character",
            "entity_id": char_id, "name": name, "physical": physical, "prompt": prompt,
            "rel_path": path.relative_to(book).as_posix(), "identity": identity}


def identity_of(card: TraitCard, bound: dict[str, TraitCard]) -> dict:
    who, differing = closest(card, bound)
    return {"closest": who, "differs": differing, "traits": card.model_dump()}


def timed_out(learn) -> Callable[[str], None]:
    """The learning a sheet read that outlived TIMEOUT leaves behind (Scarlet
    run 5: one read took 10:14 and its TimeoutError ended the run here)."""
    return lambda what: learn(Learning(step=STEP_ID, gate="identity", measured=what,
                                       threshold=f"{TIMEOUT}s", action="accepted_on_timeout"))


def bind_one(ctx, book: Path, index: int, char_id: str, card: dict, palette: str,
             bound: dict[str, TraitCard], taken: dict[str, set[str]]) -> dict | None:
    """Climb the ladder for one character; None means unbound.

    A render is judged twice.  Did it OBEY its card on the traits the channel
    can express?  Scarlet run 6: Lestrade's card said walrus moustache, the
    render came back clean-shaven and grey, and the ladder rewrote the card
    as if Hope had been matched.  A disobedient render is not a collision:
    the same card goes again on the next seed.  Only a FAITHFUL render that
    still reads as someone bound has its shared traits moved."""
    state = {"card": card, "other": None, "shared": []}

    def attempt(rung: Rung, i: int):
        fresh = not (rung is LADDER.rungs[0] and i == 0)
        if rung.name == "distinguish" and state["shared"]:
            state["card"] = distinguish(state["card"], state["shared"], state["other"], taken)
        seed = seed_for(index, rung, i)
        path, physical = render_sheet(book, char_id, state["card"], palette, seed, fresh)
        card = patiently(lambda: describe(path, seed=seed), timed_out(ctx.learn))
        return {"path": path, "physical": physical, "card": card}

    def gate(result):
        result["identity"] = identity_of(result["card"], bound)
        if not verifiable(result["card"]):
            ctx.learn(Learning(step=STEP_ID, gate="identity", measured=str(result["card"]),
                               threshold="verifiable", action="accepted_unverifiable"))
            return True, None, DISTINCT_AT
        off = disobeyed(state["card"], result["card"])
        if off:
            state.update(other=None, shared=[])
            return False, f"disobeyed {', '.join(off)}", "faithful"
        who = result["identity"]["closest"]
        if who is None or not same_look(result["card"], bound[who]):
            return True, distance(result["card"], bound[who]) if who else None, DISTINCT_AT
        state.update(other=bound[who], shared=shared(result["card"], bound[who]))
        if not movable(state["shared"], state["card"]):
            # Every shared trait is the book's own: nothing a rung may move.
            ctx.learn(Learning(step=STEP_ID, gate="identity", threshold=DISTINCT_AT,
                               measured=f"{char_id} ~ {who}: shares {', '.join(state['shared'])}",
                               action="accepted_as_written"))
            return True, distance(result["card"], bound[who]), DISTINCT_AT
        return False, f"{who}: shares {', '.join(state['shared'])}", DISTINCT_AT

    outcome = climb(LADDER, STEP_ID, attempt, gate, ctx.budget, ctx.learn, gate_name="identity",
                    substep=char_id)
    if outcome.terminal:
        return None
    bound[char_id] = outcome.result["card"]
    return followed(outcome.result, state["card"])


def followed(result: dict, card: dict) -> dict:
    """The bound result with its text rewritten to what the render drew on
    the slots the book left to invention (`distinguish.adopt`), so every
    later prompt agrees with the sheet it conditions on."""
    return {**result, "physical": render_card(adopt(card, result["card"]))}


def bind_cast(ctx, book: Path, characters: list[str], palette: str
              ) -> tuple[list[dict], list[str]]:
    cards = cast_cards(book, characters)
    taken = {slot: {c[slot] for c in cards.values()} for slot in POOLS}
    bound: dict[str, TraitCard] = {}
    records, unbound = [], []
    for index, char_id in enumerate(characters):
        result = bind_one(ctx, book, index, char_id, cards[char_id], palette, bound, taken)
        if result is None:
            unbound.append(char_id)
            continue
        name = load_json(book / "analysis/characters" / f"{char_id}.json").get("name", char_id)
        records.append(character_record(
            char_id, name, result["physical"], character_prompt(result["physical"], palette),
            result["path"], book, result["identity"]))
    return records, unbound


def location_records(book: Path, locations: list[str], scenes: list[dict], palette: str
                     ) -> list[dict]:
    records = []
    for index, loc_id in enumerate(locations):
        described = describe_location(book, loc_id, scenes)
        prompt = location_prompt(described, palette)
        ref_id = ref_id_for("location", loc_id)
        path = generate(prompt, f"REF-{ref_id}", SEED_BASE + 500 + index,
                        book / "refs/locations" / f"{ref_id}.png")
        records.append({"ref_id": ref_id, "kind": "location", "entity_id": loc_id,
                        "name": described[:90], "physical": described, "prompt": prompt,
                        "rel_path": path.relative_to(book).as_posix()})
    return records


def run(codex_id: str, ctx) -> None:
    book = ctx.book_dir
    story = StorySpec.model_validate_json((ctx.out_dir / "story.json").read_text(encoding="utf-8"))
    palette = palette_for(story.register, story.setting)
    scenes = load_json(book / "screenplay/feature/screenplay.json")["scenes"]
    characters, locations = refs_needed(book, 12)
    records, unbound = bind_cast(ctx, book, characters, palette)
    records += location_records(book, locations, scenes, palette)
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs/refs.json").write_text(json.dumps(
        {"book_id": book.name, "palette": palette, "refs": records, "unbound": unbound},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[{STEP_ID}] {len(records)} refs bound, {len(unbound)} unbound {unbound}, "
          f"palette: {palette[:60]}...")
