#!/usr/bin/env python
"""The book's main title and its thumbnail: the GPU and ffmpeg half.

    uv run python scripts/episode/book_title.py <codex_id> <episodes>

Owner 2026-10-11; decision architecture/decisions/2026-10-11_book_main_title_and_thumbnail.md.
Everything lands in library/<book>/title/book/ and is made once (present = kept):

  spec.json      title + author from source/book.json; key art + sting written
  plate.png      Krea2 key art, text-free (read back; a lettered plate is redrawn)
  hero.mp4       H3 i2v push-in on the plate (a zoompan if H3 fails)
  sting.wav      ACE-Step instrumental sting (a synthesised riser + boom if it fails)
  cold/          five segments from the book's own chapter videos
  main_title.mp4 7 s, the book's square, joined to the chapters by stream copy
  thumb_plate.png, thumbnail.jpg   the 16:9 thumbnail, type set by PIL
  verdict.json   G-BOOKTITLE: what was refused, what was flagged

`book_compilation.py` calls `ensure` before it joins; nothing here uploads.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import book_title as bt  # noqa: E402
from studio import episode_home, llm  # noqa: E402
from studio.series_title import missing_lines  # noqa: E402

FONT = ROOT / "assets" / "fonts" / "bebas_neue" / "BebasNeue-Regular.ttf"
SIDE, FPS = 1536, bt.FPS
HERO_W, HERO_H = 1024, 416
TRIES = 3
STING_AT_S = bt.TIMELINE["cold_end"] / FPS
LUFS, LUFS_BAND, CONTRAST_FLOOR = -16.0, 1.0, 7.0
ENCODE = ["-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
          "-color_primaries", "bt709", "-color_trc", "iec61966-2-1", "-colorspace", "bt709", "-r", str(FPS),
          "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2"]
"""The chapter pieces' encode (`book_compilation.cut_argv`): equal, or the
concat demuxer will not join by stream copy."""


def home(book: Path) -> Path:
    out = book / "title" / "book"
    out.mkdir(parents=True, exist_ok=True)
    return out


def book_look(book: Path) -> str:
    """The series' declared look (episode 1's plan); empty is photoreal live action."""
    path = episode_home.home(book, 1) / "plan.json"
    return (episode_home.read_json(path).get("look") or "") if path.exists() else ""


def load_spec(book: Path) -> bt.BookTitleSpec:
    path = home(book) / "spec.json"
    if path.exists():
        return bt.BookTitleSpec.model_validate_json(path.read_text(encoding="utf-8"))
    source = episode_home.read_json(book / "source" / "book.json")
    play = episode_home.read_json(book / "screenplay" / "feature" / "screenplay.json")
    spec = bt.spec(source, synopsis=play.get("logline", ""), ask=llm.structured, look=book_look(book))
    if missing := bt.glyphs_missing(spec.title + spec.author + bt.PRESENTS, FONT):
        raise SystemExit(f"REFUSED: the title font has no glyph for {missing}")
    path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    return spec


def asks(image: Path, question: str) -> str:
    from studio.comfy import run_text, stage_image
    return run_text("image_qwen3vl_caption", {"prompt": question, "image_1": stage_image(image)})


def reads(image: Path) -> str:
    return asks(image, bt.READ_ASK)


def plate(out: Path, prompt: str, look: str, *, wide: bool, seed: int) -> Path:
    """Key art in the book's own look with no writing and no one drawn twice,
    read back; redrawn up to TRIES seeds."""
    from studio.comfy import run
    if out.exists():
        return out
    ask = bt.plate_request(look, wide=wide)
    for k in range(TRIES):
        made = run(ask["workflow"], {"prompt": ask["lead"] + prompt + " No text, no letters, no writing.",
                   **ask["values"], "seed": seed + k, "filename_prefix": "book_title/plate"})[0]
        said = reads(made)
        doubled = bt.doubled(asks(made, bt.PEOPLE_ASK))
        why = "lettered: " + said[:60] if bt.has_lettering(said) else "a person drawn twice" if doubled else "clean"
        print(f"  plate try {k + 1}: {why}", flush=True)
        if why == "clean":
            shutil.copyfile(made, out)
            return out
    raise SystemExit(f"REFUSED: every key-art plate came back lettered or with a person drawn twice ({TRIES} seeds)")


def hero_prompt() -> str:
    return ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) "
            "is fully referenced.\n\nintegrated_multimodal_description: [Shot 1] Cinematic main-title "
            "key art. Begin exactly from <Picture 1>. The camera pushes in slowly and steadily for the "
            "whole shot. Smoke, light and weather drift gently; nothing new enters the frame.\n\n"
            "overall_soundscape: N/A\n\nnon_diegetic_music: N/A")


def hero(book: Path, still: Path) -> Path:
    """H3 i2v push-in on the plate; a zoompan over the still if H3 fails."""
    from studio.comfy import run, stage_image
    from studio.h3 import frames_for
    out = home(book) / "hero.mp4"
    if out.exists():
        return out
    try:
        made = run("video_minimax_h3_i2v_turbo", {"prompt": hero_prompt(), "width": HERO_W, "height": HERO_H,
                   "frames": frames_for(3.6), "steps": 8, "seed": 93000, "start_image": stage_image(still),
                   "filename_prefix": "book_title/hero"}, timeout=1800)
        shutil.copyfile(next(p for p in made if p.suffix in (".mp4", ".webm")), out)
    except Exception as why:                                   # the terminal: never park
        print(f"  hero: H3 failed ({why}); zoompan over the still", flush=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(still), "-vf",
                        f"scale=3072:-2,zoompan=z='1+0.0009*on':d=90:s={HERO_W}x{HERO_H}:fps={FPS}",
                        "-frames:v", "90", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def sting(book: Path, spec: bt.BookTitleSpec) -> Path:
    """ACE-Step's instrumental sting laid with its hit on the cut to black and a
    riser under the cold open; the synthesised one if ACE-Step fails."""
    import soundfile as sf
    from studio.comfy import run
    out = home(book) / "sting.wav"
    if out.exists():
        return out
    total = bt.TIMELINE["total"] / FPS
    try:
        made = run("audio_acestep15_music", {"tags": spec.sting, "lyrics": "[inst]", "seconds": 10.0,
                   "duration": 10.0, "bpm": 90, "keyscale": "D minor", "seed": 4100, "lm_seed": 4100,
                   "filename_prefix": "book_title/sting"}, timeout=900)[0]
        sound, rate = sf.read(str(made))
        laid = bt.align_sting(sound, rate, hit_s=bt.sting_hit(sound, rate), at_s=STING_AT_S, total_s=total)
        sf.write(str(out), laid, rate)
    except Exception as why:
        print(f"  sting: ACE-Step failed ({why}); synthesised", flush=True)
        sf.write(str(out), synth_sting(), 48000)
    return out


def synth_sting(rate: int = 48000):
    """A noise riser into a low boom at STING_AT_S, 7 s, stereo."""
    import numpy as np
    t = np.arange(int(7.0 * rate)) / rate
    rng = np.random.default_rng(7)
    rise = rng.standard_normal(t.size) * np.clip(t / STING_AT_S, 0, 1) ** 3 * (t < STING_AT_S) * 0.25
    after = np.clip(t - STING_AT_S, 0, None)
    boom = (np.sin(2 * np.pi * 48 * after) + 0.5 * np.sin(2 * np.pi * 72 * after)) * np.exp(-after * 0.9) * (t >= STING_AT_S)
    mono = rise + 0.8 * boom
    return np.stack([mono, mono], axis=1) / max(1e-9, np.abs(mono).max()) * 0.9


def sharpness(video: Path, at_s: float) -> float:
    """Mean edge strength of one frame: a soft or smeared shot scores low."""
    from PIL import Image, ImageFilter, ImageStat
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1",
                          "-vf", "scale=384:-2", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    if not png:
        return 0.0
    return ImageStat.Stat(Image.open(io.BytesIO(png)).convert("L").filter(ImageFilter.FIND_EDGES)).mean[0]


def chapter_main(book: Path, n: int) -> Path:
    return book / "compilation" / "chapters" / f"ep{n:02d}_main.mp4"


def square_short(book: Path, n: int) -> bool:
    """Whether chapter n's shipped Short is square; a portrait one pads into the band."""
    from studio import book_compilation as bc
    sha = dict(bc.published(book)).get(n)
    master = bc.uploaded_master(episode_home.home(book, n) / "cut", sha) if sha else None
    return bool(master) and bt.square_source(info(master))


def cold_candidates(book: Path, episodes: int) -> list[dict]:
    out = []
    for n in range(1, episodes + 1):
        ep = episode_home.home(book, n)
        if not (ep / "placed.json").exists() or not chapter_main(book, n).exists() or not square_short(book, n):
            continue
        for c in bt.candidates(n, episode_home.read_json(ep / "plan.json"), episode_home.read_json(ep / "placed.json")):
            out.append(c | {"sharp": sharpness(chapter_main(book, n), (c["start_s"] + c["end_s"]) / 2)})
    return out


def frame_png(video: Path, at_s: float, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(out)], check=True)
    return out


SHORTLIST = 4


def check_still(book: Path, c: dict) -> Path:
    return frame_png(chapter_main(book, c["episode"]), (c["start_s"] + c["end_s"]) / 2,
                     home(book) / "cold" / f"check_ep{c['episode']:02d}_s{c['shot']:02d}.png")


def drama(book: Path, c: dict) -> int:
    """How cinematic the reader finds the shot's middle frame, 0-10."""
    from studio.comfy import run_text, stage_image
    said = run_text("image_qwen3vl_caption", {"prompt": bt.DRAMA_ASK, "image_1": stage_image(check_still(book, c))})
    print(f"  cold ep{c['episode']:02d} shot {c['shot']}: drama {bt.drama_score(said)}", flush=True)
    return bt.drama_score(said)


def clean(book: Path):
    """A candidate is clean when the reader finds no writing in its middle frame."""
    def check(c: dict) -> bool:
        return not bt.has_lettering(reads(check_still(book, c)))
    return check


def cold_open(book: Path, episodes: int) -> list[dict]:
    """Five segments, one per fifth of the book; cached in cold/picks.json."""
    (home(book) / "cold").mkdir(exist_ok=True)
    path = home(book) / "cold" / "picks.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    n = len(bt.COLD_FRAMES)
    short = bt.shortlist(cold_candidates(book, episodes), episodes=episodes, n=n, k=SHORTLIST)
    scored = [c | {"drama": drama(book, c)} for c in short]
    picks = bt.pick_segments(scored, episodes=episodes, n=n, clean=clean(book))
    path.write_text(json.dumps(picks, indent=2), encoding="utf-8")
    return picks


def cold_lengths(count: int) -> list[int]:
    """The cold open's frames spread over the segments that survived."""
    total = bt.TIMELINE["cold_end"]
    if count == len(bt.COLD_FRAMES):
        return list(bt.COLD_FRAMES)
    return [total // count + (1 if k < total % count else 0) for k in range(count)] if count else []


def band_filter() -> str:
    _, y, w, h = bt.band_box(SIDE)
    return f"scale={SIDE}:{SIDE}:force_original_aspect_ratio=increase,crop={w}:{h}:0:{y},setsar=1"


def band_pictures(book: Path, picks: list[dict], hero_mp4: Path) -> Path:
    """The band's 168 frames: cold open, black, hero -- no type, no sound."""
    _, _, w, h = bt.band_box(SIDE)
    t, args, chains = bt.TIMELINE, [], []
    for k, (c, frames) in enumerate(zip(picks, cold_lengths(len(picks)))):
        a, _ = bt.segment_window(c, frames=frames, fps=FPS)
        args += ["-ss", f"{a:.3f}", "-i", str(chapter_main(book, c["episode"]))]
        chains.append(f"[{k}:v]{band_filter()},fps={FPS},trim=end_frame={frames},setpts=PTS-STARTPTS[c{k}]")
    blank = t["presents_end"] - (sum(cold_lengths(len(picks))) if picks else 0)
    args += ["-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={FPS}", "-i", str(hero_mp4)]
    chains.append(f"[{len(picks)}:v]trim=end_frame={blank},setpts=PTS-STARTPTS[blk]")
    hero_frames = t["total"] - t["presents_end"]
    chains.append(f"[{len(picks) + 1}:v]scale=-2:{h},crop={w}:{h},fps={FPS},setsar=1,trim=end_frame={hero_frames},setpts=PTS-STARTPTS[hero]")
    joined = "".join(f"[c{k}]" for k in range(len(picks))) + "[blk][hero]"
    graph = ";".join(chains) + f";{joined}concat=n={len(picks) + 2}:v=1:a=0[v]"
    out = home(book) / "band.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", graph, "-map", "[v]",
                    "-frames:v", str(t["total"]), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def overlays(book: Path, spec: bt.BookTitleSpec) -> Path:
    folder = home(book) / "type"
    folder.mkdir(exist_ok=True)
    _, _, w, h = bt.band_box(SIDE)
    for n in range(bt.TIMELINE["total"]):
        bt.overlay_frame(spec, n, width=w, height=h, font=FONT).save(folder / f"{n:04d}.png")
    return folder


def audio_chain() -> str:
    """The laid sting cut to the title's length, faded out, levelled."""
    total = bt.TIMELINE["total"] / FPS
    return (f"[2:a]aresample=48000,apad,atrim=end={total:.4f},asetpts=PTS-STARTPTS,"
            f"afade=t=out:st={total - 0.8:.3f}:d=0.8,loudnorm=I={LUFS}:TP=-1.5:LRA=7[a]")


def level_gain(measured: float) -> float:
    """dB to the target; within 0.3 dB is left alone."""
    gain = LUFS - measured
    return 0.0 if abs(gain) <= 0.3 else round(gain, 2)


def level(out: Path) -> Path:
    """One measured gain pass: loudnorm on a 7 s sting lands -1.5 dB short."""
    if not (gain := level_gain(loudness(out))):
        return out
    fixed = out.with_name("main_title_levelled.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out), "-c:v", "copy",
                    "-af", f"volume={gain}dB,alimiter=limit=0.84:level=false",
                    *ENCODE[ENCODE.index("-c:a"):], str(fixed)], check=True)
    fixed.replace(out)
    return out


def compose(book: Path, band: Path, type_dir: Path, sting_wav: Path) -> Path:
    """Grade + grain on the band, the type over it, the band set in the square,
    the sting under it with its hit on the cut to black."""
    _, y, _, _ = bt.band_box(SIDE)
    total = bt.TIMELINE["total"]
    video = (f"[0:v]eq=saturation=0.62:contrast=1.12:gamma=0.96,noise=alls=7:allf=t[g];"
             f"[g][1:v]overlay=0:0:format=auto,pad={SIDE}:{SIDE}:0:{y}:black,"
             f"fade=t=out:st={total / FPS - 0.8:.3f}:d=0.8,format=yuv420p[v]")
    out = home(book) / "main_title.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(band), "-framerate", str(FPS), "-i", str(type_dir / "%04d.png"),
                    "-i", str(sting_wav), "-filter_complex", video + ";" + audio_chain(),
                    "-map", "[v]", "-map", "[a]", "-frames:v", str(total), *ENCODE, str(out)], check=True)
    return level(out)


def info(video: Path) -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video)], capture_output=True, text=True, errors="replace").stderr


def frames(video: Path) -> int:
    seen = subprocess.run(["ffmpeg", "-v", "quiet", "-stats", "-i", str(video), "-map", "0:v", "-f", "null", "-"],
                          capture_output=True, text=True, errors="replace")
    return int(seen.stderr.rsplit("frame=", 1)[1].split()[0])


def loudness(video: Path) -> float:
    seen = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True, errors="replace").stderr
    return float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", seen)[-1])


def title_contrast(video: Path, spec: bt.BookTitleSpec, scratch: Path) -> float:
    """White type against the median of the title box on the held frame."""
    from PIL import Image
    _, y, w, h = bt.band_box(SIDE)
    still = Image.open(frame_png(video, 6.0, scratch)).convert("L").crop((int(w * 0.14), y + h // 4, int(w * 0.86), y + 3 * h // 4))
    values = sorted(still.getdata())
    lum = lambda v: ((v / 255 + 0.055) / 1.055) ** 2.4                       # sRGB to linear, near enough
    return bt.contrast_ratio(lum(236), lum(values[len(values) // 2]))


def judge(book: Path, spec: bt.BookTitleSpec, out: Path) -> dict:
    """G-BOOKTITLE: refuse what cannot ship, flag what a person should see."""
    ref = book / "compilation" / "chapters" / "ep01_title.mp4"
    refusals, flags = [], []
    if (got := frames(out)) != bt.TIMELINE["total"]:
        refusals.append(f"{got} frames, not {bt.TIMELINE['total']}")
    if abs((lufs := loudness(out)) - LUFS) > LUFS_BAND:
        refusals.append(f"{lufs:.1f} LUFS, not {LUFS}±{LUFS_BAND}")
    if ref.exists() and bt.stream_signature(info(out)) != bt.stream_signature(info(ref)):
        refusals.append(f"streams differ from {ref.name}: {bt.stream_signature(info(out))} vs {bt.stream_signature(info(ref))}")
    if (ratio := title_contrast(out, spec, home(book) / "judge_frame.png")) < CONTRAST_FLOOR:
        refusals.append(f"title contrast {ratio:.1f}:1 under {CONTRAST_FLOOR}:1")
    lines = bt.hero_layout(spec.title, FONT, width=SIDE, height=bt.band_box(SIDE)[3])[0]
    if missing := missing_lines(lines, reads(home(book) / "judge_frame.png")):
        flags.append(f"the reader did not find {missing} on the held frame")
    verdict = {"gate": "G-BOOKTITLE", "file": episode_home.relative(book, out), "refused": refusals,
               "flagged": flags, "contrast": round(ratio, 1), "lufs": round(lufs, 1)}
    (home(book) / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    return verdict


def make_thumbnail(book: Path, spec: bt.BookTitleSpec, episodes: int) -> Path:
    """The 16:9 plate with the title on its dark left; when no thumbnail plate
    passes (Scarlet: Holmes drawn twice on three seeds), the vetted hero plate
    over a title band."""
    from PIL import Image
    try:
        still = plate(home(book) / "thumb_plate.png", spec.thumb, book_look(book), wide=False, seed=7400)
        pic = bt.thumbnail(Image.open(still), spec, episodes=episodes, font=FONT)
    except SystemExit as why:
        print(f"  thumbnail: {why}; the hero plate over a title band", flush=True)
        pic = bt.banner_thumbnail(Image.open(home(book) / "plate.png"), spec, episodes=episodes, font=FONT)
    out = home(book) / "thumbnail.jpg"
    for quality in (92, 85, 78, 70):
        pic.save(out, "JPEG", quality=quality)
        if out.stat().st_size < 2_000_000:
            break
    return out


def ensure(book: Path, episodes: int) -> tuple[Path, Path]:
    """The main title and the thumbnail, made once and judged; refuses on a
    refusal, so the book video never ships a broken title."""
    spec = load_spec(book)
    out = home(book) / "main_title.mp4"
    if not out.exists():
        still = plate(home(book) / "plate.png", spec.hero, book_look(book), wide=True, seed=7300)
        band = band_pictures(book, cold_open(book, episodes), hero(book, still))
        compose(book, band, overlays(book, spec), sting(book, spec))
    verdict = judge(book, spec, out)
    if verdict["refused"]:
        raise SystemExit(f"REFUSED: G-BOOKTITLE {verdict['refused']}")
    return out, make_thumbnail(book, spec, episodes)


if __name__ == "__main__":
    made = ensure(episode_home.book_dir(sys.argv[1]), int(sys.argv[2]))
    print("\n".join(str(p.resolve()) for p in made))
