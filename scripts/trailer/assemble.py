#!/usr/bin/env python
"""Cut the trailer: shots to the measured music, title on the measured hit."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.sfx import impact, sub_drop
from studio.trailer_assemble import (clip_seconds, concat, extract, grade_to,
                                     luma_stats, mix, segment_start, title_card_ass)
from studio.trailer_cut import FINAL_HOLD, is_uniform

ROOT = Path(__file__).resolve().parents[2]


def build(book_glob: str, trailer_id: str = "main") -> Path:
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    out = book / "trailer" / trailer_id
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)

    width, height, fps = plan["width"], plan["height"], plan["fps"]
    # One hero look for the whole trailer.  The prompt cannot lock exposure --
    # a verbatim grade string in every prompt still gave clips spanning
    # 42.9-96.6 luma -- so it is matched here, against a real clip rather than
    # an invented target, with a floor so a uniformly dark set gets lifted.
    stats = {clip.stem: luma_stats(clip) for clip in sorted((out / "clips").glob("*.mp4"))}
    if not stats:
        raise SystemExit(f"REFUSED: no clips rendered under {out / 'clips'}")
    means = sorted(mean for mean, _ in stats.values())
    hero_mean = max(means[len(means) // 2], 58.0)
    hero_deviation = sorted(dev for _, dev in stats.values())[len(stats) // 2]
    print(f"  hero look: luma {hero_mean:.1f}/{hero_deviation:.1f} "
          f"from {len(stats)} clips spanning {means[0]:.1f}-{means[-1]:.1f}")

    uses = Counter(shot["beat_id"] for shot in plan["shots"])
    seen: Counter = Counter()
    segments: list[Path] = []
    missing: list[str] = []

    for shot in plan["shots"]:
        source = out / "clips" / f"{shot['beat_id']}.mp4"
        if not source.exists():
            missing.append(shot["beat_id"])
            continue
        usage = seen[shot["beat_id"]]
        seen[shot["beat_id"]] += 1
        start = segment_start(usage, uses[shot["beat_id"]],
                              shot["seconds"], clip_seconds(source))
        mean, deviation = stats[shot["beat_id"]]
        segments.append(extract(source, start, shot["seconds"],
                                work / f"s{shot['index']:03d}.mp4", width, height, fps,
                                grade_to(mean, deviation, hero_mean, hero_deviation)))
    if missing:
        raise SystemExit(f"REFUSED: no clip for beats {sorted(set(missing))}")

    lengths = [s["seconds"] for s in plan["shots"]]
    if is_uniform(lengths):
        raise SystemExit("REFUSED: every shot is the same length -- the amateur tell")

    # The card must still be on screen when the cue's own hit arrives.  Cutting
    # it to a fixed hold ended the trailer 0.85s BEFORE the impact -- the same
    # defect as the previous trailer's 5.29s miss, just smaller.
    title_at = sum(lengths)
    hit_at = plan["music"].get("title_impact") or title_at
    card_seconds = max(FINAL_HOLD, (hit_at - title_at) + FINAL_HOLD)
    segments.append(title_card_ass(plan["title"], work / "title.mp4",
                                   card_seconds, width, height, fps))
    picture = concat(segments, work / "picture.mp4")

    music = book / plan["music"]["rel_path"]
    # The synthesised hit reinforces the cue's hit; it does not compete with it.
    cues = [(max(hit_at - 2.4, 0.0), sub_drop(work / "sub.wav")),
            (hit_at, impact(work / "hit.wav"))]
    final = out / f"TRAILER-{book.name.split('_', 1)[1]}.mp4"
    mix(picture, music, cues, final)
    print(f"{len(segments)} shots, card at {title_at:.1f}s holding "
          f"{card_seconds:.1f}s, cue hit at {hit_at:.1f}s -> {final}")
    return final


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
