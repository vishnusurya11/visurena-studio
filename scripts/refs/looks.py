#!/usr/bin/env python
"""Step 03_04 -- this unit's new LOOKS, each one hop from the base sheet. Local, $0.

    uv run python scripts/refs/looks.py <book_id> <episode>           # report
    uv run python scripts/refs/looks.py <book_id> <episode> --draw    # draw what is missing

Decision 2026-10-10 (owner): a character has one picture per story-time look
on refs/looks.json; a look is ONE step from the base sheet -- never an edit of
an edit, never a composite (no head pasted back).  Only the looks this
episode's setups stage are drawn (build only what the episode needs); a drawn
look is reused by every later episode and never redrawn.

Route per delta kind (ROUTES), until bench B-3 picks per kind:
  garment, hat, dirt  -> edit:  Krea2 identity edit of sheet_front.png (same face)
  hair, beard, face   -> fresh: Krea2 T2I from the look's words, defining layer
                         first, the base sheet's own seed; then the one-figure crop
LOOK-STATE judges every draw (headwear, hair colour, facial hair HARD); a HARD
fault redraws on seed+1 with the faulted layer first, at most MAX_REDRAWS times;
the terminal keeps the best picture, signed flagged.  A book without a look
table has nothing to draw here (the legacy one-sheet path).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_refs, continuity, episode_home, look_timeline  # noqa: E402
from studio.episode_home import episode_arg  # noqa: E402

ROUTES = {"garment": "edit", "face": "fresh"}
"""Which one-hop route draws a look, by what it changes.  Bench B-3 (verdict S
§4) measures edit vs fresh per kind; flipping a kind is this one row."""
MAX_REDRAWS = 2
LAYER_OF = {"headwear": "headwear", "hair_colour": "hair", "facial_hair": "face", "top": "top", "dirt": "dirt"}
ORDER = ("hair", "face", "headwear", "top", "dirt")
FORM = ("Character reference sheet on a plain mid-grey backdrop with even soft light: full-body front view, "
        "three-quarter view, profile view, back view, and a head-and-shoulders face close-up.")


def look_path(book: Path, who: str, look: str) -> Path:
    return Path(book) / "refs" / "characters" / who / "looks" / f"{look}.png"


def missing_looks(book: Path, episode) -> list[tuple[str, str]]:
    """(who, look) this episode stages that is not the base and not drawn."""
    table, out = look_timeline.load(book), []
    for name, faces in continuity.faces_by_setup(episode).items() if table else []:
        for who in faces:
            card, row = table.characters.get(who), cast_refs.row(book, who)
            look = continuity.look_for(episode.setups[name], who, row)
            if card and look in card.looks and look != card.base and not look_path(book, who, look).exists() \
                    and (who, look) not in out:
                out.append((who, look))
    return out


def route_of(look) -> str:
    return ROUTES["face" if look.face_change else "garment"]


BEARD = "a full short {colour}beard covering the jaw, chin and upper lip, {grown} grown"
"""The only beard wording Krea2 + Cinematic draws (C1_L §1a): a plain full-beard
noun, 2/2 drawn; duration, stubble and qualified wordings 0/7 (ragged_greyed's
"sixteen days of grey-brown beard" 0/3).  Written from the CLOSED marker."""
GROWN = re.compile(r"\b((?:\w+|\d+) (?:days?|weeks?|months?))(?:'|\u2019)? (?:growth )?of ((?:[\w-]+ )?)beard\b", re.I)
"""A duration beard ("sixteen days of grey-brown beard"): the wording the model drops.
Only this form is rewritten -- a styled or qualified beard (Lord Garrick's chin
beard with a shaven upper lip, Lavelle's imperial) keeps the book's words."""


def drawn_face(look) -> str:
    """The face layer as drawn: under a `beard` marker a duration beard becomes the
    drawable full-beard noun, the duration kept as an adjective; any other marker
    (stubble too -- not ruled, 2026-10-11) leaves the words as they are."""
    face = look.layers.face
    if look.markers.facial_hair != "beard":
        return face
    return GROWN.sub(lambda m: BEARD.format(colour=m.group(2), grown=m.group(1).lower()), face)


def layer_said(look, key: str) -> str:
    return drawn_face(look) if key == "face" else getattr(look.layers, key)


def layers_first(look, lead: str = "") -> str:
    """The look's layers as one sentence list, `lead` (a faulted layer) first."""
    order = ([lead] if lead else []) + [k for k in ORDER if k != lead]
    said = [layer_said(look, k).strip().rstrip(".") for k in order if layer_said(look, k).strip()]
    return ". ".join(s[:1].upper() + s[1:] for s in said) + ("." if said else "")


def edit_prompt(look, lead: str = "") -> str:
    """One hop from sheet_front.png: the same person, only the look changes."""
    return (f"The same person as in the picture: same face, same build. One figure, full body, front view, "
            f"standing, plain mid-grey backdrop. Change only what this person wears and looks like now: "
            f"{layers_first(look, lead)}")


def form_of(base_prompt: str) -> str:
    """The base sheet prompt's own form sentence, else the house form."""
    found = re.search(r"Character reference sheet.*$", base_prompt or "", re.S)
    return found.group(0).strip() if found else FORM


def fresh_prompt(card, look_id: str, base_prompt: str, lead: str = "") -> str:
    """The look drawn fresh: its layers FIRST, then the invariant body, then the form."""
    return f"{layers_first(card.looks[look_id], lead)} {card.body.strip()} {form_of(base_prompt)}"


def sha8(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def base_prompt(book: Path, who: str) -> tuple[str, int]:
    """The base sheet's own prompt and seed from refs/pack.jsonl (last row wins)."""
    from studio import refs_pack
    rel, found = f"refs/characters/{who}/sheet.png", ("", refs_pack.seed_for(f"refs/characters/{who}/sheet.png"))
    pack = Path(book) / "refs" / "pack.jsonl"
    for line in pack.read_text(encoding="utf-8").splitlines() if pack.exists() else []:
        row = json.loads(line)
        if row.get("path") == rel:
            found = (row.get("prompt", ""), int(row.get("seed") or found[1]))
    return found


def crop_front(sheet: Path, target: Path) -> Path:
    """The fresh sheet's first figure, the shape every grid and take stages."""
    import numpy as np
    from PIL import Image
    from studio.sheet_front import first_figure_box
    a = np.asarray(Image.open(sheet).convert("RGB"))
    box = first_figure_box(a)
    Image.fromarray(a if box is None else a[:, box[0]:box[1]]).save(target)
    return target


def draw_one(book: Path, who: str, look_id: str, card, draws: dict, seed: int, lead: str = "") -> Path:
    """One draw of one look by its route, written to looks/<look>.png."""
    target = look_path(book, who, look_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    look = card.looks[look_id]
    if route_of(look) == "edit":
        source = Path(book) / "refs" / "characters" / who / "sheet_front.png"
        drawn = target.with_name(f"{look_id}_edit.png")
        draws["edit"](edit_prompt(look, lead), source, drawn, seed)
        return crop_front(drawn, target)
    prompt, _ = base_prompt(book, who)
    sheet = target.with_name(f"{look_id}_sheet.png")
    draws["fresh"](fresh_prompt(card, look_id, prompt, lead), sheet, seed)
    return crop_front(sheet, target)


def score(verdict) -> tuple[int, int]:
    return (sum(f.severity == "high" for f in verdict.faults), len(verdict.faults))


def lead_of(verdict) -> str:
    """The layer of the first HARD fault: written first on the redraw."""
    hard = [f for f in verdict.faults if f.severity == "high"]
    return LAYER_OF.get(hard[0].kind.removeprefix("look_"), "") if hard else ""


def climb(book: Path, who: str, look_id: str, card, draws: dict, judge) -> tuple[int, object]:
    """Draw, judge, redraw on seed+1 with the fault first (cap MAX_REDRAWS); the
    best kept.  Returns (the kept seed, its verdict, flagged when none passed)."""
    _, seed0 = base_prompt(book, who)
    best, lead = None, ""
    for k in range(MAX_REDRAWS + 1):
        path = draw_one(book, who, look_id, card, draws, seed0 + k, lead)
        verdict = judge(path, card.looks[look_id])
        if best is None or score(verdict) < score(best[1]):
            best = (seed0 + k, verdict, path.read_bytes())
        if verdict.passed:
            break
        lead = lead_of(verdict)
    look_path(book, who, look_id).write_bytes(best[2])
    flagged = not best[1].passed
    return best[0], best[1].model_copy(update={"terminal": "keep_best" if flagged else ""})


def record(book: Path, who: str, look_id: str, seed: int, verdict) -> None:
    """The drawn look into refs/looks.json (one hop from the base, by sha8) and
    its verdict into refs/looks.verdict.json."""
    table = look_timeline.load(book)
    card = table.characters[who]
    base = Path(book) / "refs" / "characters" / who / "sheet.png"
    card.base_sha8 = sha8(base) if base.exists() else card.base_sha8
    look = card.looks[look_id]
    card.looks[look_id] = look.model_copy(update={
        "sheet": episode_home.relative(book, look_path(book, who, look_id)), "made_by": route_of(look),
        "parent_sha8": card.base_sha8, "seed": seed})
    look_timeline.write_looks(book, who, card)
    path = Path(book) / "refs" / "looks.verdict.json"
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    doc[f"{who}/{look_id}"] = verdict.model_dump(mode="json")
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")


def draw_missing(book: Path, episode, draws: dict, judge) -> list[str]:
    """Every missing look of this episode drawn, judged, recorded; their keys."""
    done = []
    for who, look_id in missing_looks(book, episode):
        card = look_timeline.load(book).characters[who]
        seed, verdict = climb(book, who, look_id, card, draws, judge)
        record(book, who, look_id, seed, verdict)
        done.append(f"{who}/{look_id}" + (" (flagged)" if verdict.terminal else ""))
    return done


def comfy_draws(book: Path) -> dict:
    """The house drawers on the local GPU: the identity edit and the Krea2 T2I."""
    import shutil
    from studio import comfy, refs_pack

    def edit(prompt: str, source: Path, target: Path, seed: int) -> None:
        out = comfy.run("image_krea2_identity_edit", {"source": comfy.stage_image(source),
                                                      "prompt": prompt, "seed": seed})[0]
        shutil.copyfile(out, target)

    def fresh(prompt: str, target: Path, seed: int) -> None:
        out = comfy.run(refs_pack.T2I, {"prompt": refs_pack.styled(prompt), "seed": seed,
                                        "width": 1536, "height": 1024})[0]
        shutil.copyfile(out, target)
    return {"edit": edit, "fresh": fresh}


def where_of(book: Path, path: Path) -> str:
    """The picture's name for the verdict: book-relative, or its own path when a
    replay draws outside the book (docs/audit/.../replay)."""
    try:
        return episode_home.relative(book, path)
    except ValueError:
        return Path(path).resolve().as_posix()


def vlm_judge(book: Path):
    """LOOK-STATE with the local vision model as its reader."""
    from studio import look_back
    from studio.judges import look_state
    return lambda path, look: look_state.judge(path, look.markers, look_back.vlm_reader,
                                               where=where_of(book, path), face_change=look.face_change)


def main(book_id: str, number: int, drawing: bool) -> int:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    if look_timeline.load(book) is None:
        print("  continuity: legacy (no refs/looks.json) -- one sheet per character")
        return 0
    if drawing:
        for key in draw_missing(book, episode, comfy_draws(book), vlm_judge(book)):
            print(f"  drew look {key}")
    missing = missing_looks(book, episode)
    for who, look in missing:
        print(f"  missing  {who}/{look}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], episode_arg(sys.argv), "--draw" in sys.argv))
