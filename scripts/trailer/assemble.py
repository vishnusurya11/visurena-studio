#!/usr/bin/env python
"""Cut the trailer: shots to the measured music, title on the measured hit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.clip_cache import fresh
from studio.sfx import impact, riser, room_tone, sub_drop
from studio.trailer_assemble import (card_fits, clip_seconds, concat, extract,
                                     grade_to, line_windows, luma_stats,
                                     mix_with_lines, segment_start, title_card_ass)
from studio.trailer_cut import is_uniform, title_moment
from studio.trailer_stage_spec import VoiceLine

ROOT = Path(__file__).resolve().parents[2]

RISER_SECONDS = 2.5
"""How long the rise into the hard out runs (D: riser >= 2 s before the title).

`sfx.riser` was written, tested by nobody, and never called once across
eleven runs.  The stop it leads into is only a stop if something was building
towards it."""

SUB_SECONDS = 2.4
"""The sub-drop, kept where it always was -- landing ON the stop rather than
inside the silence after it, so the held breath measures as a held breath."""

IMPACT_SECONDS = 3.0
"""The hit on the card.  D asks for a tail >= 3 s, and a hit that has already
decayed is the thing run 10 shipped: the card landed at -46 LUFS."""


def designed_layer(work: Path, hard_out: float, hit: float,
                   seconds: float) -> list[tuple[float, Path]]:
    """The synthesised cues that make the button a button.

    A riser and a sub-drop that both END on the hard out, room tone across
    the silence the hard out opens, and the impact on the card.  The room
    tone is the piece run 10 had no equivalent of: its pre-title gap was
    digital silence, every sample zero, which reads as a dropped stream
    rather than as a designed one (E).
    """
    return [(max(hard_out - RISER_SECONDS, 0.0), riser(work / "riser.wav", RISER_SECONDS)),
            (max(hard_out - SUB_SECONDS, 0.0), sub_drop(work / "sub.wav", SUB_SECONDS)),
            (hard_out, room_tone(work / "room.wav", max(seconds - hard_out, 0.1))),
            (hit, impact(work / "hit.wav", IMPACT_SECONDS))]


def clips_doc(out: Path) -> dict:
    """What step 07 promoted.  Without it the cut would be guessing, and
    guessing is how run 10 cut a quarter of its picture from old renders."""
    path = out / "clips.json"
    if not path.exists():
        raise SystemExit(f"REFUSED: no clips.json under {out}; nothing says "
                         f"which takes this plan rendered")
    return json.loads(path.read_text(encoding="utf-8"))


def takes_for(plan: dict, clips: dict, book: Path) -> dict[str, Path]:
    """The clip each shot reads: its own, and only if it is THIS run's.

    A clip counts when step 07's record and the file's own sidecar agree
    (`clip_cache.fresh`).  Anything else -- never rendered, dropped, or left
    behind by an earlier plan -- refuses the cut, because the alternative
    the assembler used to take was a neighbouring take played twice.
    """
    have = set(fresh(clips, book))
    lack = sorted({s["beat_id"] for s in plan["shots"]} - have)
    if lack:
        raise SystemExit(f"REFUSED: no fresh clip for beats {lack}; re-plan "
                         f"around the takes that exist rather than reusing one")
    by_id = {c["beat_id"]: book / c["rel_path"] for c in clips["clips"]}
    return {s["beat_id"]: by_id[s["beat_id"]] for s in plan["shots"]}


def spoken_lines(plan: dict, out: Path) -> list[tuple[float, Path]]:
    """The voice step's lines at their planned windows; nothing when the step
    has not run, so a trailer built before step 05 exists is the old mix."""
    voice = out / "voice.json"
    if not voice.exists():
        return []
    lines = [VoiceLine.model_validate(v) for v in json.loads(voice.read_text(encoding="utf-8"))]
    return line_windows(plan, lines, out.parents[1])


def build(book_glob: str, trailer_id: str = "main") -> Path:
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    return build_at(book, trailer_id)


def build_at(book: Path, trailer_id: str = "main") -> Path:
    out = book / "trailer" / trailer_id
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)

    width, height, fps = plan["width"], plan["height"], plan["fps"]
    # Which take each shot reads, decided BEFORE anything is measured.  The
    # directory outlives the plan, so a rebuild that produces fewer beats
    # leaves the extra renders behind; globbing them read last plan's
    # pictures into the grade calibration and then offered them as
    # substitutes -- 24% of run 10's delivered picture.
    takes = takes_for(plan, clips_doc(out), book)
    # One hero look for the whole trailer.  The prompt cannot lock exposure --
    # a verbatim grade string in every prompt still gave clips spanning
    # 42.9-96.6 luma -- so it is matched here, against a real clip rather than
    # an invented target, with a floor so a uniformly dark set gets lifted.
    stats = {beat_id: luma_stats(clip) for beat_id, clip in sorted(takes.items())}
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

    # One take, one shot: every segment is the middle of its OWN clip, and
    # no clip is opened twice.  The old code spread a take's several uses
    # across its length, which made a reused picture less obvious without
    # making it any less a repeat.
    segments: list[Path] = []
    for shot in plan["shots"]:
        source = takes[shot["beat_id"]]
        start = segment_start(0, 1, shot["seconds"], clip_seconds(source))
        mean, deviation = stats[shot["beat_id"]]
        segments.append(extract(source, start, shot["seconds"],
                                work / f"s{shot['index']:03d}.mp4", width, height, fps,
                                grade_to(mean, deviation, hero_mean, hero_deviation)))

    lengths = [s["seconds"] for s in plan["shots"]]
    if is_uniform(lengths):
        raise SystemExit("REFUSED: every shot is the same length -- the amateur tell")

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
                         f"plan; the bed would stop somewhere the picture is not")
    # The cue's own title hit is not what the card lands on any more.  With
    # the no-reuse rule the picture usually ends BEFORE it (run 10 had
    # title_impact None on every seed of every caption), and chasing a hit
    # the cue may not have is how the card came to be held over a bed that
    # had already faded to -46 LUFS.  So the shape is made, not found: the
    # bed STOPS on the last cut, the card runs on room tone for a held
    # breath, and the synthesised impact lands on it while it is still alive.
    hard_out_at, hit_at, card_seconds = title_moment(title_at)
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
    seconds = clip_seconds(picture)

    music = book / plan["music"]["rel_path"]
    cues = designed_layer(work, hard_out_at, hit_at, seconds)
    final = out / f"TRAILER-{book.name.split('_', 1)[1]}.mp4"
    lines = spoken_lines(plan, out)
    mix_with_lines(picture, music, cues, lines, final, seconds=seconds,
                   hard_out=hard_out_at)
    print(f"{len(segments)} shots, {len(lines)} spoken line(s), bed out at "
          f"{hard_out_at:.1f}s, {hit_at - hard_out_at:.1f}s of room tone, hit at "
          f"{hit_at:.1f}s, card holding {card_seconds:.1f}s -> {final}")
    return final


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
