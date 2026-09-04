"""Step 02 -- refs: the sheets that bind identity, judged by a recogniser.

`build_refs.py` rendered sheets and hoped; a cast that measured as the same
man shipped once (Watson/Holmes at 0.420).  Here every character sheet is
embedded and compared with the cast already bound.  A collision climbs the
ladder -- another seed, then another pose, the FUNCTION (this character,
distinct) unchanged -- and a character the recogniser cannot separate after
five more renders is UNBOUND: listed in refs.json, absent from `refs`, so no
setup downstream can carry it.  The palette is derived from story.json.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.trailer.build_refs import describe_location, generate, refs_needed
from studio.cast_card import cards_for, infer_gender, render_card
from studio.identity import SFACE, UNVERIFIABLE_BELOW, verdict
from studio.identity_gate import embed_file, ensure_models, open_sessions, worst_against
from studio.ladder import Ladder, Rung, climb
from studio.learnings import Learning
from studio.trailer_refs import (character_prompt, load_json, location_prompt, palette_for,
                                 physical_of, ref_id_for)
from studio.trailer_stage_spec import StorySpec

STEP_ID = "02"
NAME = "refs"
SEED_BASE = 40000
RENDER_SECONDS = 30
POSES = ("Three-quarter view, eyes to camera.",
         "Head turned toward profile, chin lifted, eyes off camera.")
LADDER = Ladder([Rung("reroll_seed", RENDER_SECONDS, tries=3),
                 Rung("alternate_pose", RENDER_SECONDS, tries=2)], terminal="unbound")


def seed_for(index: int, rung: Rung, i: int) -> int:
    """First try keeps build_refs' seed (an existing sheet is reused); every
    later try on every rung is a seed no earlier try used."""
    rung_offset = 5000 * LADDER.rungs.index(rung) if rung in LADDER.rungs else 0
    return SEED_BASE + index + rung_offset + 1000 * i


def pose_for(rung: Rung, i: int) -> str:
    return POSES[i % len(POSES)] if rung.name == "alternate_pose" else ""


def cast_cards(book: Path, characters: list[str]) -> dict[str, dict]:
    """One distinct card per character, from the analysis the book has."""
    docs = {c: load_json(book / "analysis/characters" / f"{c}.json") for c in characters}
    physical = {c: physical_of(d) for c, d in docs.items()}
    genders = {c: infer_gender(d.get("name", c), d.get("aliases", []), physical[c])
               for c, d in docs.items()}
    roles = {c: (d.get("role") or "").lower() for c, d in docs.items()}
    return cards_for(characters, physical, genders, roles)


def render_sheet(book: Path, char_id: str, card: dict, palette: str, seed: int,
                 pose: str, fresh: bool) -> tuple[Path, str]:
    physical = f"{render_card(card)} {pose}".strip()
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


def bind_one(ctx, book: Path, index: int, char_id: str, card: dict, palette: str,
             sessions, bound: dict) -> dict | None:
    """Climb the ladder for one character; None means unbound."""
    def attempt(rung: Rung, i: int):
        fresh = not (rung is LADDER.rungs[0] and i == 0)
        path, physical = render_sheet(book, char_id, card, palette, seed_for(index, rung, i),
                                      pose_for(rung, i), fresh)
        vector, px = embed_file(sessions, path)
        return {"path": path, "physical": physical, "vector": vector, "px": px}

    def gate(result):
        if result["vector"] is None or result["px"] < UNVERIFIABLE_BELOW:
            ctx.learn(Learning(step=STEP_ID, gate="identity", measured=result["px"],
                               threshold=UNVERIFIABLE_BELOW, action="accepted_unverifiable"))
            return True, None, SFACE.same_person_at
        who, score = worst_against(result["vector"], bound)
        result["identity"] = {"closest": who, "similarity": round(score, 3)}
        return verdict(score, result["px"], SFACE) != "fail", round(score, 3), SFACE.same_person_at

    outcome = climb(LADDER, STEP_ID, attempt, gate, ctx.budget, ctx.learn, gate_name="identity")
    if outcome.terminal:
        return None
    result = outcome.result
    if result["vector"] is not None:
        bound[char_id] = result["vector"]
    return result


def bind_cast(ctx, book: Path, characters: list[str], palette: str, sessions
              ) -> tuple[list[dict], list[str]]:
    cards = cast_cards(book, characters)
    bound: dict = {}
    records, unbound = [], []
    for index, char_id in enumerate(characters):
        result = bind_one(ctx, book, index, char_id, cards[char_id], palette, sessions, bound)
        if result is None:
            unbound.append(char_id)
            continue
        name = load_json(book / "analysis/characters" / f"{char_id}.json").get("name", char_id)
        records.append(character_record(
            char_id, name, result["physical"], character_prompt(result["physical"], palette),
            result["path"], book, result.get("identity", {})))
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
    sessions = open_sessions(ensure_models())
    records, unbound = bind_cast(ctx, book, characters, palette, sessions)
    records += location_records(book, locations, scenes, palette)
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs/refs.json").write_text(json.dumps(
        {"book_id": book.name, "palette": palette, "refs": records, "unbound": unbound},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[{STEP_ID}] {len(records)} refs bound, {len(unbound)} unbound {unbound}, "
          f"palette: {palette[:60]}...")
