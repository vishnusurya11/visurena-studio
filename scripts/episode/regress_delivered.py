#!/usr/bin/env python
"""The deciders replayed on a DELIVERED episode, diffed against its committed baseline (deadline retro item 6).

    uv run --no-sync python scripts/episode/regress_delivered.py                      # every fixture; exit 1 on a diff
    uv run --no-sync python scripts/episode/regress_delivered.py --touched            # only when a GUARDED path moved
    uv run --no-sync python scripts/episode/regress_delivered.py --rebaseline ep01 "<why>"   # its own commit
    uv run --no-sync python scripts/episode/regress_delivered.py --freeze <codex_id> <n>     # copy the records

A delivered episode is a frozen input set: its records (tests/fixtures/delivered/<ep>/, copies of the named
record files) and stat.json (each file's size and mtime, each kept take's sha8, the signed eye's
fingerprint; never a video).  The replay builds a stand-in of the episode in a temp folder -- the records,
and a placeholder of each take's recorded size and mtime -- and asks package A's decider library
(repair_dry_check: takes_r2v.wants_render over take_currency.held_in, take_overlap.early_cures,
take_ladder.route -> batch_for, take_ladder.pick_best, take_currency.frozen_in) what every take would do:
`bare` with no repair window (the deciders alone), `held` under the repair that governs (what a launch
does).  Each cell is `render`, `keep`, `retake` or `swap` with its why.  Any cell that differs from
actions.baseline.json fails, by take and column.  A re-baseline states its reason and the rows it moved,
and is refused while a guarded path is uncommitted: the change commits first, the baseline after it.

The card words are the delivered cards' (takes/r2v/shots.json): the fixture holds no book refs and no
pictures, so a prompt-word change is replayed by rewording the delivered words (`reword`), never by a
rebuild; pictures are not compared.  The live rebuild on the real book is the dry check's, at launch.

INCIDENT 3 (2026-10-19 11:18 PDT): P03 reworded two sentences of the take prompts and all 28 of Jekyll HEL
ep01's delivered takes read stale; the repair launch was found by launching.  This runs in seconds on the
CPU before the commit (tests/test_regress_delivered_matches_baseline.py, the default run)."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.episode import repair_dry_check as dry  # noqa: E402
from studio import take_currency as tc  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "delivered"
BASELINE = "actions.baseline.json"
STAT = "stat.json"
ROOM = Path("takes") / "r2v"
HOME_RECORDS = ("manifest.json", "repair.jsonl", "attempts.json", "clock.jsonl", "clock_reset.json",
                "budget.jsonl", "timing.jsonl")
ROOM_RECORDS = ("shots.json", "ladder.json")
ROOM_GLOBS = ("T[0-9][0-9].graph.json", "T[0-9][0-9].dq.json", "eye_*.json")
KEPT = "T[0-9][0-9].mp4"
DRAWS = "attempts/T[0-9][0-9]_fail*.mp4"
COLUMNS = ("bare", "held")

GUARDED = ("studio/episode_ref_official.py", "studio/house_style.py", "scripts/episode/takes_r2v.py",
           "studio/take_currency.py", "studio/take_ladder.py", "studio/take_overlap.py",
           "studio/repair_clock.py", "scripts/episode/repair_dry_check.py", "scripts/episode/regress_delivered.py")
"""The paths whose commit owes the replay: the prompt words, take_currency, the ladder and the deciders."""


# ---- the frozen records (a copy, once per delivered episode) -------------------------------------

def record_names(src: Path) -> list[str]:
    """The record files the deciders read, as posix paths relative to the episode; only what exists."""
    room = Path(src) / ROOM
    named = [n for n in HOME_RECORDS if (Path(src) / n).is_file()]
    named += [(ROOM / n).as_posix() for n in ROOM_RECORDS if (room / n).is_file()]
    return named + sorted((ROOM / p.name).as_posix() for g in ROOM_GLOBS for p in room.glob(g))


def copy_record(src: Path, dest: Path) -> None:
    """One JSON record copied as text with LF endings: a record, never a take's bytes."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def file_row(path: Path) -> dict:
    st = Path(path).stat()
    return {"size": st.st_size, "mtime_ns": st.st_mtime_ns}


def video_rows(src: Path) -> dict:
    """The kept takes (size, mtime, sha8), the archived draws (size, mtime) and the signed eye's
    fingerprint (eye_verdict.fingerprint over the kept takes' bytes), each file read once."""
    room, eye, kept = Path(src) / ROOM, hashlib.sha256(), {}
    for take in sorted(room.glob(KEPT)):
        body = take.read_bytes()
        eye.update(body)
        kept[(ROOM / take.name).as_posix()] = {**file_row(take), "sha8": hashlib.sha256(body).hexdigest()[:8]}
    draws = {(ROOM / p.relative_to(room)).as_posix(): file_row(p) for p in sorted(room.glob(DRAWS))}
    return {"kept": kept, "draws": draws, "eye": eye.hexdigest()[:8]}


def freeze(src: Path, dest: Path) -> dict:
    """Copy a delivered episode's records into `dest` and write stat.json beside them; no video."""
    names = record_names(src)
    for rel in names:
        copy_record(Path(src) / rel, Path(dest) / rel)
    doc = {"files": {rel: file_row(Path(src) / rel) for rel in names}, **video_rows(src)}
    write_json(Path(dest) / STAT, doc)
    return doc


def write_json(path: Path, doc) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")


# ---- the stand-in episode ----------------------------------------------------------------------------

def stand_in(fixture: Path) -> tuple[Path, dict]:
    """(a stand-in episode in a fresh temp folder, stat.json): the records with their recorded mtimes, a
    placeholder of each take's and draw's recorded size and mtime.  It writes nowhere else."""
    doc = json.loads((Path(fixture) / STAT).read_text(encoding="utf-8"))
    home = Path(tempfile.mkdtemp(prefix="regress_delivered_")) / Path(fixture).name
    for rel, row in doc["files"].items():
        copy_record(Path(fixture) / rel, home / rel)
        os.utime(home / rel, ns=(row["mtime_ns"], row["mtime_ns"]))
    for rel, row in {**doc["kept"], **doc["draws"]}.items():
        placeholder(home / rel, row)
    return home, doc


def placeholder(path: Path, row: dict) -> None:
    """An empty file grown to the recorded size (a draw is matched to its dq row by size), at its mtime."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    os.truncate(path, row["size"])
    os.utime(path, ns=(row["mtime_ns"], row["mtime_ns"]))


@contextlib.contextmanager
def recorded_bytes(home: Path, doc: dict):
    """While open, a stand-in take hashes to its recorded sha8 and the kept set to the signed eye's
    fingerprint; the three seams the deciders hash through are put back on the way out."""
    from scripts.episode import take_dq
    from studio import eye_verdict
    sha = {(Path(home) / rel).resolve(): row["sha8"] for rel, row in doc["kept"].items()}
    kept, seams = set(sha), (tc.sha8_of, take_dq.take_sha8, eye_verdict.fingerprint)
    tc.sha8_of = take_dq.take_sha8 = lambda p: sha.get(Path(p).resolve()) or seams[0](p)
    eye_verdict.fingerprint = lambda paths: doc["eye"] if {Path(p).resolve() for p in paths} == kept \
        else seams[2](paths)
    try:
        yield
    finally:
        tc.sha8_of, take_dq.take_sha8, eye_verdict.fingerprint = seams


# ---- the action table ---------------------------------------------------------------------------------

def cards_of(home: Path, reword=None) -> list[dict]:
    """The delivered cards (takes/r2v/shots.json), their words passed through `reword` when given."""
    rows = json.loads((Path(home) / ROOM / "shots.json").read_text(encoding="utf-8"))
    return [{**c, "prompt": reword(c.get("prompt") or "")} if reword else c for c in rows]


def state_of(c: dict, home: Path, window: dict | None, records: dict) -> tuple[str, str]:
    """(current | frozen | render, why): the render pass's own question (dry.take_state), said short."""
    take, canvas = Path(home) / ROOM / f"T{int(c['index']):02d}.mp4", (c["width"], c["height"])
    state, _ = dry.take_state(c, take, home, window, None, canvas, records)
    stale = tc.stale_why(c.get("prompt") or "", take, None, canvas)
    if state == "render":
        return state, dry.render_why(c, take, records, stale)
    if state == "frozen":
        return state, f"frozen {tc.frozen_in(window, take, home)}, stale by {stale}"
    return state, "current"


def action_of(i: int, state: tuple[str, str], would: dict[str, set[int]]) -> str:
    """The take's action: render, else a retake (early round, then the ladder), else a swap, else keep."""
    if i in would[dry.RENDER_PASS]:
        return f"render: {state[1]}"
    for site, word in ((dry.EARLY, "retake: early round"), (dry.RUNG, "retake: ladder"), (dry.SWAP, "swap")):
        if i in would[site]:
            return f"{word} ({site.split(' (')[1]}"
    return f"keep: {state[1]}" + ("; the freeze does not hold it" if i in would[dry.FREEZE] else "")


def column(home: Path, cards: list[dict], window: dict | None) -> dict[str, str]:
    """T<nn> -> its action under `window`, every decider asked once over the whole room."""
    records = {int(c["index"]): c for c in cards}
    states = {int(c["index"]): state_of(c, home, window, records) for c in cards}
    would = dry.would_render(home, window, states)
    return {f"T{i:02d}": action_of(i, states[i], would) for i in sorted(states)}


def replay(home: Path, doc: dict, reword=None) -> dict[str, dict[str, str]]:
    """T<nn> -> {bare, held}: the table for a stand-in episode, under its recorded bytes."""
    with recorded_bytes(home, doc):
        cards = cards_of(home, reword)
        cols = {"bare": column(home, cards, None), "held": column(home, cards, tc.governing(home))}
    return {take: {name: cols[name][take] for name in COLUMNS} for take in cols["bare"]}


def table(fixture: Path, reword=None) -> dict[str, dict[str, str]]:
    """The action table of one delivered fixture; the stand-in is removed after."""
    home, doc = stand_in(fixture)
    try:
        return replay(home, doc, reword)
    finally:
        shutil.rmtree(home.parent, ignore_errors=True)


# ---- the baseline --------------------------------------------------------------------------------------

def diff(base: dict, now: dict) -> list[str]:
    """One line per moved cell, naming its take and column: `T00 bare: keep: current -> render: ...`."""
    out = []
    for take in sorted(set(base) | set(now)):
        if take not in base or take not in now:
            out.append(f"{take}: {'not in the baseline' if take not in base else 'gone from the table'}")
            continue
        out += [f"{take} {c}: {base[take].get(c)} -> {now[take].get(c)}" for c in COLUMNS
                if base[take].get(c) != now[take].get(c)]
    return out


def read_baseline(fixture: Path) -> dict:
    return json.loads((Path(fixture) / BASELINE).read_text(encoding="utf-8"))


def rebaseline(fixture: Path, reason: str) -> list[str]:
    """Write today's table as the baseline with its reason and the rows it moved; refused without a
    reason, and while a guarded path is uncommitted (the change commits first, the baseline after it)."""
    if not reason.strip():
        raise SystemExit("a re-baseline states its reason (one line: why the deciders moved these takes)")
    if moving := touched(changed_paths()):
        raise SystemExit(f"commit the change first, then re-baseline in its own commit: {', '.join(moving)}")
    now, path = table(fixture), Path(fixture) / BASELINE
    moved = diff(read_baseline(fixture)["rows"], now) if path.exists() else []
    write_json(path, {"reason": reason.strip(), "moved": moved, "rows": now})
    return moved


# ---- the wiring ------------------------------------------------------------------------------------------

def touched(paths: list[str]) -> list[str]:
    """The guarded paths among `paths`: a commit touching any of them owes the replay."""
    said = {Path(p).as_posix() for p in paths}
    return sorted(p for p in GUARDED if p in said)


def changed_paths() -> list[str]:
    """Every path that differs from HEAD, staged or not (git diff --name-only HEAD)."""
    out = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def fixtures() -> list[Path]:
    return sorted(p.parent for p in Path(FIXTURES).glob(f"*/{BASELINE}"))


def check(found: list[Path]) -> list[str]:
    """Every fixture's moved cells, each line led by its episode."""
    return [f"{fixture.name} {line}" for fixture in found for line in diff(read_baseline(fixture)["rows"],
                                                                            table(fixture))]


def main(argv: list[str]) -> int:
    if argv[:1] == ["--freeze"]:
        from studio import episode_home
        number = int(argv[2])
        doc = freeze(episode_home.home(episode_home.book_dir(argv[1]), number), Path(FIXTURES) / f"ep{number:02d}")
        print(f"froze {len(doc['files'])} records, {len(doc['kept'])} takes, {len(doc['draws'])} draws")
        return 0
    if argv[:1] == ["--rebaseline"]:
        moved = rebaseline(Path(FIXTURES) / argv[1], " ".join(argv[2:]))
        print(f"re-baselined {argv[1]}: {len(moved)} cell(s) moved" + "".join(f"\n  {m}" for m in moved))
        return 0
    if argv[:1] == ["--touched"] and not (moving := touched(changed_paths())):
        print("no guarded path moved: the delivered replay is not owed")
        return 0
    moved = check(fixtures())
    print("\n".join(moved) if moved else f"delivered replay: {len(fixtures())} episode(s) match their baseline")
    return 1 if moved else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
