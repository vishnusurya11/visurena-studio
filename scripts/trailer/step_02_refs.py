"""Step 02 -- refs: the sheets that bind identity, judged by a vision model.

`build_refs.py` rendered sheets and hoped; a cast that measured as the same
man shipped once (Watson/Holmes at 0.420).  A face recogniser then gated the
sheets, but a cosine says only THAT two sheets read alike, so its rungs were
another seed and another pose -- and Lestrade collided five times in a row on
the same words.  Here every sheet is READ BACK by the local Qwen3-VL into a
trait card (`studio.describe`) and compared with the cast already bound:
fewer than DISTINCT_AT traits apart is a collision.  The ladder is one
reroll, then three `distinguish` rungs that rewrite exactly the traits the
two sheets share; a character that still collides is UNBOUND: listed in
refs.json, absent from `refs`, so no setup downstream can carry it.  The
palette is derived from story.json.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.trailer.build_refs import describe_location, generate, refs_needed
from studio.cast_card import POOLS, cards_for, infer_gender, render_card
from studio.describe import DISTINCT_AT, TraitCard, closest, describe, same_look, shared, verifiable
from studio.distinguish import distinguish
from studio.ladder import Ladder, Rung, climb
from studio.learnings import Learning
from studio.trailer_refs import (character_prompt, load_json, location_prompt, palette_for,
                                 physical_of, ref_id_for)
from studio.trailer_stage_spec import StorySpec

STEP_ID = "02"
NAME = "refs"
SEED_BASE = 40000
RENDER_SECONDS = 30
DESCRIBE_SECONDS = 60
LADDER = Ladder([Rung("reroll_seed", RENDER_SECONDS + DESCRIBE_SECONDS, tries=1),
                 Rung("distinguish", RENDER_SECONDS + DESCRIBE_SECONDS, tries=3)],
                terminal="unbound")


def seed_for(index: int, rung: Rung, i: int) -> int:
    """First try keeps build_refs' seed (an existing sheet is reused); every
    later try on every rung is a seed no earlier try used."""
    rung_offset = 5000 * LADDER.rungs.index(rung) if rung in LADDER.rungs else 0
    return SEED_BASE + index + rung_offset + 1000 * i


def cast_cards(book: Path, characters: list[str]) -> dict[str, dict]:
    """One distinct card per character, from the analysis the book has."""
    docs = {c: load_json(book / "analysis/characters" / f"{c}.json") for c in characters}
    physical = {c: physical_of(d) for c, d in docs.items()}
    genders = {c: infer_gender(d.get("name", c), d.get("aliases", []), physical[c])
               for c, d in docs.items()}
    roles = {c: (d.get("role") or "").lower() for c, d in docs.items()}
    return cards_for(characters, physical, genders, roles)


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


def bind_one(ctx, book: Path, index: int, char_id: str, card: dict, palette: str,
             bound: dict[str, TraitCard], taken: dict[str, set[str]]) -> dict | None:
    """Climb the ladder for one character; None means unbound."""
    state = {"card": card, "other": None, "shared": []}

    def attempt(rung: Rung, i: int):
        fresh = not (rung is LADDER.rungs[0] and i == 0)
        if rung.name == "distinguish":
            state["card"] = distinguish(state["card"], state["shared"], state["other"], taken)
        seed = seed_for(index, rung, i)
        path, physical = render_sheet(book, char_id, state["card"], palette, seed, fresh)
        return {"path": path, "physical": physical, "card": describe(path, seed=seed)}

    def gate(result):
        result["identity"] = identity_of(result["card"], bound)
        if not verifiable(result["card"]):
            ctx.learn(Learning(step=STEP_ID, gate="identity", measured=str(result["card"]),
                               threshold="verifiable", action="accepted_unverifiable"))
            return True, None, DISTINCT_AT
        who = result["identity"]["closest"]
        if who is None or not same_look(result["card"], bound[who]):
            return True, len(result["identity"]["differs"]), DISTINCT_AT
        state.update(other=bound[who], shared=shared(result["card"], bound[who]))
        return False, f"{who}: shares {', '.join(state['shared'])}", DISTINCT_AT

    outcome = climb(LADDER, STEP_ID, attempt, gate, ctx.budget, ctx.learn, gate_name="identity")
    if outcome.terminal:
        return None
    bound[char_id] = outcome.result["card"]
    return outcome.result


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
