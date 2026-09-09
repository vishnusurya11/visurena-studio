"""Every beat of the page as a shot H3 can actually render.

The page says WHAT a beat is for; this says what the camera does.  One
structured call turns each `ScriptBeat` into the fields `h3_prompt.build`
needs -- which reference is bound, where it is set, the action, the framing it
opens on, the framing it arrives at, and the move between them -- and the
six-section Ref2V document is assembled from those.

THE SAME RULE AS THE PAGE: a shot may only name a reference that EXISTS.  The
model picks from the sheets step 02 bound, by id, and a shot naming anything
else is refused (`NoSuchRef`).  Identity in this pipeline is a reference sheet,
not a description, so a shot that points at no sheet is a shot with nobody in it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field

from studio import h3_prompt, llm
from studio.trailer_script import TrailerScript

TIER = "reasoning"


TRIES = 3
"""How many times a refused shot list is asked again before the run gives up."""


class NoSuchRef(ValueError):
    """The shot named a reference sheet the book does not have."""


class Shot(BaseModel):
    """One beat as a camera instruction, bound to the sheets that exist."""

    beat_id: str
    character: str | None = Field(default=None, description="ref_id of the person bound in frame")
    second: str | None = Field(default=None, description="ref_id of a second person, for a two-shot")
    place: str = Field(description="ref_id of the location the shot is set in")
    action: str = Field(min_length=20, description="what happens, in one or two sentences")
    open_framing: str = Field(min_length=20, description="the composition the take opens on")
    close_framing: str = Field(min_length=20, description="the composition the move arrives at")
    camera: str = Field(min_length=20, description="the single camera move between them")
    arc: str = Field(default="build", description="quiet, build or hit — what the score is doing")


class ShotList(BaseModel):
    shots: list[Shot] = Field(min_length=1)


def sheets(refs: dict) -> dict[str, dict]:
    """Every bound reference by id, so a shot can be checked against them."""
    return {r["ref_id"]: r for r in refs.get("refs", [])}


def menu(refs: dict, kind: str) -> str:
    """The sheets of one kind, as the model may refer to them."""
    return "\n".join(f'- {r["ref_id"]} ({r["name"]}): {r.get("physical", "")[:160]}'
                     for r in refs.get("refs", []) if r["kind"] == kind)


def beat_menu(page: TrailerScript) -> str:
    """The page, as the shot list must answer it beat for beat."""
    return "\n".join(
        f'{b.id} [{b.movement}/{b.function}] {b.seconds:.1f}s — SEE: {b.see or b.card} — '
        f'HEAR: {b.hear or "—"}'
        + (f' — LINE ({b.speaker}): "{b.line}"' if b.line else "")
        + f' — WHY: {b.why}'
        for b in page.beats)


def brief(page: TrailerScript, refs: dict) -> str:
    """What the model is shown: the page, the sheets, and the frame."""
    return (
        f"Turn each beat of this trailer into ONE camera instruction for a "
        f"reference-to-video model that renders a single continuous take.\n\n"
        f"The trailer is '{page.title}', {page.genre}, shot {page.aspect} VERTICAL — "
        f"compose for a tall frame, with the subject in the centre band, because the "
        f"top and bottom of the frame are covered by platform interface.\n\n"
        f"THE LOOK, which every shot shares: {refs.get('palette', '')}\n\n"
        f"THE PAGE:\n{beat_menu(page)}\n\n"
        f"PEOPLE YOU MAY PUT IN FRAME — use the ref_id exactly, or none at all:\n"
        f"{menu(refs, 'character')}\n\n"
        f"PLACES YOU MAY SET A SHOT IN — use the ref_id exactly:\n"
        f"{menu(refs, 'location')}\n\n"
        f"ONLY TWO FACES CAN BE KEPT. The renderer takes two reference images, so a "
        f"shot may bind at most two people. If a beat names more, bind the two the "
        f"beat is ABOUT and keep the others out of frame, turned away, or in "
        f"silhouette -- a face nobody bound is invented, and an invented face is a "
        f"different person in every shot.\n\n"
        f"For every beat give: the person bound in frame (or none, for a shot of a "
        f"place or an object), the place, the ACTION, the framing the take OPENS on, "
        f"the framing the move ARRIVES at, and the single CAMERA move between them. "
        f"Open wider and arrive tighter, so one render contains both sizes for the "
        f"cut. Name the period detail — gaslight, fog, wet cobbles, oil lamp, "
        f"hansom — and say what the light is doing. Keep every beat's action to what "
        f"one continuous take can hold: one move, one place, no cutaways.\n\n"
        f"Return one shot per beat, in the same order, with the same beat ids.")


def check(shots: ShotList, page: TrailerScript, bound: dict[str, dict]) -> ShotList:
    """Every shot answers a beat and names sheets that exist."""
    wanted = [b.id for b in page.beats]
    if [s.beat_id for s in shots.shots] != wanted:
        raise NoSuchRef(f"the shot list must answer every beat in order: {wanted}")
    for shot in shots.shots:
        for ref in (shot.character, shot.second, shot.place):
            if ref and ref not in bound:
                raise NoSuchRef(f"{shot.beat_id}: no reference sheet called {ref}")
    return shots


def document(shot: Shot, beat, bound: dict[str, dict], palette: str) -> str:
    """One beat's full six-section Ref2V prompt."""
    person = bound.get(shot.character or "", {}).get("physical", "")
    other = bound.get(shot.second or "", {}).get("physical", "")
    place = bound.get(shot.place, {}).get("physical") or shot.place
    return h3_prompt.build(style=palette, character=person, place=place,
                           action=shot.action, open_framing=shot.open_framing,
                           close_framing=shot.close_framing, camera=shot.camera,
                           seconds=beat.seconds, arc=shot.arc, second=other)


def write(out_dir: Path, page: TrailerScript, refs: dict,
          model: Callable | None = None) -> ShotList:
    """Ask for the shot list, check it, and write the prompts beside the page."""
    bound = sheets(refs)
    ask = model or llm.structured
    text, refused, shots = brief(page, refs), "", None
    for _ in range(TRIES):
        try:
            asked = "\n\n".join(filter(None, (text, refused)))
            shots = check(ask(TIER, asked, ShotList), page, bound)
            break
        except NoSuchRef as why:
            refused = (f"Your previous shot list was REFUSED: {why}. Only the ref_ids "
                       f"listed above exist as reference sheets -- a person without one "
                       f"cannot be shown in frame. Write it again, using a sheet that "
                       f"exists or no person at all.")
    if shots is None:
        raise NoSuchRef(refused)
    beats = {b.id: b for b in page.beats}
    palette = refs.get("palette", "")
    records = [{"beat_id": s.beat_id, "seconds": beats[s.beat_id].seconds,
                "character": s.character, "second": s.second, "place": s.place,
                "prompt": document(s, beats[s.beat_id], bound, palette)}
               for s in shots.shots]
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "shot_prompts.json").write_text(
        json.dumps({"title": page.title, "aspect": page.aspect, "shots": records},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    (Path(out_dir) / "shot_prompts.txt").write_text(readable(records), encoding="utf-8")
    return shots


def readable(records: list[dict]) -> str:
    """The prompts as a file a person can read and edit."""
    out = []
    for r in records:
        who = " + ".join(filter(None, (r["character"], r["second"]))) or "no one"
        out.append(f"{'=' * 78}\n{r['beat_id']}  {r['seconds']:.1f}s  "
                   f"[{who} @ {r['place']}]\n{'=' * 78}\n{r['prompt']}")
    return "\n\n".join(out)
