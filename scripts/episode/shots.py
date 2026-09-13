#!/usr/bin/env python
"""Animate every storyboard panel into its take, in one resident H3 round.

    uv run python scripts/episode/shots.py <codex_id> <episode>            # render
    uv run python scripts/episode/shots.py <codex_id> <episode> --prompts  # run cards only
    uv run python scripts/episode/shots.py <codex_id> <episode> --engine=r2v  # the ref2va hybrid, into shots_r2v/

Each shot's panel (`frames/SNN.png`) is the take's first frame, image-to-video.
The panel carries identity and the room; H3 is asked only to animate it.
Measured: a pinned first frame has no head leak, and first-last-frame between
two panels is a morph, so every take is i2v from its own panel and the cut
starts at 0.  Seconds are MEASURED from the file afterwards.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import canvas, episode_board as board, episode_home
from studio import episode_ref_prompt as ref_prompt
from studio import episode_take_prompt as take_prompt
from studio.comfy import run, stage_image
from studio.episode_spec import Episode, Shot
from studio.h3 import frames_for
from studio.trailer_assemble import clip_seconds
from studio.trailer_refs import contract_description

W, H = canvas.size("9:16")
"""Rebound from the plan in `main`; the plan declares the aspect."""
WORKFLOW = "video_minimax_h3_i2v_turbo"
DIALOGUE_WORKFLOW = "video_minimax_h3_i2v_turbo_speak"
"""The audio-driven H3 workflow for a speaking shot: the fl2va base with the
panel as first frame and the line's wav as an audio guide at `audio_frame_idx`
(MiniMaxH3AddGuide).  MEASURED 2026-09-10 on Watson's panel + IndexTTS2 line
(docs/analysis/research/episode-06-lipsync-h3.md): words verbatim (WER 0),
voice 0.844 against the input, mouth motion 10x higher during the line than
after it, identity and framing the panel's."""
R2V_WORKFLOW = "video_minimax_h3_r2v_turbo_anchored"
"""ENGINE r2v (owner's call, 2026-09-10): the ref2va base with the cast sheets,
the storyboard sheet and the plate as <Picture N> references, the panel
anchored at frame 0 and the line wav (silence for a narration shot) anchored
at frame 6 through MiniMaxH3AddGuide.  Every shot runs this one workflow."""
AUDIO_HEAD = HANDLE_FRAMES = 6
"""The line starts 0.25 s in (6 frames at 24 fps): the panel is mouth-closed,
so it gets a beat before the first syllable, and the timeline lays the same
wav at t_start + 0.25 on the master."""
STEPS = 8
HANDLE = 0.25
SEED_BASE = 81000
TIMEOUT = 1800.0
R2V_TIMEOUT = 7200.0
REF_IMAGE_SIZE = "match"
"""MEASURED 2026-09-10: T01 (277 f) with four refs at "max" -- the 2048x3072
storyboard sheet among them -- took 2383 s, 8.6 s/frame against 3.0 for i2v;
T00 (90 f) 477 s.  At "max" the whole episode is ~10 h.  "match" scales every
ref to the target size, so the sheet's tokens fall ~4x; the panel anchored at
frame 0 carries the identity anyway.  T00 and T01 were rendered at "max"."""
"""MEASURED 2026-09-10: the hybrid's first long take (277 f, four refs at
"max") was still rendering when the 1800 s wait expired; the job finished
on its own and was adopted by hand.  Refs ride every step, so r2v is slower
than i2v by a factor still being measured."""


def take_frames(seconds: float) -> int:
    """The legal H3 frame count covering the PLACED shot length plus a handle."""
    return frames_for(seconds + HANDLE)


def panel_of(frames_dir: Path, shot: Shot) -> Path:
    return frames_dir / f"S{shot.index:02d}.png"


def run_card(shot: Shot, episode: Episode, start: Path, seed: int, placed: dict,
             audio: Path | None = None) -> dict:
    """Everything needed to reproduce one take anywhere: the prompt and the settings."""
    lane = placed.get("lane", "narration")
    workflow = DIALOGUE_WORKFLOW if lane == "dialogue" and DIALOGUE_WORKFLOW else WORKFLOW
    return {"index": shot.index, "section": shot.section, "lane": lane, "workflow": workflow,
            "model": "MiniMax-H3", "mode": "image-to-video (Start Frame)" + (
                " + audio" if workflow == DIALOGUE_WORKFLOW and DIALOGUE_WORKFLOW else ""),
            "start_image": start.name, "audio": audio.name if audio else None,
            "width": W, "height": H, "fps": 24, "placed_seconds": placed["seconds"],
            "frames": take_frames(placed["seconds"]),
            "seconds": round(take_frames(placed["seconds"]) / 24, 2),
            "steps": STEPS, "seed": seed, "prompt": take_prompt.build(episode, shot)}


def cast_of(episode: Episode, shot: Shot) -> list[str]:
    """The faces first, then the rest of the setup's cast; two reference slots."""
    ordered = list(shot.faces) + [w for w in episode.setups[shot.setup].cast if w not in shot.faces]
    return ordered[:2]


def sheet_of(episode: Episode, shot: Shot) -> str:
    groups = board.chunks([s for s in episode.shots if s.setup == shot.setup])
    return next(f"board_{shot.setup}_{k}" for k, group in enumerate(groups) if shot in group)


def ref_images(book: Path, episode: Episode, number: int, shot: Shot) -> list[Path]:
    """<Picture 1..2> the cast sheets, <Picture 3> the storyboard sheet, <Picture 4> the plate."""
    frames_dir = episode_home.frames_dir(book, number)
    refs = [book / "refs" / "characters" / f"char-{who}.png" for who in cast_of(episode, shot)]
    return refs + [frames_dir / f"{sheet_of(episode, shot)}.png", frames_dir / f"plate_{shot.setup}.png"]


def r2v_prompt(book: Path, episode: Episode, number: int, shot: Shot, seconds: float) -> str:
    physical = {r["entity_id"]: contract_description(r.get("physical", ""))
                for r in episode_home.read_json(book / "refs" / "refs.json")["refs"]
                if r.get("kind") == "character"}
    spoken = [l for l in episode.lines_of(shot.index) if l.kind == "dialogue"]
    if spoken:
        line = spoken[0]
        measured = {r["index"]: r for r in episode_home.read_json(episode_home.lines_dir(book, number) / "lines.json")}
        body = ref_prompt.speaking_body(shot, line.speaker, line.text, measured[line.index]["seconds"], seconds)
        sound = f"{ref_prompt.name_of(line.speaker)}'s voice, close and dry, and the room's own tone; no other voice."
    else:
        body = ref_prompt.silent_body(shot, seconds)
        sound = "The room's own tone only; no voice."
    return ref_prompt.build(cast_of(episode, shot), physical, body, sound)


def r2v_card(book: Path, episode: Episode, number: int, shot: Shot, seed: int, placed: dict,
             audio: Path | None) -> dict:
    """The r2v engine's run card: the i2v card's settings, the hybrid workflow and prompt,
    the references by slot, and an audio for every shot (silence when there is no line)."""
    card = run_card(shot, episode, panel_of(episode_home.frames_dir(book, number), shot), seed, placed, audio)
    refs = ref_images(book, episode, number, shot)
    return {**card, "workflow": R2V_WORKFLOW, "lane": card["lane"], "ref_image_size": REF_IMAGE_SIZE,
            "mode": "reference-to-video + panel anchored at frame 0 + audio anchored at frame 6",
            "refs": [p.name for p in refs], "audio": audio.name if audio else f"silence_{shot.index:02d}.wav",
            "prompt": r2v_prompt(book, episode, number, shot, card["seconds"])}


def silence(seconds: float, out: Path) -> Path:
    import wave

    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(b"\x00\x00" * int(24000 * seconds))
    return out


def values_for(card: dict, start: Path, audio: Path | None = None) -> dict:
    values = {"prompt": card["prompt"], "width": card["width"], "height": card["height"],
              "frames": card["frames"], "steps": card["steps"], "seed": card["seed"],
              "start_image": stage_image(start), "filename_prefix": f"ep_shot_{card['index']:02d}"}
    if audio is not None and card["workflow"] in (DIALOGUE_WORKFLOW, R2V_WORKFLOW):
        values["audio"] = stage_image(audio)
        values["audio_frame_idx"] = AUDIO_HEAD
    if card["workflow"] == R2V_WORKFLOW:
        values["ref_image_size"] = card.get("ref_image_size", REF_IMAGE_SIZE)
        for k, name in enumerate(card["refs"], start=1):
            values[f"ref_image_{k}"] = name  # staged by the caller (refs_staged)
    return values


def render(card: dict, start: Path, out: Path, audio: Path | None = None) -> dict:
    began = time.time()
    timeout = R2V_TIMEOUT if card["workflow"] == R2V_WORKFLOW else TIMEOUT
    made = run(card["workflow"], values_for(card, start, audio), timeout=timeout)
    video = next((p for p in made if p.suffix in (".mp4", ".webm")), None)
    if video is None:
        raise RuntimeError(f"{out.stem} produced no video: {made}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(video.read_bytes())
    return {**card, "measured_seconds": clip_seconds(out),
            "render_s": round(time.time() - began, 1)}


def audio_of(book: Path, episode: Episode, number: int, shot: Shot) -> Path | None:
    """The dialogue line's wav that drives a speaking shot."""
    spoken = [l for l in episode.lines_of(shot.index) if l.kind == "dialogue"]
    return (episode_home.lines_dir(book, number) / f"l{spoken[0].index:02d}.wav") if spoken else None


def cards(book: Path, episode: Episode, number: int, engine: str = "i2v") -> list[dict]:
    frames_dir = episode_home.frames_dir(book, number)
    placed = {s["index"]: s for s in
              episode_home.read_json(episode_home.home(book, number) / "placed.json")["shots"]}
    if engine == "r2v":
        return [r2v_card(book, episode, number, shot, SEED_BASE + number * 1000 + shot.index + 7919 * shot.take,
                         placed[shot.index], audio_of(book, episode, number, shot))
                for shot in episode.shots]
    return [run_card(shot, episode, panel_of(frames_dir, shot),
                     SEED_BASE + number * 1000 + shot.index + 7919 * shot.take,
                     placed[shot.index], audio_of(book, episode, number, shot))
            for shot in episode.shots]


def audio_for(book: Path, episode: Episode, number: int, shot: Shot, card: dict, out_dir: Path) -> Path | None:
    """The wav a take is driven by: the line for a speaking shot; for the r2v
    engine a narration shot gets silence of the take's length (the guide node
    needs a file; the cut drops the take's sound anyway)."""
    line = audio_of(book, episode, number, shot)
    if line is not None or card["workflow"] != R2V_WORKFLOW:
        return line
    return silence(card["seconds"], out_dir / f"silence_{shot.index:02d}.wav")


def prompts(book_id: str, number: int, engine: str = "i2v") -> None:
    """Every take's run card, before any render, in ONE place: `<takes>/prompts.json`."""
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    out = episode_home.write_json(episode_home.takes_dir(book, number, engine) / "prompts.json",
                                  cards(book, episode, number, engine))
    print(f"{len(episode.shots)} run cards -> {out}", flush=True)


def main(book_id: str, number: int, engine: str = "i2v") -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    global W, H
    W, H = canvas.size(episode.aspect)   # the plan declares the canvas (studio/canvas.py)
    frames_dir = episode_home.frames_dir(book, number)
    out_dir = episode_home.takes_dir(book, number, engine)
    sheet = out_dir / "shots.json"
    records = {r["index"]: r for r in episode_home.read_json(sheet)} if sheet.exists() else {}
    ordered = sorted(zip(episode.shots, cards(book, episode, number, engine)),
                     key=lambda pair: (pair[1]["lane"] == "dialogue" and engine == "i2v", pair[0].index))
    for shot, card in ordered:  # one lane at a time: a lane's weights load once
        out = out_dir / f"T{shot.index:02d}.mp4"
        if shot.index in records and out.exists():
            continue
        if card["workflow"] == R2V_WORKFLOW:
            for ref in ref_images(book, episode, number, shot):
                stage_image(ref)
        record = render(card, panel_of(frames_dir, shot), out, audio_for(book, episode, number, shot, card, out_dir))
        record["rel_path"] = episode_home.relative(book, out)
        records[shot.index] = record
        episode_home.write_json(sheet, [records[k] for k in sorted(records)])
        print(f"  T{shot.index:02d} {record['frames']:3}f {record['measured_seconds']:.2f}s "
              f"in {record['render_s']:.0f}s", flush=True)
    print(f"{len(records)} takes -> {sheet}", flush=True)


if __name__ == "__main__":
    entry = prompts if "--prompts" in sys.argv else main
    entry(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1,
          episode_home.engine_arg(sys.argv))
