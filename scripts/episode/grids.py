#!/usr/bin/env python
"""Draw one setup's storyboard grid, from the plan's own prose. Local, $0.

    uv run python scripts/episode/grids.py <book_id> <episode> <setup> <cols> <rows> [tag]
                                           [--shots=1,2,3] [--seed-bump=N] [--prompt=v1|v2]

Qwen-Image-2.1 edit-multi, up to three references: cast sheets first (the
identity slots), the setup's own place picture last (the scene and style
slot). Each grid is filed under episodes/epNN/storyboard/grids/ -- the picture,
the prompt it was drawn from, and a manifest naming its shots -- and
`panels.py` cuts the panels out of it from that manifest.

Promoted from a session driver (audit 2026-09-22, items 9, 12, 16, 22). On the
way in:
- the book and the episode come from the command line; the driver once had
  `load_plan(book, 8)` in its body while it was being run for episode 9;
- the place picture is the SETUP's own view (`location_view(view=...)`): the
  driver asked for the book anchor, so after the book rows were restored it
  would have drawn ep09's pit on the old Horsell Common picture;
- grid names carry the episode: `grid_{setup}_{cols}x{rows}` in ComfyUI's one
  shared output folder would let ep10's "pit" overwrite ep09's, and the
  exporter cut the newest file of that name;
- the manifest is written AFTER the render succeeds, beside the grid, with a
  hash of the plan it was drawn from.

The prompt text is exactly the session driver's; its known faults are fixed in
their own commits, measured before and after.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_refs, episode_home, pack_refs
from studio.comfy import load_workflow, stage_image, submit, wait
from studio.episode_home import episode_arg
from studio.ref_slots import stage_only
from studio.storyboard_grid import (cut_clause, grid_prompt, grid_prompt_v2, no_duplicates,
                                    varied_group, whole_subject)

CLIP = "qwen3vl_8b_fp8_scaled.safetensors"
MAX_SLOTS = 3
"""The vendor's ceiling: 1-3 references, and a fourth makes it no more faithful
(researched 2026-09-20). Slot 1 is the identity anchor, the last is the scene."""

STYLE = ("DRAWN IN EXACTLY THE ART STYLE OF <image{scene}>, copied from it and not invented: a flat "
         "angular stylised 3d CGI look with visible brush-stroke colour texture, broad simplified "
         "shapes, strong flat colour, high chroma, clean poster-like edges and NO photographic "
         "depth of field, NO camera blur, NO photoreal skin or cloth. Match the palette, the "
         "brush texture and the level of stylisation of <image{scene}> exactly")

NEGATIVE = ("text, caption, subtitles, watermark, signature, blurry, photographic, modern "
            "clothing, two men dressed alike, two men in the same hat, duplicated people, "
            "extra limbs, deformed hands, mountains, cliffs, lettering, letters, words, "
            "panel labels, numbers, beard on the narrator")

SAID = {"wide": "WIDE", "medium": "MEDIUM", "medium_close": "MEDIUM CLOSE",
        "close": "BIG CLOSE-UP", "insert": "INSERT"}

CREATURE = re.compile(r"\b(?:cab horse|horse|pony|mare|dog|cat|cow|ox|donkey|bird)\b", re.I)
PART = re.compile(r"\b(?:head|face|hand|hands|eye|eyes|hoof|hooves|foot|feet|paw|muzzle|nose|ear|ears)\b", re.I)


def grid_name(number: int, setup: str, cols: int, rows: int, tag: str = "") -> str:
    """A grid's name, scoped to its episode so two episodes' grids never collide."""
    return f"ep{number:02d}_grid_{setup}_{cols}x{rows}{('_' + tag) if tag else ''}"


def grids_dir(book: Path, number: int) -> Path:
    return episode_home.home(book, number) / "storyboard" / "grids"


def plan_sha(book: Path, number: int) -> str:
    """Which plan a grid was drawn from, so a panel can be refused once it isn't."""
    return hashlib.sha256(episode_home.plan_path(book, number).read_bytes()).hexdigest()[:16]


SHOT_FIELDS = ("index", "setup", "size", "frame", "at_rest", "faces", "extras")
SETUP_FIELDS = ("location", "view", "described")
"""Exactly what `prompt_for` reads. A shot's `motion` is the take's, not the
grid's: ep09's retakes changed three camera moves, and hashing the whole shot
would have redrawn three good grids for words they never saw."""


def shots_sha(ep, indices: list[int]) -> str:
    """What a grid is drawn from: the fields of its own shots and their setups
    that its prompt reads, and nothing else of the plan. One hash of the whole
    plan made a word changed in shot 11 stale every grid in ep09."""
    shots = [s for s in ep.shots if s.index in indices]
    setups = sorted({s.setup for s in shots})
    body = {"shots": [s.model_dump(mode="json", include=set(SHOT_FIELDS)) for s in shots],
            "setups": {k: ep.setups[k].model_dump(mode="json", include=set(SETUP_FIELDS))
                       for k in setups}}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def drawn_inputs(book: Path, ep, setup: str, indices: list[int], cols: int, rows: int,
                 version: str) -> str:
    """Everything a grid is drawn from: the prompt it would be given now and the
    bytes of every picture it would stage. Plan fields alone missed a rebound
    row, a redrawn sheet or place, and a prompt-builder fix -- so the chapter-6
    wardrobe on every ep09 grid could never have read as stale (2026-09-23)."""
    shots = [s for s in ep.shots if s.index in indices]
    return inputs_sha(*prompt_for(book, ep, setup, shots, cols, rows, version))


def inputs_sha(text: str, slots: dict) -> str:
    pictures = sorted(hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in slots.values())
    return hashlib.sha256(json.dumps([text, pictures]).encode()).hexdigest()[:16]


def wide_for(book: Path, setup) -> Path:
    """This setup's own place picture: the SETUP's view, through the same door
    the take uses, so the panel and the take can never open on different
    pictures of one place."""
    return pack_refs.location_view(book, getattr(setup, "location", "") or "",
                                   view=getattr(setup, "view", "") or "")


def sheet_of(book: Path, who: str) -> Path | None:
    p = Path(book) / "refs" / "characters" / who / "sheet.png"
    return p if p.exists() else None


def cast_of(book: Path, shots: list) -> tuple[list[dict], dict]:
    """Every person the panels name, from the bound rows, and the slots their
    sheets go in -- what is staged and what is said are the same list."""
    who = [f for s in shots for f in (s.faces or [])]
    who = list(dict.fromkeys(who))                      # first-appearance order
    people, slots, n = [], {}, 0
    for name in who:
        # THE ROW THE TAKE READS: refs.json, stamped with this episode's chapter
        # (chapter_refusal checks it). This used to read the dossier with the
        # chapter hard-coded as six, and dressed every ep09 grid from chapter 6
        # (2026-09-23).
        row = cast_refs.row(book, name)
        sheet, ref = sheet_of(book, name), None
        if sheet is not None and n < MAX_SLOTS - 1:     # one slot is always the place
            n += 1
            ref = n
            slots[str(100 + n)] = sheet
        said = re.sub(r"^(my|the|a|an)\s+", "", row["name"].strip(), flags=re.I).upper()
        people.append({
            "ref": ref, "name": said, "entity": name,
            "wear": " ".join(row["physical"].split()),
            "against": (f"{said} is no other person in this storyboard: nobody else wears "
                        f"these clothes and {said} never wears anyone else's")})
    return people, slots


def creature_insert(shot) -> tuple[str, str] | None:
    """(creature, part) when an INSERT isolates part of a living thing: a horse's
    head cannot exist on its own (owner, 2026-09-20)."""
    if shot.size != "insert":
        return None
    beast, part = CREATURE.search(shot.frame or ""), PART.search(shot.frame or "")
    return (beast.group(0), part.group(0)) if beast and part else None


def body_of(shot) -> str:
    """The plan's own words: what is in frame, then where everything sits."""
    parts = [shot.frame.strip()]
    if rest := (getattr(shot, "at_rest", "") or "").strip():
        parts.append(rest)
    if found := creature_insert(shot):
        parts.append(whole_subject(f"the {found[0]}", f"its {found[1]}"))
    if said := varied_group(" ".join(parts)):          # a count of walk-ons is not one man repeated
        parts.append(said)
    return " ".join(parts)


def grid_shots(ep, setup: str, cols: int, rows: int, only: list[int] | None) -> list:
    shots = [s for s in ep.shots if s.index in only] if only else [s for s in ep.shots if s.setup == setup]
    if len(shots) != cols * rows:
        raise SystemExit(f"setup {setup!r} has {len(shots)} shots ({[s.index for s in shots]}), "
                         f"grid {cols}x{rows} wants {cols * rows}")
    return shots


def _v1(blocks: list, cols: int, rows: int, place: tuple, cast: list, style_slot: int) -> str:
    cast = [{**p, "wear": p["wear"][:600]} for p in cast]      # v1's own cut, kept byte for byte
    text = grid_prompt(blocks, cols, rows, place=place, cast=cast, style=STYLE.format(scene=style_slot))
    return text + "\n\n" + no_duplicates([p["name"] for p in cast])


PROMPTS = {"v1": _v1, "v2": grid_prompt_v2}
"""v2 (subject first, garments not a cut-off identity block, no "panel" in a
single picture) is the default since the same-seed A/B on ep09 (2026-09-22,
docs/calibration/grid_prompt_ab.md): v1 cloned both leads at tea and drew the
lawn's insert as a copy of its wide. v1 stays callable to reproduce old grids."""


def compose(version: str, blocks: list, cols: int, rows: int, place: tuple, cast: list,
            style_slot: int) -> str:
    if version not in PROMPTS:
        raise SystemExit(f"--prompt={version}: known versions are {sorted(PROMPTS)}")
    return PROMPTS[version](blocks, cols, rows, place, cast, style_slot)


def prompt_version(argv: list[str]) -> str:
    return next((a.split("=", 1)[1] for a in argv if a.startswith("--prompt=")), "v2")


def prompt_for(book: Path, ep, setup: str, shots: list, cols: int, rows: int,
               version: str = "v2") -> tuple[str, dict]:
    """(the grid prompt, {LoadImage node: picture}). Only the shots this grid
    OWNS put people in the slots; a borrowed shot's cast drew line-ups."""
    owned = [s for s in shots if s.setup == setup] or shots
    cast, char_slots = cast_of(book, owned)
    place_slot = len(char_slots) + 1
    slots = {**char_slots, str(100 + place_slot): wide_for(book, ep.setups[shots[0].setup])}
    said_as = {p["entity"]: p["name"] for p in cast}
    blocks = [{"size": SAID[s.size], "body": body_of(s),
               "cut": cut_clause(s.size, peopled=bool(s.faces)),
               "who": [said_as[f] for f in (s.faces or []) if f in said_as],
               "extras": getattr(s, "extras", 0)} for s in shots]
    place = ([place_slot], ep.setups[shots[0].setup].described)
    return compose(version, blocks, cols, rows, place, cast, place_slot), slots


def graph_for(text: str, slots: dict, cols: int, rows: int, seed: int, name: str) -> dict:
    template, _ = load_workflow("image_qwen_image_2_1_edit_multi")
    graph = {k: v for k, v in template.items()}
    graph["3"]["inputs"]["clip_name"] = CLIP
    # NOTHING STAGED THAT THE PROMPT DOES NOT NAME: an unused LoadImage holds
    # ComfyUI's example.png -- a doll -- and the encoder reads it.
    stage_only(graph, {node: stage_image(path) for node, path in slots.items()})
    graph["5"]["inputs"].update(prompt=text, negative_prompt=NEGATIVE, resolution=1024)
    graph["6"]["inputs"].update(width=1024 * cols, height=1024 * rows)
    graph["7"]["inputs"].update(seed=seed, steps=25, cfg=1.0)
    graph["9"]["inputs"]["filename_prefix"] = name
    return graph


def file_grid(book: Path, number: int, name: str, made: list, text: str, manifest: dict) -> Path:
    """Copy the render into the episode, with its prompt and its manifest --
    AFTER it succeeded, so no manifest ever names a grid that was not drawn."""
    folder = grids_dir(book, number)
    folder.mkdir(parents=True, exist_ok=True)
    grid = folder / f"{name}.png"
    shutil.copyfile(made[0], grid)
    (folder / f"{name}.txt").write_text(text, encoding="utf-8")
    (folder / f"{name}.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return grid


def main(book_id: str, number: int, setup: str, cols: int, rows: int, tag: str = "",
         only: list[int] | None = None, seed_bump: int = 0, version: str = "v2") -> None:
    book = episode_home.book_dir(book_id)
    ep = episode_home.load_plan(book, number)
    from studio import cast_refs
    if why := cast_refs.chapter_refusal(book, number):   # this chapter's clothes (audit item 9)
        raise SystemExit(why)
    shots = grid_shots(ep, setup, cols, rows, only)
    text, slots = prompt_for(book, ep, setup, shots, cols, rows, version)
    name = grid_name(number, setup, cols, rows, tag)
    seed = 40500 + sum(s.index for s in shots) + seed_bump
    print(f"{name}: shots {[s.index for s in shots]} | slots {sorted(slots)} | prompt {len(text)} chars",
          flush=True)
    began = time.time()
    made = wait(submit(graph_for(text, slots, cols, rows, seed, name)), timeout=3600)
    grid = file_grid(book, number, name, made, text, {
        "name": name, "episode": number, "setup": setup, "cols": cols, "rows": rows,
        "shots": [s.index for s in shots], "seed": seed, "plan": plan_sha(book, number),
        "drawn_from": shots_sha(ep, [s.index for s in shots]),
        "inputs": inputs_sha(text, slots), "prompt": version})
    print(f"{name} in {time.time() - began:.0f}s -> {episode_home.relative(book, grid)}", flush=True)


if __name__ == "__main__":
    plain = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = [int(v) for a in sys.argv if a.startswith("--shots=") for v in a.split("=", 1)[1].split(",") if v]
    bump = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--seed-bump=")), "0"))
    main(plain[0], episode_arg(sys.argv), plain[2], int(plain[3]), int(plain[4]),
         plain[5] if len(plain) > 5 else "", only or None, bump, prompt_version(sys.argv))
