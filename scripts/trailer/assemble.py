#!/usr/bin/env python
"""Cut the trailer: shots to the measured music, title on the measured hit."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.sfx import impact, sub_drop
from studio.trailer_assemble import (card_fits, clip_seconds, concat, extract,
                                     grade_to, luma_stats, mix, segment_start,
                                     title_card_ass)
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
    # The floor is 32, not something brighter.  Measured across 50 released
    # trailers the MEDIAN frame-average luma is 28/255, with the 5th
    # percentile at 3.2 -- trailers are dark, and the picture goes to
    # near-black repeatedly.  A floor of 58 would have washed out exactly the
    # Victorian gloom these two books want.  It exists only so a batch that
    # came back almost black is lifted to somewhere legible.
    hero_mean = max(means[len(means) // 2], 32.0)
    hero_deviation = sorted(dev for _, dev in stats.values())[len(stats) // 2]
    print(f"  hero look: luma {hero_mean:.1f}/{hero_deviation:.1f} "
          f"from {len(stats)} clips spanning {means[0]:.1f}-{means[-1]:.1f}")

    seen: Counter = Counter()
    segments: list[Path] = []
    missing: list[str] = []

    # Substitute rather than refuse.  A beat whose clip never rendered used to
    # abort the whole assembly, so one failure at 4am meant no trailer at all
    # instead of a slightly less varied one.  Below a floor it still refuses,
    # because a trailer cut from two takes is not a trailer.
    have = sorted(clip.stem for clip in (out / "clips").glob("*.mp4"))
    beat_ids = [beat["beat_id"] for beat in plan["beats"]]
    if len(have) < max(4, len(beat_ids) * 0.6):
        raise SystemExit(f"REFUSED: only {len(have)} of {len(beat_ids)} beats "
                         f"rendered; too few to cut from")
    if len(have) < len(beat_ids):
        print(f"  WARNING: {len(beat_ids) - len(have)} beats have no clip; "
              f"their shots fall back to neighbouring takes")

    def source_for(beat_id: str, order: int) -> str:
        """The beat's own take, or a stand-in chosen deterministically."""
        return beat_id if beat_id in have else have[order % len(have)]

    # Resolve every shot to the take it will actually use BEFORE counting, so
    # a take standing in for several beats still spreads its segments across
    # its whole length instead of reusing one moment.
    resolved = {shot["index"]: source_for(shot["beat_id"], shot["index"])
                for shot in plan["shots"]}
    uses = Counter(resolved.values())

    for shot in plan["shots"]:
        actual = resolved[shot["index"]]
        source = out / "clips" / f"{actual}.mp4"
        if not source.exists():
            missing.append(shot["beat_id"])
            continue
        usage = seen[actual]
        seen[actual] += 1
        start = segment_start(usage, uses[actual],
                              shot["seconds"], clip_seconds(source))
        mean, deviation = stats[actual]
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
    # MEASURE the picture; do not trust the plan's arithmetic.  ffmpeg's -t
    # cannot render a fraction of a frame -- it rounds each shot UP to the next
    # whole one -- and thirty-three of those roundings accumulated to 1.28s of
    # drift, so the card cut in early and the cue's braam landed 5.13s into it
    # instead of 3.85s.  The plan said one thing and the file did another, and
    # nothing compared them.
    shots_only = concat(segments, work / "shots.mp4")
    title_at = clip_seconds(shots_only)
    planned = sum(lengths)
    drift = abs(title_at - planned)
    print(f"  picture: planned {planned:.2f}s, measured {title_at:.2f}s "
          f"(drift {drift:+.3f}s)")
    if drift > 2.0 / fps:
        raise SystemExit(f"REFUSED: delivered picture drifts {drift:.3f}s from the "
                         f"plan; the title would miss the cue's hit")
    hit_at = plan["music"].get("title_impact") or title_at
    card_seconds = max(FINAL_HOLD, (hit_at - title_at) + FINAL_HOLD)
    card = title_card_ass(plan["title"], work / "title.mp4",
                          card_seconds, width, height, fps)
    # Measure the card rather than trusting it.  The Jekyll title shipped
    # clipped off both edges -- the film's own name unreadable -- because
    # nothing ever looked at the rendered frame.
    fits, note = card_fits(card, width, height)
    if not fits:
        raise SystemExit(f"REFUSED: the title card does not fit the frame ({note})")
    print(f"  title card: {note}")
    segments.append(card)
    picture = concat(segments, work / "picture.mp4")

    music = book / plan["music"]["rel_path"]
    # The synthesised hit reinforces the cue's hit; it does not compete with it.
    cues = [(max(hit_at - 2.4, 0.0), sub_drop(work / "sub.wav")),
            (hit_at, impact(work / "hit.wav"))]
    final = out / f"TRAILER-{book.name.split('_', 1)[1]}.mp4"
    mix(picture, music, cues, final, seconds=clip_seconds(picture))
    print(f"{len(segments)} shots, card at {title_at:.1f}s holding "
          f"{card_seconds:.1f}s, cue hit at {hit_at:.1f}s -> {final}")
    return final


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
