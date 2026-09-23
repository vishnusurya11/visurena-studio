#!/usr/bin/env python
"""ENGINE r2v, take-based: a take is a run of consecutive shots (<= 12 s, one
setup); every shot's panel is anchored at its start frame, the next take's
first panel at the last frame; the cast sheets go in ONLY for faces the take
shows readable; the plate is a reference only when the take has a wide enough
cell to place it against; a dialogue line's wav is anchored at its own frame,
otherwise silence.

    uv run python scripts/episode/takes_r2v.py <codex_id> <episode>            # render
    uv run python scripts/episode/takes_r2v.py <codex_id> <episode> --prompts  # cards only
    uv run python scripts/episode/takes_r2v.py <codex_id> <episode> --from-refs
                          # no storyboard cell: the plate + the cast cards only (see FROM_REFS)

Takes -> `shots_r2v/T<first>.mp4`; records in `shots_r2v/shots.json` carry
`shots` (the run) so the cut and the run cards know the grouping.
Owner's design, 2026-09-10 ("use three frames from the storyboard, the third
is your final frame; match the voice timeline").
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.episode_home import episode_arg
from studio import panel_dq
from studio import approval, canvas, episode_board as board, episode_home, episode_ref_official as ro, episode_ref_prompt as rp
from studio import house_style, pack_refs
from studio import take_currency
from studio import take_refs
from studio import plan_gates
from studio import episode_seq_board as sq
from studio import episode_takes as tk
from studio import h3_anchors
from studio.comfy import apply_inject, load_workflow, stage_image, submit, wait_record, outputs_of
from studio import episode_spec as spec
from studio.episode_spec import Episode
from studio.trailer_assemble import clip_seconds
from studio.trailer_refs import contract_description

sys.path.insert(0, str(Path(__file__).resolve().parent))
import no_last_frame  # noqa: E402  the owner's rule, checked on the built prompt

W, H, FPS, STEPS = canvas.size("9:16") + (24, 8)
"""W and H are rebound from the plan in `main`; the plan declares the aspect."""
BASE = "video_minimax_h3_r2v_turbo_ref8"
"""The ref2va-FAMILY turbo (dedicated lightx2v Ref2V 8-step v1.0 768p LoRA,
shift 12/3 per its release post; iteration 3 ran at 6/3, the FL2VA row).  Episode 1's first r2v master was rendered on `r2v_turbo`, whose
ckpt850 LoRA is FL2VA-lineage: a family mismatch the owner caught
(2026-09-10 22:30); it showed as camera-scale pumping."""
REF_IMAGE_SIZE = "match"
SEED_BASE = 81000
TIMEOUT = 7200.0
MAX_FACES = 4
"""Anyone the scene NAMES gets their sheet (owner, 2026-09-12).  Four is the real
ceiling here: the node takes nine references, and the rest are the plate and at
most four pinned cells."""
"""PINS (engine designer, 2026-09-10 evening): frame 0 of each shot in the
take, using the APPROVED panel `frames/SNN.png` at the shot's cut frame.
Nothing else is pinned: a pinned cell is reproduced exactly, and cells drawn
at different camera distances (55 % between cells 4-5 of take 3's old 3x3
sheet) became snaps and wobble.  The 2x3 sheet is the storyboard REFERENCE
and the DQ expectation, never a hard frame."""
NARRATOR = "john_watson"


def on_grid(frame: int) -> int:
    """A pin lands on a token start: 17 frames per 5 tokens (see episode_takes.grid_frame).

    OWNER (audio-first): the snap is FORWARD, so the picture cut lands on or after the
    voice cut it belongs to.  Spec 3.20 proposes `tk.near_grid` instead -- the token
    start nearest the whole second the prompt states, which would move T01's cut from
    frame 77 (3.208 s, 0.208 s after the stated 00:03) to frame 73 (3.042 s, 0.042 s).
    Measured cost of taking it: a backward snap of up to 14 frames puts the picture
    ahead of the line it is cut to.  The A/B flips this one return."""
    return tk.grid_frame(frame)


def physicals(book: Path) -> dict[str, str]:
    return {r["entity_id"]: contract_description(r.get("physical", ""))
            for r in episode_home.read_json(book / "refs" / "refs.json")["refs"]
            if r.get("kind") == "character"}


def named_in(shot, cast: list[str]) -> list[str]:
    """Whoever the shot's own words name, across every text the drawer and the model
    are given: the frame, the motion, the camera, what is at rest, the END picture."""
    fields = ("frame", "motion", "camera", "at_rest", "end", "changed")
    blobs = [getattr(shot, f, "") or "" for f in fields]
    blobs += [getattr(cut, f, "") or "" for cut in shot.cuts for f in fields]
    return ro.people_in(" ".join(blobs), cast)


def faces_of(shots: list, cast: list[str] | None = None) -> list[str]:
    """Every person the take shows, in first-appearance order.

    `faces` says whose face has to READ; it does not say who is in the room.

    ONLY A FACE THAT READS.  Owner 2026-09-12 gave a sheet to anyone the prose
    NAMED, after Take 00 listed Stamford alone, turned Watson to camera in its
    motion, and rendered him without his moustache.  Measured a day later, that
    rule staged 6 sheets in episode 3 for faces no segment shows -- T04 took two
    for a take declaring no readable face at all.  Each is a full-length studio
    portrait competing with the storyboard cell for the same man, and at T02's
    4.0 s the render put exactly that composition into the room.

    The moustache fault is now answered where it belongs: a cast sheet is a
    DEFINITION (`episode_ref_official.subjects`), so the man named in the prose
    is described there without spending a whole-frame picture on him."""
    seen: list[str] = []
    for shot in shots:
        for who in [w for w in shot.faces] + [w for cut in shot.cuts for w in cut.faces]:
            if who not in seen:
                seen.append(who)
    return seen[:MAX_FACES]


def people_staged(shots: list, cast: list[str]) -> list[str]:
    """Everyone a references-only take must stage: whoever has to READ, plus
    whoever the shot's own words NAME, in first-appearance order.

    OWNER 2026-09-17: a wide of Jefferson Hope's body staged no Hope, and a wide
    of Holmes and Watson at the hearth staged neither, because `faces` means
    "whose face must read" and a wide names nobody.  With a drawn cell that was
    harmless -- the cell carried the men.  With references alone the men are only
    in the take if their cards are."""
    seen: list[str] = []
    for shot in shots:
        # WHO IS SHOWN, not who is mentioned: `named_in` reads the camera and the
        # motion too, and "from Holmes's chair across the hearth" is where the
        # camera STANDS -- staging his card there would put him in a shot the
        # plan gives to Watson alone (ep14 T05).
        shown = ro.people_in(" ".join([shot.frame or "", getattr(shot, "at_rest", "") or ""]), cast)
        for who in list(getattr(shot, "faces", [])) + shown:
            if who not in seen:
                seen.append(who)
    return seen[:MAX_FACES]


def ref_name(book: Path, path: Path) -> str:
    """How a record names a reference: the bare file name, as it always was, or
    the book-relative path for a picture in the pack's per-entity folders
    (`refs/characters/<id>/sheet.png`), where the bare name says nothing."""
    path, refs = Path(path), Path(book) / "refs"
    kinds = ("characters", "locations", "props")
    if path.parent.parent.name in kinds and path.parent.parent.parent == refs:
        return path.relative_to(book).as_posix()
    # A storyboard panel lives under episodes/epNN/storyboard/h3/ and its bare
    # name says nothing either: `graph_for` resolves a bare name against the
    # boards' cell folder, and looked for shot_00.png among the cells.
    if path.parent.name == "h3" and path.parent.parent.name == "storyboard":
        return path.relative_to(book).as_posix()
    return path.name


def narrator_of(lines) -> str:
    """Whoever speaks the narration; the old constant when there is none.  It was
    `john_watson` for every book."""
    return next((l.speaker for l in lines if l.kind == "narration"), NARRATOR)


def adopt_names(rows: list[dict]) -> None:
    """The book's declared display names and women, for the prompt builder.  A
    row with no `display` keeps its title-cased id; no rows restores the default."""
    ro.DISPLAY.clear()
    ro.WOMEN.clear()
    ro.CREATURES.clear()
    for r in rows:
        if r.get("kind") != "character":
            continue
        if r.get("display"):
            ro.DISPLAY[r["entity_id"]] = r["display"]
        if r.get("gender") == "female":
            ro.WOMEN.add(r["entity_id"])
        if r.get("gender") == "creature":
            ro.CREATURES.add(r["entity_id"])


def reference_list(book: Path, boards: Path, faces: list[str], setup: str,
                   segs: list[tuple[int, int]], ends: list[tuple[int, int]], strip: Path,
                   state: str = "", sizes: list[str] | None = None) -> list[Path]:
    """The take's picture slots, in the order `graph_for` stages them and therefore in
    the order `episode_ref_official` numbers them (spec 1.1): cast sheets, the plate,
    every pinned cell in first-pin order, the END cells, the strip."""
    refs = [sq.cast_sheet(book, who, setup, state) for who in faces]
    # THE PLATE WAS THE EPISODE'S TOP OPEN FAULT.  MEASURED on episode 2: 13 of
    # the 14 foreign frames are the take's OWN plate at 0.988-0.998, and every
    # one came from a close or insert segment with no wider cell in the take
    # (Fisher p = 0.0072; 0 of 64 wider frame samples).  A take of nothing but
    # tight cells cannot place a room, so the plate stops being a definition and
    # becomes the only whole picture the model can fall back on -- T03 opens on
    # Holmes's face and by 1.5 s the frame IS plate_sofa.png, violin and all.
    # Dropping it here is only half the fix: `picture_numbers` closes the slot
    # too, or the prompt cites a picture the graph never staged (L11).
    if sq.places_the_plate(sizes or []):
        refs += [sq.plates_in(boards) / f"plate_{setup}.png"]
    refs += [sq.cells_in(boards) / sq.cell_name(a, b) for a, b in segs]
    refs += [sq.cells_in(boards) / sq.cell_name(a, b, end=True) for a, b in ends]
    # OWNER 2026-09-11: no strip.  On a one-segment take it was the cell again, pixel for
    # pixel; on a multi-shot take its trailing panels were read as later shots and the take
    # cut back to them.  Every cell is staged whole and named, which is all the strip said.
    if len(refs) > ro.MAX_PICTURES:
        raise SystemExit(f"take {segs[0][0]:02d}: {len(refs)} references; the wall is "
                         f"{ro.MAX_PICTURES} (MiniMaxH3ReferenceToVideo.ref_images max=9)")
    return refs


FROM_REFS = False

PIN_PANEL = True
"""Whether the staged storyboard panel is the take's FIRST FRAME.

Owner 2026-09-20 chose the pin (option 2) because a weak_reference has no
authority over framing and ep05 shipped with T14's horse cropped to a head.
`--no-pin` puts it back to a weak_reference, which is what ep01-05 rendered
with, so the two can be measured against each other on the same shots."""
"""RENDER FROM THE REFERENCES ALONE: the plate and the cast cards, no cell.
Turned on by `--from-refs`; OFF is the normal path and the default.

WHY IT EXISTS.  On 2026-09-17 the paid image API that draws the storyboard
sheets had no credits, so no episode can have its cells drawn.  Everything
upstream of the sheets is free and already on disk: the plan, the location
plates, the cast cards, the measured voice.  The experiment this switch runs is
whether those alone carry a take -- the model shown WHO is in it and WHERE it
is, and told the shot in words.

WHAT IT CHANGES, and nothing else: the reference list is the cast sheets and the
plate; no cell is staged, none is pinned, no END cell is drawn on, and the strip
is not composed (it opens every cell, and there are none).  Audio, frames,
seconds, the seed and every other record field are built exactly as they are on
the normal path.

AND THE PLATE IS ALWAYS STAGED here -- see `refs_from_cards`."""


def location_picture(book: Path, boards: Path, setup, name: str, shot=None) -> Path:
    """The picture that says WHERE: the book's own location when the setup names
    one, else this episode's plate of the same place.

    OWNER 2026-09-17: "use the same location references refs/locations". They are
    drawn once for the series, so the room is the same room in every episode."""
    named = getattr(setup, "location", "") or ""
    if not named:
        return sq.plates_in(boards) / f"plate_{name}.png"
    # THE PACK LAYOUT (2026-09-18): a folder of views per location, and the view
    # is chosen by the shot's size, because the take opens at its framing.
    if (Path(book) / "refs" / "locations" / named).is_dir():
        return pack_refs.location_view(book, named, getattr(shot, "size", "wide"),
                                       view=getattr(setup, "view", "") or "")
    path = Path(book) / "refs" / "locations" / f"loc-{named}.png"
    if not path.exists():
        raise SystemExit(f"setup {name!r} names location {named!r}; {path.name} is not on disk")
    return path


def refs_from_cards(book: Path, boards: Path, faces: list[str], setup: str,
                    state: str = "", sizes: list[str] | None = None,
                    place: Path | None = None, panel: bool = False) -> list[Path]:
    """FROM_REFS: this take's cast sheets, and its plate where the take is wide
    enough to place one -- or where it has nothing else to stage.

    MEASURED on ep14's first references-only run: staging the plate on every take
    put the room at frame 0 of a medium close (T20, cosine 0.999, then a dissolve
    into an invented library) and of an insert (T21, 0.999, hard cut at frame 14).
    That is episode 2's fault without a cell in it: the plate stops being a
    definition and becomes the only whole picture the model can fall back on.
    `places_the_plate` answers exactly this, so it is consulted here too.

    The exception is not a preference: a take with no cast sheet has nothing else
    to stage, and `graph_for` reads `paths[0]` before it counts."""
    refs = [sq.cast_sheet(book, who, setup, state) for who in faces]
    # THE PLACE IS ALWAYS STAGED HERE.  `places_the_plate` withholds the room from
    # a take of nothing but tight cells, because beside a close-up CELL the room
    # becomes the only whole picture the model can fall back on (ep02, 13 of 14
    # foreign frames).  There is no cell here to be the tighter picture, and a
    # close that stages no room was measured inventing one -- ep14's T04, T05,
    # T06 and T22 put Holmes and Watson in a Gothic panelled hall.  OWNER
    # 2026-09-17: "this needs location image too ... so you define the position
    # relative to things in location".
    # UNLESS A STORYBOARD PANEL IS STAGED. MEASURED 2026-09-21, ep06 T17 and
    # T21: both opened on this plate and hard-cut into the shot at frame 8 --
    # ep14's fault again, at almost the same frame. The reason the plate is
    # staged anyway is that a take with only a face invents the wrong room, and
    # a panel cannot: it IS this shot's room, at this hour, in this style.
    # Beside the panel the plate is a second whole picture to open on.
    if panel:
        return refs
    return refs + [place or sq.plates_in(boards) / f"plate_{setup}.png"]


def staged_facts(sizes: list[str], from_refs: bool, faces: list[str] | None = None,
                 panel: bool = False) -> dict:
    """What `episode_ref_official.build` is told about the pictures it may cite.

    FROM_REFS says no cell is staged; whether the plate is staged follows the same
    rule as the normal path (`places_the_plate`), with the one exception
    `refs_from_cards` makes: a take with no cast sheet keeps its plate because it
    would otherwise stage nothing at all.  The normal path leaves `cells_staged`
    at the builder's own default, so every episode already built is told exactly
    what it was told before."""
    if from_refs:
        # A STAGED PANEL IS THE ROOM. MEASURED 2026-09-21 on ep06 T17 and T21:
        # both opened on the plate and hard-cut into the shot at frame 8, the
        # same fault ep14's T21 had at frame 14. The plate was staged anyway
        # because a take with only a FACE invented the wrong room -- and a
        # storyboard panel cannot invent it, because it IS this shot's room at
        # this hour in this style. Staged beside the panel the plate is only a
        # second whole picture for the model to open on.
        return {"has_plate": not panel, "cells_staged": False}
    return {"has_plate": sq.places_the_plate(sizes)}


def mode_said(from_refs: bool) -> str:
    """The card's own account of what was staged.  A record that claims a cell it
    never staged is the artefact a later reader measures the render against."""
    if from_refs:
        return ("reference-to-video from the references alone (--from-refs): a cast sheet for every "
                "face the take shows + the location plate, always; no storyboard cell, nothing "
                "pinned; the dialogue wavs at their offsets anchored at frame 0")
    return ("reference-to-video: a cast sheet for every face the take shows + the plate as a "
            "DEFINITION when the take has a wide cell to place it against + one <Picture N> per "
            "pinned cell + the END cells + the take's own storyboard strip as a weak_reference; "
            "each cell pinned once at its start frame; the dialogue wavs at their offsets "
            "anchored at frame 0")


def sheet_of(episode: Episode, shot) -> str:
    groups = board.chunks([s for s in episode.shots if s.setup == shot.setup])
    return next(f"board_{shot.setup}_{k}" for k, group in enumerate(groups) if shot in group)


def measured_seconds(path: Path) -> float:
    """How long this wav really is, or a value that forces a rebuild.

    Being unable to measure is not a pass (`bed_gate`'s rule): an unreadable or
    truncated guide must be rebuilt, never trusted."""
    try:
        return clip_seconds(path)
    except Exception:
        return -1.0


def composite(lines: list[tuple[Path, float]], seconds: float, out: Path) -> Path:
    """The take's audio: dialogue wavs at their offsets over silence, 24 kHz mono.

    THE CACHE IS KEYED ON THE LENGTH, not on the filename.  This audio is the
    model's SHARED CLOCK -- H3 lays the audio latents on the same t-axis as the
    target frames -- so its duration is a statement about when the picture ends.
    MEASURED on episode 3: `silence_02.wav` and `silence_11.wav` were 12.25 s
    files left over a pair of takes re-planned to 6.583 s, and the node crops
    silently, so nothing errored.  Too long is harmless; too SHORT ends the
    model's clock before the video, which is the early-arrival fault this
    pipeline has been chasing."""
    if out.exists() and abs(measured_seconds(out) - seconds) <= 1.0 / FPS:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    # ffmpeg will not create the directory it is told to write into, and its
    # failure surfaces as a bare CalledProcessError with a Windows exit status,
    # which reads like a codec fault and not a missing folder. A fresh episode
    # has no shots_<engine>/ until something makes one, and the take audio is
    # the first thing that writes there.
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono:d={seconds:.3f}"]
    for wav, _ in lines:
        cmd += ["-i", str(wav)]
    chain = "".join(f"[{k + 1}]adelay={int(at * 1000)}|{int(at * 1000)}[d{k}];" for k, (_, at) in enumerate(lines))
    mix = "[0]" + "".join(f"[d{k}]" for k in range(len(lines)))
    cmd += ["-filter_complex", f"{chain}{mix}amix=inputs={len(lines) + 1}:normalize=0[a]",
            "-map", "[a]", "-t", f"{seconds:.3f}", "-ac", "1", "-ar", "24000", str(out)]
    subprocess.run(cmd, check=True)
    return out


def cell_anchors(shots: list, take: dict) -> list[tuple[str, int]]:
    """Every segment's cell, pinned ONCE at its own start frame within the take."""
    by = {s["index"]: s for s in take["placed"]}
    anchors = []
    for s in shots:
        t0 = by[s.index]["t_start"] - take["t_start"]
        anchors.append((sq.cell_name(s.index, 0), on_grid(round(t0 * FPS))))
        for k, cut in enumerate(s.cuts, start=1):
            anchors.append((sq.cell_name(s.index, k), on_grid(round((t0 + cut.at_s) * FPS))))
    return anchors


def refuse_missing_cells(cells: Path, anchors: list[tuple[str, int]], index: int) -> None:
    """A pin needs its picture: refuse before the GPU, naming the step that draws it."""
    for name, _ in anchors:
        if not (Path(cells) / name).exists():
            raise SystemExit(f"take {index:02d}: sequence cell {name} missing: run seq_boards.py first")


def refuse_double_pins(anchors: list[tuple[str, int]], index: int) -> None:
    """MEASURED 2026-09-11 (task force, 71 segments): any end pin -- the start cell
    again or a drawn END cell -- is reached within ~1 s and then HELD (65 % / 59 %
    frozen vs 30 % start-only).  A pin is a soft conditioning row at its time, so
    two pins on one cell say "nothing changes".  Every cell is pinned ONCE, at its
    start; the next start pin closes the segment."""
    if len({n for n, _ in anchors}) != len(anchors):
        raise SystemExit(f"take {index:02d}: a cell is pinned twice: {anchors}")


def storyboard_panel(book: Path, number: int, index: int) -> Path | None:
    """This take's own storyboard panel, at H3's native size, or None.

    Drawn by the Qwen-Image-2.1 pass and cut one-per-take with its gutter shed
    (`studio.storyboard_grid.panel_box`). Absent means the episode was never
    storyboarded, and the take builds exactly as it did before."""
    path = (episode_home.home(book, number) / "storyboard" / "h3" / f"shot_{index:02d}.png")
    return path if path.exists() else None


def card(book: Path, episode: Episode, number: int, take: dict, measured: dict) -> dict:
    shots = [episode.shot(i) for i in take["shots"]]
    first = shots[0]
    boards = episode_home.boards_dir(book, number)
    faces = faces_of(shots, sorted(physicals(book)))
    segs = [(s.index, k) for s in shots for k in range(0, len(s.cuts) + 1)]
    sizes = [s.size for s in shots] + [c.size for s in shots for c in s.cuts]
    state = episode.setups[first.setup].state
    if FROM_REFS:
        ends, anchors = [], []
        where = location_picture(book, boards, episode.setups[first.setup], first.setup, first)
        faces = people_staged(shots, sorted(physicals(book)))
        refs = refs_from_cards(book, boards, faces, first.setup, state, sizes, where,
                               panel=storyboard_panel(book, number, first.index) is not None)
        # THE SETUP'S PROP SHEETS, after the place (ep02: the cylinder) -- but
        # only the ones THIS TAKE'S OWN PROSE NAMES.  `Setup.props` is a
        # setup-level field, and staging all of it on every take of the setup
        # put chapter 5's humped dome at the mast's foot from shot zero, twenty
        # shots before it rises (`pack_refs.props_named`).
        staged_props = pack_refs.props_named(
            book, list(getattr(episode.setups[first.setup], "props", []) or []),
            pack_refs.shot_prose(shots))
        refs += [path for path, _ in staged_props]
        props = [row for _, row in staged_props]
    else:
        props = []
        sheet = reference_strip(boards, episode, shots)
        ends = end_cells(sq.cells_in(boards), segs, seg_sizes(shots), seg_motions(shots))
        refs = reference_list(book, boards, faces, first.setup, segs, ends, sheet, state, sizes)
        anchors = cell_anchors(shots, take)
        refuse_missing_cells(sq.cells_in(boards), anchors, first.index)
        refuse_double_pins(anchors, first.index)
    lines = [l for l in episode.lines if l.shot in take["shots"]]
    at = {l.index: (measured[l.index]["at"], measured[l.index]["seconds"]) for l in lines}
    spoken = [l for l in lines if l.kind == "dialogue"]
    # THE STORYBOARD PANEL, where one has been drawn for this take's first shot.
    # It leads on a silent take and follows on a speaking one: ref2va drives
    # lips off the voice wav and wants a clean face to drive, and a panel's face
    # is small and half turned on an over-the-shoulder (see studio/take_refs).
    panel = storyboard_panel(book, number, first.index)
    if panel is not None:
        refs = take_refs.with_panel(refs, panel, speaking=bool(spoken))
    # OWNER 2026-09-11 06:00: only DIALOGUE goes into a take's audio.  Anchored narration made the
    # face on screen mouth the narrator's words (Stamford at the introduction) despite the
    # "lips remain closed" sentence; narration is laid on the master, never in the take.
    voice = [(book / measured[l.index]["rel_path"], round(measured[l.index]["at"] - take["t_start"], 3))
             for l in spoken]
    setup = episode.setups[first.setup]
    prompt = ro.build(shots, take["placed"], lines, at, take["frames"], faces, physicals(book),
                      setup.described, narrator_of(episode.lines), ends=end_numbers(segs, ends), setup=setup,
                      refs=len(refs), fps=FPS, props=props, panel=panel is not None, pin=PIN_PANEL,
                      **staged_facts(sizes, FROM_REFS, faces, panel=panel is not None))
    return {"index": first.index, "shots": take["shots"], "section": first.section, "setup": first.setup,
            "lane": "dialogue" if spoken else "narration", "workflow": BASE + " + anchors",
            "model": "MiniMax-H3 ref2va + Ref2V 8-step LoRA", "mode": mode_said(FROM_REFS),
            "refs": [ref_name(book, p) for p in refs], "faces": faces, "ref_image_size": REF_IMAGE_SIZE,
            "anchors": anchors, "audio": [(p.name, a) for p, a in voice] or "silence",
            "width": W, "height": H, "fps": FPS, "placed_seconds": take["seconds"], "frames": take["frames"],
            "seconds": round(take["frames"] / FPS, 2), "steps": STEPS,
            "seed": SEED_BASE + number * 1000 + first.index + 7919 * first.take, "prompt": prompt}


def reference_strip(boards: Path, episode: Episode, shots: list) -> Path:
    """The take's own storyboard: its cells from the sequence board side by
    side, then its END frames.  No neighbour cells.  Free (no drawing)."""
    from studio import episode_strip_ref
    from PIL import Image

    segs = [seg for s in shots for seg in [(s.index, 0)] + [(s.index, k) for k in range(1, len(s.cuts) + 1)]]
    # The strip is the take's own cells only.  MEASURED 2026-09-11: the picture that leaked into
    # take 1 was the PLATE (0.88 / 0.996), not a strip neighbour (0.16) -- the plate leaks because the
    # prompt declares the room "appears in [Shot 2]" and the narration lips sentence spans the cut.
    # Own cells only is still right: each pinned cell needs its own <Picture N> at full resolution.
    window = segs
    panels = [Image.open(sq.cells_in(boards) / sq.cell_name(a, b)).convert("RGB") for a, b in window]
    ends = end_cells(sq.cells_in(boards), segs, seg_sizes(shots), seg_motions(shots))  # the take's own END frames, after its panels
    panels += [Image.open(sq.cells_in(boards) / sq.cell_name(a, b, end=True)).convert("RGB") for a, b in ends]
    out = boards / f"ref_take_{shots[0].index:02d}.png"
    episode_strip_ref.compose(panels).save(out)
    return out


NO_ENDS = True
"""THE OWNER'S RULE, 2026-09-16: the ref2v workflow pins NO last frame. A take is
given its first frame and the arrival is said in WORDS
(`episode_ref_official.arrival_clause`), never as a second picture.

WHY, and what a last-frame pin actually does (`docs/calibration/end_frames.md`
section 2, and measured again on episode 8 as delivered):

    the model moves to the END picture as fast as the distance allows,
    then holds it until the pin.

So the pin has no good setting. A near-copy END (sim ~ 0.9) freezes the segment;
a far END glides -- and the glide is WHATEVER separates the two pictures, so when
what separates them is the background, the background dissolves. That is the
warping the owner saw, and it is not a bug to be gated: it is what the pin does.

Episode 8 is the measurement that settled it. All 15 END-pinned takes were on a
travelling camera; 7 of the 15 had START/END pictures FARTHER apart than the 0.45
re-staging floor (Q15_0 at 0.041 -- the two pictures share nothing), admitted only
because `sq.reaches` drops that floor for a camera told to move. 7 of the 15 then
froze 0.8-2.1 s before their pin, against 3 of the 13 unpinned takes.

This was `False` for eight episodes because the experiment that would have set it
was ordered on 2026-09-13 and never run. `--ends` puts the pins back for a
comparison; nothing in the pipeline asks for them."""


def seg_sizes(shots: list) -> list[str]:
    """Every segment's size, in SEGMENT order: each shot followed by its own cuts.

    `card` also builds a flat `sizes` list -- every shot, then every cut -- for
    `places_the_plate`, which only counts them.  The two orders agree while a
    take holds one shot and disagree the moment one holds two, so anything that
    needs a size FOR a segment asks here."""
    return [size for s in shots for size in [s.size] + [c.size for c in s.cuts]]


def seg_motions(shots: list[Shot]) -> list[str]:
    """Every segment's own motion, in the same flat order as `seg_sizes`.

    `reaches` needs it to know whether the camera TRAVELS, and the two lists are
    walked together, so they are built the same way for the reason `seg_sizes`
    gives: the orders agree while a take holds one shot and disagree the moment
    one holds two."""
    return [said for s in shots for said in [s.motion] + [c.motion for c in s.cuts]]


def end_cells(cells: Path, segs: list[tuple[int, int]], sizes: list[str] | None = None,
              motions: list[str] | None = None) -> list[tuple[int, int]]:
    """The (shot, sub) segments of a take with an END frame ONE CAMERA MOVE AWAY.

    An END frame on disk is not enough. MEASURED on episode 2: 9 of the 13 drawn
    END cells are re-staged to a different camera setup (`sq.reaches`), and the
    take is then sent toward a picture no simple move can travel to -- which is
    every one of the episode's seven hard drift failures. The sheet gate is where
    a re-staged END pair belongs; here it is simply not a destination.

    AND WITH THE MOTION. `reaches` drops the 0.45 re-staging floor for a shot
    whose camera TRAVELS -- a camera told to move cannot be judged by how far it
    moved -- and this call omitted it, so the floor came back at the one place
    that decides whether a take is GIVEN its END cell. The drawing side of that
    fix landed and the spending side did not. MEASURED on episode 7: Q11_0E,
    Q14_0E and Q24_0E were drawn on paid sheets, passed the sheet gate, were
    looked at by eye and found correct, and were withheld here in silence.
    Three of six."""
    if NO_ENDS:
        return []
    sizes = sizes or [""] * len(segs)
    saids = motions or [""] * len(segs)
    return [(a, b) for (a, b), size, said in zip(segs, sizes, saids)
            if sq.reaches(cells / sq.cell_name(a, b), cells / sq.cell_name(a, b, end=True),
                          size, said)]


def end_numbers(segs: list[tuple[int, int]], ends: list[tuple[int, int]]) -> list[int]:
    """1-based [Shot N] numbers, within the take, of the segments with END frames."""
    return [segs.index(e) + 1 for e in ends]


def cards(book: Path, episode: Episode, number: int) -> list[dict]:
    placed = episode_home.load_placed(book, number, episode)   # refused when stale
    shots = [dict(s, setup=episode.shot(s["index"]).setup) for s in placed["shots"]]
    measured = {l["index"]: l for l in placed["lines"]}
    for l in episode_home.read_json(episode_home.lines_dir(book, number) / "lines.json"):
        measured[l["index"]]["rel_path"] = l["rel_path"]
    out, refused = [], []
    for take in tk.takes(shots):
        take["placed"] = shots
        try:
            out.append(named_card(lambda: card(book, episode, number, take, measured), take))
        except SystemExit as e:
            refused.append(str(e))
    if refused:  # every refusal at once: one dry build, not one per fault (ep13 took three)
        raise SystemExit("take prompts refused:\n  " + "\n  ".join(refused))
    return out


def named_card(build, take: dict) -> dict:
    """The card, or the lint's refusal led by the take it belongs to: every
    single-shot take's own shot is [Shot 1], so the lint alone names none (ep13)."""
    try:
        return build()
    except ValueError as e:
        raise SystemExit(f"T{take['shots'][0]:02d} (shots {take['shots']}): {e}") from e


def drop_second_slot(graph: dict, base: str) -> dict:
    """A take with ONE reference stages one picture, not the same one twice.

    The template wires LoadImage 19 into `ref_images.ref_image_1`. Episode 3's
    T15 is a single insert on a blood smear -- no readable face, and no cell wide
    enough to place a plate against -- so its whole reference list is one cell.
    Repeating that cell in the second slot would run, and would tell the model
    two pictures where the prompt defines `<Picture 1>` alone."""
    wired = graph[base]["inputs"].pop("ref_images.ref_image_1", None)
    if wired:
        graph.pop(wired[0], None)
    return graph


def ref_paths(c: dict, book: Path, number: int) -> list[Path]:
    """The reference pictures this card stages, in slot order."""
    boards = episode_home.boards_dir(book, number)
    return [sq.picture_path(boards, book, n) for n in c["refs"]]


def card_pictures(c: dict, book: Path, number: int) -> list[Path]:
    """EVERY picture this card stages: its references and its anchor cells. The
    renderer and the currency check both read this, so a take is current only
    to the bytes it would be rendered from (audit 2026-09-22, item 10)."""
    boards = episode_home.boards_dir(book, number)
    return ref_paths(c, book, number) + [sq.cells_in(boards) / name for name, _ in c["anchors"]]


def graph_for(c: dict, book: Path, number: int, take_dir: Path, base: str = "") -> dict:
    boards = episode_home.boards_dir(book, number)
    template, inject = load_workflow(base or BASE)
    values = {"prompt": c["prompt"], "width": W, "height": H, "frames": c["frames"], "steps": STEPS,
              "seed": c["seed"], "ref_image_size": c["ref_image_size"],
              "filename_prefix": f"ep_take_{c['index']:02d}"}
    paths = ref_paths(c, book, number)
    # (a setup variant is named char-<who>_<setup>.png and lives beside the plain sheet)
    # the strip must be the LAST picture slot: the prompt numbers it after the cast, the plate,
    # the pinned cells and the END cells (reference_list IS that order)
    values["ref_image_1"] = stage_image(paths[0])
    values["ref_image_2"] = stage_image(paths[1] if len(paths) > 1 else paths[0])
    graph = apply_inject(template, inject, values)
    base = next(k for k, n in graph.items() if n["class_type"] == "MiniMaxH3ReferenceToVideo")
    if len(paths) == 1:
        drop_second_slot(graph, base)
    for k, path in enumerate(paths[2:], start=2):
        node = h3_anchors.next_id(graph)  # a node id is not always a number: `lora_second`
        graph[node] = {"class_type": "LoadImage", "inputs": {"image": stage_image(path), "upload": "image"},
                       "_meta": {"title": f"ref_image_{k + 1}"}}
        graph[base]["inputs"][f"ref_images.ref_image_{k}"] = [node, 0]
    anchors = [(stage_image(sq.cells_in(boards) / name), frame) for name, frame in c["anchors"]]
    if c["audio"] == "silence":
        wav = composite([], c["seconds"], take_dir / f"silence_{c['index']:02d}.wav")
        audio = (stage_image(wav), 0)
    else:
        lines = [(episode_home.lines_dir(book, number) / n, at) for n, at in c["audio"]]
        wav = composite(lines, c["seconds"], take_dir / f"voice_{c['index']:02d}.wav")
        audio = (stage_image(wav), 0)
    return h3_anchors.anchored(graph, anchors, audio)



def ran_for(record: dict) -> float | None:
    """Seconds ComfyUI says this prompt executed, from its own timestamps.

    Wall time from submission is a lie inside a batch: the third take's clock
    would carry the first two.  ComfyUI stamps execution_start and the end, so
    the number we report is the number the machine measured."""
    messages = record.get("status", {}).get("messages", [])
    started = next((m[1].get("timestamp") for m in messages if m[0] == "execution_start"), None)
    ended = next((m[1].get("timestamp") for m in messages
                  if m[0] in ("execution_success", "execution_error", "execution_interrupted")), None)
    return round((ended - started) / 1000, 1) if started and ended else None


def submit_all(jobs: list[tuple[dict, dict]], approved: bool = False) -> list[tuple[dict, str]]:
    """Hand ComfyUI every take BEFORE collecting any of them.

    Owner, 2026-09-12: "do all ref2v videos in one go; doing other jobs in the
    middle will do a cold load every time".  MEASURED that morning: back to
    back the takes ran 407-583 s; with another production's jobs landing
    between them the same graph took 742-998 s, because each switch evicts the
    MiniMax weights.  Submitting one and waiting for it leaves a gap after
    every take, and the gap is where the other job gets in.  Queued together
    they run consecutively and the weights are loaded once.

    Every approval is asked BEFORE the first submission, so a refusal stops the
    run rather than stranding it half-queued."""
    for c, _ in jobs:
        approval.require("render", f"take T{c['index']:02d} ({c['frames']} frames) on ComfyUI", 0.0, approved)
    return [(c, submit(graph)) for c, graph in jobs]


def collect(c: dict, prompt_id: str, out: Path) -> dict:
    """Wait for one submitted take and keep its video."""
    began = time.time()
    record = wait_record(prompt_id, timeout=TIMEOUT)
    made = outputs_of(record)
    video = next((p for p in made if p.suffix in (".mp4", ".webm")), None)
    if video is None:
        raise RuntimeError(f"take {c['index']} produced no video: {made}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(video.read_bytes())
    waited = round(time.time() - began, 1)
    return {**c, "measured_seconds": clip_seconds(out),
            "render_s": ran_for(record) if ran_for(record) is not None else waited,
            "waited_s": waited}


def collect_all(tickets: list[tuple[dict, str]], where, on_take=None) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Claim every submitted take, and let one take's misfortune cost only itself.

    T17 was interrupted at 07:13 on 2026-09-12 and the loop collecting the batch
    died with it, leaving takes 18, 20 and 22 executing on ComfyUI with nobody
    waiting for them -- three takes of GPU time rendered into nothing.  A take
    that is interrupted, errors, or times out is now recorded as lost and the
    queue behind it is still claimed; the lost ones come back named, to be
    re-rendered."""
    done, lost = [], []
    for c, prompt_id in tickets:
        try:
            record = collect(c, prompt_id, where(c))
        except Exception as raised:                    # interrupted, errored, timed out
            lost.append((c, str(raised)))
            print(f"  T{c['index']:02d} LOST: {raised}", flush=True)
            continue
        done.append(record)
        if on_take:
            on_take(c, record)
    return done, lost


def render(c: dict, graph: dict, out: Path, approved: bool = False) -> dict:
    """One take, submitted and collected on its own.  `submit_all` + `collect`
    is the way a whole run goes; this stays for a single take."""
    (_, prompt_id), = submit_all([(c, graph)], approved)
    return collect(c, prompt_id, out)


def refuse_long_shots(episode) -> None:
    """A shot longer than a take is a take nobody can render: refuse BEFORE
    spending.  `episode_takes.groups` caps a run of shots at BUDGET seconds and
    cannot split a single shot, so nothing downstream would catch it -- episode
    4's first plan put five takes at 9.4-12.25 s, the band that passed 0 of 2 in
    episode 3 at a mean of 3.75, and it took reading the take cards by hand."""
    long = episode.long_shots()
    if long:
        raise SystemExit("; ".join(f"shot {i} projects {s} s" for i, s in long)
                         + f" -- longer than a take ({tk.BUDGET} s). Split each into two "
                           "shots with two lines; a run can be split by the packer, one shot cannot")


def refuse_still_motions(episode) -> None:
    """A motion whose head names no camera move renders a photograph.

    MEASURED over 92 judged takes: every one of the 10 stillest takes in
    episodes 4-5 has a head with no camera move, and not one of the 19 takes
    whose head names one was ever penalised (Fisher one-sided p = 0.0041).  The
    camera move is the only instruction in the prompt that H3 cannot satisfy by
    rendering the pinned cell and holding.

    M9 is the owner's own note, 2026-09-14: "remove unnatural movement like
    paper turning on its own on table ... keep the movement simple".  It is the
    same fault seen from the other end -- with no camera move, the motion got
    handed to the props.

    Refused here and in `seq_boards`, so it costs nothing: before the $0.20
    sheets and before the GPU."""
    faults = [f for f in episode.still_motions() if f[1] in spec.HARD_MOTION]
    advice = [f for f in episode.still_motions() if f[1] not in spec.HARD_MOTION]
    for index, code, why in advice:
        print(f"  advisory shot {index:2d} {code}: {why}", flush=True)
    if faults:
        raise SystemExit("\n".join(f"shot {i} {c}: {w}" for i, c, w in faults)
                         + f"\n\n{len(faults)} motion(s) refused. Open every head with a "
                           "camera move -- `The camera pushes in ... across the whole shot, "
                           "travelling a forearm; <action>; <action>` -- and give every "
                           "moving object a hand.")


def opened(book_id: str, number: int):
    """The ONE road into `cards`: the book, the plan, and the canvas the plan
    declares.  Both entry points take it.

    `main` used to rebind the canvas for itself and `prompts` did not, so the
    free preview built every card at the module default -- episode 4's plan says
    1:1, the preview cards said 768x1344, the graph that ran said 768x768.  A
    preview that differs from the run by one line of setup is a different
    program, and its whole job is to be the run."""
    global W, H
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    W, H = canvas.size(episode.aspect)
    # AND THE PLACE, on the same road and for the same reason the canvas is
    # here.  Episode 8 was drawn and rendered saying "1881 London" over an
    # 1847 Utah desert: `Episode.palette` reached the location plate alone.
    house_style.adopt(episode.where, episode.light)
    house_style.adopt_look(getattr(episode, "look", ""))
    adopt_names(episode_home.read_json(book / "refs" / "refs.json").get("refs", [])
                if (book / "refs" / "refs.json").exists() else [])
    # And the plan's light and authoring floors, before any GPU second: a take
    # prompt is built from the plan, and episode 9's were built from one whose
    # first-frame prose was a quarter of ep04-08's under a colour-list style line.
    if unlit := house_style.faults(episode):
        raise SystemExit("G-LIGHT refuses the plan:\n  " + "\n  ".join(unlit))
    if thin := plan_gates.faults(episode):
        raise SystemExit("the plan fails the authoring gates:\n  " + "\n  ".join(thin))
    refuse_long_shots(episode)
    refuse_still_motions(episode)
    return book, episode


def prompts(book_id: str, number: int) -> None:
    book, episode = opened(book_id, number)
    out = episode_home.write_json(episode_home.takes_dir(book, number, "r2v") / "prompts.json",
                                  cards(book, episode, number))
    print(f"take cards -> {out}", flush=True)


def retake_list(argv: list[str]) -> list[int]:
    """The take indices `--retake=3,4,15` names; none without the flag."""
    return [int(v) for a in argv if a.startswith("--retake=") for v in a.split("=", 1)[1].split(",") if v]


def retake_why(argv: list[str]) -> str:
    """The reason `--why=<text>` carries -- the gate row or the finding the round
    answers.  The shell hands it over as one argument, spaces and all."""
    return next((a.split("=", 1)[1].strip() for a in argv if a.startswith("--why=")), "")


def retake_refusal(retake: list[int], why: str, last: bool) -> str | None:
    """ONE BATCHED RETAKE ROUND PER MASTER, WITH A WRITTEN REASON (ep10 synthesis F1).

    Episode 10 ordered ten renders in four waves as the reviews arrived; nine
    were reviewer-driven, three waves were one or two takes, each wave paid a
    ~300 s cold load and a re-cut + qc + eye cycle, and 30.8 min of GPU never
    reached the picture.  A round of ONE take as its own wave cost 14.4 min of
    wall for a 6.6 s take.  So: a retake names its reason, which run.py stamps
    into the clock note, and a round of one take is refused unless the caller
    declares it the last (`--last`) -- after the take review AND the owner's
    read are both in, the retakes are ordered once."""
    if not retake:
        return None
    if not why:
        return "a retake names its reason: --why=<the gate row or finding it answers>"
    if len(retake) == 1 and not last:
        return (f"a round of one take (T{retake[0]:02d}) is refused: batch every retake the "
                "review and the owner's read call for into one round, or pass --last to "
                "declare this the last round for this master")
    return None


def mark_retake(c: dict, tries: int, why: str) -> None:
    """A retaken card: a fresh seed, its try count, and the reason that ordered
    it -- `retake_why` rides into the take's record beside the render numbers."""
    c["seed"] += 101 * tries
    c["tries"] = tries
    c["retake_why"] = why


def refuse_stale_cells(boards: Path) -> None:
    """NO CELL FROM AN OLDER NUMBERING.  A cell is named by shot index, so a plan
    that gains or loses a shot re-points every name after it at a different
    picture.  Episode 8 gained five and three takes were then aimed at other
    shots' END panels -- which reads, in the DQ, exactly like a renderer that
    could not reach its mark.  Free to check, and it runs before the first GPU
    second: the cost of being wrong is a whole episode of takes.

    FROM_REFS stages no cell at all, so no cell on disk -- current or stale --
    can reach the render, and an old one is not a reason to refuse the run."""
    if FROM_REFS:
        return
    if left := sq.stale_cells(boards):
        raise SystemExit(
            "these cells belong to an older numbering of the plan; no sheet drawn for "
            "the current one claims them:\n  " + "\n  ".join(left)
            + "\nRedraw the boards, or move them out of boards/cells/ first.")


def refuse_failed_panels(book: Path, number: int, episode: Episode) -> None:
    """No take is rendered from a panel the panel gate failed, never judged, or
    judged before it was redrawn (audit 2026-09-22, item 5: this runner never
    read panel_dq.json, so a failed panel went straight to the GPU).

    An episode with no storyboard panels at all is refs-only, and has none to
    judge."""
    home = episode_home.home(book, number) / "storyboard"
    panels = sorted(home.glob("shot_*.png"))
    if not panels and not (home / "h3").is_dir():
        return
    wanted = [s.index for s in episode.shots]
    # BOTH panel gates: the statistics (panel_check) and what is actually IN
    # the picture (panel_content_check). Same row shape, same refusal.
    for verdict, runner in (("panel_dq.json", "panel_check.py"),
                            ("panel_content.json", "panel_content_check.py")):
        if why := panel_dq.panel_refusal(home / verdict, panels, wanted):
            raise SystemExit(f"takes refused ({verdict}): {why}\n  run: uv run python "
                             f"scripts/episode/{runner} <book> {number}")


def main(book_id: str, number: int, retake: list[int] | None = None, approved: bool = False,
         why: str = "") -> None:
    """Render every take that has no record yet; `retake` re-renders those
    indices with a fresh seed (the failed file is kept as T<NN>_failN.mp4)
    and `why` -- the reason the round was ordered -- goes into each record."""
    book, episode = opened(book_id, number)
    refuse_stale_cells(episode_home.boards_dir(book, number))
    refuse_failed_panels(book, number, episode)
    take_dir = episode_home.takes_dir(book, number, "r2v")
    sheet = take_dir / "shots.json"
    records = {r["index"]: r for r in episode_home.read_json(sheet)} if sheet.exists() else {}
    # NO LAST FRAME, CHECKED ON THE BUILT PROMPT (owner, 2026-09-16). `NO_ENDS` and
    # the L11 lint both already say this; so did the skill, twice, while 15 pins
    # shipped in episode 8 through an artefact nobody was reading. A rule broken
    # that way is checked on the thing that goes to the GPU, not on the flag.
    built = cards(book, episode, number)
    if pinned := no_last_frame.take_faults(built):
        raise SystemExit(
            "a last frame reached the take prompts, which warps the render "
            "(docs/calibration/end_frames.md):\n  "
            + "\n  ".join(f"T{i:02d}: {'; '.join(said)}" for i, said in sorted(pinned.items())))
    # Every graph is built first and the whole run is queued in one go, so the
    # takes execute consecutively and the weights load once (owner, 2026-09-12).
    jobs, wheres = [], {}
    for c in built:
        out = take_dir / f"T{c['index']:02d}.mp4"
        if retake and c["index"] in retake:
            if out.exists():
                out.rename(episode_home.next_fail(take_dir, c["index"]))
            mark_retake(c, records.get(c["index"], {}).get("tries", 0) + 1, why)
        # NOT the shot grouping alone.  MEASURED 2026-09-20 on ep05: a reviewer pass
        # rewrote seven shots and the prop filter dropped a dome from the rest, so all
        # 28 prompts changed while the grouping did not -- every take would have been
        # kept, the fix reaching no picture while DQ repeated the old numbers.
        elif (c["index"] in records and records[c["index"]].get("shots") == c["shots"]
              and take_currency.is_current(c.get("prompt") or "", out,
                                           pictures=card_pictures(c, book, number))):
            continue
        graph = graph_for(c, book, number, take_dir)
        episode_home.write_json(out.with_suffix(".graph.json"), graph)  # the exact graph this take ran with
        jobs.append((c, graph))
        wheres[c["index"]] = out
    if jobs:
        print(f"  queueing {len(jobs)} takes in one go: "
              f"{', '.join('T%02d' % c['index'] for c, _ in jobs)}", flush=True)
    def keep(c: dict, record: dict) -> None:
        record["rel_path"] = episode_home.relative(book, wheres[c["index"]])
        records[c["index"]] = record
        episode_home.write_json(sheet, [records[k] for k in sorted(records)])
        print(f"  T{c['index']:02d} shots {c['shots']} {c['frames']:3}f {record['measured_seconds']:.2f}s "
              f"in {record['render_s']:.0f}s", flush=True)

    _, lost = collect_all(submit_all(jobs, approved), lambda c: wheres[c["index"]], keep)
    print(f"{len(records)} takes -> {sheet}", flush=True)
    if lost:
        # named, not swallowed: the run is incomplete and the next command has to know
        raise SystemExit(f"{len(lost)} takes were lost and need re-rendering: "
                         f"--retake={','.join(str(c['index']) for c, _ in lost)}")


def _set_no_ends(argv: list[str]) -> None:
    """`--ends` is the only way back to last-frame pinning, and it is a control,
    not an option: see `NO_ENDS`. `--no-ends` still parses so an older command
    line means what it always meant."""
    global NO_ENDS
    NO_ENDS = "--ends" not in argv


def _set_pin_panel(argv: list[str]) -> None:
    """`--no-pin` stages the panel as a weak_reference instead of a first frame."""
    global PIN_PANEL
    PIN_PANEL = "--no-pin" not in argv


def _set_from_refs(argv: list[str]) -> None:
    """`--from-refs` is the only way into the no-cell mode: see `FROM_REFS`."""
    global FROM_REFS
    FROM_REFS = "--from-refs" in argv


if __name__ == "__main__":
    _set_no_ends(sys.argv)
    _set_from_refs(sys.argv)
    _set_pin_panel(sys.argv)
    number = episode_arg(sys.argv)
    retake, why = retake_list(sys.argv), retake_why(sys.argv)
    if refused := retake_refusal(retake, why, "--last" in sys.argv):
        raise SystemExit(refused)
    if "--prompts" in sys.argv:
        prompts(sys.argv[1], number)
    else:
        main(sys.argv[1], number, retake, approval.approved_for("render", sys.argv), why)
