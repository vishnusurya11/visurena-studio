#!/usr/bin/env python
"""ENGINE r2v, take-based: a take is a run of consecutive shots (<= 12 s, one
setup); every shot's panel is anchored at its start frame, the next take's
first panel at the last frame; the cast sheets go in ONLY for faces the take
shows readable; the plate is a reference only when the take has a wide enough
cell to place it against; a dialogue line's wav is anchored at its own frame,
otherwise silence.

    uv run python scripts/episode/takes_r2v.py <codex_id> <episode>            # render
    uv run python scripts/episode/takes_r2v.py <codex_id> <episode> --prompts  # cards only

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

from studio import approval, canvas, episode_board as board, episode_home, episode_ref_official as ro, episode_ref_prompt as rp
from studio import episode_seq_board as sq
from studio import episode_takes as tk
from studio import h3_anchors
from studio.comfy import apply_inject, load_workflow, stage_image, submit, wait_record, outputs_of
from studio.episode_spec import Episode
from studio.trailer_assemble import clip_seconds
from studio.trailer_refs import contract_description

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


def card(book: Path, episode: Episode, number: int, take: dict, measured: dict) -> dict:
    shots = [episode.shot(i) for i in take["shots"]]
    first = shots[0]
    boards = episode_home.boards_dir(book, number)
    faces = faces_of(shots, sorted(physicals(book)))
    sheet = reference_strip(boards, episode, shots)
    segs = [(s.index, k) for s in shots for k in range(0, len(s.cuts) + 1)]
    sizes = [s.size for s in shots] + [c.size for s in shots for c in s.cuts]
    ends = end_cells(sq.cells_in(boards), segs, seg_sizes(shots))
    refs = reference_list(book, boards, faces, first.setup, segs, ends, sheet,
                          episode.setups[first.setup].state, sizes)
    lines = [l for l in episode.lines if l.shot in take["shots"]]
    at = {l.index: (measured[l.index]["at"], measured[l.index]["seconds"]) for l in lines}
    spoken = [l for l in lines if l.kind == "dialogue"]
    # OWNER 2026-09-11 06:00: only DIALOGUE goes into a take's audio.  Anchored narration made the
    # face on screen mouth the narrator's words (Stamford at the introduction) despite the
    # "lips remain closed" sentence; narration is laid on the master, never in the take.
    voice = [(book / measured[l.index]["rel_path"], round(measured[l.index]["at"] - take["t_start"], 3))
             for l in spoken]
    by = {s["index"]: s for s in take["placed"]}
    anchors = []
    for s in shots:
        t0 = by[s.index]["t_start"] - take["t_start"]
        anchors.append((sq.cell_name(s.index, 0), on_grid(round(t0 * FPS))))
        for k, cut in enumerate(s.cuts, start=1):
            anchors.append((sq.cell_name(s.index, k), on_grid(round((t0 + cut.at_s) * FPS))))
    for name, _ in anchors:
        if not (sq.cells_in(boards) / name).exists():
            raise SystemExit(f"take {first.index:02d}: sequence cell {name} missing: run seq_boards.py first")
    # MEASURED 2026-09-11 (task force, 71 segments): any end pin, the start cell again or a drawn END
    # cell, is reached within ~1 s and then HELD (65 % / 59 % frozen vs 30 % start-only).  A pin is a
    # soft conditioning row at its time, so two pins say "nothing changes".  Every cell is pinned ONCE,
    # at its start; the next start pin closes the segment; END cells stay in the strip and the prompt.
    if len({n for n, _ in anchors}) != len(anchors):
        raise SystemExit(f"take {first.index:02d}: a cell is pinned twice: {anchors}")
    setup = episode.setups[first.setup]
    prompt = ro.build(shots, take["placed"], lines, at, take["frames"], faces, physicals(book),
                      setup.described, NARRATOR, ends=end_numbers(segs, ends), setup=setup,
                      refs=len(refs), fps=FPS, has_plate=sq.places_the_plate(sizes))
    return {"index": first.index, "shots": take["shots"], "section": first.section, "setup": first.setup,
            "lane": "dialogue" if spoken else "narration", "workflow": BASE + " + anchors",
            "model": "MiniMax-H3 ref2va + Ref2V 8-step LoRA", "mode": "reference-to-video: a cast sheet for "
            "every face the take shows + the plate as a DEFINITION when the take has a wide cell to place it "
            "against + one <Picture N> per pinned cell + the "
            "END cells + the take's own storyboard strip as a weak_reference; each cell pinned once at its "
            "start frame; the dialogue wavs at their offsets anchored at frame 0",
            "refs": [p.name for p in refs], "faces": faces, "ref_image_size": REF_IMAGE_SIZE,
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
    ends = end_cells(sq.cells_in(boards), segs, seg_sizes(shots))  # the take's own END frames, after its panels
    panels += [Image.open(sq.cells_in(boards) / sq.cell_name(a, b, end=True)).convert("RGB") for a, b in ends]
    out = boards / f"ref_take_{shots[0].index:02d}.png"
    episode_strip_ref.compose(panels).save(out)
    return out


NO_ENDS = False
"""THE EXPERIMENT, owner 2026-09-13: render every take with NO END picture and
the arrival said in words instead (`episode_ref_official.arrival_clause`), then
compare against the same episode rendered with them.  A flag, not a deletion, so
the control stays reproducible and the change is one line to undo."""


def seg_sizes(shots: list) -> list[str]:
    """Every segment's size, in SEGMENT order: each shot followed by its own cuts.

    `card` also builds a flat `sizes` list -- every shot, then every cut -- for
    `places_the_plate`, which only counts them.  The two orders agree while a
    take holds one shot and disagree the moment one holds two, so anything that
    needs a size FOR a segment asks here."""
    return [size for s in shots for size in [s.size] + [c.size for c in s.cuts]]


def end_cells(cells: Path, segs: list[tuple[int, int]], sizes: list[str] | None = None) -> list[tuple[int, int]]:
    """The (shot, sub) segments of a take with an END frame ONE CAMERA MOVE AWAY.

    An END frame on disk is not enough. MEASURED on episode 2: 9 of the 13 drawn
    END cells are re-staged to a different camera setup (`sq.reaches`), and the
    take is then sent toward a picture no simple move can travel to -- which is
    every one of the episode's seven hard drift failures. The sheet gate is where
    a re-staged END pair belongs; here it is simply not a destination."""
    if NO_ENDS:
        return []
    sizes = sizes or [""] * len(segs)
    return [(a, b) for (a, b), size in zip(segs, sizes)
            if sq.reaches(cells / sq.cell_name(a, b), cells / sq.cell_name(a, b, end=True), size)]


def end_numbers(segs: list[tuple[int, int]], ends: list[tuple[int, int]]) -> list[int]:
    """1-based [Shot N] numbers, within the take, of the segments with END frames."""
    return [segs.index(e) + 1 for e in ends]


def cards(book: Path, episode: Episode, number: int) -> list[dict]:
    placed = episode_home.read_json(episode_home.home(book, number) / "placed.json")
    shots = [dict(s, setup=episode.shot(s["index"]).setup) for s in placed["shots"]]
    measured = {l["index"]: l for l in placed["lines"]}
    for l in episode_home.read_json(episode_home.lines_dir(book, number) / "lines.json"):
        measured[l["index"]]["rel_path"] = l["rel_path"]
    out = []
    for take in tk.takes(shots):
        take["placed"] = shots
        out.append(card(book, episode, number, take, measured))
    return out


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


def graph_for(c: dict, book: Path, number: int, take_dir: Path, base: str = "") -> dict:
    boards = episode_home.boards_dir(book, number)
    template, inject = load_workflow(base or BASE)
    values = {"prompt": c["prompt"], "width": W, "height": H, "frames": c["frames"], "steps": STEPS,
              "seed": c["seed"], "ref_image_size": c["ref_image_size"],
              "filename_prefix": f"ep_take_{c['index']:02d}"}
    paths = [sq.picture_path(boards, book, n) for n in c["refs"]]
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
        node = str(max(int(x) for x in graph) + 1)
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


def next_fail(take_dir: Path, index: int) -> Path:
    """The next FREE `T<NN>_failN.mp4`, read off disk rather than from a counter.

    The retake stage crashed with FileExistsError at 07:37 on 2026-09-12 renaming
    T02.mp4 to T02_fail1.mp4, because T02_fail1.mp4 was already there from an
    earlier retake: the name came from `tries` in the record, which a re-run does
    not know about.  Disk knows.  `take_dq.next_fail` has always done it this way;
    the renderer had its own, worse, copy of the idea."""
    used = [int(p.stem.rsplit("_fail", 1)[1]) for p in take_dir.glob(f"T{index:02d}_fail*.mp4")
            if p.stem.rsplit("_fail", 1)[1].isdigit()]
    return take_dir / f"T{index:02d}_fail{max(used, default=0) + 1}.mp4"


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
    refuse_long_shots(episode)
    return book, episode


def prompts(book_id: str, number: int) -> None:
    book, episode = opened(book_id, number)
    out = episode_home.write_json(episode_home.takes_dir(book, number, "r2v") / "prompts.json",
                                  cards(book, episode, number))
    print(f"take cards -> {out}", flush=True)


def main(book_id: str, number: int, retake: list[int] | None = None, approved: bool = False) -> None:
    """Render every take that has no record yet; `retake` re-renders those
    indices with a fresh seed (the failed file is kept as T<NN>_failN.mp4)."""
    book, episode = opened(book_id, number)
    take_dir = episode_home.takes_dir(book, number, "r2v")
    sheet = take_dir / "shots.json"
    records = {r["index"]: r for r in episode_home.read_json(sheet)} if sheet.exists() else {}
    # Every graph is built first and the whole run is queued in one go, so the
    # takes execute consecutively and the weights load once (owner, 2026-09-12).
    jobs, wheres = [], {}
    for c in cards(book, episode, number):
        out = take_dir / f"T{c['index']:02d}.mp4"
        if retake and c["index"] in retake:
            tries = records.get(c["index"], {}).get("tries", 0) + 1
            if out.exists():
                out.rename(next_fail(take_dir, c["index"]))
            c["seed"] += 101 * tries
            c["tries"] = tries
        elif c["index"] in records and records[c["index"]].get("shots") == c["shots"] and out.exists():
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
    global NO_ENDS
    NO_ENDS = "--no-ends" in argv


if __name__ == "__main__":
    _set_no_ends(sys.argv)
    number = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1
    retake = [int(v) for a in sys.argv if a.startswith("--retake=") for v in a.split("=", 1)[1].split(",") if v]
    if "--prompts" in sys.argv:
        prompts(sys.argv[1], number)
    else:
        main(sys.argv[1], number, retake, approval.approved_for("render", sys.argv))
