#!/usr/bin/env python
"""A/B: the ref2va HYBRID against the episode's i2v take, one shot at a time.

    uv run python scripts/episode/ab_ref2v.py <codex_id> <episode> <shot> [<shot> ...]

Hybrid = `video_minimax_h3_r2v_turbo_anchored`: cast sheets, the storyboard
sheet and the plate as <Picture N> references, the panel anchored at frame 0,
the line wav (or silence) anchored at frame 6.  Same frames and seed as the
i2v take.  Writes, under `episodes/epNN/work/`: `ab_ref2v_SNN.mp4`, its
values as `.json`, and `ab_SNN_strip.png` = panel | i2v start, mid, end |
hybrid start, mid, end.  For a speaking shot the hybrid's own track is
scored against the input wav.  Owner's ask, 2026-09-10.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_board as board, episode_home, episode_ref_prompt as rp
from studio.comfy import run, stage_image
from studio.episode_spec import Episode, Shot

WORKFLOW = "video_minimax_h3_r2v_turbo_anchored"
W, H, FPS, STEPS, AUDIO_HEAD = 768, 1344, 24, 8, 6


def _storyboard():
    spec = importlib.util.spec_from_file_location("ep_storyboard", ROOT / "scripts/episode/storyboard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cast_of(episode: Episode, shot: Shot) -> list[str]:
    """The speaker/faces first, then the rest of the setup's cast; two slots."""
    ordered = list(shot.faces) + [w for w in episode.setups[shot.setup].cast if w not in shot.faces]
    return ordered[:2]


def sheet_of(episode: Episode, shot: Shot) -> str:
    groups = board.chunks([s for s in episode.shots if s.setup == shot.setup])
    return next(f"board_{shot.setup}_{k}" for k, group in enumerate(groups) if shot in group)


def silence(seconds: float, out: Path) -> Path:
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(b"\x00\x00" * int(24000 * seconds))
    return out


def prompt_for(episode: Episode, shot: Shot, physical: dict, line, line_s: float, seconds: float) -> str:
    cast = cast_of(episode, shot)
    if line:
        body = rp.speaking_body(shot, line.speaker, line.text, line_s, seconds)
        sound = f"{rp.name_of(line.speaker)}'s voice, close and dry, and the room's own tone; no other voice."
    else:
        body = rp.silent_body(shot, seconds)
        sound = "The room's own tone only; no voice."
    return rp.build(cast, physical, body, sound)


def values_for(book: Path, episode: Episode, number: int, shot: Shot, record: dict,
               audio: Path, prompt: str) -> dict:
    frames_dir = episode_home.frames_dir(book, number)
    refs = [book / "refs" / "characters" / f"char-{who}.png" for who in cast_of(episode, shot)]
    refs += [frames_dir / f"{sheet_of(episode, shot)}.png", frames_dir / f"plate_{shot.setup}.png"]
    values = {"prompt": prompt, "width": W, "height": H, "frames": record["frames"], "steps": STEPS,
              "seed": record["seed"], "ref_image_size": "max",
              "start_image": stage_image(frames_dir / f"S{shot.index:02d}.png"),
              "audio": stage_image(audio), "audio_frame_idx": AUDIO_HEAD,
              "filename_prefix": f"ab_ref2v_{shot.index:02d}"}
    for k, ref in enumerate(refs, start=1):
        values[f"ref_image_{k}"] = stage_image(ref)
    return values


def still(video: Path, at: float, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(video),
                    "-frames:v", "1", str(out)], check=True)
    return out


def strip(panel: Path, a: Path, b: Path, seconds: float, work: Path, index: int) -> Path:
    sb = _storyboard()
    stills = [panel]
    for tag, video in (("i2v", a), ("hyb", b)):
        for name, at in (("start", 0.3), ("mid", seconds / 2), ("end", max(seconds - 0.1, 0))):
            stills.append(still(video, at, work / f"ab_S{index:02d}_{tag}_{name}.png"))
    return sb.contact([tuple(stills)], work / f"ab_S{index:02d}_strip.png")


def judge_voice(video: Path, wav: Path, work: Path, index: int) -> dict:
    """The hybrid's own track against the input line: similarity and words."""
    from studio import voice_ear, voice_qc

    track = work / f"ab_S{index:02d}_track.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "24000",
                    str(track)], check=True)
    return {"similarity": round(voice_ear.similarity(track, wav), 3),
            "heard": voice_qc.any_transcriber()(track)}


def one(book: Path, episode: Episode, number: int, index: int) -> dict:
    home, work = episode_home.home(book, number), episode_home.home(book, number) / "work"
    work.mkdir(exist_ok=True)
    shot = episode.shot(index)
    record = next(r for r in episode_home.read_json(home / "shots" / "shots.json") if r["index"] == index)
    placed = next(s for s in episode_home.read_json(home / "placed.json")["shots"] if s["index"] == index)
    measured = {r["index"]: r for r in episode_home.read_json(home / "lines" / "lines.json")}
    spoken = [l for l in episode.lines_of(index) if l.kind == "dialogue"]
    line = spoken[0] if spoken else None
    wav = (book / measured[line.index]["rel_path"]) if line else silence(record["seconds"], work / f"ab_silence_{index:02d}.wav")
    prompt = prompt_for(episode, shot, _storyboard().physicals(book), line,
                        measured[line.index]["seconds"] if line else 0.0, record["seconds"])
    values = values_for(book, episode, number, shot, record, wav, prompt)
    out = work / f"ab_ref2v_S{index:02d}.mp4"
    started = time.time()
    if not out.exists():
        made = run(WORKFLOW, values, timeout=3600)
        out.write_bytes(next(p for p in made if p.suffix in (".mp4", ".webm")).read_bytes())
    result = {"shot": index, "workflow": WORKFLOW, "values": values, "render_s": round(time.time() - started, 1),
              "i2v": record["rel_path"], "hybrid": str(out.relative_to(book)).replace("\\", "/")}
    result["strip"] = str(strip(episode_home.frames_dir(book, number) / f"S{index:02d}.png",
                                book / record["rel_path"], out, record["seconds"], work, index))
    if line:
        result["voice"] = judge_voice(out, wav, work, index)
    episode_home.write_json(work / f"ab_ref2v_S{index:02d}.json", result)
    print(f"shot {index}: hybrid {out} ({result['render_s']} s) strip {result['strip']} "
          f"{result.get('voice', '')}", flush=True)
    return result


def main(book_id: str, number: int, shots: list[int]) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    for index in shots:
        one(book, episode, number, index)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), [int(a) for a in sys.argv[3:]])
