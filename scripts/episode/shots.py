#!/usr/bin/env python
"""Animate every storyboard panel into its take, in one resident H3 round.

    uv run python scripts/episode/shots.py <codex_id> <episode>            # render
    uv run python scripts/episode/shots.py <codex_id> <episode> --prompts  # run cards only

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

from studio import episode_home
from studio import episode_take_prompt as take_prompt
from studio.comfy import run, stage_image
from studio.episode_spec import Episode, Shot
from studio.h3 import frames_for
from studio.trailer_assemble import clip_seconds

W, H = 768, 1344
WORKFLOW = "video_minimax_h3_i2v_turbo"
DIALOGUE_WORKFLOW = "video_minimax_h3_i2v_turbo_speak"
"""The audio-driven H3 workflow for a speaking shot: the fl2va base with the
panel as first frame and the line's wav as an audio guide at `audio_frame_idx`
(MiniMaxH3AddGuide).  MEASURED 2026-09-10 on Watson's panel + IndexTTS2 line
(docs/analysis/research/episode-06-lipsync-h3.md): words verbatim (WER 0),
voice 0.844 against the input, mouth motion 10x higher during the line than
after it, identity and framing the panel's."""
AUDIO_HEAD = HANDLE_FRAMES = 6
"""The line starts 0.25 s in (6 frames at 24 fps): the panel is mouth-closed,
so it gets a beat before the first syllable, and the timeline lays the same
wav at t_start + 0.25 on the master."""
STEPS = 8
HANDLE = 0.25
SEED_BASE = 81000
TIMEOUT = 1800.0


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


def values_for(card: dict, start: Path, audio: Path | None = None) -> dict:
    values = {"prompt": card["prompt"], "width": card["width"], "height": card["height"],
              "frames": card["frames"], "steps": card["steps"], "seed": card["seed"],
              "start_image": stage_image(start), "filename_prefix": f"ep_shot_{card['index']:02d}"}
    if audio is not None and card["workflow"] == DIALOGUE_WORKFLOW and DIALOGUE_WORKFLOW:
        values["audio"] = stage_image(audio)
        values["audio_frame_idx"] = AUDIO_HEAD
    return values


def render(card: dict, start: Path, out: Path, audio: Path | None = None) -> dict:
    began = time.time()
    made = run(card["workflow"], values_for(card, start, audio), timeout=TIMEOUT)
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


def cards(book: Path, episode: Episode, number: int) -> list[dict]:
    frames_dir = episode_home.frames_dir(book, number)
    placed = {s["index"]: s for s in
              episode_home.read_json(episode_home.home(book, number) / "placed.json")["shots"]}
    return [run_card(shot, episode, panel_of(frames_dir, shot),
                     SEED_BASE + number * 1000 + shot.index + 7919 * shot.take,
                     placed[shot.index], audio_of(book, episode, number, shot))
            for shot in episode.shots]


def prompts(book_id: str, number: int) -> None:
    """Every take's run card, before any render, in ONE place: `shots/prompts.json`."""
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    out = episode_home.write_json(episode_home.shots_dir(book, number) / "prompts.json",
                                  cards(book, episode, number))
    print(f"{len(episode.shots)} run cards -> {out}", flush=True)


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    frames_dir = episode_home.frames_dir(book, number)
    out_dir = episode_home.shots_dir(book, number)
    sheet = out_dir / "shots.json"
    records = {r["index"]: r for r in episode_home.read_json(sheet)} if sheet.exists() else {}
    ordered = sorted(zip(episode.shots, cards(book, episode, number)),
                     key=lambda pair: (pair[1]["lane"] == "dialogue", pair[0].index))
    for shot, card in ordered:  # one lane at a time: a lane's weights load once
        out = out_dir / f"T{shot.index:02d}.mp4"
        if shot.index in records and out.exists():
            continue
        record = render(card, panel_of(frames_dir, shot), out, audio_of(book, episode, number, shot))
        record["rel_path"] = episode_home.relative(book, out)
        records[shot.index] = record
        episode_home.write_json(sheet, [records[k] for k in sorted(records)])
        print(f"  T{shot.index:02d} {record['frames']:3}f {record['measured_seconds']:.2f}s "
              f"in {record['render_s']:.0f}s", flush=True)
    print(f"{len(records)} takes -> {sheet}", flush=True)


if __name__ == "__main__":
    entry = prompts if "--prompts" in sys.argv else main
    entry(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 1)
