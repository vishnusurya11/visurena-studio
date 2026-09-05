#!/usr/bin/env python
"""Render one video clip per beat, every one bound to its reference sheets.

ONE TAKE, ONE SHOT.  The take used to be long coverage the edit cut several
shots out of, and that is precisely what produced four moments of one image
instead of four images.  A take is now the length of its shot plus the head
trim it has to skip, so the frames the machine samples are the frames the cut
plays: run 10 rendered 175 frames a take and threw 65 of them away, about 50
minutes of a five-hour run.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.clip_cache import digest_of, is_current, record
from studio.comfy import run, stage_image
from studio.h3 import NATIVE_H, NATIVE_W, frames_for
from studio.h3_prompt import build as h3_document
from studio.shot_grammar import FRAMING, LADDER
from studio.trailer_assemble import HANDLE, HEAD_TRIM
from studio.trailer_refs import visual_description
from studio.trailer_shot import is_scene_safe

ROOT = Path(__file__).resolve().parents[2]
READ_WINDOW = 0.75
"""The shortest stretch of usable take the identity reader can sample.

`frames_of` takes three stills PAST the head trim, so a take with nothing past
it cannot be read at all and its gate becomes a picture of the reference sheet.
Only a shot under this is lengthened, and MIN_SHOT is 0.5s."""
STEPS = 8
"""Eight, not four.  At four steps the final Euler step drops sigma from ~0.72
to zero -- one step doing three quarters of the denoising -- which is the
arithmetic behind the mushy, smeared look.  Two independent published sources
call four a draft mode."""
FAST_STEPS = 4
FAST_INSERTS = False
"""OFF until one take measures it.  Four steps is a draft mode everywhere a
viewer can read the frame -- but an insert held 0.8s is under twenty frames of
an object filling the middle of the picture, and the published objection is
about faces and motion.  The code path exists so run 11 can measure ONE take
against its eight-step twin; the flag turns on from that measurement, never
from this argument."""
FAST_SIZES = ("insert", "extreme_close")
FAST_SECONDS = 1.0


def is_complete(video: Path) -> bool:
    """True when a file is not just present but finished and readable.

    An existence check is not a completeness check.  mp4 writes its index last,
    so a render interrupted mid-copy leaves a file that looks done, gets
    skipped as done, and silently poisons the cut with an unreadable take.
    """
    if not video.exists() or video.stat().st_size < 10_000:
        return False
    result = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    return not result.stderr.strip()


WORKFLOW = "video_minimax_h3_r2v_turbo"
SEED_BASE = 51000


def bound_slots(beat: dict, refs: dict) -> list[str]:
    """The sheets H3 binds: the beat's characters, then its location, two at most."""
    chars = [f"char-{c}" for c in beat["cast"] if f"char-{c}" in refs]
    loc = f"loc-{beat['location_id']}"
    return (chars + ([loc] if loc in refs else []))[:2]


def shot_seconds(beat_id: str, plan: dict) -> float:
    """The longest shot the cut wants from this beat.  One take, one shot, so
    this is normally THE shot; a plan that still doubles up gets the longer."""
    return max((s["seconds"] for s in plan["shots"] if s["beat_id"] == beat_id), default=0.0)


def take_seconds(beat_id: str, plan: dict) -> float:
    """Exactly what the cut takes from this beat, and the leak it must skip.

    Run 10 rendered every take at a flat 7.29s and used 2.0s of it past a 2.6s
    head trim: 65 frames a take, ~50 minutes of the run, sampled and thrown
    away.  The 7.0s floor was there so ONE take could hold FOUR shots; it holds
    one now.  The final hold outruns MAX_SHOT by design, and a take that cannot
    hold its shot starts the cut inside the reference leak (Scarlet run 6).
    """
    return max(shot_seconds(beat_id, plan), READ_WINDOW) + HEAD_TRIM + HANDLE


def steps_for(beat_id: str, plan: dict, fast: bool = None) -> int:
    """Sampling steps for this beat's take: four only for an insert the cut
    holds a second or less, where there is no face and no time to read a smear."""
    fast = FAST_INSERTS if fast is None else fast
    shots = [s for s in plan["shots"] if s["beat_id"] == beat_id]
    if fast and shots and all(s["size"] in FAST_SIZES and s["seconds"] <= FAST_SECONDS
                              for s in shots):
        return FAST_STEPS
    return STEPS


def take_values(beat: dict, plan: dict, refs: dict, style: str, seed: int,
                tightest: str | None = None) -> dict:
    """What the model is asked for one beat's take.

    The take opens on the widest size this beat's shots ask for and arrives at
    the tightest -- with one shot per beat those are the same size, and the
    move is the shot's own.  `tightest` overrides the arrival: the identity
    ladder's alternate setup asks for a face the recogniser can read, and
    holds that size for the whole take.

    Two cast members bound are two subjects, never one person described twice:
    the second takes H3's second slot and the place goes by prompt.
    """
    char_ids = [r for r in bound_slots(beat, refs) if r.startswith("char-")]
    described = [visual_description(refs[c]["physical"]) for c in char_ids]
    for who, text in zip(char_ids, described):
        if not is_scene_safe(text):
            raise ValueError(f"{who}'s description carries reference-sheet language, "
                             f"which would animate a character sheet: {text[:120]}")
    loc_id = f"loc-{beat['location_id']}"
    wanted = sorted({s["size"] for s in plan["shots"] if s["beat_id"] == beat["beat_id"]}
                    or {"medium"}, key=LADDER.index)
    open_size, close = (tightest, tightest) if tightest else (wanted[-1], wanted[0])
    seconds = take_seconds(beat["beat_id"], plan)
    return {
        "prompt": h3_document(
            style=style, character=described[0] if described else "",
            second=described[1] if len(described) > 1 else "",
            place=refs[loc_id]["name"] if loc_id in refs else beat["location_id"],
            action=beat["image_prompt"], open_framing=FRAMING[open_size],
            close_framing=FRAMING[close], camera=beat["motion"], seconds=seconds,
            arc=beat["arc"]),
        "width": NATIVE_W, "height": NATIVE_H, "frames": frames_for(seconds),
        "steps": steps_for(beat["beat_id"], plan), "seed": seed, "ref_image_size": "max",
        "filename_prefix": f"TR-{beat['beat_id']}"}


def recipe_for(values: dict, bound: list[str], refs: dict, book: Path,
               workflow: str = WORKFLOW) -> dict:
    """Everything that decides what the model draws -- what identifies the clip.

    Skipping on the beat ID meant a plan rebuilt from scratch reused every old
    render under the new names.  A chosen LoRA is named only when there is
    one, so takes fingerprinted before the choice existed still match.
    """
    lora = {"lora": values["lora_name"]} if values.get("lora_name") else {}
    return {"prompt": values["prompt"], "refs": bound, "seed": values["seed"],
            "frames": values["frames"], "steps": values["steps"],
            "width": values["width"], "height": values["height"], "workflow": workflow,
            "ref_digests": [digest_of(book / refs[r]["rel_path"]) for r in bound], **lora}


def render_take(values: dict, bound: list[str], refs: dict, book: Path, dest: Path,
                workflow: str = WORKFLOW) -> Path:
    """One H3 render, staged references in, the finished mp4 at `dest`."""
    values = dict(values)
    for slot, ref_id in enumerate(bound, start=1):
        values[f"ref_image_{slot}"] = stage_image(book / refs[ref_id]["rel_path"])
    written = run(workflow, values, timeout=3600)
    video = next((p for p in written if p.suffix in (".mp4", ".webm")), None)
    if not video:
        raise RuntimeError(f"{dest.stem} produced no video: {written}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(video.read_bytes())
    record(dest, recipe_for(values, bound, refs, book, workflow))
    return dest


def main(book_glob: str, trailer_id: str = "main") -> None:
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    out = book / "trailer" / trailer_id
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    refs_doc = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    refs = {r["ref_id"]: r for r in refs_doc["refs"]}
    clips_dir = out / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    for index, beat in enumerate(plan["beats"]):
        dest = clips_dir / f"{beat['beat_id']}.mp4"
        bound = bound_slots(beat, refs)
        if not bound:
            print(f"  {beat['beat_id']} SKIPPED: nothing to bind to")
            continue
        try:
            values = take_values(beat, plan, refs, refs_doc["palette"], SEED_BASE + index * 7)
        except ValueError as exc:
            raise SystemExit(f"REFUSED: {exc}")
        values["filename_prefix"] = f"TR-{book.name[:8]}-{beat['beat_id']}"
        recipe = recipe_for(values, bound, refs, book)
        # Two questions, asked separately: is the file finished, and is it the
        # file this plan asks for.  Conflating them is what silently shipped
        # nine of nine Scarlet clips from the previous plan.
        if is_complete(dest) and is_current(dest, recipe):
            print(f"  {beat['beat_id']} is current, skipping")
            continue
        if dest.exists():
            reason = "stale" if is_complete(dest) else "unreadable"
            print(f"  {beat['beat_id']} is {reason}; re-rendering")
            dest.unlink()
        print(f"  [{index + 1}/{len(plan['beats'])}] {beat['beat_id']} <- {', '.join(bound)}")
        render_take(values, bound, refs, book, dest)
        print(f"      -> {dest.name}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
