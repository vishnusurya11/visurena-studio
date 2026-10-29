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

A verdict is served again, unread, while the take's bytes, every row it is
judged against (`judged_row`, the asks among them), the reading engine and
GATE_VERSION are the same (package H, retro 2026-10-20); a pass of hits never
asks the engine.  GATE_VERSION is pinned to the hash of JUDGES, the import
closure of the judging code, so no judging edit reaches the key unseen.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import code_closure, comfy, episode_home, figure_who as fw, frames, panel_content as pc, panel_dq, take_content as tc
from studio.episode_home import episode_arg

WORKFLOW = "image_qwen3vl_caption"
SAMPLES = 3
ROOT = Path(__file__).resolve().parents[2]
JUDGES = tuple(sorted({"scripts/episode/take_content_check.py", "studio/frames.py",
                       *code_closure.closure(ROOT, ("studio/take_content.py", "studio/figure_who.py"))}))
"""The code a take's reads are judged by -- this script, the frames it samples and the import
closure of the judges (look_table, panel_dq, people_count came in by lazy imports; package H
skeptic) -- its hash pinned to GATE_VERSION (tests/fixtures/gate_pins.json)."""
GATE_VERSION = "6"
"""What a cached content verdict must have been judged under.  Bump it when the judging changes a
verdict on unchanged reads; a refactor or a log line re-pins the hash only.  A changed ask needs no
bump: the asks are in the key (`words_sha8`), as they are in the VL text cache."""


FRAME_READ_S = 120.0
"""One frame read's deadline (package H, retro 2026-10-20): ep01's cold pass read a take's three
frames in about 45 s, and a read waited up to 600 s.  A read past this is interrupted
(comfy.run_text), the engine freed, and asked once more; a second stall raises, as the 600 s did."""


def watched(ask):
    """`ask()`, and once more after a /free when it stalls past FRAME_READ_S."""
    try:
        return ask()
    except comfy.StillRunning as stall:
        print(f"WATCHDOG take_content: {stall}; the engine is freed and asked once more", flush=True)
        comfy.free_models()
        return ask()


def read_frame(path: Path, seed: int) -> pc.Seen:
    values = {"image_1": comfy.stage_image(path), "prompt": pc.ASK, "seed": seed, "max_new_tokens": 1024}
    said = watched(lambda: comfy.cached_text(WORKFLOW, values, readable=pc.readable, timeout=FRAME_READ_S))
    return pc.parse(said if isinstance(said, str) else str(said))


def read_take(video: Path, seconds: float, work: Path) -> list[pc.Seen]:
    """SAMPLES frames past H3's one-second head leak, each read alone."""
    work.mkdir(parents=True, exist_ok=True)
    return [read_frame(frames.frame_at(video, at, work / f"{video.stem}_{i}.png"), seed=11 + i)
            for i, at in enumerate(frames.frame_times(seconds, SAMPLES))]


def read_twin_frame(path: Path, seed: int) -> pc.Twins:
    """The G-TWIN ask on one already-extracted take frame (seed 23+i, cached)."""
    values = {"image_1": comfy.stage_image(path), "prompt": pc.TWIN_ASK, "seed": seed, "max_new_tokens": 256}
    said = watched(lambda: comfy.cached_text(WORKFLOW, values, readable=pc.twin_readable, timeout=FRAME_READ_S))
    return pc.parse_twins(said if isinstance(said, str) else str(said))


def twin_faults_for(shot, reads: list[pc.Seen], work: Path, stem: str) -> list[str]:
    """G-TWIN over the SAMPLES frames `read_take` already extracted -- zero
    extra frame extraction.  A frame whose main read saw two people gets the
    dedicated same-face-AND-same-dress ask; fewer distinct than figures is a
    fault, and an unreadable ask on these sizes is one too."""
    planned, out = len(shot.faces or []), []
    for i, seen in enumerate(reads):
        if not pc.twin_applies(planned, shot.size, seen.people):
            continue
        try:
            t = read_twin_frame(work / f"{stem}_{i}.png", seed=23 + i)
        except pc.Unreadable as why:
            out.append(f"unread: twin {str(why)[:100]}")
            continue
        if bad := pc.twin_fault(t):
            out.append(bad)
    return out


def read_who_frame(path: Path, seed: int) -> list[dict]:
    """The G-WHO ask on one already-extracted take frame (seed 31+i, cached)."""
    values = {"image_1": comfy.stage_image(path), "prompt": fw.ASK, "seed": seed, "max_new_tokens": 512}
    said = watched(lambda: comfy.cached_text(WORKFLOW, values, readable=fw.readable, timeout=FRAME_READ_S))
    return fw.parse(said if isinstance(said, str) else str(said))


def who_faults_for(shot, reads: list[pc.Seen], work: Path, stem: str, staged: dict) -> list[str]:
    """G-WHO over the frames `read_take` extracted: two figures of one frame that each read as the
    same cast member fail the take (owner 2026-10-28); an unreadable ask on these sizes is a fault."""
    planned, out = len(shot.faces or []), []
    for i, seen in enumerate(reads):
        if not fw.applies(planned, shot.size, seen.people):
            continue
        try:
            figures = read_who_frame(work / f"{stem}_{i}.png", seed=31 + i)
        except pc.Unreadable as why:
            out.append(f"unread: who {str(why)[:100]}")
            continue
        if bad := fw.fault(figures, staged):
            out.append(bad)
    return out


def with_twins(row: dict, twins: list[str]) -> dict:
    """A take's verdict row with its twin faults carried; any twin fails it."""
    if not twins:
        return row
    return {**row, "faults": list(row.get("faults") or []) + twins, "passed": False}


def judged_row(book: Path, shot, setup, panel_people: int | None = None) -> dict:
    """Every row a take's reads are judged against: the words of its verdict, and of its cache key."""
    faces = list(shot.faces or [])
    return {"planned": len(faces), "crowd": pc.crowd_declared(shot, setup),
            "flat": pc.flat_place(book, setup.location), "night": pc.judged_at_night(setup.described),
            "physical": [pc_row(book, w) for w in faces], "frame": pc.stage_text(shot, setup),
            "banned": pc.banned_subjects(book), "size": shot.size, "extras": getattr(shot, "extras", 0),
            "markers": look_markers(book, faces, setup), "panel_people": panel_people}


def look_markers(book: Path, faces: list[str], setup):
    from studio import cast_refs
    return cast_refs.look_markers(book, faces, setup)


def verdict_for(book: Path, shot, setup, reads: list[pc.Seen], panel_people: int | None = None) -> dict:
    rows = judged_row(book, shot, setup, panel_people)
    got = tc.take_faults(reads, **rows)
    whole = tc.busiest(reads)
    return {"passed": not got, "faults": got, "look_log": tc.look_log(reads, rows["markers"]), "people": whole.people,
            "lookalikes": whole.lookalikes, "hour": whole.hour, "text": whole.text,
            "panel_people": panel_people, "shape_advisory": pc.shape_read(reads)[1]}


def panel_people_of(book: Path, number: int, shot_index: int) -> int | None:
    """The people the shot's own panel read held (storyboard/panel_content.json),
    or None when no row exists: the take is then judged on the plan's count."""
    path = episode_home.home(book, number) / "storyboard" / "panel_content.json"
    rows = episode_home.read_json(path) if path.exists() else []
    return next((r.get("people") for r in rows if r.get("shot") == shot_index), None)


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
    from studio import cast_refs
    setup = ep.setups[shot.setup]
    row = verdict_for(book, shot, setup, reads, panel_people_of(book, ep.number, shot.index))
    staged = cast_refs.who_marks(book, list(shot.faces or []), setup)
    return with_twins(row, twin_faults_for(shot, reads, work, video.stem) + who_faults_for(shot, reads, work, video.stem, staged))


def judges_sha8() -> str:
    """The judging code's fingerprint (line endings normalised): the pin test's half of the key."""
    import hashlib
    body = b"".join((ROOT / rel).read_bytes().replace(b"\r\n", b"\n") for rel in JUDGES)
    return hashlib.sha256(body).hexdigest()[:8]


def engine_sha8() -> str:
    """The reading engine as the VL text cache keys it (workflow JSON, inject map, TEXT_CACHE_VERSION);
    'absent' when the workflow is not on disk -- the reads then fail unread and nothing is kept."""
    try:
        return comfy.text_key(WORKFLOW, {})[:8]
    except FileNotFoundError:
        return "absent"


def words_sha8(row: dict, seconds: float) -> str:
    """The judged rows, the asks, the engine, the frames sampled: everything but the bytes that makes a verdict."""
    import hashlib
    import json
    body = json.dumps({"row": row, "ask": pc.ASK, "twin_ask": pc.TWIN_ASK, "who_ask": fw.ASK, "workflow": WORKFLOW,
                       "engine": engine_sha8(), "samples": SAMPLES, "seconds": seconds},
                      sort_keys=True, default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]


def verdict_key(video: Path, row: dict, seconds: float) -> dict:
    import hashlib
    return {"take_sha8": hashlib.sha256(Path(video).read_bytes()).hexdigest()[:8],
            "judged_sha8": words_sha8(row, seconds), "gate_version": GATE_VERSION}


def take_key(book: Path, ep, record: dict, take_dir: Path) -> dict:
    """The key of the verdict `judge_take` would write for this take now."""
    shot = ep.shot(record["shots"][0])
    from studio import cast_refs
    setup = ep.setups[shot.setup]
    row = {**judged_row(book, shot, setup, panel_people_of(book, ep.number, shot.index)),
           "who": cast_refs.who_marks(book, list(shot.faces or []), setup)}
    return verdict_key(take_dir / f"T{record['index']:02d}.mp4", row, float(record.get("seconds") or 4.0))


def keyed(row: dict, key: dict) -> dict:
    """A verdict carrying its key; an unread one carries none, so the next pass reads it again."""
    if any(str(f).startswith("unread") for f in row.get("faults") or []):
        return row
    return {**row, **key}


def cached(path: Path, key: dict) -> dict | None:
    """The verdict on disk when it was judged under exactly this key, or None."""
    doc = episode_home.read_json(path) if Path(path).exists() else None
    return doc if isinstance(doc, dict) and all(doc.get(k) == v for k, v in key.items()) else None


def written(take_dir: Path, index: int, row: dict) -> dict:
    """The verdict written (a hit too: the ladder asks for a fresh verdict file) and its line printed."""
    episode_home.write_json(take_dir / f"T{index:02d}.content.json", row)
    print(f"  {'ok  ' if row['passed'] else 'FAIL'} T{index:02d}  {'; '.join(row['faults'])}", flush=True)
    return row


def judge_all(book: Path, ep, records: list[dict], take_dir: Path, work: Path) -> list[int]:
    """Every take's verdict, the hits first; the misses in ONE model batch, entered only for a miss."""
    keys = {r["index"]: take_key(book, ep, r, take_dir) for r in records}
    rows = {i: written(take_dir, i, hit) for i, k in keys.items()
            if (hit := cached(take_dir / f"T{i:02d}.content.json", k)) is not None}
    print(f"  {len(rows)}/{len(records)} content verdicts cached (bytes, judged rows and gate unchanged)", flush=True)
    if misses := [r for r in records if r["index"] not in rows]:
        with comfy.model_kept():        # the VL model loaded once for the batch (speed plan #6)
            for record in misses:
                i = record["index"]
                rows[i] = written(take_dir, i, keyed(judge_take(book, ep, record, take_dir, work), keys[i]))
    return [r["index"] for r in records if not rows[r["index"]]["passed"]]


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
    failed = judge_all(book, ep, records, take_dir, work)
    print(f"\n{len(records) - len(failed)}/{len(records)} takes clean on content; failing {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    plain = [a for a in sys.argv[1:] if not a.startswith("--")]
    raise SystemExit(main(plain[0], episode_arg(sys.argv), [int(a) for a in plain[2:] if a.isdigit()]))
