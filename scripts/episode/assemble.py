#!/usr/bin/env python
"""Cut the takes to the plan, lay the lines and the bed, burn the captions.

    uv run python scripts/episode/assemble.py <codex_id> <episode>

The plan's shot times ARE the cut: every take is trimmed to its shot, the
segments are joined, the lines are placed at their `at` and levelled through
the trailer's mixer (`mix_with_lines`: -16 LUFS lines, bed ducked to -24
under them, master at -14 / -2 dBTP), the captions are burned in the safe
box, and a two-second end chip follows the cut to black.  Nothing here is new
sound engineering; it is the trailer's assemble stage under an episode's plan.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_gutter, episode_home
from studio.comfy import run
from studio.episode_spec import Episode
from studio.trailer_assemble import concat, extract, integrated, mix_with_lines, true_peak

W, H, FPS = 768, 1344, 24
BED_WORKFLOW = "audio_acestep15_music"
BED_TAGS = ("sparse dark ambient underscore, low sustained cello and double bass drone, "
            "distant piano notes, Victorian London, tension, cinematic, no drums, no vocals, "
            "slow, quiet, minimal")
BED_SECONDS = 100.0
END_CHIP_SECONDS = 2.0
"""Black tail after the last frame.  No text anywhere on the picture: the
owner removed captions, chip and end card (2026-09-10)."""


def bed(out: Path, seed: int, runtime: float = BED_SECONDS) -> Path:
    """A quiet instrumental bed, made once, long enough for the placed runtime."""
    seconds = float(max(BED_SECONDS, int(runtime) + 10))
    if out.exists():
        import soundfile as sf
        info = sf.info(str(out))
        if info.frames / info.samplerate >= runtime:
            return out
        out.unlink()  # too short for this runtime: make a longer one
    made = run(BED_WORKFLOW, {"tags": BED_TAGS, "lyrics": "[inst]", "seconds": seconds,
                              "duration": seconds, "bpm": 60, "keyscale": "D minor",
                              "seed": seed, "lm_seed": seed, "filename_prefix": "ep_bed"},
              timeout=900)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(made[0].read_bytes())
    return out


def guard(take: Path, seconds: float, work: Path) -> str:
    """The gutter guard's crop for one take, from its first, middle and last frame."""
    import numpy as np
    from PIL import Image

    greys = []
    for k, at in enumerate((0.0, seconds / 2, max(seconds - 0.1, 0.0))):
        png = work / f"guard_{take.stem}_{k}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(take),
                        "-frames:v", "1", str(png)], check=True)
        greys.append(np.asarray(Image.open(png).convert("L"), dtype=float))
    return episode_gutter.crop_filter(episode_gutter.box(greys), W, H)


def picture(placed: dict, takes: dict[int, Path], work: Path) -> Path:
    """Every take trimmed from its first frame to its PLACED seconds, guarded
    against the storyboard gutter, joined in order.  `work/gutter.json` says
    what was cropped where."""
    segments, guarded = [], {}
    for shot in placed["shots"]:
        crop = guard(takes[shot["index"]], shot["seconds"], work)
        if crop:
            guarded[shot["index"]] = crop
        seg = extract(takes[shot["index"]], 0.0, shot["seconds"], work / f"seg{shot['index']:02d}.mp4",
                      W, H, FPS, pre=crop)
        segments.append(seg)
    episode_home.write_json(work / "gutter.json", guarded)
    print(f"gutter guard cropped {len(guarded)} takes: {guarded}", flush=True)
    return concat(segments, work / "picture.mp4")


def tail(master: Path, title: Path | None, out: Path, work: Path) -> Path:
    """After the last frame: the book's animated title card if it exists (its
    own sound kept), then black with silence.  No text is burned anywhere."""
    black = work / "black.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={END_CHIP_SECONDS}",
                    "-f", "lavfi", "-t", str(END_CHIP_SECONDS), "-i", "anullsrc=r=48000:cl=stereo",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-c:a", "aac", "-ar", "48000",
                    "-shortest", str(black)], check=True)
    parts = [master]
    if title and title.exists():
        card = work / "title_conformed.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(title),
                        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                               f"fps={FPS},format=yuv420p",
                        "-af", "aresample=48000", "-c:v", "libx264", "-preset", "fast", "-crf", "17",
                        "-c:a", "aac", "-ar", "48000", str(card)], check=True)
        parts.append(card)
    parts.append(black)
    listing = work / "final.txt"
    listing.write_text("".join("file '" + p.as_posix() + "'\n" for p in parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", str(out)], check=True)
    return out


TARGET_LUFS, FLOOR_LUFS, TP_CEILING = -14.0, -15.5, -1.0


def final_gain(lufs: float, tp: float) -> float:
    """One last gain toward -14, never past the true-peak ceiling.

    The mixer's gain is bounded by the peak before the end chip's silence is
    appended, so the delivered file measured -15.8 LUFS with 0.7 dB of peak
    headroom left (first master, 2026-09-10).  Spend that headroom, no more."""
    if lufs >= FLOOR_LUFS:
        return 0.0
    return round(max(0.0, min(TARGET_LUFS - lufs, TP_CEILING - 0.1 - tp)), 2)


def trim(master: Path, work: Path) -> Path:
    gain = final_gain(integrated(master), true_peak(master))
    if gain <= 0:
        return master
    louder = work / "trimmed.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(master), "-c:v", "copy",
                    "-af", f"volume={gain}dB", "-c:a", "aac", "-b:a", "256k", str(louder)], check=True)
    master.write_bytes(louder.read_bytes())
    return master


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    home = episode_home.home(book, number)
    work = home / "work"
    work.mkdir(parents=True, exist_ok=True)
    takes = {r["index"]: book / r["rel_path"]
             for r in episode_home.read_json(episode_home.shots_dir(book, number) / "shots.json")}
    placed = episode_home.read_json(home / "placed.json")
    wavs = {r["index"]: book / r["rel_path"]
            for r in episode_home.read_json(episode_home.lines_dir(book, number) / "lines.json")}
    missing = [s.index for s in episode.shots if s.index not in takes]
    if missing:
        raise SystemExit(f"no take for shots {missing}")

    cut = picture(placed, takes, work)
    music = bed(home / "audio" / "bed.wav", 90000 + number, placed["duration_s"])
    mixed = mix_with_lines(cut, music, [], [(line["at"], wavs[line["index"]])
                                            for line in placed["lines"]],
                           work / "mixed.mp4", seconds=placed["duration_s"])
    card = book / "title" / f"ep{number:02d}.mp4"
    out = tail(mixed, card if card.exists() else book / "title" / "title.mp4",
               episode_home.master_path(book, number), work)
    trim(out, work)
    keep = next(n for n in range(1, 100) if not (home / f"master_iter{n}.mp4").exists())
    (home / f"master_iter{keep}.mp4").write_bytes(out.read_bytes())
    print(f"master -> {out}  (kept as master_iter{keep}.mp4)")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
