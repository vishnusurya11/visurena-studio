#!/usr/bin/env python
"""The content gate on rendered takes: a vision model lists what is in frames
of each take, and code judges the list against the plan. Local, $0.

    uv run python scripts/episode/take_content_check.py <book_id> <episode> [index ...]

Writes takes/r2v/T<NN>.content.json beside each take's T<NN>.dq.json. QC and
the upload read both: a take with no current content verdict has not passed
(studio/judged.py). Exits 1 on any failed or unread take, or nothing to judge.

Promoted from a session driver (audit 2026-09-22, item 4). On the way in:
- judged by the same rules as its panel: the shot's size and declared
  `extras`, the setup's crowd, the location row's `landform`, the book's
  banned list -- the driver's own lists had drifted from the panel runner's
  (it still banned "car", so a railway carriage failed);
- each frame is read ON ITS OWN: a contact sheet of three frames of one man
  read as "3 figures, 3 copies" on ten single-person takes of ep07;
- an unread take is a failure, and the frames go under the episode, not a
  session folder.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import comfy, episode_home, frames, panel_content as pc, panel_dq, take_content as tc
from studio.episode_home import episode_arg

WORKFLOW = "image_qwen3vl_caption"
SAMPLES = 3


def read_frame(path: Path, seed: int) -> pc.Seen:
    said = comfy.run_text(WORKFLOW, {"image_1": comfy.stage_image(path), "prompt": pc.ASK,
                                     "seed": seed, "max_new_tokens": 1024})
    return pc.parse(said if isinstance(said, str) else str(said))


def read_take(video: Path, seconds: float, work: Path) -> list[pc.Seen]:
    """SAMPLES frames past H3's one-second head leak, each read alone."""
    work.mkdir(parents=True, exist_ok=True)
    return [read_frame(frames.frame_at(video, at, work / f"{video.stem}_{i}.png"), seed=11 + i)
            for i, at in enumerate(frames.frame_times(seconds, SAMPLES))]


def verdict_for(book: Path, shot, setup, reads: list[pc.Seen]) -> dict:
    got = tc.take_faults(
        reads, planned=len(shot.faces or []), crowd=bool((setup.crowd or "").strip()),
        flat=pc.flat_place(book, setup.location), night=panel_dq.at_night(setup.described),
        physical=" ".join(pc_row(book, w) for w in (shot.faces or [])),
        frame=f"{shot.frame} {shot.at_rest}", banned=pc.banned_subjects(book),
        size=shot.size, extras=getattr(shot, "extras", 0))
    whole = tc.busiest(reads)
    return {"passed": not got, "faults": got, "people": whole.people,
            "lookalikes": whole.lookalikes, "hour": whole.hour, "text": whole.text}


def pc_row(book: Path, who: str) -> str:
    from studio import cast_refs
    return cast_refs.row(book, who).get("physical", "")


def judge_take(book: Path, ep, record: dict, take_dir: Path, work: Path) -> dict:
    """One take's content verdict; an unreadable frame is a failed verdict."""
    index = record["index"]
    shot = ep.shot(record["shots"][0])
    video = take_dir / f"T{index:02d}.mp4"
    try:
        reads = read_take(video, float(record.get("seconds") or 4.0), work)
    except (pc.Unreadable, ValueError) as why:
        return {"passed": False, "faults": [f"unread: {str(why)[:120]}"]}
    return verdict_for(book, shot, ep.setups[shot.setup], reads)


def main(book_id: str, number: int, only: list[int]) -> int:
    book = episode_home.book_dir(book_id)
    ep = episode_home.load_plan(book, number)
    from studio import cast_refs
    if why := cast_refs.chapter_refusal(book, number):   # this chapter's clothes (audit item 9)
        raise SystemExit(why)
    take_dir = episode_home.takes_dir(book, number, "r2v")
    records = [r for r in episode_home.read_json(take_dir / "shots.json")
               if (take_dir / f"T{r['index']:02d}.mp4").exists() and (not only or r["index"] in only)]
    if not records:
        print(f"no takes to judge under {episode_home.relative(book, take_dir)}")
        return 1
    work = episode_home.work_dir(book, number, "r2v") / "content"
    failed = []
    for record in records:
        row = judge_take(book, ep, record, take_dir, work)
        episode_home.write_json(take_dir / f"T{record['index']:02d}.content.json", row)
        print(f"  {'ok  ' if row['passed'] else 'FAIL'} T{record['index']:02d}  "
              f"{'; '.join(row['faults'])}", flush=True)
        if not row["passed"]:
            failed.append(record["index"])
    print(f"\n{len(records) - len(failed)}/{len(records)} takes clean on content; failing {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    plain = [a for a in sys.argv[1:] if not a.startswith("--")]
    raise SystemExit(main(plain[0], episode_arg(sys.argv), [int(a) for a in plain[2:] if a.isdigit()]))
